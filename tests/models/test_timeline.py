"""
Tests for timeline data models.
"""

import pytest
from datetime import datetime
from pathlib import Path

from yacl.models.timeline import (
    Timeline, Checkpoint, TimelineBranch, TimelineStatus,
    TimelineError, TimelineValidationError, TimelineRepositoryError,
    TimelineCheckpointError, TimelineBranchError, TimelineFileError
)
from yacl.models.game_type import GameType


class TestCheckpoint:
    """Tests for the Checkpoint class."""
    
    def test_checkpoint_creation(self):
        """Test creating a checkpoint with valid data."""
        checkpoint = Checkpoint(
            commit_hash="abc123",
            timestamp=datetime.now(),
            message="Test checkpoint",
            author="Test Author"
        )
        
        assert checkpoint.commit_hash == "abc123"
        assert checkpoint.message == "Test checkpoint"
        assert checkpoint.author == "Test Author"
        assert isinstance(checkpoint.timestamp, datetime)
        assert checkpoint.parent_hashes == []
    
    def test_checkpoint_with_parent_hashes(self):
        """Test creating a checkpoint with parent hashes."""
        parent_hashes = ["parent1", "parent2"]
        checkpoint = Checkpoint(
            commit_hash="abc123",
            timestamp=datetime.now(),
            message="Test checkpoint",
            author="Test Author",
            parent_hashes=parent_hashes
        )

        assert checkpoint.parent_hashes == parent_hashes
    
    def test_checkpoint_string_representation(self):
        """Test checkpoint string representation."""
        checkpoint = Checkpoint(
            commit_hash="abc123def456",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            message="Test checkpoint",
            author="Test Author"
        )
        
        str_repr = str(checkpoint)
        assert "abc123de" in str_repr  # First 8 chars of hash
        assert "Test checkpoint" in str_repr


class TestTimelineBranch:
    """Tests for the TimelineBranch class."""
    
    def test_branch_creation(self):
        """Test creating a timeline branch."""
        branch = TimelineBranch(
            name="main",
            checkpoints={},
            head_commit=None,
            is_main=True
        )
        
        assert branch.name == "main"
        assert branch.checkpoints == {}
        assert branch.head_commit is None
        assert branch.is_main is True
        assert isinstance(branch.created_at, datetime)
    
    def test_add_checkpoint(self, sample_checkpoint):
        """Test adding a checkpoint to a branch."""
        branch = TimelineBranch(
            name="test-branch",
            checkpoints={},
            head_commit=None
        )
        
        branch.add_checkpoint(sample_checkpoint)
        
        assert sample_checkpoint.commit_hash in branch.checkpoints
        assert branch.checkpoints[sample_checkpoint.commit_hash] == sample_checkpoint
        assert branch.head_commit == sample_checkpoint.commit_hash
    
    def test_get_latest_checkpoint(self, sample_checkpoint):
        """Test getting the latest checkpoint from a branch."""
        branch = TimelineBranch(
            name="test-branch",
            checkpoints={sample_checkpoint.commit_hash: sample_checkpoint},
            head_commit=sample_checkpoint.commit_hash
        )
        
        latest = branch.get_latest_checkpoint()
        assert latest == sample_checkpoint
    
    def test_get_latest_checkpoint_empty_branch(self):
        """Test getting latest checkpoint from empty branch."""
        branch = TimelineBranch(
            name="empty-branch",
            checkpoints={},
            head_commit=None
        )
        
        latest = branch.get_latest_checkpoint()
        assert latest is None
    
    def test_get_checkpoint_count(self, sample_checkpoint):
        """Test getting checkpoint count."""
        branch = TimelineBranch(
            name="test-branch",
            checkpoints={sample_checkpoint.commit_hash: sample_checkpoint},
            head_commit=sample_checkpoint.commit_hash
        )
        
        count = branch.get_checkpoint_count()
        assert count == 1


