"""
Tests for timeline tab controller.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk

from yacl.controllers.timeline_tab_controller import TimelineTabController
from yacl.models.timeline import (
    TimelineError, TimelineValidationError, TimelineRepositoryError,
    TimelineCheckpointError, TimelineBranchError, TimelineFileError
)
from yacl.models.game_type import GameType


class MockTimelineTab:
    """Mock timeline tab view for testing."""
    
    def __init__(self):
        self.parent_frame = Mock()
        
        # Mock UI components
        self.save_game_listbox = Mock()
        self.checkpoint_listbox = Mock()
        self.timeline_info_text = Mock()
        self.checkpoint_details_text = Mock()
        self.refresh_button = Mock()
        self.create_checkpoint_button = Mock()
        self.restore_checkpoint_button = Mock()
        self.create_branch_button = Mock()
        self.switch_branch_button = Mock()
        self.checkpoint_message_entry = Mock()
        self.checkpoint_message_var = Mock()
        self.current_branch_label = Mock()
        self.branch_combobox = Mock()
        
        # Mock methods
        self.clear_save_games_list = Mock()
        self.add_save_game_to_list = Mock()
        self.get_selected_save_game_index = Mock()
        self.clear_timeline_info = Mock()
        self.set_timeline_info = Mock()
        self.clear_checkpoints_list = Mock()
        self.add_checkpoint_to_list = Mock()
        self.get_selected_checkpoint_index = Mock()
        self.clear_checkpoint_details = Mock()
        self.set_checkpoint_details = Mock()
        self.set_current_branch = Mock()
        self.set_branches = Mock()
        self.get_checkpoint_message = Mock()
        self.clear_checkpoint_message = Mock()
        self.get_selected_branch = Mock()
        self.enable_timeline_operations = Mock()
        self.enable_checkpoint_operations = Mock()


class TestTimelineTabControllerInitialization:
    """Tests for TimelineTabController initialization."""
    
    def test_controller_creation(self, mock_event_manager):
        """Test creating a timeline tab controller."""
        mock_view = MockTimelineTab()
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        assert controller.view == mock_view
        assert controller.event_manager == mock_event_manager
        assert controller.current_game_type is None
        assert controller.current_save_games == []
        assert controller.selected_save_game is None
        assert controller.selected_timeline is None
        assert controller.current_checkpoints == []
        assert controller.selected_checkpoint is None
    
    def test_event_subscription(self, mock_event_manager):
        """Test that controller subscribes to events."""
        mock_view = MockTimelineTab()
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        # Check that subscribe was called for relevant events
        assert mock_event_manager.subscribe.called
        
        # Check specific event subscriptions
        subscribe_calls = mock_event_manager.subscribe.call_args_list
        event_names = [call[0][0] for call in subscribe_calls]
        
        expected_events = [
            'CURRENT_GAME_TYPE_CHANGED',
            'TIMELINE_CREATED',
            'TIMELINE_DELETED',
            'CHECKPOINT_CREATED',
            'CHECKPOINT_RESTORED',
            'BRANCH_CREATED',
            'BRANCH_SWITCHED',
            'TAB_CHANGED'
        ]
        
        for event in expected_events:
            assert any(event in str(call) for call in subscribe_calls)


class TestTimelineTabControllerEventHandling:
    """Tests for event handling in timeline tab controller."""
    
    def test_on_current_game_type_changed(self, mock_event_manager):
        """Test handling game type change event."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch.object(controller, '_refresh_save_games') as mock_refresh:
            controller._on_current_game_type_changed(game_type=GameType.dda)
            
            assert controller.current_game_type == GameType.dda
            mock_refresh.assert_called_once()
    
    def test_on_timeline_created(self, mock_event_manager):
        """Test handling timeline created event."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch.object(controller, '_refresh_save_games') as mock_refresh:
            controller._on_timeline_created()
            
            mock_refresh.assert_called_once()
    
    def test_on_checkpoint_created(self, mock_event_manager):
        """Test handling checkpoint created event."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_timeline = Mock()
        
        with patch.object(controller, '_refresh_timeline_display') as mock_refresh:
            controller._on_checkpoint_created()
            
            mock_refresh.assert_called_once()
    
    def test_on_tab_changed_timeline_tab(self, mock_event_manager):
        """Test handling tab change to timeline tab."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch.object(controller, '_refresh_save_games') as mock_refresh:
            controller._on_tab_changed(tab_name='Timeline')
            
            mock_refresh.assert_called_once()
    
    def test_on_tab_changed_other_tab(self, mock_event_manager):
        """Test handling tab change to other tab."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch.object(controller, '_refresh_save_games') as mock_refresh:
            controller._on_tab_changed(tab_name='Game')
            
            mock_refresh.assert_not_called()


