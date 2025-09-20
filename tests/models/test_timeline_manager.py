"""
Tests for timeline manager.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from yacl.models.timeline_manager import TimelineManager
from yacl.models.timeline import (
    Timeline, Checkpoint, TimelineBranch, TimelineStatus,
    TimelineError, TimelineValidationError, TimelineRepositoryError,
    TimelineCheckpointError, TimelineBranchError, TimelineFileError
)
from yacl.models.game_type import GameType
from yacl.models.backup import SaveGame


class TestTimelineManagerInitialization:
    """Tests for TimelineManager initialization."""
    
    def test_timeline_manager_creation(self, mock_event_manager):
        """Test creating a timeline manager."""
        with patch('yacl.models.timeline_manager.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_get_paths.return_value = mock_paths
            
            manager = TimelineManager(mock_event_manager)
            
            assert manager.event_manager == mock_event_manager
            assert manager.paths == mock_paths
            assert manager.timelines == {}
            assert manager.repositories == {}
            assert manager._is_initialized is False
    
    def test_timeline_manager_initialize(self, mock_event_manager):
        """Test initializing the timeline manager."""
        with patch('yacl.models.timeline_manager.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_get_paths.return_value = mock_paths
            
            manager = TimelineManager(mock_event_manager)
            
            with patch.object(manager, '_initialize_game_repository', return_value=True) as mock_init:
                result = manager.initialize()
                
                assert result is True
                assert manager._is_initialized is True
                # Should initialize for all game types except 'other'
                expected_calls = len([gt for gt in GameType.all if gt != GameType.other])
                assert mock_init.call_count == expected_calls


class TestTimelineManagerValidation:
    """Tests for TimelineManager validation methods."""
    
    def test_validate_save_game_valid(self, mock_event_manager, sample_save_game):
        """Test validating a valid save game."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Should not raise any exception
            manager._validate_save_game(sample_save_game)
    
    def test_validate_save_game_none(self, mock_event_manager):
        """Test validating None save game."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineValidationError, match="Save game cannot be None"):
                manager._validate_save_game(None)
    
    def test_validate_save_game_invalid(self, mock_event_manager, temp_dir):
        """Test validating invalid save game."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Create save game with non-existent path
            invalid_save = SaveGame(
                name="invalid",
                game=GameType.dda,
                path=temp_dir / "nonexistent"
            )
            
            with pytest.raises(TimelineFileError, match="Save game directory does not exist"):
                manager._validate_save_game(invalid_save)
    
    def test_validate_checkpoint_message_valid(self, mock_event_manager):
        """Test validating valid checkpoint message."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Should not raise any exception
            manager._validate_checkpoint_message("Valid message")
    
    def test_validate_checkpoint_message_empty(self, mock_event_manager):
        """Test validating empty checkpoint message."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineValidationError, match="Checkpoint message cannot be empty"):
                manager._validate_checkpoint_message("")
            
            with pytest.raises(TimelineValidationError, match="Checkpoint message cannot be empty"):
                manager._validate_checkpoint_message("   ")
    
    def test_validate_checkpoint_message_too_long(self, mock_event_manager):
        """Test validating too long checkpoint message."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            long_message = "x" * 501
            with pytest.raises(TimelineValidationError, match="Checkpoint message cannot exceed 500 characters"):
                manager._validate_checkpoint_message(long_message)
    
    def test_validate_branch_name_valid(self, mock_event_manager):
        """Test validating valid branch name."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Should not raise any exception
            manager._validate_branch_name("valid-branch_name123")
    
    def test_validate_branch_name_empty(self, mock_event_manager):
        """Test validating empty branch name."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineValidationError, match="Branch name cannot be empty"):
                manager._validate_branch_name("")
    
    def test_validate_branch_name_invalid_chars(self, mock_event_manager):
        """Test validating branch name with invalid characters."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineValidationError, match="Branch name can only contain"):
                manager._validate_branch_name("invalid@branch")
    
    def test_validate_branch_name_reserved(self, mock_event_manager):
        """Test validating reserved branch name."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineValidationError, match="Branch name 'main' is reserved"):
                manager._validate_branch_name("main")
    
    def test_validate_repository_valid(self, mock_event_manager):
        """Test validating valid repository."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Mock repository
            mock_repo = Mock()
            mock_repo.path = "/mock/path"
            manager.repositories[GameType.dda] = mock_repo
            
            with patch('pathlib.Path.exists', return_value=True):
                # Should not raise any exception
                manager._validate_repository(GameType.dda)
    
    def test_validate_repository_missing(self, mock_event_manager):
        """Test validating missing repository."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineRepositoryError, match="No repository initialized"):
                manager._validate_repository(GameType.dda)


class TestTimelineManagerSaveGameDiscovery:
    """Tests for save game discovery functionality."""
    
    def test_discover_save_games_empty_directory(self, mock_event_manager, temp_dir):
        """Test discovering save games in empty directory."""
        with patch('yacl.models.timeline_manager.get_paths') as mock_get_paths:
            mock_paths = Mock()
            mock_paths.get_saves_dir.return_value = temp_dir / "nonexistent"
            mock_get_paths.return_value = mock_paths
            
            manager = TimelineManager(mock_event_manager)
            save_games = manager.discover_save_games(GameType.dda)
            
            assert save_games == []
    
    def test_discover_save_games_with_saves(self, mock_event_manager, temp_dir):
        """Test discovering save games with existing saves."""
        with patch('yacl.models.timeline_manager.get_paths') as mock_get_paths:
            saves_dir = temp_dir / "saves"
            saves_dir.mkdir()
            
            # Create test save directories
            (saves_dir / "save1").mkdir()
            (saves_dir / "save2").mkdir()
            (saves_dir / "save1" / "data.dat").write_text("test")
            (saves_dir / "save2" / "data.dat").write_text("test")
            
            mock_paths = Mock()
            mock_paths.get_saves_dir.return_value = saves_dir
            mock_get_paths.return_value = mock_paths
            
            manager = TimelineManager(mock_event_manager)
            save_games = manager.discover_save_games(GameType.dda)
            
            assert len(save_games) == 2
            save_names = [sg.name for sg in save_games]
            assert "save1" in save_names
            assert "save2" in save_names
    
    def test_get_save_games_without_timelines(self, mock_event_manager, temp_dir):
        """Test getting save games without timelines."""
        with patch('yacl.models.timeline_manager.get_paths') as mock_get_paths:
            saves_dir = temp_dir / "saves"
            saves_dir.mkdir()
            
            # Create test save directories
            (saves_dir / "save1").mkdir()
            (saves_dir / "save2").mkdir()
            (saves_dir / "save1" / "data.dat").write_text("test")
            (saves_dir / "save2" / "data.dat").write_text("test")
            
            mock_paths = Mock()
            mock_paths.get_saves_dir.return_value = saves_dir
            mock_get_paths.return_value = mock_paths
            
            manager = TimelineManager(mock_event_manager)
            
            # Mock existing timelines (save1 has timeline, save2 doesn't)
            manager.timelines[GameType.dda] = {"save1": Mock()}
            
            with patch.object(manager, 'discover_save_games') as mock_discover:
                mock_save_games = [
                    SaveGame("save1", GameType.dda, saves_dir / "save1"),
                    SaveGame("save2", GameType.dda, saves_dir / "save2")
                ]
                mock_discover.return_value = mock_save_games
                
                saves_without_timelines = manager.get_save_games_without_timelines(GameType.dda)
                
                assert len(saves_without_timelines) == 1
                assert saves_without_timelines[0].name == "save2"


class TestTimelineManagerCheckpoints:
    """Tests for checkpoint management functionality."""
    
    def test_create_checkpoint_success(self, mock_event_manager, sample_save_game, sample_timeline):
        """Test successfully creating a checkpoint."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Setup mocks
            manager.timelines[sample_save_game.game] = {sample_save_game.name: sample_timeline}
            
            mock_repo = Mock()
            manager.repositories[sample_save_game.game] = mock_repo
            
            with patch('yacl.models.timeline_manager.Repo') as mock_repo_class:
                mock_wt_repo = Mock()
                mock_worktree = Mock()
                mock_worktree.commit.return_value = b"abc123def456"
                mock_wt_repo.get_worktree.return_value = mock_worktree
                mock_repo_class.return_value = mock_wt_repo
                
                # Mock file iteration
                with patch.object(sample_timeline.worktree_path, 'iterdir') as mock_iterdir:
                    mock_file = Mock()
                    mock_file.is_file.return_value = True
                    mock_file.name = "save.dat"
                    mock_iterdir.return_value = [mock_file]
                    
                    checkpoint = manager.create_checkpoint(sample_save_game, "Test checkpoint")
                    
                    assert checkpoint is not None
                    assert checkpoint.message == "Test checkpoint"
                    assert checkpoint.commit_hash == "abc123def456"
    
    def test_create_checkpoint_validation_error(self, mock_event_manager, temp_dir):
        """Test creating checkpoint with validation error."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Create invalid save game
            invalid_save = SaveGame(
                name="",  # Invalid empty name
                game=GameType.dda,
                path=temp_dir / "save"
            )
            
            with pytest.raises(TimelineValidationError):
                manager.create_checkpoint(invalid_save, "Test message")
    
    def test_create_checkpoint_no_timeline(self, mock_event_manager, sample_save_game):
        """Test creating checkpoint when no timeline exists."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # No timeline exists for this save game
            manager.timelines[sample_save_game.game] = {}
            
            with pytest.raises(TimelineCheckpointError, match="No timeline found"):
                manager.create_checkpoint(sample_save_game, "Test message")


