"""
Tests for TimelineTree.from_worktree method.

This module tests the ability to load timeline trees from existing git worktrees.
"""

import pytest
import shutil
import tempfile
import logging
from pathlib import Path
from datetime import datetime

from dulwich.repo import Repo
from dulwich import porcelain

from yacl.models.timeline import TimelineTree, TimelineStatus, Checkpoint, Timeline
from yacl.models.timeline import (
    TimelineRepositoryError, 
    TimelineValidationError, 
    TimelineBranchError, 
    TimelineCheckpointError
)
from yacl.models.game_type import GameType


# Enable debug logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def game_type():
    """Create a test game type."""
    return GameType(
        name="test_game",
        display_name="Test Game",
        repository="test/repo",
        executable_name={"windows": "test.exe", "linux": "test"}
    )


@pytest.fixture
def git_repo_with_worktrees(temp_dir):
    """Create a git repository with worktrees similar to the POC."""
    base_path = temp_dir
    
    # Create savegame directories and files
    savegame01_path = base_path / "savegame01"
    savegame01_path.mkdir(exist_ok=True)
    (savegame01_path / "data01-01.txt").write_text("Initial data for savegame01\n")
    
    savegame02_path = base_path / "savegame02"
    savegame02_path.mkdir(exist_ok=True)
    (savegame02_path / "data02-01.txt").write_text("Initial data for savegame02\n")
    
    # Create main repository
    repo = porcelain.init(str(base_path))
    
    # Create initial commit
    readme_path = base_path / "README.md"
    with open(readme_path, "w") as f:
        f.write("# Test Repository\n\nThis is a test repository.\n")
    
    worktree = repo.get_worktree()
    worktree.stage(["README.md"])
    worktree.commit(message=b"Initial commit")
    
    # Create worktree for savegame01
    _create_worktree_and_commit(repo, savegame01_path, "savegame01-main", ["data01-01.txt"])
    
    # Create worktree for savegame02
    _create_worktree_and_commit(repo, savegame02_path, "savegame02-main", ["data02-01.txt"])
    
    # Add more commits to savegame01
    _add_file_and_commit(savegame01_path, "data01-02.txt", "Second data file\n", "Add data01-02.txt")
    
    # Add more commits to savegame02
    _add_file_and_commit(savegame02_path, "data02-02.txt", "Second data file\n", "Add data02-02.txt")
    _add_file_and_commit(savegame02_path, "data02-03.txt", "Third data file\n", "Add data02-03.txt")
    
    # Create a branch in savegame01
    _create_branch_and_commit(savegame01_path, "savegame01-branch01", "data01-03.txt", "Branch data\n", "Add branch data")
    
    # Switch back to main branch for savegame01
    wt_repo = Repo(str(savegame01_path))
    porcelain.checkout(wt_repo, "savegame01-main")
    
    return {
        "base_path": base_path,
        "repo": repo,
        "savegame01_path": savegame01_path,
        "savegame02_path": savegame02_path
    }


def _create_worktree_and_commit(repo, worktree_path, branch_name, files_to_add):
    """Helper function to create worktree and commit files."""
    # Temporarily move existing directory
    temp_dir = None
    if worktree_path.exists():
        temp_dir = Path(tempfile.mkdtemp())
        for item in worktree_path.iterdir():
            shutil.move(str(item), str(temp_dir))
        worktree_path.rmdir()
    
    # Create worktree
    wt_repo_path = porcelain.worktree_add(
        repo=repo.path,
        path=str(worktree_path),
        branch=branch_name
    )
    
    # Move files back
    if temp_dir:
        for item in temp_dir.iterdir():
            shutil.move(str(item), str(worktree_path))
        temp_dir.rmdir()
    
    # Stage and commit files
    wt_repo = Repo(wt_repo_path)
    worktree = wt_repo.get_worktree()
    
    if files_to_add:
        worktree.stage(files_to_add)
        worktree.commit(message=f"Initial commit for {branch_name}".encode())


def _add_file_and_commit(worktree_path, filename, content, commit_message):
    """Helper function to add file and commit."""
    file_path = worktree_path / filename
    with open(file_path, 'w') as f:
        f.write(content)
    
    wt_repo = Repo(str(worktree_path))
    worktree = wt_repo.get_worktree()
    worktree.stage([filename])
    worktree.commit(message=commit_message.encode())


