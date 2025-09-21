"""
Pytest configuration and fixtures for YACL tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from yacl.models.game_type import GameType
from yacl.models.backup import SaveGame
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