class TestTimelineManagerBranches:
    """Tests for branch management functionality."""
    
    def test_create_branch_success(self, mock_event_manager, sample_save_game, sample_timeline):
        """Test successfully creating a branch."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Setup timeline
            manager.timelines[sample_save_game.game] = {sample_save_game.name: sample_timeline}
            
            with patch.object(manager, 'get_timeline', return_value=sample_timeline):
                with patch('yacl.models.timeline_manager.Repo') as mock_repo_class:
                    mock_wt_repo = Mock()
                    mock_repo_class.return_value = mock_wt_repo
                    
                    result = manager.create_branch(sample_save_game, "new-branch")
                    
                    assert result is True
    
    def test_create_branch_validation_error(self, mock_event_manager, sample_save_game):
        """Test creating branch with validation error."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            with pytest.raises(TimelineValidationError):
                manager.create_branch(sample_save_game, "invalid@branch")
    
    def test_create_branch_already_exists(self, mock_event_manager, sample_save_game, sample_timeline):
        """Test creating branch that already exists."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Add existing branch
            existing_branch = TimelineBranch(name="existing-branch", checkpoints={}, head_commit=None)
            sample_timeline.add_branch(existing_branch)
            
            with patch.object(manager, 'get_timeline', return_value=sample_timeline):
                with pytest.raises(TimelineBranchError, match="Branch 'existing-branch' already exists"):
                    manager.create_branch(sample_save_game, "existing-branch")


class TestTimelineManagerEventHandling:
    """Tests for event handling functionality."""
    
    def test_event_subscription(self, mock_event_manager):
        """Test that manager subscribes to events."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            # Check that subscribe was called for relevant events
            assert mock_event_manager.subscribe.called
    
    def test_event_unsubscription(self, mock_event_manager):
        """Test that manager unsubscribes from events on shutdown."""
        with patch('yacl.models.timeline_manager.get_paths'):
            manager = TimelineManager(mock_event_manager)
            
            manager.shutdown()
            
            # Check that unsubscribe was called
            assert mock_event_manager.unsubscribe.called