class TestTimeline:
    """Tests for the Timeline class."""
    
    def test_timeline_creation(self, temp_dir, sample_game_type, sample_timeline_branch, sample_checkpoint):
        """Test creating a timeline with valid data."""
        save_path = temp_dir / "save"
        save_path.mkdir()
        worktree_path = temp_dir / "worktree"
        worktree_path.mkdir()
        repo_path = temp_dir / "repo"
        repo_path.mkdir()
        
        timeline = Timeline(
            name="test_timeline",
            game_type=sample_game_type,
            save_path=save_path,
            worktree_path=worktree_path,
            repository_path=repo_path,
            main_branch=sample_timeline_branch,
            current_branch=sample_timeline_branch,
            current_checkpoint=sample_checkpoint,
            status=TimelineStatus.ACTIVE
        )
        
        assert timeline.name == "test_timeline"
        assert timeline.game_type == sample_game_type
        assert timeline.save_path == save_path
        assert timeline.worktree_path == worktree_path
        assert timeline.repository_path == repo_path
        assert timeline.main_branch == sample_timeline_branch
        assert timeline.current_branch == sample_timeline_branch
        assert timeline.current_checkpoint == sample_checkpoint
        assert timeline.status == TimelineStatus.ACTIVE
        assert isinstance(timeline.created_at, datetime)
        assert isinstance(timeline.last_updated, datetime)
    
    def test_timeline_post_init(self, sample_timeline):
        """Test timeline post-initialization setup."""
        # Main branch should be in branches dict
        assert sample_timeline.main_branch.name in sample_timeline.branches
        assert sample_timeline.branches[sample_timeline.main_branch.name] == sample_timeline.main_branch
        
        # Main branch should be marked as main
        assert sample_timeline.main_branch.is_main is True
    
    def test_add_branch(self, sample_timeline):
        """Test adding a new branch to timeline."""
        new_branch = TimelineBranch(
            name="feature-branch",
            checkpoints={},
            head_commit=None
        )
        
        original_updated = sample_timeline.last_updated
        sample_timeline.add_branch(new_branch)
        
        assert "feature-branch" in sample_timeline.branches
        assert sample_timeline.branches["feature-branch"] == new_branch
        assert sample_timeline.last_updated > original_updated
    
    def test_switch_branch_success(self, sample_timeline, sample_checkpoint):
        """Test successfully switching to an existing branch."""
        # Add a new branch
        new_branch = TimelineBranch(
            name="feature-branch",
            checkpoints={sample_checkpoint.commit_hash: sample_checkpoint},
            head_commit=sample_checkpoint.commit_hash
        )
        sample_timeline.add_branch(new_branch)
        
        # Switch to the new branch
        result = sample_timeline.switch_branch("feature-branch")
        
        assert result is True
        assert sample_timeline.current_branch == new_branch
        assert sample_timeline.current_checkpoint == sample_checkpoint
    
    def test_switch_branch_nonexistent(self, sample_timeline):
        """Test switching to a non-existent branch."""
        result = sample_timeline.switch_branch("nonexistent-branch")
        
        assert result is False
        # Current branch should remain unchanged
        assert sample_timeline.current_branch == sample_timeline.main_branch
    
    def test_get_branch_names(self, sample_timeline):
        """Test getting list of branch names."""
        # Add additional branches
        sample_timeline.add_branch(TimelineBranch(name="branch1", checkpoints={}, head_commit=None))
        sample_timeline.add_branch(TimelineBranch(name="branch2", checkpoints={}, head_commit=None))
        
        branch_names = sample_timeline.get_branch_names()
        
        assert isinstance(branch_names, list)
        assert sample_timeline.main_branch.name in branch_names
        assert "branch1" in branch_names
        assert "branch2" in branch_names
        assert len(branch_names) == 3
    
    def test_get_main_branch_name(self, sample_timeline):
        """Test getting main branch name."""
        main_name = sample_timeline.get_main_branch_name()
        expected_name = f"{sample_timeline.name}-main"
        assert main_name == expected_name
    
    def test_timeline_string_representation(self, sample_timeline):
        """Test timeline string representation."""
        str_repr = str(sample_timeline)
        
        assert sample_timeline.name in str_repr
        assert str(len(sample_timeline.branches)) in str_repr
        assert sample_timeline.status.value in str_repr


class TestTimelineExceptions:
    """Tests for timeline exception classes."""
    
    def test_timeline_error(self):
        """Test TimelineError exception."""
        with pytest.raises(TimelineError) as exc_info:
            raise TimelineError("Test timeline error")
        
        assert str(exc_info.value) == "Test timeline error"
    
    def test_timeline_validation_error(self):
        """Test TimelineValidationError exception."""
        with pytest.raises(TimelineValidationError) as exc_info:
            raise TimelineValidationError("Test validation error")
        
        assert str(exc_info.value) == "Test validation error"
        assert isinstance(exc_info.value, TimelineError)
    
    def test_timeline_repository_error(self):
        """Test TimelineRepositoryError exception."""
        with pytest.raises(TimelineRepositoryError) as exc_info:
            raise TimelineRepositoryError("Test repository error")
        
        assert str(exc_info.value) == "Test repository error"
        assert isinstance(exc_info.value, TimelineError)
    
    def test_timeline_checkpoint_error(self):
        """Test TimelineCheckpointError exception."""
        with pytest.raises(TimelineCheckpointError) as exc_info:
            raise TimelineCheckpointError("Test checkpoint error")
        
        assert str(exc_info.value) == "Test checkpoint error"
        assert isinstance(exc_info.value, TimelineError)
    
    def test_timeline_branch_error(self):
        """Test TimelineBranchError exception."""
        with pytest.raises(TimelineBranchError) as exc_info:
            raise TimelineBranchError("Test branch error")
        
        assert str(exc_info.value) == "Test branch error"
        assert isinstance(exc_info.value, TimelineError)
    
    def test_timeline_file_error(self):
        """Test TimelineFileError exception."""
        with pytest.raises(TimelineFileError) as exc_info:
            raise TimelineFileError("Test file error")
        
        assert str(exc_info.value) == "Test file error"
        assert isinstance(exc_info.value, TimelineError)


class TestTimelineStatus:
    """Tests for TimelineStatus enum."""
    
    def test_timeline_status_values(self):
        """Test that all expected status values exist."""
        assert TimelineStatus.ACTIVE.value == "active"
        assert TimelineStatus.INACTIVE.value == "inactive"
        assert TimelineStatus.ERROR.value == "error"
        assert TimelineStatus.INITIALIZING.value == "initializing"
    
    def test_timeline_status_comparison(self):
        """Test timeline status comparison."""
        assert TimelineStatus.ACTIVE == TimelineStatus.ACTIVE
        assert TimelineStatus.ACTIVE != TimelineStatus.INACTIVE