class TestTimelineTabControllerUIEvents:
    """Tests for UI event handling in timeline tab controller."""
    
    def test_on_save_game_selected_valid(self, mock_event_manager, sample_save_game):
        """Test handling valid save game selection."""
        mock_view = MockTimelineTab()
        mock_view.get_selected_save_game_index.return_value = 0
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.current_save_games = [sample_save_game]
        
        with patch.object(controller, '_load_timeline_for_save_game') as mock_load:
            # Create mock event
            mock_event = Mock()
            controller._on_save_game_selected(mock_event)
            
            assert controller.selected_save_game == sample_save_game
            mock_load.assert_called_once()
    
    def test_on_save_game_selected_invalid_index(self, mock_event_manager):
        """Test handling invalid save game selection."""
        mock_view = MockTimelineTab()
        mock_view.get_selected_save_game_index.return_value = None
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch.object(controller, '_clear_timeline_display') as mock_clear:
            mock_event = Mock()
            controller._on_save_game_selected(mock_event)
            
            assert controller.selected_save_game is None
            assert controller.selected_timeline is None
            mock_clear.assert_called_once()
    
    def test_on_checkpoint_selected_valid(self, mock_event_manager, sample_checkpoint):
        """Test handling valid checkpoint selection."""
        mock_view = MockTimelineTab()
        mock_view.get_selected_checkpoint_index.return_value = 0
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.current_checkpoints = [sample_checkpoint]
        
        with patch.object(controller, '_display_checkpoint_details') as mock_display:
            mock_event = Mock()
            controller._on_checkpoint_selected(mock_event)
            
            assert controller.selected_checkpoint == sample_checkpoint
            mock_display.assert_called_once()
            mock_view.enable_checkpoint_operations.assert_called_with(True)
    
    def test_on_refresh_timelines(self, mock_event_manager):
        """Test handling refresh button click."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch.object(controller, '_refresh_save_games') as mock_refresh:
            controller._on_refresh_timelines()
            
            mock_refresh.assert_called_once()


class TestTimelineTabControllerCheckpointOperations:
    """Tests for checkpoint operations in timeline tab controller."""
    
    def test_create_checkpoint_success(self, mock_event_manager, sample_save_game, sample_timeline):
        """Test successful checkpoint creation."""
        mock_view = MockTimelineTab()
        mock_view.get_checkpoint_message.return_value = "Test checkpoint"
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_save_game = sample_save_game
        controller.selected_timeline = sample_timeline
        
        mock_checkpoint = Mock()
        
        with patch('yacl.controllers.timeline_tab_controller.get_timeline_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.create_checkpoint.return_value = mock_checkpoint
            mock_get_manager.return_value = mock_manager
            
            with patch('tkinter.messagebox.showinfo') as mock_info:
                controller._on_create_checkpoint()
                
                mock_manager.create_checkpoint.assert_called_once_with(sample_save_game, "Test checkpoint")
                mock_view.clear_checkpoint_message.assert_called_once()
                mock_info.assert_called_once()
    
    def test_create_checkpoint_no_save_game(self, mock_event_manager):
        """Test checkpoint creation with no save game selected."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_save_game = None
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            controller._on_create_checkpoint()
            
            mock_error.assert_called_once()
    
    def test_create_checkpoint_empty_message(self, mock_event_manager, sample_save_game, sample_timeline):
        """Test checkpoint creation with empty message."""
        mock_view = MockTimelineTab()
        mock_view.get_checkpoint_message.return_value = ""
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_save_game = sample_save_game
        controller.selected_timeline = sample_timeline
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            controller._on_create_checkpoint()
            
            mock_error.assert_called_once()
    
    def test_create_checkpoint_validation_error(self, mock_event_manager, sample_save_game, sample_timeline):
        """Test checkpoint creation with validation error."""
        mock_view = MockTimelineTab()
        mock_view.get_checkpoint_message.return_value = "Test message"
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_save_game = sample_save_game
        controller.selected_timeline = sample_timeline
        
        with patch('yacl.controllers.timeline_tab_controller.get_timeline_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.create_checkpoint.side_effect = TimelineValidationError("Validation error")
            mock_get_manager.return_value = mock_manager
            
            with patch('tkinter.messagebox.showerror') as mock_error:
                controller._on_create_checkpoint()
                
                mock_error.assert_called_once()
                assert "Validation Error" in str(mock_error.call_args)


class TestTimelineTabControllerBranchOperations:
    """Tests for branch operations in timeline tab controller."""
    
    def test_create_branch_success(self, mock_event_manager, sample_save_game, sample_checkpoint):
        """Test successful branch creation."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_save_game = sample_save_game
        controller.selected_checkpoint = sample_checkpoint
        
        with patch('yacl.controllers.timeline_tab_controller.BranchDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog.show_modal.return_value = "new-branch"
            mock_dialog_class.return_value = mock_dialog
            
            with patch.object(controller, '_perform_branch_creation') as mock_perform:
                controller._on_create_branch()
                
                mock_perform.assert_called_once_with("new-branch")
    
    def test_create_branch_no_checkpoint(self, mock_event_manager):
        """Test branch creation with no checkpoint selected."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_checkpoint = None
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            controller._on_create_branch()
            
            mock_error.assert_called_once()
    
    def test_switch_branch_success(self, mock_event_manager, sample_save_game):
        """Test successful branch switching."""
        mock_view = MockTimelineTab()
        mock_view.get_selected_branch.return_value = "feature-branch"
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_save_game = sample_save_game
        
        with patch('yacl.controllers.timeline_tab_controller.get_timeline_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.switch_branch.return_value = True
            mock_get_manager.return_value = mock_manager
            
            with patch('tkinter.messagebox.showinfo') as mock_info:
                controller._on_switch_branch()
                
                mock_manager.switch_branch.assert_called_once_with(sample_save_game, "feature-branch")
                mock_info.assert_called_once()
    
    def test_switch_branch_no_selection(self, mock_event_manager):
        """Test branch switching with no branch selected."""
        mock_view = MockTimelineTab()
        mock_view.get_selected_branch.return_value = ""
        
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            controller._on_switch_branch()
            
            mock_error.assert_called_once()


class TestTimelineTabControllerBusinessLogic:
    """Tests for business logic methods in timeline tab controller."""
    
    def test_refresh_save_games_success(self, mock_event_manager):
        """Test successful save games refresh."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.current_game_type = GameType.dda
        
        mock_save_games = [Mock(name="save1"), Mock(name="save2")]
        
        with patch('yacl.controllers.timeline_tab_controller.get_timeline_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.discover_save_games.return_value = mock_save_games
            mock_manager.get_timelines_for_game.return_value = {"save1": Mock()}
            mock_get_manager.return_value = mock_manager
            
            controller._refresh_save_games()
            
            assert controller.current_save_games == mock_save_games
            mock_view.clear_save_games_list.assert_called_once()
            assert mock_view.add_save_game_to_list.call_count == 2
    
    def test_refresh_save_games_no_game_type(self, mock_event_manager):
        """Test save games refresh with no game type."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.current_game_type = None
        
        with patch('yacl.controllers.timeline_tab_controller.get_installation_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.current_game_type = GameType.dda
            mock_get_manager.return_value = mock_manager
            
            with patch.object(controller, '_clear_all_displays') as mock_clear:
                controller._refresh_save_games()
                
                assert controller.current_game_type == GameType.dda
    
    def test_display_checkpoint_details(self, mock_event_manager, sample_checkpoint):
        """Test displaying checkpoint details."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        controller.selected_checkpoint = sample_checkpoint
        
        controller._display_checkpoint_details()
        
        mock_view.set_checkpoint_details.assert_called_once()
        # Check that the details contain expected information
        call_args = mock_view.set_checkpoint_details.call_args[0][0]
        assert sample_checkpoint.commit_hash in call_args
        assert sample_checkpoint.message in call_args
    
    def test_clear_timeline_display(self, mock_event_manager):
        """Test clearing timeline display."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        controller._clear_timeline_display()
        
        mock_view.clear_timeline_info.assert_called_once()
        mock_view.clear_checkpoints_list.assert_called_once()
        mock_view.clear_checkpoint_details.assert_called_once()
        mock_view.set_current_branch.assert_called_once_with("No timeline selected")
        mock_view.set_branches.assert_called_once_with([])
        mock_view.enable_timeline_operations.assert_called_once_with(False)


class TestTimelineTabControllerShutdown:
    """Tests for controller shutdown functionality."""
    
    def test_shutdown(self, mock_event_manager):
        """Test controller shutdown."""
        mock_view = MockTimelineTab()
        controller = TimelineTabController(mock_view, mock_event_manager)
        
        controller.shutdown()
        
        # Check that unsubscribe was called
        assert mock_event_manager.unsubscribe.called
