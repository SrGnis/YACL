"""
Timeline Tab Controller for YACL

This module provides the controller for the timeline management tab that handles
all business logic and event management for timeline operations.
"""

import logging
from typing import Optional, List
import tkinter as tk
import tkinter.messagebox as messagebox

from yacl.services.events import EventManager, Events
from yacl.views.tabs.timeline_tab import TimelineTab
from yacl.views.dialogs.checkpoint_dialog import CheckpointDialog, BranchDialog
from yacl.views.dialogs.timeline_creation_dialog import TimelineCreationDialog, RestoreConfirmationDialog
from yacl.models.timeline_manager import get_timeline_manager
from yacl.models.timeline import (
    TimelineError, TimelineValidationError, TimelineRepositoryError,
    TimelineCheckpointError, TimelineBranchError, TimelineFileError
)
from yacl.models.backup import SaveGame
from yacl.models.installation_manager import get_installation_manager
from yacl.models.timeline import Timeline, Checkpoint
from yacl.models.game_type import GameType


class TimelineTabController:
    """
    Controller for the timeline tab that handles all business logic and event management.
    
    This controller:
    - Manages timeline listing and filtering by game type
    - Handles checkpoint creation, restoration, and branch management
    - Coordinates with TimelineManager and InstallationManager
    - Manages save game selection and timeline details display
    - Handles all user input events and business logic
    """
    
    def __init__(self, view: TimelineTab, event_manager: EventManager):
        """
        Initialize the timeline tab controller.
        
        Args:
            view: The TimelineTab view instance
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger("YACL")
        self.view = view
        self.event_manager = event_manager
        
        # State variables
        self.current_game_type: Optional[GameType] = None
        self.current_save_games: List[SaveGame] = []
        self.selected_save_game: Optional[SaveGame] = None
        self.selected_timeline: Optional[Timeline] = None
        self.current_checkpoints: List[Checkpoint] = []
        self.selected_checkpoint: Optional[Checkpoint] = None

        # Event handling guards to prevent recursive calls
        self._handling_save_game_selection = False
        self._handling_checkpoint_selection = False

        # Selection preservation state
        self._last_valid_save_game_index: Optional[int] = None
        self._last_valid_save_game_name: Optional[str] = None
        
        # Setup event handlers and subscriptions
        self._setup_event_handlers()
        self._subscribe_to_events()
        
        self.logger.info("Timeline tab controller initialized")

    def _setup_event_handlers(self):
        """Setup event handlers by directly binding to view widgets."""
        # Direct widget binding following established patterns

        self.view.save_game_listbox.bind("<<ListboxSelect>>", self._on_save_game_selected)
        self.view.checkpoint_listbox.bind("<<ListboxSelect>>", self._on_checkpoint_selected)

        self.view.refresh_button.configure(command=self._on_refresh_timelines)
        self.view.create_timeline_button.configure(command=self._on_create_timeline)
        self.view.create_checkpoint_button.configure(command=self._on_create_checkpoint)
        self.view.restore_checkpoint_button.configure(command=self._on_restore_checkpoint)
        self.view.create_branch_button.configure(command=self._on_create_branch)
        self.view.switch_branch_button.configure(command=self._on_switch_branch)
        
        # Bind Enter key to create checkpoint when in message entry
        self.view.checkpoint_message_entry.bind("<Return>", lambda _: self._on_create_checkpoint())
        
        # Bind branch combobox selection
        self.view.branch_combobox.bind("<<ComboboxSelected>>", self._on_branch_selected)

    def _subscribe_to_events(self):
        """Subscribe to events."""
        try:
            self.event_manager.subscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_current_game_type_changed)
            self.event_manager.subscribe(Events.TIMELINE_CREATED, self._on_timeline_created)
            self.event_manager.subscribe(Events.TIMELINE_DELETED, self._on_timeline_deleted)
            self.event_manager.subscribe(Events.CHECKPOINT_CREATED, self._on_checkpoint_created)
            self.event_manager.subscribe(Events.CHECKPOINT_RESTORED, self._on_checkpoint_restored)
            self.event_manager.subscribe(Events.BRANCH_CREATED, self._on_branch_created)
            self.event_manager.subscribe(Events.BRANCH_SWITCHED, self._on_branch_switched)
            self.event_manager.subscribe(Events.TAB_CHANGED, self._on_tab_changed)

            self.logger.debug("Subscribed to timeline events")

        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")

    def _unsubscribe_from_events(self):
        """Unsubscribe from events."""
        try:
            self.event_manager.unsubscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_current_game_type_changed)
            self.event_manager.unsubscribe(Events.TIMELINE_CREATED, self._on_timeline_created)
            self.event_manager.unsubscribe(Events.TIMELINE_DELETED, self._on_timeline_deleted)
            self.event_manager.unsubscribe(Events.CHECKPOINT_CREATED, self._on_checkpoint_created)
            self.event_manager.unsubscribe(Events.CHECKPOINT_RESTORED, self._on_checkpoint_restored)
            self.event_manager.unsubscribe(Events.BRANCH_CREATED, self._on_branch_created)
            self.event_manager.unsubscribe(Events.BRANCH_SWITCHED, self._on_branch_switched)
            self.event_manager.unsubscribe(Events.TAB_CHANGED, self._on_tab_changed)

            self.logger.debug("Unsubscribed from timeline events")

        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")

    # Event Handlers
    def _on_current_game_type_changed(self, **kwargs):
        """Handle current game type changed event."""
        try:
            game_type = kwargs.get('game_type')
            if game_type:
                self.logger.debug(f"[EVENT] Game type changed to: {game_type.name}")
                self.current_game_type = game_type
                self._refresh_save_games()
        except Exception as e:
            self.logger.error(f"Error handling game type change: {e}")

    def _on_timeline_created(self, **kwargs):
        """Handle timeline created event."""
        _ = kwargs  # Unused parameter
        try:
            self.logger.debug(f"[EVENT] Timeline created event received")
            self._refresh_save_games()
        except Exception as e:
            self.logger.error(f"Error handling timeline created event: {e}")

    def _on_timeline_deleted(self, **kwargs):
        """Handle timeline deleted event."""
        _ = kwargs  # Unused parameter
        try:
            self.logger.debug(f"[EVENT] Timeline deleted event received")
            self._refresh_save_games()
        except Exception as e:
            self.logger.error(f"Error handling timeline deleted event: {e}")

    def _on_checkpoint_created(self, **kwargs):
        """Handle checkpoint created event."""
        _ = kwargs  # Unused parameter
        try:
            if self.selected_timeline:
                self.logger.debug(f"[EVENT] Checkpoint created - refreshing timeline display")
                self._refresh_timeline_display()
        except Exception as e:
            self.logger.error(f"Error handling checkpoint created event: {e}")

    def _on_checkpoint_restored(self, **kwargs):
        """Handle checkpoint restored event."""
        _ = kwargs  # Unused parameter
        try:
            if self.selected_timeline:
                self.logger.debug(f"[EVENT] Checkpoint restored - refreshing timeline display")
                self._refresh_timeline_display()
        except Exception as e:
            self.logger.error(f"Error handling checkpoint restored event: {e}")

    def _on_branch_created(self, **kwargs):
        """Handle branch created event."""
        _ = kwargs  # Unused parameter
        try:
            if self.selected_timeline:
                self.logger.debug(f"[EVENT] Branch created - refreshing timeline display")
                self._refresh_timeline_display()
        except Exception as e:
            self.logger.error(f"Error handling branch created event: {e}")

    def _on_branch_switched(self, **kwargs):
        """Handle branch switched event."""
        _ = kwargs  # Unused parameter
        try:
            if self.selected_timeline:
                self.logger.debug(f"[EVENT] Branch switched - refreshing timeline display")
                self._refresh_timeline_display()
        except Exception as e:
            self.logger.error(f"Error handling branch switched event: {e}")

    def _on_tab_changed(self, **kwargs):
        """Handle tab changed event."""
        try:
            tab_name = kwargs.get('tab_name')
            if tab_name == 'Timeline':
                self.logger.debug(f"[EVENT] Tab changed to Timeline - refreshing save games")
                self._refresh_save_games()
        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")

    # UI Event Handlers
    def _on_save_game_selected(self, event):
        """Handle save game selection."""
        _ = event  # Unused parameter

        # Prevent recursive calls
        if self._handling_save_game_selection:
            self.logger.debug(f"[SELECTION] Ignoring recursive save game selection event")
            return

        try:
            self._handling_save_game_selection = True
            selection_index = self.view.get_selected_save_game_index()

            # Add stack trace for debugging when selection is None
            if selection_index is None:
                import traceback
                self.logger.debug(f"[SELECTION] Save game selection is None - stack trace:")
                for line in traceback.format_stack()[-5:]:  # Last 5 stack frames
                    self.logger.debug(f"[STACK] {line.strip()}")

            self.logger.debug(f"[SELECTION] Save game selected - index: {selection_index}, total games: {len(self.current_save_games)}")

            if selection_index is not None and selection_index < len(self.current_save_games):
                self.selected_save_game = self.current_save_games[selection_index]
                # PRESERVE this valid selection for restoration
                self._last_valid_save_game_index = selection_index
                self._last_valid_save_game_name = self.selected_save_game.name
                self.logger.debug(f"[SELECTION] Selected save game: {self.selected_save_game.name} (preserved for restoration)")
                self._load_timeline_for_save_game()
            else:
                self.logger.debug(f"[SELECTION] Clearing save game selection - invalid index or no games")
                # Don't clear the preserved selection here - we might need to restore it
                self.selected_save_game = None
                self.selected_timeline = None
                self._clear_timeline_display()
        except Exception as e:
            self.logger.error(f"Error handling save game selection: {e}")
        finally:
            self._handling_save_game_selection = False

    def _on_checkpoint_selected(self, event):
        """Handle checkpoint selection."""
        _ = event  # Unused parameter

        # Prevent recursive calls
        if self._handling_checkpoint_selection:
            self.logger.debug(f"[SELECTION] Ignoring recursive checkpoint selection event")
            return

        try:
            self._handling_checkpoint_selection = True

            # Use the last valid save game selection for restoration
            save_game_index = self._last_valid_save_game_index
            save_game_name = self._last_valid_save_game_name
            self.logger.debug(f"[SELECTION] Using preserved save game selection - index: {save_game_index}, name: {save_game_name}")

            selection_index = self.view.get_selected_checkpoint_index()
            self.logger.debug(f"[SELECTION] Checkpoint selected - index: {selection_index}, total checkpoints: {len(self.current_checkpoints)}")

            if selection_index is not None and selection_index < len(self.current_checkpoints):
                self.selected_checkpoint = self.current_checkpoints[selection_index]
                self.logger.debug(f"[SELECTION] Selected checkpoint: {self.selected_checkpoint.commit_hash[:8]} - {self.selected_checkpoint.message}")
                self._display_checkpoint_details()
                self.view.enable_checkpoint_operations(True)
            else:
                self.logger.debug(f"[SELECTION] Clearing checkpoint selection - invalid index or no checkpoints")
                self.selected_checkpoint = None
                self.view.clear_checkpoint_details()
                self.view.enable_checkpoint_operations(False)

            # RESTORE save game selection if it was lost (immediate restoration)
            current_save_game_index = self.view.get_selected_save_game_index()
            if current_save_game_index is None and save_game_index is not None:
                self.logger.debug(f"[SELECTION] Save game selection was lost, restoring to index: {save_game_index}")
                self.view.set_selected_save_game_index(save_game_index)
                # Also restore the selected_save_game object
                if save_game_index < len(self.current_save_games):
                    self.selected_save_game = self.current_save_games[save_game_index]

            # Schedule a delayed restoration in case the immediate one doesn't work
            if save_game_index is not None:
                self.view.parent_frame.after(10, lambda: self._delayed_save_game_restoration(save_game_index))

        except Exception as e:
            self.logger.error(f"Error handling checkpoint selection: {e}")
        finally:
            self._handling_checkpoint_selection = False

    def _delayed_save_game_restoration(self, save_game_index: int):
        """Delayed restoration of save game selection to handle timing issues."""
        try:
            current_index = self.view.get_selected_save_game_index()
            if current_index is None and save_game_index < len(self.current_save_games):
                self.logger.debug(f"[SELECTION] Delayed restoration - setting save game index: {save_game_index}")
                self.view.set_selected_save_game_index(save_game_index)
                self.selected_save_game = self.current_save_games[save_game_index]
            else:
                self.logger.debug(f"[SELECTION] Delayed restoration not needed - current index: {current_index}")
        except Exception as e:
            self.logger.error(f"Error in delayed save game restoration: {e}")

    def _on_refresh_timelines(self):
        """Handle refresh button click."""
        try:
            self.logger.debug(f"[EVENT] Refresh button clicked - refreshing save games")
            self._refresh_save_games()
        except Exception as e:
            self.logger.error(f"Error refreshing timelines: {e}")

    def _on_create_timeline(self):
        """Handle create timeline button click."""
        if not self.selected_save_game:
            messagebox.showerror("Error", "Please select a save game first.")
            return

        try:
            # Show timeline creation dialog
            from yacl.views.dialogs.timeline_creation_dialog import TimelineCreationDialog

            def on_timeline_created(save_game_name: Optional[str]):
                if save_game_name:
                    self.logger.info(f"Timeline created for {save_game_name}")
                    # Refresh the display to show the new timeline
                    self._refresh_save_games()

            dialog = TimelineCreationDialog(
                self.view.parent_frame,
                [self.selected_save_game.name],  # available_saves
                on_timeline_created  # callback
            )

            dialog.show_modal()

        except Exception as e:
            self.logger.error(f"Error creating timeline: {e}")
            messagebox.showerror("Error", f"Failed to create timeline: {e}")

    def _on_create_checkpoint(self):
        """Handle create checkpoint button click."""
        try:
            if not self.selected_save_game or not self.selected_timeline:
                messagebox.showerror("Error", "Please select a save game with a timeline.")
                return

            # Get checkpoint message from the entry
            message = self.view.get_checkpoint_message()
            if not message:
                messagebox.showerror("Error", "Please enter a checkpoint message.")
                return

            # Create checkpoint
            timeline_manager = get_timeline_manager()
            if timeline_manager:
                checkpoint = timeline_manager.create_checkpoint(self.selected_save_game, message)
                if checkpoint:
                    self.view.clear_checkpoint_message()
                    messagebox.showinfo("Success", f"Checkpoint created: {checkpoint.commit_hash[:8]}")
                else:
                    messagebox.showerror("Error", "Failed to create checkpoint.")
            else:
                messagebox.showerror("Error", "Timeline manager not available.")

        except TimelineValidationError as e:
            self.logger.error(f"Validation error creating checkpoint: {e}")
            messagebox.showerror("Validation Error", str(e))
        except TimelineCheckpointError as e:
            self.logger.error(f"Checkpoint error: {e}")
            messagebox.showerror("Checkpoint Error", str(e))
        except TimelineRepositoryError as e:
            self.logger.error(f"Repository error creating checkpoint: {e}")
            messagebox.showerror("Repository Error", str(e))
        except TimelineFileError as e:
            self.logger.error(f"File error creating checkpoint: {e}")
            messagebox.showerror("File Error", str(e))
        except TimelineError as e:
            self.logger.error(f"Timeline error creating checkpoint: {e}")
            messagebox.showerror("Timeline Error", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error creating checkpoint: {e}")
            messagebox.showerror("Error", f"Failed to create checkpoint: {e}")

    def _on_restore_checkpoint(self):
        """Handle restore checkpoint button click."""
        try:
            if not self.selected_checkpoint:
                messagebox.showerror("Error", "Please select a checkpoint to restore.")
                return

            # Show confirmation dialog
            def on_restore_confirmed(confirmed: bool):
                if confirmed:
                    self._perform_checkpoint_restore()

            dialog = RestoreConfirmationDialog(
                self.view.parent_frame,
                self.selected_checkpoint.commit_hash,
                self.selected_checkpoint.message,
                self.selected_checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                on_restore_confirmed
            )
            dialog.show_modal()

        except Exception as e:
            self.logger.error(f"Error initiating checkpoint restore: {e}")
            messagebox.showerror("Error", f"Failed to restore checkpoint: {e}")

    def _perform_checkpoint_restore(self):
        """Perform the actual checkpoint restoration."""
        try:
            timeline_manager = get_timeline_manager()
            if timeline_manager and self.selected_save_game and self.selected_checkpoint:
                success = timeline_manager.restore_checkpoint(self.selected_save_game, self.selected_checkpoint)
                if success:
                    messagebox.showinfo("Success", "Checkpoint restored successfully.")
                else:
                    messagebox.showerror("Error", "Failed to restore checkpoint.")
            else:
                messagebox.showerror("Error", "Timeline manager not available.")

        except TimelineError as e:
            self.logger.error(f"Timeline error restoring checkpoint: {e}")
            messagebox.showerror("Timeline Error", str(e))
        except Exception as e:
            self.logger.error(f"Error restoring checkpoint: {e}")
            messagebox.showerror("Error", f"Failed to restore checkpoint: {e}")

    def _on_create_branch(self):
        """Handle create branch button click."""
        try:
            if not self.selected_checkpoint:
                messagebox.showerror("Error", "Please select a checkpoint to branch from.")
                return

            # Show branch creation dialog
            def on_branch_created(branch_name: Optional[str]):
                if branch_name:
                    self._perform_branch_creation(branch_name)

            dialog = BranchDialog(
                self.view.parent_frame,
                self.selected_save_game.name if self.selected_save_game else "Unknown",
                self.selected_checkpoint.commit_hash,
                on_branch_created
            )
            dialog.show_modal()

        except Exception as e:
            self.logger.error(f"Error initiating branch creation: {e}")
            messagebox.showerror("Error", f"Failed to create branch: {e}")

    def _perform_branch_creation(self, branch_name: str):
        """Perform the actual branch creation."""
        try:
            timeline_manager = get_timeline_manager()
            if timeline_manager and self.selected_save_game and self.selected_checkpoint:
                success = timeline_manager.create_branch(
                    self.selected_save_game,
                    branch_name,
                    self.selected_checkpoint
                )
                if success:
                    messagebox.showinfo("Success", f"Branch '{branch_name}' created successfully.")
                else:
                    messagebox.showerror("Error", "Failed to create branch.")
            else:
                messagebox.showerror("Error", "Timeline manager not available.")

        except TimelineValidationError as e:
            self.logger.error(f"Validation error creating branch: {e}")
            messagebox.showerror("Validation Error", str(e))
        except TimelineBranchError as e:
            self.logger.error(f"Branch error: {e}")
            messagebox.showerror("Branch Error", str(e))
        except TimelineRepositoryError as e:
            self.logger.error(f"Repository error creating branch: {e}")
            messagebox.showerror("Repository Error", str(e))
        except TimelineError as e:
            self.logger.error(f"Timeline error creating branch: {e}")
            messagebox.showerror("Timeline Error", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error creating branch: {e}")
            messagebox.showerror("Error", f"Failed to create branch: {e}")

    def _on_switch_branch(self):
        """Handle switch branch button click."""
        try:
            selected_branch = self.view.get_selected_branch()
            if not selected_branch:
                messagebox.showerror("Error", "Please select a branch to switch to.")
                return

            timeline_manager = get_timeline_manager()
            if timeline_manager and self.selected_save_game:
                success = timeline_manager.switch_branch(self.selected_save_game, selected_branch)
                if success:
                    messagebox.showinfo("Success", f"Switched to branch '{selected_branch}'.")
                else:
                    messagebox.showerror("Error", "Failed to switch branch.")
            else:
                messagebox.showerror("Error", "Timeline manager not available.")

        except TimelineError as e:
            self.logger.error(f"Timeline error switching branch: {e}")
            messagebox.showerror("Timeline Error", str(e))
        except Exception as e:
            self.logger.error(f"Error switching branch: {e}")
            messagebox.showerror("Error", f"Failed to switch branch: {e}")

    def _on_branch_selected(self, event):
        """Handle branch selection in combobox."""
        _ = event  # Unused parameter
        try:
            selected_branch = self.view.get_selected_branch()
            if selected_branch:
                self.view.switch_branch_button.config(state=tk.NORMAL)
            else:
                self.view.switch_branch_button.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Error handling branch selection: {e}")

    # Business Logic Methods
    def _refresh_save_games(self):
        """Refresh the save games list for the current game type."""
        try:
            self.logger.debug(f"[REFRESH] Starting save games refresh")

            if not self.current_game_type:
                installation_manager = get_installation_manager()
                if installation_manager:
                    self.current_game_type = installation_manager.current_game_type

            if not self.current_game_type:
                self.logger.debug(f"[REFRESH] No current game type, clearing displays")
                self._clear_all_displays()
                return

            timeline_manager = get_timeline_manager()
            if not timeline_manager:
                self.logger.debug(f"[REFRESH] No timeline manager, clearing displays")
                self._clear_all_displays()
                return

            # Preserve current save game selection
            selected_save_game_index = self.view.get_selected_save_game_index()
            selected_save_game_name = None
            if (selected_save_game_index is not None and
                self.selected_save_game is not None):
                selected_save_game_name = self.selected_save_game.name

            self.logger.debug(f"[REFRESH] Current selection - index: {selected_save_game_index}, name: {selected_save_game_name}")

            # Get all save games for this game type
            self.current_save_games = timeline_manager.discover_save_games(self.current_game_type)
            self.logger.debug(f"[REFRESH] Found {len(self.current_save_games)} save games")

            # Update the UI
            self.view.clear_save_games_list()

            for save_game in self.current_save_games:
                # Check if this save game has a timeline
                timelines = timeline_manager.get_timelines_for_game(self.current_game_type)
                has_timeline = save_game.name in timelines
                self.view.add_save_game_to_list(save_game.name, has_timeline)

            # Restore save game selection if it was valid and still exists
            if selected_save_game_name:
                self.logger.debug(f"[REFRESH] Attempting to restore selection for: {selected_save_game_name}")
                # Find the save game in the new list
                for i, save_game in enumerate(self.current_save_games):
                    if save_game.name == selected_save_game_name:
                        self.logger.debug(f"[REFRESH] Restoring selection - index: {i}, name: {save_game.name}")
                        self.view.set_selected_save_game_index(i)
                        self.selected_save_game = save_game
                        self._load_timeline_for_save_game()
                        return  # Exit early to preserve selection

                self.logger.debug(f"[REFRESH] Could not find save game '{selected_save_game_name}' in new list")

            # Only clear selection if no previous selection to restore
            self.logger.debug(f"[REFRESH] Clearing selection - no previous selection to restore")
            self.selected_save_game = None
            self.selected_timeline = None
            self._clear_timeline_display()

        except Exception as e:
            self.logger.error(f"Error refreshing save games: {e}")
            self._clear_all_displays()

    def _load_timeline_for_save_game(self):
        """Load timeline data for the selected save game."""
        try:
            if not self.selected_save_game:
                self._clear_timeline_display()
                return

            timeline_manager = get_timeline_manager()
            if not timeline_manager:
                self._clear_timeline_display()
                return

            # Get timeline for this save game
            timelines = timeline_manager.get_timelines_for_game(self.selected_save_game.game)
            if self.selected_save_game.name in timelines:
                self.selected_timeline = timelines[self.selected_save_game.name]
                self._refresh_timeline_display()
            else:
                # No timeline exists - offer to create one
                self.selected_timeline = None
                self._display_no_timeline_message()

        except Exception as e:
            self.logger.error(f"Error loading timeline for save game: {e}")
            self._clear_timeline_display()

    def _refresh_timeline_display(self):
        """Refresh the timeline display for the selected timeline."""
        try:
            self.logger.debug(f"[TIMELINE_REFRESH] Starting timeline display refresh")

            if not self.selected_timeline:
                self.logger.debug(f"[TIMELINE_REFRESH] No selected timeline, clearing display")
                self._clear_timeline_display()
                return

            self.logger.debug(f"[TIMELINE_REFRESH] Refreshing display for timeline: {self.selected_timeline.name}")

            # Display timeline info
            info_text = f"Timeline: {self.selected_timeline.name}\n"
            info_text += f"Game: {self.selected_timeline.game_type.name}\n"
            info_text += f"Current Branch: {self.selected_timeline.current_branch.name}\n"
            info_text += f"Total Checkpoints: {len(self.selected_timeline.current_branch.checkpoints)}\n"
            info_text += f"Total Branches: {len(self.selected_timeline.branches)}"

            self.view.set_timeline_info(info_text)
            self.view.set_current_branch(self.selected_timeline.current_branch.name)

            # Load checkpoints for current branch
            current_branch = self.selected_timeline.current_branch

            if current_branch:
                self.current_checkpoints = list(current_branch.checkpoints.values())
            else:
                self.current_checkpoints = []

            self.logger.debug(f"[TIMELINE_REFRESH] Found {len(self.current_checkpoints)} checkpoints")

            # Preserve current checkpoint selection
            selected_checkpoint_index = self.view.get_selected_checkpoint_index()
            self.logger.debug(f"[TIMELINE_REFRESH] Current checkpoint selection index: {selected_checkpoint_index}")

            # Update checkpoints list
            self.view.clear_checkpoints_list()
            for checkpoint in self.current_checkpoints:
                checkpoint_text = f"{checkpoint.commit_hash[:8]} - {checkpoint.message} ({checkpoint.timestamp.strftime('%Y-%m-%d %H:%M')})"
                self.view.add_checkpoint_to_list(checkpoint_text)

            # Restore checkpoint selection if it was valid
            if (selected_checkpoint_index is not None and
                selected_checkpoint_index < len(self.current_checkpoints)):
                self.logger.debug(f"[TIMELINE_REFRESH] Restoring checkpoint selection - index: {selected_checkpoint_index}")
                self.view.set_selected_checkpoint_index(selected_checkpoint_index)
                # Ensure the selected checkpoint object is still valid
                self.selected_checkpoint = self.current_checkpoints[selected_checkpoint_index]
                self._display_checkpoint_details()
                self.view.enable_checkpoint_operations(True)
            else:
                self.logger.debug(f"[TIMELINE_REFRESH] No checkpoint selection to restore")

            # Update branches combobox
            branch_names = list(self.selected_timeline.branches.keys())
            self.view.set_branches(branch_names)

            # Show normal timeline mode (hide create timeline button)
            self.view.show_timeline_creation_mode(False)

        except Exception as e:
            self.logger.error(f"Error refreshing timeline display: {e}")
            self._clear_timeline_display()

    def _display_checkpoint_details(self):
        """Display details for the selected checkpoint."""
        try:
            if not self.selected_checkpoint:
                self.view.clear_checkpoint_details()
                return

            details_text = f"Hash: {self.selected_checkpoint.commit_hash}\n"
            details_text += f"Message: {self.selected_checkpoint.message}\n"
            details_text += f"Timestamp: {self.selected_checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            details_text += f"Author: {self.selected_checkpoint.author}\n"

            if self.selected_checkpoint.parent_hashes:
                details_text += f"\nParent Commits: {len(self.selected_checkpoint.parent_hashes)}\n"
                for parent_hash in self.selected_checkpoint.parent_hashes:
                    details_text += f"  - {parent_hash[:8]}\n"

            self.view.set_checkpoint_details(details_text)

        except Exception as e:
            self.logger.error(f"Error displaying checkpoint details: {e}")
            self.view.clear_checkpoint_details()

    def _display_no_timeline_message(self):
        """Display message when no timeline exists for the save game."""
        info_text = "No timeline exists for this save game.\n\n"
        info_text += "Timeline management allows you to:\n"
        info_text += "• Create checkpoints of your game progress\n"
        info_text += "• Restore to previous save states\n"
        info_text += "• Create branches for different playthroughs\n"
        info_text += "• Track your game history with Git\n\n"
        info_text += "Click 'Create Timeline' to get started."

        self.view.set_timeline_info(info_text)
        self.view.clear_checkpoints_list()
        self.view.clear_checkpoint_details()
        self.view.set_current_branch("No timeline")
        self.view.set_branches([])

        # Show create timeline mode
        self.view.show_timeline_creation_mode(True)

    def _clear_timeline_display(self):
        """Clear all timeline display elements."""
        self.view.clear_timeline_info()
        self.view.clear_checkpoints_list()
        self.view.clear_checkpoint_details()
        self.view.set_current_branch("No timeline selected")
        self.view.set_branches([])
        self.view.enable_timeline_operations(False)
        self.view.enable_create_timeline_button(False)

    def _clear_all_displays(self):
        """Clear all display elements."""
        self.view.clear_save_games_list()
        self._clear_timeline_display()

    def refresh_ui(self):
        """Public method to refresh the UI - called during initialization."""
        try:
            self._refresh_save_games()
        except Exception as e:
            self.logger.error(f"Error refreshing timeline UI: {e}")

    def shutdown(self):
        """Shutdown the controller and clean up resources."""
        try:
            self._unsubscribe_from_events()
            self.logger.info("Timeline tab controller shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during timeline tab controller shutdown: {e}")
