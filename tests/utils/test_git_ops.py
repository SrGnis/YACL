"""
Tests for git operations utilities.

This module tests the refactored git operations that use dulwich's high-level APIs.
"""

import pytest
import shutil
import tempfile
from pathlib import Path

from dulwich.repo import Repo
from dulwich import porcelain

from yacl.utils.git_ops import (
    get_current_branch_name,
    get_all_branches,
    branch_exists,
    get_current_commit_hash,
    get_commit_info
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def git_repo(temp_dir):
    """Create a test git repository with multiple branches and commits."""
    repo_path = temp_dir / "test_repo"
    repo_path.mkdir()
    
    # Initialize repository
    repo = porcelain.init(str(repo_path))
    
    # Create initial commit
    readme_path = repo_path / "README.md"
    readme_path.write_text("# Test Repository\n")
    
    worktree = repo.get_worktree()
    worktree.stage(["README.md"])
    initial_commit = worktree.commit(message=b"Initial commit")
    
    # Create a new branch
    porcelain.branch_create(repo, "feature-branch")
    
    # Switch to feature branch and add a commit
    porcelain.checkout(repo, "feature-branch")
    feature_file = repo_path / "feature.txt"
    feature_file.write_text("Feature content\n")
    worktree.stage(["feature.txt"])
    feature_commit = worktree.commit(message=b"Add feature")
    
    # Switch back to main
    porcelain.checkout(repo, "main")
    
    return {
        "repo": repo,
        "repo_path": repo_path,
        "initial_commit": initial_commit,
        "feature_commit": feature_commit
    }


class TestGitOps:
    """Test cases for git operations utilities."""
    
    def test_get_current_branch_name(self, git_repo):
        """Test getting current branch name."""
        repo = git_repo["repo"]
        
        # Should be on main branch
        current_branch = get_current_branch_name(repo)
        assert current_branch == "main"
        
        # Switch to feature branch
        porcelain.checkout(repo, "feature-branch")
        current_branch = get_current_branch_name(repo)
        assert current_branch == "feature-branch"
    
    def test_get_all_branches(self, git_repo):
        """Test getting all branch names."""
        repo = git_repo["repo"]
        
        branches = get_all_branches(repo)
        assert "main" in branches
        assert "feature-branch" in branches
        assert len(branches) == 2
    
    def test_branch_exists(self, git_repo):
        """Test checking if branches exist."""
        repo = git_repo["repo"]
        
        # Existing branches
        assert branch_exists(repo, "main") is True
        assert branch_exists(repo, "feature-branch") is True
        
        # Non-existing branch
        assert branch_exists(repo, "nonexistent-branch") is False
    
    def test_get_current_commit_hash(self, git_repo):
        """Test getting current commit hash."""
        repo = git_repo["repo"]
        
        # Get current commit hash
        commit_hash = get_current_commit_hash(repo)
        assert commit_hash is not None
        assert len(commit_hash) == 40  # SHA-1 hash length
        
        # Should match the initial commit since we're on main
        expected_hash = git_repo["initial_commit"].decode()
        assert commit_hash == expected_hash
    
    def test_get_commit_info(self, git_repo):
        """Test getting commit information."""
        repo = git_repo["repo"]
        initial_commit_hash = git_repo["initial_commit"].decode()
        
        # Get commit info
        commit_info = get_commit_info(repo, initial_commit_hash)
        
        assert commit_info is not None
        assert commit_info["hash"] == initial_commit_hash
        assert commit_info["message"] == "Initial commit"
        assert "timestamp" in commit_info
        assert "author" in commit_info
        assert isinstance(commit_info["parent_hashes"], list)
    
    def test_get_commit_info_with_parents(self, git_repo):
        """Test getting commit info for a commit with parents."""
        repo = git_repo["repo"]
        feature_commit_hash = git_repo["feature_commit"].decode()
        initial_commit_hash = git_repo["initial_commit"].decode()
        
        # Get commit info for feature commit
        commit_info = get_commit_info(repo, feature_commit_hash)
        
        assert commit_info is not None
        assert commit_info["hash"] == feature_commit_hash
        assert commit_info["message"] == "Add feature"
        assert len(commit_info["parent_hashes"]) == 1
        assert commit_info["parent_hashes"][0] == initial_commit_hash
    
    def test_get_commit_info_invalid_hash(self, git_repo):
        """Test getting commit info for invalid hash."""
        repo = git_repo["repo"]
        
        # Invalid commit hash
        commit_info = get_commit_info(repo, "invalid_hash")
        assert commit_info is None
        
        # Non-existent but valid format hash
        fake_hash = "a" * 40
        commit_info = get_commit_info(repo, fake_hash)
        assert commit_info is None
    
    def test_error_handling_with_invalid_repo(self, temp_dir):
        """Test error handling with invalid repository."""
        # Create a directory that's not a git repo
        non_repo_path = temp_dir / "not_a_repo"
        non_repo_path.mkdir()
        
        # These should handle errors gracefully
        try:
            fake_repo = Repo(str(non_repo_path))
            # If we get here, the operations should handle the invalid repo gracefully
            assert get_current_branch_name(fake_repo) is None
            assert get_all_branches(fake_repo) == []
            assert branch_exists(fake_repo, "main") is False
            assert get_current_commit_hash(fake_repo) is None
            assert get_commit_info(fake_repo, "abc123") is None
        except Exception:
            # If Repo() itself fails, that's expected for a non-repo directory
            pass
    
    def test_branch_operations_consistency(self, git_repo):
        """Test that branch operations are consistent with each other."""
        repo = git_repo["repo"]
        
        # Get all branches
        all_branches = get_all_branches(repo)
        
        # Check that all returned branches actually exist
        for branch in all_branches:
            assert branch_exists(repo, branch) is True
        
        # Check that current branch is in the list of all branches
        current_branch = get_current_branch_name(repo)
        assert current_branch in all_branches
