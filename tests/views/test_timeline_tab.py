"""
Tests for timeline tab view and controller.

This module tests the timeline management UI components and their integration.
"""

import pytest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import tkinter as tk
from tkinter import ttk

from yacl.views.tabs.timeline_tab import TimelineTab
from yacl.controllers.timeline_tab_controller import TimelineTabController
from yacl.services.events import EventManager
from yacl.models.game_type import GameType
from yacl.models.backup import SaveGame


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def tk_root():
    """Create a Tkinter root for testing."""
    root = tk.Tk()
    root.withdraw()  # Hide the window during testing
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass  # Window already destroyed


@pytest.fixture
def event_manager():
    """Create a mock event manager."""
    return Mock(spec=EventManager)


@pytest.fixture
def timeline_tab_view(tk_root, event_manager):
    """Create a timeline tab view for testing."""
    parent_frame = ttk.Frame(tk_root)
    view = TimelineTab(parent_frame, event_manager)
    return view


@pytest.fixture
def mock_timeline_manager():
    """Create a mock timeline manager."""
    with patch('yacl.controllers.timeline_tab_controller.TimelineManager') as mock:
        manager_instance = Mock()
        mock.return_value = manager_instance
        yield manager_instance


class TestTimelineTab:
    """Test cases for timeline tab view."""
    
    def test_timeline_tab_initialization(self, timeline_tab_view):
        """Test that timeline tab initializes correctly."""
        assert timeline_tab_view is not None
        assert hasattr(timeline_tab_view, 'save_games_listbox')
        assert hasattr(timeline_tab_view, 'save_game_info_text')
        assert hasattr(timeline_tab_view, 'initialize_timeline_button')
        assert hasattr(timeline_tab_view, 'delete_timeline_button')
        assert hasattr(timeline_tab_view, 'branch_selector')
        assert hasattr(timeline_tab_view, 'current_branch_label')
    
    def test_timeline_tab_create_ui(self, timeline_tab_view):
        """Test that timeline tab UI can be created."""
        # This should not raise an exception
        timeline_tab_view.create_ui()
        
        # Check that widgets are properly initialized
        assert timeline_tab_view.save_games_listbox is not None
        assert timeline_tab_view.save_game_info_text is not None
        assert timeline_tab_view.initialize_timeline_button is not None
    
    def test_update_save_games_list(self, timeline_tab_view):
        """Test updating the save games list."""
        timeline_tab_view.create_ui()
        
        save_games = ["save1", "save2", "save3"]
        timeline_tab_view.update_save_games_list(save_games)
        
        # Check that listbox contains the save games
        listbox_items = [timeline_tab_view.save_games_listbox.get(i) 
                        for i in range(timeline_tab_view.save_games_listbox.size())]
        assert listbox_items == save_games
    
    def test_update_save_game_info(self, timeline_tab_view):
        """Test updating save game information display."""
        timeline_tab_view.create_ui()
        
        info_text = "Test save game information"
        timeline_tab_view.update_save_game_info(info_text)
        
        # Text widget should be disabled after update
        assert timeline_tab_view.save_game_info_text['state'] == 'disabled'
    
    def test_update_branch_selector(self, timeline_tab_view):
        """Test updating the branch selector."""
        timeline_tab_view.create_ui()
        
        branches = ["main", "feature-branch", "experimental"]
        timeline_tab_view.update_branch_selector(branches)
        
        # Check that combobox has the correct values
        assert timeline_tab_view.branch_selector['values'] == tuple(branches)
        assert timeline_tab_view.branch_selector.get() == branches[0]
    
    def test_set_timeline_buttons_state(self, timeline_tab_view):
        """Test setting timeline button states."""
        timeline_tab_view.create_ui()
        
        # Test enabling initialize button
        timeline_tab_view.set_timeline_buttons_state(True, False)
        assert timeline_tab_view.initialize_timeline_button['state'] == 'normal'
        assert timeline_tab_view.delete_timeline_button['state'] == 'disabled'
        
        # Test enabling delete button
        timeline_tab_view.set_timeline_buttons_state(False, True)
        assert timeline_tab_view.initialize_timeline_button['state'] == 'disabled'
        assert timeline_tab_view.delete_timeline_button['state'] == 'normal'
    
    def test_set_branch_controls_state(self, timeline_tab_view):
        """Test setting branch control states."""
        timeline_tab_view.create_ui()
        
        # Test enabling branch controls
        timeline_tab_view.set_branch_controls_state(True)
        assert timeline_tab_view.branch_selector['state'] == 'readonly'
        
        # Test disabling branch controls
        timeline_tab_view.set_branch_controls_state(False)
        assert timeline_tab_view.branch_selector['state'] == 'disabled'