def _create_branch_and_commit(worktree_path, branch_name, filename, content, commit_message):
    """Helper function to create branch and commit."""
    wt_repo = Repo(str(worktree_path))
    
    # Get current commit
    current_commit = wt_repo.head()
    
    # Create new branch
    new_branch_ref = f"refs/heads/{branch_name}".encode()
    wt_repo.refs[new_branch_ref] = current_commit
    
    # Checkout new branch
    porcelain.checkout(wt_repo, branch_name)
    
    # Add file and commit
    _add_file_and_commit(worktree_path, filename, content, commit_message)


class TestTimelineFromWorktree:
    """Test cases for TimelineTree.from_worktree method."""
    
    def test_from_worktree_basic_functionality(self, git_repo_with_worktrees, game_type):
        """Test basic functionality of from_worktree method."""
        savegame01_path = git_repo_with_worktrees["savegame01_path"]
        
        # Load timeline from worktree
        timeline = TimelineTree.from_worktree(savegame01_path, game_type)
        
        # Verify basic properties
        assert timeline.name == "savegame01"
        assert timeline.game_type == game_type
        assert timeline.save_path == savegame01_path
        assert timeline.worktree_path == savegame01_path
        assert timeline.status == TimelineStatus.ACTIVE
        
        # Verify main branch
        assert timeline.main_branch.name == "savegame01-main"
        assert timeline.main_branch.is_main is True
        assert len(timeline.main_branch.checkpoints) > 0
        
        # Verify branches
        assert "savegame01-main" in timeline.branches
        assert "savegame01-branch01" in timeline.branches
        assert len(timeline.branches) == 2
        
        # Verify current checkpoint
        assert timeline.current_checkpoint is not None
        assert isinstance(timeline.current_checkpoint, Checkpoint)
    
    def test_from_worktree_multiple_branches(self, git_repo_with_worktrees, game_type):
        """Test loading timeline with multiple branches."""
        savegame01_path = git_repo_with_worktrees["savegame01_path"]
        
        timeline = TimelineTree.from_worktree(savegame01_path, game_type)
        
        # Check that both branches are loaded
        main_branch = timeline.branches["savegame01-main"]
        branch01 = timeline.branches["savegame01-branch01"]
        
        # Main branch should have more commits (initial + data01-02.txt)
        assert len(main_branch.checkpoints) >= 2
        
        # Branch should have at least one commit
        assert len(branch01.checkpoints) >= 1
        
        # Verify branch properties
        assert main_branch.is_main is True
        assert branch01.is_main is False
    
    def test_from_worktree_current_branch_detection(self, git_repo_with_worktrees, game_type):
        """Test that current branch is correctly detected."""
        savegame01_path = git_repo_with_worktrees["savegame01_path"]
        
        timeline = TimelineTree.from_worktree(savegame01_path, game_type)
        
        # Should be on main branch (we switched back in fixture)
        assert timeline.current_branch.name == "savegame01-main"
        assert timeline.current_branch == timeline.main_branch
    
    def test_from_worktree_checkpoint_loading(self, git_repo_with_worktrees, game_type):
        """Test that checkpoints are properly loaded."""
        savegame02_path = git_repo_with_worktrees["savegame02_path"]
        
        timeline = TimelineTree.from_worktree(savegame02_path, game_type)
        
        main_branch = timeline.main_branch
        
        # Should have multiple checkpoints (initial + data02-02.txt + data02-03.txt)
        assert len(main_branch.checkpoints) >= 3
        
        # Verify checkpoint properties
        for checkpoint in main_branch.checkpoints.values():
            assert isinstance(checkpoint, Checkpoint)
            assert checkpoint.commit_hash
            assert isinstance(checkpoint.timestamp, datetime)
            assert checkpoint.message
            assert checkpoint.author
    
    def test_from_worktree_invalid_path(self, game_type):
        """Test error handling for invalid worktree path."""
        invalid_path = Path("/nonexistent/path")
        
        with pytest.raises(TimelineRepositoryError):
            TimelineTree.from_worktree(invalid_path, game_type)
    
    def test_from_worktree_missing_main_branch(self, temp_dir, game_type):
        """Test error handling when main branch doesn't exist."""
        # Create a simple repo without the expected main branch
        repo_path = temp_dir / "test_repo"
        repo_path.mkdir()
        
        repo = porcelain.init(str(repo_path))
        readme_path = repo_path / "README.md"
        readme_path.write_text("Test")
        
        worktree = repo.get_worktree()
        worktree.stage(["README.md"])
        worktree.commit(message=b"Initial commit")
        
        # Try to load timeline - should fail because there's no "test_repo-main" branch
        with pytest.raises(TimelineValidationError):
            TimelineTree.from_worktree(repo_path, game_type)
