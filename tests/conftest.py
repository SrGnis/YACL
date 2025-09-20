"""
Pytest configuration and fixtures for YACL tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

from yacl.models.game_type import GameType
from yacl.models.backup import SaveGame
from yacl.models.timeline import Timeline, Checkpoint, TimelineBranch, TimelineStatus
from yacl.services.events import EventManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_event_manager():
    """Create a mock event manager."""
    event_manager = Mock(spec=EventManager)
    event_manager.emit = Mock()
    event_manager.subscribe = Mock()
    event_manager.unsubscribe = Mock()
    return event_manager


@pytest.fixture
def sample_game_type():
    """Create a sample game type for testing."""
    return GameType.dda


@pytest.fixture
def sample_save_game(temp_dir, sample_game_type):
    """Create a sample save game for testing."""
    save_dir = temp_dir / "test_save"
    save_dir.mkdir()
    
    # Create some sample save files
    (save_dir / "save.dat").write_text("sample save data")
    (save_dir / "world.dat").write_text("sample world data")
    
    return SaveGame(
        name="test_save",
        game=sample_game_type,
        path=save_dir
    )


@pytest.fixture
def sample_checkpoint():
    """Create a sample checkpoint for testing."""
    return Checkpoint(
        commit_hash="abc123def456",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        message="Test checkpoint",
        author="Test Author"
    )


@pytest.fixture
def sample_timeline_branch(sample_checkpoint):
    """Create a sample timeline branch for testing."""
    branch = TimelineBranch(
        name="main",
        checkpoints={sample_checkpoint.commit_hash: sample_checkpoint},
        head_commit=sample_checkpoint.commit_hash,
        is_main=True
    )
    return branch


@pytest.fixture
def sample_timeline(temp_dir, sample_game_type, sample_timeline_branch, sample_checkpoint):
    """Create a sample timeline for testing."""
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
    return timeline


@pytest.fixture
def mock_dulwich_repo():
    """Create a mock dulwich repository."""
    repo = Mock()
    repo.path = "/mock/repo/path"
    repo.get_worktree = Mock()
    
    worktree = Mock()
    worktree.stage = Mock()
    worktree.commit = Mock(return_value=b"abc123def456")
    repo.get_worktree.return_value = worktree
    
    return repo


@pytest.fixture
def mock_paths_service(temp_dir):
    """Create a mock paths service."""
    paths = Mock()
    paths.get_saves_dir = Mock(return_value=temp_dir / "saves")
    paths.get_backup_dir = Mock(return_value=temp_dir / "backups")
    return paths


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_dir):
    """Set up test environment with temporary directories."""
    # Create test directory structure
    saves_dir = temp_dir / "saves"
    saves_dir.mkdir()
    
    backups_dir = temp_dir / "backups"
    backups_dir.mkdir()
    
    # Mock the paths service to use temp directories
    def mock_get_saves_dir(game_name):
        return saves_dir / game_name
    
    def mock_get_backup_dir(game_name):
        return backups_dir / game_name
    
    # This would need to be adjusted based on how paths are imported in the actual code
    # monkeypatch.setattr("yacl.services.paths.get_paths", lambda: mock_paths_service)


class MockTimelineManager:
    """Mock timeline manager for testing."""
    
    def __init__(self):
        self.timelines = {}
        self.repositories = {}
        self.event_manager = Mock()
        
    def initialize(self):
        return True
        
    def create_timeline(self, save_game):
        return Mock()
        
    def create_checkpoint(self, save_game, message):
        return Mock()
        
    def restore_checkpoint(self, save_game, checkpoint_hash):
        return True
        
    def create_branch(self, save_game, branch_name, from_checkpoint=None):
        return True
        
    def switch_branch(self, save_game, branch_name):
        return True
        
    def get_timeline(self, save_game):
        return Mock()
        
    def discover_save_games(self, game_type):
        return []


@pytest.fixture
def mock_timeline_manager():
    """Create a mock timeline manager."""
    return MockTimelineManager()


# Test data constants
TEST_CHECKPOINT_HASH = "abc123def456789"
TEST_BRANCH_NAME = "test-branch"
TEST_COMMIT_MESSAGE = "Test commit message"
TEST_AUTHOR = "Test Author <test@example.com>"

# Helper functions for tests
def create_test_save_files(save_dir: Path, file_count: int = 3):
    """Create test save files in a directory."""
    save_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(file_count):
        (save_dir / f"save_file_{i}.dat").write_text(f"Test save data {i}")
    
    return list(save_dir.glob("*.dat"))


def assert_checkpoint_valid(checkpoint: Checkpoint):
    """Assert that a checkpoint has valid data."""
    assert checkpoint.commit_hash
    assert checkpoint.message
    assert checkpoint.timestamp
    assert checkpoint.author
    assert isinstance(checkpoint.timestamp, datetime)


def assert_timeline_valid(timeline: Timeline):
    """Assert that a timeline has valid data."""
    assert timeline.name
    assert timeline.game_type
    assert timeline.save_path.exists()
    assert timeline.worktree_path.exists()
    assert timeline.repository_path.exists()
    assert timeline.main_branch
    assert timeline.current_branch
    assert timeline.status in TimelineStatus
