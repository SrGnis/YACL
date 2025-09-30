"""
Timeline Tab Controller for YACL

This module provides the controller for the timeline management tab that handles
all business logic and event management for timeline operations.
"""

import logging
import traceback
from typing import Optional, List, Dict
import tkinter as tk
from datetime import datetime

from yacl.services.events import EventManager, Events
from yacl.views.tabs.timeline_tab import TimelineTab
from yacl.models.timeline_manager import get_timeline_manager
from yacl.models.timeline import TimelineTree, TimelineError
from yacl.models.backup import SaveGame
from yacl.models.game_type import GameType


class TimelineTabController:
    """
    Controller for the timeline tab that handles all business logic and event management.
    
    This controller:
    - Manages save game listing and filtering by game type
    - Handles timeline initialization and deletion
    - Manages branch selection and information display
    - Coordinates with TimelineManager for timeline operations
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
        
        # Get timeline manager instance
        self.timeline_manager = get_timeline_manager()
        
        # State variables
        self.current_game_type: Optional[GameType] = None
        self.current_save_games: List[SaveGame] = []
        self.selected_save_game: Optional[SaveGame] = None
        self.current_timeline: Optional[TimelineTree] = None
        
        # Setup event handlers and subscriptions
        self._setup_event_handlers()
        self._setup_event_subscriptions()
        
        # Initialize with first game type if available
        if GameType.all:
            self._handle_game_type_changed(GameType.all[0])
        
        self.logger.info("Timeline tab controller initialized")

    def refresh_ui(self):
        """Refresh the UI with current data."""
        try:
            # Refresh save games for current game type if set
            if self.current_game_type:
                self._handle_game_type_changed(self.current_game_type)
            else:
                # Initialize with first game type if available
                if GameType.all:
                    self._handle_game_type_changed(GameType.all[0])

            self.logger.debug("Timeline tab UI refreshed")

        except Exception as e:
            self.logger.error(f"Failed to refresh timeline tab UI: {e}")

    def _setup_event_handlers(self):
        """Setup UI event handlers."""
        try:
            # Save game selection
            self.view.save_games_listbox.bind('<<ListboxSelect>>', self._on_save_game_selected)
            
            # Timeline management buttons
            self.view.initialize_timeline_button.configure(command=self._on_initialize_timeline)
            self.view.delete_timeline_button.configure(command=self._on_delete_timeline)
            
            # Branch selection
            self.view.branch_selector.bind('<<ComboboxSelected>>', self._on_branch_selected)

            # Checkpoint management
            self.view.checkpoints_listbox.bind('<<ListboxSelect>>', self.on_checkpoint_selected)
            self.view.create_checkpoint_button.configure(command=self.on_create_checkpoint)
            self.view.restore_checkpoint_button.configure(command=self.on_restore_checkpoint)
            self.view.delete_checkpoint_button.configure(command=self.on_delete_checkpoint)

            self.logger.debug("Timeline tab event handlers setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup timeline tab event handlers: {e}")
            raise
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions."""
        try:
            # Subscribe to game type changes
            self.event_manager.subscribe(Events.CURRENT_GAME_TYPE_CHANGED, self._on_game_type_changed)
            
            # Subscribe to timeline events
            self.event_manager.subscribe(Events.TIMELINE_CREATED, self._on_timeline_created)
            self.event_manager.subscribe(Events.TIMELINE_DELETED, self._on_timeline_deleted)
            
            self.logger.debug("Timeline tab event subscriptions setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup timeline tab event subscriptions: {e}")
            raise
    
    def _on_game_type_changed(self, sender, game_type: GameType, **kwargs):
        """Handle game type change event."""
        try:
            self._handle_game_type_changed(game_type)
        except Exception as e:
            self.logger.error(f"Error handling game type change: {e}")
    
    def _handle_game_type_changed(self, game_type: GameType):
        """Handle game type change and refresh save games."""
        try:
            self.logger.debug(f"Handling game type change to: {game_type.display_name}")
            
            self.current_game_type = game_type
            self.selected_save_game = None
            self.current_timeline = None
            
            # Discover save games for the new game type
            self.current_save_games = self.timeline_manager.discover_save_games(game_type)
            
            # Update the view
            save_game_names = [sg.name for sg in self.current_save_games]
            self.view.update_save_games_list(save_game_names)
            
            # Clear other displays
            self.view.update_save_game_info("Select a save game to view timeline information.")
            self.view.update_branch_selector([])
            self.view.update_current_branch("No timeline selected")
            self.view.update_branch_info("No timeline selected.")
            
            # Disable all buttons initially
            self.view.set_timeline_buttons_state(False, False)
            self.view.set_branch_controls_state(False)
            
            self.logger.info(f"Found {len(self.current_save_games)} save games for {game_type.display_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle game type change: {e}")
            self._show_error("Failed to load save games for the selected game type.")
    
    def _on_save_game_selected(self, event):
        """Handle save game selection."""
        try:
            selection = self.view.save_games_listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            if index >= len(self.current_save_games):
                return
            
            self.selected_save_game = self.current_save_games[index]
            self._update_save_game_display()
            
        except Exception as e:
            self.logger.error(f"Error handling save game selection: {e}")
    
    def _update_save_game_display(self):
        """Update the save game information display."""
        if not self.selected_save_game:
            return
        
        try:
            save_game = self.selected_save_game
            
            # Check if timeline exists
            timeline_exists = self.timeline_manager.get_timeline(save_game) is not None
            
            # Build info text
            info_lines = [
                f"Save Game: {save_game.name}",
                f"Game Type: {save_game.game.display_name}",
                f"Path: {save_game.path}",
                f"Exists: {'Yes' if save_game.exists else 'No'}",
                "",
                f"Timeline Status: {'Initialized' if timeline_exists else 'Not initialized'}"
            ]
            
            if timeline_exists:
                try:
                    # Try to load timeline information
                    timeline = TimelineTree.from_worktree(save_game.path, save_game.game)
                    self.current_timeline = timeline
                    
                    info_lines.extend([
                        f"Current Branch: {timeline.current_branch.name}",
                        f"Total Branches: {len(timeline.branches)}",
                        f"Status: {timeline.status.value}",
                        f"Last Updated: {timeline.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
                    ])
                    
                    # Update branch controls
                    branch_names = list(timeline.branches.keys())
                    self.view.update_branch_selector(branch_names)
                    # Set the selector to the current branch explicitly
                    self.view.branch_selector.set(timeline.current_branch.name)
                    self.view.update_current_branch(timeline.current_branch.name)
                    self.view.set_branch_controls_state(True)
                    
                    # Update branch info
                    self._update_branch_info_display()

                    # Update checkpoint display
                    self.refresh_checkpoint_display()

                except Exception as e:
                    self.logger.warning(f"Failed to load timeline details: {e}")
                    info_lines.append(f"Error loading timeline: {str(e)}")
                    self.current_timeline = None
                    self.view.set_branch_controls_state(False)
                    self.view.set_checkpoint_controls_state(False)
            else:
                self.current_timeline = None
                self.view.update_branch_selector([])
                self.view.update_current_branch("No timeline")
                self.view.update_branch_info("Timeline not initialized.")
                self.view.set_branch_controls_state(False)
            
            # Update info display
            info_text = "\n".join(info_lines)
            self.view.update_save_game_info(info_text)
            
            # Update button states
            can_initialize = save_game.exists and not timeline_exists
            can_delete = timeline_exists
            self.view.set_timeline_buttons_state(can_initialize, can_delete)
            
        except Exception as e:
            self.logger.error(f"Failed to update save game display: {e}")
            self._show_error("Failed to load save game information.")
    
    def _update_branch_info_display(self):
        """Update the branch information display."""
        if not self.current_timeline:
            self.view.update_branch_info("No timeline selected.")
            return
        
        try:
            current_branch = self.current_timeline.current_branch
            
            info_lines = [
                f"Branch: {current_branch.name}",
                f"Is Main Branch: {'Yes' if current_branch.is_main else 'No'}",
                f"Checkpoints: {len(current_branch.checkpoints)}",
                f"Created: {current_branch.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            if current_branch.head_commit:
                info_lines.append(f"Head Commit: {current_branch.head_commit[:8]}...")
            
            latest_checkpoint = current_branch.get_latest_checkpoint()
            if latest_checkpoint:
                info_lines.extend([
                    "",
                    "Latest Checkpoint:",
                    f"  Message: {latest_checkpoint.message}",
                    f"  Author: {latest_checkpoint.author}",
                    f"  Time: {latest_checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                ])
            
            info_text = "\n".join(info_lines)
            self.view.update_branch_info(info_text)
            
        except Exception as e:
            self.logger.error(f"Failed to update branch info display: {e}")
    
    def _on_branch_selected(self, event):
        """Handle branch selection and switch to the selected branch."""
        try:
            selected_branch = self.view.branch_selector.get()
            if not selected_branch or not self.current_timeline:
                return

            # Check if this is actually a different branch
            if selected_branch == self.current_timeline.current_branch.name:
                return  # Already on this branch

            self.logger.debug(f"Branch selected: {selected_branch}")

            # Check if the branch exists in our timeline
            if selected_branch not in self.current_timeline.branches:
                self.logger.warning(f"Branch {selected_branch} not found in timeline")
                return

            # Switch to the selected branch
            success = self._switch_to_branch(selected_branch)

            if success:
                # Update the current branch in the timeline
                self.current_timeline.current_branch = self.current_timeline.branches[selected_branch]

                # Update UI displays
                self.view.update_current_branch(selected_branch)
                self._update_branch_info_display()
                self.refresh_checkpoint_display()

                self.logger.info(f"Successfully switched to branch: {selected_branch}")
            else:
                self.logger.error(f"Failed to switch to branch: {selected_branch}")
                # Revert the selector to the current branch
                self.view.branch_selector.set(self.current_timeline.current_branch.name)

        except Exception as e:
            self.logger.error(f"Error handling branch selection: {e}")
            # Revert the selector to the current branch if possible
            if self.current_timeline and self.current_timeline.current_branch:
                self.view.branch_selector.set(self.current_timeline.current_branch.name)
    
    def _on_initialize_timeline(self):
        """Handle timeline initialization."""
        if not self.selected_save_game:
            return
        
        try:
            self.logger.info(f"Initializing timeline for {self.selected_save_game.name}")
            
            # Disable button during operation
            self.view.initialize_timeline_button.config(state=tk.DISABLED)
            
            # Initialize timeline
            timeline = self.timeline_manager.create_timeline(self.selected_save_game)
            
            if timeline:
                self.logger.info(f"Timeline initialized successfully for {self.selected_save_game.name}")
                self._update_save_game_display()
            else:
                self._show_error("Failed to initialize timeline. Check logs for details.")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize timeline: {e}")
            self._show_error(f"Failed to initialize timeline: {str(e)}")
        finally:
            # Re-enable button
            self.view.initialize_timeline_button.config(state=tk.NORMAL)
    
    def _on_delete_timeline(self):
        """Handle timeline deletion (placeholder for future implementation)."""
        if not self.selected_save_game:
            return
        
        try:
            self.logger.info(f"Timeline deletion requested for {self.selected_save_game.name}")
            # TODO: Implement timeline deletion with confirmation dialog
            self._show_error("Timeline deletion not yet implemented.")
            
        except Exception as e:
            self.logger.error(f"Failed to delete timeline: {e}")
            self._show_error(f"Failed to delete timeline: {str(e)}")
    
    def _on_timeline_created(self, sender, timeline: TimelineTree, **kwargs):
        """Handle timeline created event."""
        try:
            self.logger.debug(f"Timeline created event received for {timeline.name}")
            # Refresh display if it's for the currently selected save game
            if (self.selected_save_game and 
                self.selected_save_game.name == timeline.name):
                self._update_save_game_display()
        except Exception as e:
            self.logger.error(f"Error handling timeline created event: {e}")
    
    def _on_timeline_deleted(self, sender, timeline: TimelineTree, **kwargs):
        """Handle timeline deleted event."""
        try:
            self.logger.debug(f"Timeline deleted event received for {timeline.name}")
            # Refresh display if it's for the currently selected save game
            if (self.selected_save_game and 
                self.selected_save_game.name == timeline.name):
                self._update_save_game_display()
        except Exception as e:
            self.logger.error(f"Error handling timeline deleted event: {e}")
    
    def _show_error(self, message: str):
        """Show error message to user."""
        self.logger.error(message)
        # Emit error event for status bar or other error handling
        self.event_manager.emit(Events.ERROR_OCCURRED, message=message)

    # Checkpoint Management Methods

    def get_current_checkpoints(self) -> List[Dict]:
        """
        Get checkpoints for the currently selected branch.

        Returns:
            List of checkpoint dictionaries
        """
        if not self.current_timeline or not self.selected_save_game:
            return []

        try:
            # Get the currently selected branch from the UI
            selected_branch = self.view.branch_selector.get()
            if not selected_branch:
                selected_branch = self.current_timeline.current_branch.name

            # Get checkpoints from timeline manager for the selected branch
            checkpoints = self.timeline_manager.get_commit_history(
                self.selected_save_game,
                branch_name=selected_branch,
                limit=50
            )
            # Convert Checkpoint objects to dictionaries
            checkpoint_dicts = []
            for checkpoint in checkpoints:
                if hasattr(checkpoint, '__dict__'):
                    # It's a Checkpoint object, convert to dict
                    checkpoint_dict = {
                        'hash': checkpoint.commit_hash,
                        'timestamp': checkpoint.timestamp,
                        'message': checkpoint.message,
                        'author': checkpoint.author,
                        'parent_hashes': checkpoint.parent_hashes
                    }
                else:
                    # It's already a dict
                    checkpoint_dict = checkpoint
                checkpoint_dicts.append(checkpoint_dict)
            return checkpoint_dicts
        except Exception as e:
            self.logger.error(f"Failed to get checkpoints: {e}")
            return []

    def refresh_checkpoint_display(self):
        """Refresh the checkpoint list display."""
        try:
            checkpoints = self.get_current_checkpoints()
            self.view.update_checkpoints_list(checkpoints)

            # Enable/disable checkpoint controls based on availability
            has_checkpoints = len(checkpoints) > 0
            self.view.set_checkpoint_controls_state(has_checkpoints)

        except Exception as e:
            self.logger.error(f"Failed to refresh checkpoint display: {e}")

    def on_checkpoint_selected(self, event):
        """Handle checkpoint selection in the listbox."""
        try:
            selection = self.view.get_selected_checkpoint()
            if selection is not None:
                checkpoints = self.get_current_checkpoints()
                if 0 <= selection < len(checkpoints):
                    checkpoint = checkpoints[selection]
                    self.view.update_checkpoint_info(checkpoint)

                    # Enable action buttons when a checkpoint is selected
                    self.view.set_checkpoint_action_buttons_state(True)
                else:
                    self.view.clear_checkpoint_info()
                    self.view.set_checkpoint_action_buttons_state(False)
            else:
                self.view.clear_checkpoint_info()
                self.view.set_checkpoint_action_buttons_state(False)

        except Exception as e:
            self.logger.error(f"Error handling checkpoint selection: {e}")

    def on_create_checkpoint(self):
        """Handle create checkpoint button click."""
        if not self.selected_save_game or not self.current_timeline:
            self._show_error("No save game or timeline selected.")
            return

        try:
            from yacl.ui.dialogs.input_dialog import show_text_input_dialog

            # Get commit message from user
            commit_message = show_text_input_dialog(
                self.view.parent_frame,
                "Create Checkpoint",
                "Enter commit message:",
                "Checkpoint created via YACL"
            )

            if commit_message is None:  # User cancelled
                return

            if not commit_message.strip():
                self._show_error("Commit message cannot be empty.")
                return

            # Disable button during operation
            self.view.create_checkpoint_button.config(state=tk.DISABLED)

            # Create checkpoint using timeline manager
            success = self.timeline_manager.create_checkpoint(
                self.selected_save_game,
                commit_message.strip()
            )

            if success:
                self.logger.info(f"Checkpoint created successfully: {commit_message}")
                # Refresh displays
                self._update_save_game_display()
                self.refresh_checkpoint_display()

                from yacl.ui.dialogs.input_dialog import show_info_dialog
                show_info_dialog(
                    self.view.parent_frame,
                    "Success",
                    "Checkpoint created successfully!"
                )
            else:
                self._show_error("Failed to create checkpoint. Check logs for details.")

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            self._show_error(f"Failed to create checkpoint: {str(e)}")
        finally:
            # Re-enable button
            self.view.create_checkpoint_button.config(state=tk.NORMAL)

    def on_delete_checkpoint(self):
        """Handle delete checkpoint button click."""
        if not self.selected_save_game or not self.current_timeline:
            self._show_error("No save game or timeline selected.")
            return

        try:
            selection = self.view.get_selected_checkpoint()
            if selection is None:
                self._show_error("No checkpoint selected.")
                return

            checkpoints = self.get_current_checkpoints()
            if not (0 <= selection < len(checkpoints)):
                self._show_error("Invalid checkpoint selection.")
                return

            selected_checkpoint = checkpoints[selection]

            from yacl.ui.dialogs.input_dialog import show_confirmation_dialog

            # Confirm deletion
            confirmed = show_confirmation_dialog(
                self.view.parent_frame,
                "Confirm Checkpoint Deletion",
                f"Are you sure you want to delete the selected checkpoint and all commits after it?\n\n"
                f"Checkpoint: {selected_checkpoint['hash'][:8]}... - {selected_checkpoint['message']}\n\n"
                f"This action cannot be undone!"
            )

            if not confirmed:
                return

            # Disable button during operation
            self.view.delete_checkpoint_button.config(state=tk.DISABLED)

            # Find the parent commit to reset to
            if selection == len(checkpoints) - 1:
                # This is the oldest commit, can't delete it
                self._show_error("Cannot delete the initial commit.")
                return

            # Reset to the commit before the selected one
            target_commit = checkpoints[selection + 1]

            # Perform the reset using timeline manager
            success = self._reset_to_checkpoint(target_commit['hash'])

            if success:
                self.logger.info(f"Successfully reset to checkpoint: {target_commit['hash'][:8]}")
                # Refresh displays
                self._update_save_game_display()
                self.refresh_checkpoint_display()

                from yacl.ui.dialogs.input_dialog import show_info_dialog
                show_info_dialog(
                    self.view.parent_frame,
                    "Success",
                    "Checkpoint deleted successfully!"
                )
            else:
                self._show_error("Failed to delete checkpoint. Check logs for details.")

        except Exception as e:
            self.logger.error(f"Failed to delete checkpoint: {e}")
            self._show_error(f"Failed to delete checkpoint: {str(e)}")
        finally:
            # Re-enable button
            self.view.delete_checkpoint_button.config(state=tk.NORMAL)

    def on_restore_checkpoint(self):
        """Handle restore checkpoint button click."""
        if not self.selected_save_game or not self.current_timeline:
            self._show_error("No save game or timeline selected.")
            return

        try:
            selection = self.view.get_selected_checkpoint()
            if selection is None:
                self._show_error("No checkpoint selected.")
                return

            checkpoints = self.get_current_checkpoints()
            if not (0 <= selection < len(checkpoints)):
                self._show_error("Invalid checkpoint selection.")
                return

            selected_checkpoint = checkpoints[selection]

            # Check if there are commits after this one
            has_commits_after = selection > 0

            if has_commits_after:
                # Need to create a new branch
                from yacl.ui.dialogs.input_dialog import show_branch_name_dialog

                branch_name = show_branch_name_dialog(
                    self.view.parent_frame,
                    self.selected_save_game.name
                )

                if branch_name is None:  # User cancelled
                    return

                # Disable button during operation
                self.view.restore_checkpoint_button.config(state=tk.DISABLED)

                # Create and checkout new branch
                success = self._create_and_checkout_branch(branch_name, selected_checkpoint['hash'])

                if success:
                    self.logger.info(f"Successfully created and checked out branch: {branch_name}")
                    # Refresh displays
                    self._update_save_game_display()
                    self.refresh_checkpoint_display()

                    from yacl.ui.dialogs.input_dialog import show_info_dialog
                    show_info_dialog(
                        self.view.parent_frame,
                        "Success",
                        f"Created new branch '{branch_name}' and restored to checkpoint!"
                    )
                else:
                    self._show_error("Failed to create branch and restore checkpoint.")
            else:
                # This is the latest commit on the branch, we can reset to it instead of checkout
                self.view.restore_checkpoint_button.config(state=tk.DISABLED)

                success = self._reset_to_checkpoint(selected_checkpoint['hash'])

                if success:
                    self.logger.info(f"Successfully reset to checkpoint: {selected_checkpoint['hash'][:8]}")
                    # Refresh displays
                    self._update_save_game_display()
                    self.refresh_checkpoint_display()

                    from yacl.ui.dialogs.input_dialog import show_info_dialog
                    show_info_dialog(
                        self.view.parent_frame,
                        "Success",
                        "Checkpoint restored successfully!"
                    )
                else:
                    self._show_error("Failed to restore checkpoint.")

        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint: {e}")
            self._show_error(f"Failed to restore checkpoint: {str(e)}")
        finally:
            # Re-enable button
            self.view.restore_checkpoint_button.config(state=tk.NORMAL)

    # Helper methods for Git operations

    def _reset_to_checkpoint(self, commit_hash: str) -> bool:
        """
        Reset the repository to a specific checkpoint.

        Args:
            commit_hash: The commit hash to reset to

        Returns:
            True if successful, False otherwise
        """
        try:
            from dulwich.repo import Repo
            from yacl.utils.git_ops import reset_to_commit

            # Check if we have a current timeline
            if not self.current_timeline:
                self.logger.error("No current timeline available")
                return False

            # Open the worktree repository
            timeline = self.current_timeline
            wt_repo = Repo(str(timeline.worktree_path))

            # Perform hard reset
            success = reset_to_commit(wt_repo, commit_hash, hard=True)

            if success:
                self.logger.info(f"Successfully reset to commit: {commit_hash}")
                return True
            else:
                self.logger.error(f"Failed to reset to commit: {commit_hash}")
                return False

        except Exception as e:
            self.logger.error(f"Error resetting to checkpoint: {e}")
            return False

    def _checkout_checkpoint(self, commit_hash: str) -> bool:
        """
        Checkout a specific checkpoint.

        Args:
            commit_hash: The commit hash to checkout

        Returns:
            True if successful, False otherwise
        """
        try:
            from dulwich.repo import Repo
            from yacl.utils.git_ops import checkout_commit

            # Check if we have a current timeline
            if not self.current_timeline:
                self.logger.error("No current timeline available")
                return False

            # Open the worktree repository
            timeline = self.current_timeline
            wt_repo = Repo(str(timeline.worktree_path))

            # Checkout the commit
            success = checkout_commit(wt_repo, commit_hash)

            if success:
                self.logger.info(f"Successfully checked out commit: {commit_hash}")
                return True
            else:
                self.logger.error(f"Failed to checkout commit: {commit_hash}")
                return False

        except Exception as e:
            self.logger.error(f"Error checking out checkpoint: {e}")
            return False

    def _create_and_checkout_branch(self, branch_name: str, commit_hash: str) -> bool:
        """
        Create a new branch from a specific commit and checkout to it.

        Args:
            branch_name: Name of the new branch
            commit_hash: The commit hash to start the branch from

        Returns:
            True if successful, False otherwise
        """
        try:
            from dulwich.repo import Repo
            from yacl.utils.git_ops import create_branch, checkout_branch

            # Check if we have a current timeline
            if not self.current_timeline:
                self.logger.error("No current timeline available")
                return False

            # Open the worktree repository
            timeline = self.current_timeline
            wt_repo = Repo(str(timeline.worktree_path))

            # Create the branch
            if not create_branch(wt_repo, branch_name, commit_hash):
                self.logger.error(f"Failed to create branch: {branch_name}")
                return False

            # Checkout the new branch
            if not checkout_branch(wt_repo, branch_name):
                self.logger.error(f"Failed to checkout branch: {branch_name}")
                return False

            self.logger.info(f"Successfully created and checked out branch: {branch_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating and checking out branch: {e}")
            return False

    def _switch_to_branch(self, branch_name: str) -> bool:
        """
        Switch to an existing branch.

        Args:
            branch_name: Name of the branch to switch to

        Returns:
            True if successful, False otherwise
        """
        try:
            from dulwich.repo import Repo
            from yacl.utils.git_ops import checkout_branch

            # Check if we have a current timeline
            if not self.current_timeline:
                self.logger.error("No current timeline available")
                return False

            # Open the worktree repository
            timeline = self.current_timeline
            wt_repo = Repo(str(timeline.worktree_path))

            # Checkout the branch
            success = checkout_branch(wt_repo, branch_name)

            if success:
                self.logger.info(f"Successfully switched to branch: {branch_name}")
                return True
            else:
                self.logger.error(f"Failed to switch to branch: {branch_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error switching to branch: {e}")
            return False
