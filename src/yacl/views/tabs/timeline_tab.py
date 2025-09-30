"""
Timeline Tab Implementation for YACL

This module provides the timeline management tab UI components with save game listing,
timeline initialization, branch management, and checkpoint operations using Tkinter.
This is the View component in the MVC pattern - it only handles UI rendering and layout.
"""

from typing import Optional, List, Dict
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.base_tab import BaseTab
from yacl.services.events import EventManager
from yacl.services.icon_service import load_icon
from yacl.models.game_type import GameType


class TimelineTab(BaseTab):
    """
    Timeline management tab view for YACL using Tkinter.

    This view provides UI components for:
    - Save game listing for current game type
    - Timeline initialization and management
    - Branch selection and management
    - Checkpoint operations (UI only, functionality to be implemented)
    """

    def __init__(self, parent_frame: ttk.Frame, event_manager: EventManager):
        """
        Initialize the timeline tab view.

        Args:
            parent_frame: The parent frame to create content in
            event_manager: Event manager for component communication
        """
        # Initialize the base tab
        super().__init__(parent_frame, event_manager)

        # UI widget references for save game management
        self.save_games_listbox: tk.Listbox
        self.save_game_info_text: tk.Text
        self.initialize_timeline_button: ttk.Button
        self.delete_timeline_button: ttk.Button

        # UI widget references for branch management
        self.branch_selector: ttk.Combobox
        self.current_branch_label: ttk.Label
        self.branch_info_text: tk.Text

        # UI widget references for checkpoint management (placeholder)
        self.checkpoints_listbox: tk.Listbox
        self.checkpoint_info_text: tk.Text
        self.create_checkpoint_button: ttk.Button
        self.restore_checkpoint_button: ttk.Button
        self.delete_checkpoint_button: ttk.Button

        # State variables
        self.current_game_type: Optional[GameType] = None

        # Create the tab content
        self._create_tab_content()

        self.logger.info("Timeline tab view initialized")

    def _create_tab_content(self):
        """Create the main content of the timeline tab."""
        if not self.scrollable_frame:
            self.logger.error("Scrollable frame not available")
            return

        try:
            # Save game management section (top row)
            self._create_save_game_section(self.scrollable_frame)

            # Timeline branch management section (second row)
            self._create_branch_section(self.scrollable_frame)

            # Checkpoint management section (third row - placeholder)
            self._create_checkpoint_section(self.scrollable_frame)

        except Exception as e:
            self.logger.error(f"Failed to create timeline tab content: {e}")
            raise

    def _create_save_game_section(self, parent_frame: ttk.Frame):
        """Create the save game management section."""
        save_game_frame = self.create_section_frame(parent_frame, "Save Game Timeline Management")

        # Create two-column layout
        columns_frame = ttk.Frame(save_game_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left panel - Save games list
        left_frame = ttk.LabelFrame(columns_frame, text="Save Games", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Save games listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.save_games_listbox = tk.Listbox(
            listbox_frame,
            height=8,
            selectmode=tk.SINGLE
        )
        save_games_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.save_games_listbox.config(yscrollcommand=save_games_scrollbar.set)
        save_games_scrollbar.config(command=self.save_games_listbox.yview)

        self.save_games_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        save_games_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - Save game info and actions
        right_frame = ttk.LabelFrame(columns_frame, text="Timeline Information", padding=5)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Info display
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.save_game_info_text = tk.Text(
            info_frame,
            height=6,
            width=40,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL)
        self.save_game_info_text.config(yscrollcommand=info_scrollbar.set)
        info_scrollbar.config(command=self.save_game_info_text.yview)

        self.save_game_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X)

        self.initialize_timeline_button = ttk.Button(
            actions_frame,
            text="Initialize Timeline",
            image=load_icon("git-branch", 16) or "",
            compound=tk.LEFT,
            state=tk.DISABLED
        )
        self.initialize_timeline_button.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_timeline_button = ttk.Button(
            actions_frame,
            text="Delete Timeline",
            image=load_icon("trash-2", 16) or "",
            compound=tk.LEFT,
            state=tk.DISABLED
        )
        self.delete_timeline_button.pack(side=tk.LEFT)

    def _create_branch_section(self, parent_frame: ttk.Frame):
        """Create the timeline branch management section."""
        branch_frame = self.create_section_frame(parent_frame, "Timeline Branch Management")

        # Branch selector row
        selector_frame = ttk.Frame(branch_frame)
        selector_frame.pack(fill=tk.X, pady=5)

        ttk.Label(selector_frame, text="Current Timeline:").pack(side=tk.LEFT)

        self.branch_selector = ttk.Combobox(
            selector_frame,
            state="readonly",
            width=30
        )
        self.branch_selector.pack(side=tk.LEFT, padx=(10, 20))

        ttk.Label(selector_frame, text="Active Branch:").pack(side=tk.LEFT)

        self.current_branch_label = ttk.Label(
            selector_frame,
            text="No timeline selected",
            font=("TkDefaultFont", 9, "bold")
        )
        self.current_branch_label.pack(side=tk.LEFT, padx=(10, 0))

        # Branch info display
        info_frame = ttk.LabelFrame(branch_frame, text="Branch Information", padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.branch_info_text = tk.Text(
            info_frame,
            height=4,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        branch_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL)
        self.branch_info_text.config(yscrollcommand=branch_scrollbar.set)
        branch_scrollbar.config(command=self.branch_info_text.yview)

        self.branch_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        branch_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_checkpoint_section(self, parent_frame: ttk.Frame):
        """Create the checkpoint management section."""
        checkpoint_frame = self.create_section_frame(parent_frame, "Checkpoint Management")

        # Create two-column layout
        columns_frame = ttk.Frame(checkpoint_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left panel - Checkpoints list
        left_frame = ttk.LabelFrame(columns_frame, text="Checkpoints", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Checkpoints listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.checkpoints_listbox = tk.Listbox(
            listbox_frame,
            height=6,
            selectmode=tk.SINGLE,
            state=tk.NORMAL  # Enable the listbox
        )
        checkpoints_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.checkpoints_listbox.config(yscrollcommand=checkpoints_scrollbar.set)
        checkpoints_scrollbar.config(command=self.checkpoints_listbox.yview)

        self.checkpoints_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        checkpoints_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right panel - Checkpoint info and actions
        right_frame = ttk.LabelFrame(columns_frame, text="Checkpoint Information", padding=5)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Info display
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.checkpoint_info_text = tk.Text(
            info_frame,
            height=4,
            width=40,
            wrap=tk.WORD,
            state=tk.DISABLED  # Keep disabled for editing, but will be enabled for updates
        )
        checkpoint_info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL)
        self.checkpoint_info_text.config(yscrollcommand=checkpoint_info_scrollbar.set)
        checkpoint_info_scrollbar.config(command=self.checkpoint_info_text.yview)

        self.checkpoint_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        checkpoint_info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons (disabled for now)
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X)

        self.create_checkpoint_button = ttk.Button(
            actions_frame,
            text="Create Checkpoint",
            image=load_icon("save", 16) or "",
            compound=tk.LEFT,
            state=tk.DISABLED
        )
        self.create_checkpoint_button.pack(side=tk.LEFT, padx=(0, 5))

        self.restore_checkpoint_button = ttk.Button(
            actions_frame,
            text="Restore",
            image=load_icon("rotate-ccw", 16) or "",
            compound=tk.LEFT,
            state=tk.DISABLED
        )
        self.restore_checkpoint_button.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_checkpoint_button = ttk.Button(
            actions_frame,
            text="Delete",
            image=load_icon("trash-2", 16) or "",
            compound=tk.LEFT,
            state=tk.DISABLED
        )
        self.delete_checkpoint_button.pack(side=tk.LEFT)

    def update_save_games_list(self, save_games: List[str]):
        """Update the save games listbox with new data."""
        self.save_games_listbox.delete(0, tk.END)
        for save_game in save_games:
            self.save_games_listbox.insert(tk.END, save_game)

    def update_save_game_info(self, info_text: str):
        """Update the save game information display."""
        self.save_game_info_text.config(state=tk.NORMAL)
        self.save_game_info_text.delete(1.0, tk.END)
        self.save_game_info_text.insert(1.0, info_text)
        self.save_game_info_text.config(state=tk.DISABLED)

    def update_branch_selector(self, branches: List[str]):
        """Update the branch selector with available branches."""
        self.branch_selector['values'] = branches
        if branches:
            self.branch_selector.set(branches[0])
        else:
            self.branch_selector.set("")

    def update_current_branch(self, branch_name: str):
        """Update the current branch display."""
        self.current_branch_label.config(text=branch_name)

    def update_branch_info(self, info_text: str):
        """Update the branch information display."""
        self.branch_info_text.config(state=tk.NORMAL)
        self.branch_info_text.delete(1.0, tk.END)
        self.branch_info_text.insert(1.0, info_text)
        self.branch_info_text.config(state=tk.DISABLED)

    # Checkpoint Management Methods

    def update_checkpoints_list(self, checkpoints: List[Dict]):
        """Update the checkpoints listbox with checkpoint data."""
        try:
            # Clear current items
            self.checkpoints_listbox.delete(0, tk.END)

            # Add checkpoints to listbox
            for checkpoint in checkpoints:
                # Format: "abc1234... - Commit message"
                short_hash = checkpoint['hash'][:8]
                message = checkpoint['message']
                # Truncate long messages
                if len(message) > 50:
                    message = message[:47] + "..."
                display_text = f"{short_hash}... - {message}"
                self.checkpoints_listbox.insert(tk.END, display_text)

        except Exception as e:
            self.logger.error(f"Failed to update checkpoints list: {e}")

    def get_selected_checkpoint(self) -> Optional[int]:
        """Get the index of the currently selected checkpoint."""
        try:
            selection = self.checkpoints_listbox.curselection()
            if selection:
                return selection[0]
            return None
        except Exception as e:
            self.logger.error(f"Failed to get selected checkpoint: {e}")
            return None

    def update_checkpoint_info(self, checkpoint: Dict):
        """Update the checkpoint information display."""
        try:
            self.checkpoint_info_text.config(state=tk.NORMAL)
            self.checkpoint_info_text.delete(1.0, tk.END)

            # Format checkpoint information
            info_lines = [
                f"Commit Hash: {checkpoint['hash']}",
                f"Author: {checkpoint['author']}",
                f"Date: {checkpoint['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "Message:",
                checkpoint['message']
            ]

            info_text = "\n".join(info_lines)
            self.checkpoint_info_text.insert(1.0, info_text)
            self.checkpoint_info_text.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Failed to update checkpoint info: {e}")

    def clear_checkpoint_info(self):
        """Clear the checkpoint information display."""
        try:
            self.checkpoint_info_text.config(state=tk.NORMAL)
            self.checkpoint_info_text.delete(1.0, tk.END)
            self.checkpoint_info_text.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Failed to clear checkpoint info: {e}")

    def set_checkpoint_controls_state(self, enabled: bool):
        """Enable or disable checkpoint controls."""
        try:
            state = tk.NORMAL if enabled else tk.DISABLED
            self.checkpoints_listbox.config(state=state)
            self.checkpoint_info_text.config(state=tk.DISABLED)  # Always disabled for editing

            # Enable create button if we have a timeline
            self.create_checkpoint_button.config(state=state)

        except Exception as e:
            self.logger.error(f"Failed to set checkpoint controls state: {e}")

    def set_checkpoint_action_buttons_state(self, enabled: bool):
        """Enable or disable checkpoint action buttons (restore, delete)."""
        try:
            state = tk.NORMAL if enabled else tk.DISABLED
            self.restore_checkpoint_button.config(state=state)
            self.delete_checkpoint_button.config(state=state)

        except Exception as e:
            self.logger.error(f"Failed to set checkpoint action buttons state: {e}")

    def set_timeline_buttons_state(self, initialize_enabled: bool, delete_enabled: bool):
        """Set the state of timeline management buttons."""
        self.initialize_timeline_button.config(
            state=tk.NORMAL if initialize_enabled else tk.DISABLED
        )
        self.delete_timeline_button.config(
            state=tk.NORMAL if delete_enabled else tk.DISABLED
        )

    def set_branch_controls_state(self, enabled: bool):
        """Set the state of branch management controls."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.branch_selector.config(state="readonly" if enabled else tk.DISABLED)