class TestTimelineTabController:
    """Test cases for timeline tab controller."""
    
    def test_controller_initialization(self, timeline_tab_view, event_manager, mock_timeline_manager):
        """Test that controller initializes correctly."""
        controller = TimelineTabController(timeline_tab_view, event_manager)
        
        assert controller.view == timeline_tab_view
        assert controller.event_manager == event_manager
        assert controller.current_game_type is not None  # Should be set to first game type
        assert controller.current_save_games == []
        assert controller.selected_save_game is None
    
    def test_refresh_ui(self, timeline_tab_view, event_manager, mock_timeline_manager):
        """Test UI refresh functionality."""
        mock_timeline_manager.discover_save_games.return_value = []
        
        controller = TimelineTabController(timeline_tab_view, event_manager)
        timeline_tab_view.create_ui()
        
        # This should not raise an exception
        controller.refresh_ui()
        
        # Should have called discover_save_games
        mock_timeline_manager.discover_save_games.assert_called()
    
    def test_game_type_change_handling(self, timeline_tab_view, event_manager, mock_timeline_manager):
        """Test handling of game type changes."""
        # Create mock save games
        mock_save_games = [
            SaveGame("save1", GameType.all[0], Path("/fake/path1")),
            SaveGame("save2", GameType.all[0], Path("/fake/path2"))
        ]
        mock_timeline_manager.discover_save_games.return_value = mock_save_games
        
        controller = TimelineTabController(timeline_tab_view, event_manager)
        timeline_tab_view.create_ui()
        
        # Simulate game type change
        new_game_type = GameType.all[0]
        controller._handle_game_type_changed(new_game_type)
        
        # Check that save games were updated
        assert controller.current_game_type == new_game_type
        assert len(controller.current_save_games) == 2
        
        # Check that view was updated
        listbox_items = [timeline_tab_view.save_games_listbox.get(i) 
                        for i in range(timeline_tab_view.save_games_listbox.size())]
        assert "save1" in listbox_items
        assert "save2" in listbox_items
    
    def test_save_game_selection(self, timeline_tab_view, event_manager, mock_timeline_manager):
        """Test save game selection handling."""
        # Create mock save games
        mock_save_games = [
            SaveGame("save1", GameType.all[0], Path("/fake/path1")),
        ]
        mock_timeline_manager.discover_save_games.return_value = mock_save_games
        mock_timeline_manager.has_timeline.return_value = False
        
        controller = TimelineTabController(timeline_tab_view, event_manager)
        timeline_tab_view.create_ui()
        controller._handle_game_type_changed(GameType.all[0])
        
        # Simulate save game selection
        timeline_tab_view.save_games_listbox.selection_set(0)
        controller._on_save_game_selected(Mock())
        
        # Check that save game was selected
        assert controller.selected_save_game == mock_save_games[0]
    
    def test_error_handling(self, timeline_tab_view, event_manager, mock_timeline_manager):
        """Test error handling in controller."""
        # Make discover_save_games raise an exception
        mock_timeline_manager.discover_save_games.side_effect = Exception("Test error")
        
        controller = TimelineTabController(timeline_tab_view, event_manager)
        timeline_tab_view.create_ui()
        
        # This should not crash, but handle the error gracefully
        controller._handle_game_type_changed(GameType.all[0])
        
        # Should have emitted an error event
        event_manager.emit.assert_called()
        
        # Find the error event call
        error_calls = [call for call in event_manager.emit.call_args_list 
                      if call[0][0] == 'error_occurred']
        assert len(error_calls) > 0
