"""
Timeline Tab Implementation for YACL

This module provides the timeline management tab UI components with timeline listing,
checkpoint display, and timeline operations using Tkinter.
This is the View component in the MVC pattern - it only handles UI rendering and layout.
"""

from typing import Optional, List
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from yacl.ui.widgets.base_tab import BaseTab
from yacl.services.events import EventManager
from yacl.services.icon_service import load_icon


class TimelineTab(BaseTab):
    """
    Timeline management tab view for YACL using Tkinter.

    This view provides UI components for:
    - Timeline listing for current game type
    - Checkpoint history display
    - Timeline operations (create checkpoint, restore, branch)
    - Save game selection and timeline management
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

        # UI widget references
        self.save_game_listbox: tk.Listbox
        self.timeline_info_text: tk.Text
        self.checkpoint_listbox: tk.Listbox
        self.checkpoint_details_text: tk.Text
        self.refresh_button: ttk.Button
        self.create_timeline_button: ttk.Button
        self.create_checkpoint_button: ttk.Button
        self.restore_checkpoint_button: ttk.Button
        self.create_branch_button: ttk.Button
        self.switch_branch_button: ttk.Button
        self.checkpoint_message_entry: ttk.Entry
        self.checkpoint_message_var: tk.StringVar
        self.current_branch_label: ttk.Label
        self.branch_combobox: ttk.Combobox

    def _create_tab_content(self):
        """Create the timeline tab specific content."""
        if not self.scrollable_frame:
            return

        # Main container
        main_container = ttk.Frame(self.scrollable_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the top section with save games and timeline info
        self._create_top_section(main_container)

        # Create the middle section with checkpoints and details
        self._create_middle_section(main_container)

        # Create action buttons row
        self._create_action_buttons(main_container)

        # Create checkpoint creation form
        self._create_checkpoint_form(main_container)

    def _create_top_section(self, parent: ttk.Frame):
        """Create the top section with save games list and timeline info."""
        # Top section frame
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configure grid weights for equal columns
        top_frame.grid_columnconfigure(0, weight=1, uniform="top_columns")
        top_frame.grid_columnconfigure(1, weight=1, uniform="top_columns")
        top_frame.grid_rowconfigure(0, weight=1)

        # Left column: Save games list
        self._create_save_games_section(top_frame)

        # Right column: Timeline info
        self._create_timeline_info_section(top_frame)

    def _create_save_games_section(self, parent: ttk.Frame):
        """Create the save games list section."""
        # Left column frame
        left_frame = ttk.LabelFrame(parent, text="Save Games", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Save games listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.save_game_listbox = tk.Listbox(
            listbox_frame,
            height=8,
            selectmode=tk.SINGLE,
            font=("Consolas", 10)
        )
        self.save_game_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for save games list
        save_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.save_game_listbox.yview)
        save_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.save_game_listbox.config(yscrollcommand=save_scrollbar.set)

    def _create_timeline_info_section(self, parent: ttk.Frame):
        """Create the timeline info section."""
        # Right column frame
        right_frame = ttk.LabelFrame(parent, text="Timeline Info", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Timeline info text with scrollbar
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)

        self.timeline_info_text = tk.Text(
            info_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9)
        )
        self.timeline_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for timeline info
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.timeline_info_text.yview)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.timeline_info_text.config(yscrollcommand=info_scrollbar.set)

    def _create_middle_section(self, parent: ttk.Frame):
        """Create the middle section with checkpoints and details."""
        # Middle section frame
        middle_frame = ttk.Frame(parent)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configure grid weights for equal columns
        middle_frame.grid_columnconfigure(0, weight=1, uniform="middle_columns")
        middle_frame.grid_columnconfigure(1, weight=1, uniform="middle_columns")
        middle_frame.grid_rowconfigure(0, weight=1)

        # Left column: Checkpoints list
        self._create_checkpoints_section(middle_frame)

        # Right column: Checkpoint details
        self._create_checkpoint_details_section(middle_frame)

    def _create_checkpoints_section(self, parent: ttk.Frame):
        """Create the checkpoints list section."""
        # Left column frame
        left_frame = ttk.LabelFrame(parent, text="Checkpoints", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Current branch info
        branch_frame = ttk.Frame(left_frame)
        branch_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(branch_frame, text="Current Branch:").pack(side=tk.LEFT)
        self.current_branch_label = ttk.Label(branch_frame, text="No timeline selected", foreground="blue")
        self.current_branch_label.pack(side=tk.LEFT, padx=(5, 0))

        # Checkpoints listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.checkpoint_listbox = tk.Listbox(
            listbox_frame,
            height=8,
            selectmode=tk.SINGLE,
            font=("Consolas", 9)
        )
        self.checkpoint_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for checkpoints list
        checkpoint_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.checkpoint_listbox.yview)
        checkpoint_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.checkpoint_listbox.config(yscrollcommand=checkpoint_scrollbar.set)

    def _create_checkpoint_details_section(self, parent: ttk.Frame):
        """Create the checkpoint details section."""
        # Right column frame
        right_frame = ttk.LabelFrame(parent, text="Checkpoint Details", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Checkpoint details text with scrollbar
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)

        self.checkpoint_details_text = tk.Text(
            details_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9)
        )
        self.checkpoint_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for checkpoint details
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.checkpoint_details_text.yview)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.checkpoint_details_text.config(yscrollcommand=details_scrollbar.set)

    def _create_action_buttons(self, parent: ttk.Frame):
        """Create the action buttons row."""
        # Action buttons frame
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        # Center the buttons
        button_container = ttk.Frame(action_frame)
        button_container.pack(anchor=tk.CENTER)

        # Refresh button
        self.refresh_button = ttk.Button(
            button_container,
            text="Refresh",
            width=12
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))

        # Create timeline button (for save games without timelines)
        self.create_timeline_button = ttk.Button(
            button_container,
            text="Create Timeline",
            width=12,
            state=tk.DISABLED
        )
        self.create_timeline_button.pack(side=tk.LEFT, padx=5)

        # Restore checkpoint button
        self.restore_checkpoint_button = ttk.Button(
            button_container,
            text="Restore",
            width=12,
            state=tk.DISABLED
        )
        self.restore_checkpoint_button.pack(side=tk.LEFT, padx=5)

        # Create branch button
        self.create_branch_button = ttk.Button(
            button_container,
            text="Create Branch",
            width=12,
            state=tk.DISABLED
        )
        self.create_branch_button.pack(side=tk.LEFT, padx=5)

        # Branch selection and switch
        branch_frame = ttk.Frame(button_container)
        branch_frame.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(branch_frame, text="Branch:").pack(side=tk.LEFT)
        self.branch_combobox = ttk.Combobox(branch_frame, width=15, state="readonly")
        self.branch_combobox.pack(side=tk.LEFT, padx=(5, 5))

        self.switch_branch_button = ttk.Button(
            branch_frame,
            text="Switch",
            width=8,
            state=tk.DISABLED
        )
        self.switch_branch_button.pack(side=tk.LEFT)

    def _create_checkpoint_form(self, parent: ttk.Frame):
        """Create the checkpoint creation form."""
        # Checkpoint form frame
        form_frame = ttk.LabelFrame(parent, text="Create Checkpoint", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # Message entry
        entry_frame = ttk.Frame(form_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(entry_frame, text="Message:").pack(side=tk.LEFT)

        self.checkpoint_message_var = tk.StringVar()
        self.checkpoint_message_entry = ttk.Entry(
            entry_frame,
            textvariable=self.checkpoint_message_var,
            width=50
        )
        self.checkpoint_message_entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)

        # Create checkpoint button
        self.create_checkpoint_button = ttk.Button(
            entry_frame,
            text="Create Checkpoint",
            width=15,
            state=tk.DISABLED
        )
        self.create_checkpoint_button.pack(side=tk.RIGHT)

    def _setup_event_handlers(self):
        """Setup event handlers for UI components."""
        # This will be implemented by the controller
        pass

    def _refresh_ui(self):
        """Refresh the UI state."""
        # This will be implemented by the controller
        pass

    # UI Helper Methods
    def clear_save_games_list(self):
        """Clear the save games list."""
        self.save_game_listbox.delete(0, tk.END)

    def add_save_game_to_list(self, save_name: str, has_timeline: bool = False):
        """Add a save game to the list."""
        display_text = f"{'[T] ' if has_timeline else '[ ] '}{save_name}"
        self.save_game_listbox.insert(tk.END, display_text)

    def get_selected_save_game_index(self) -> Optional[int]:
        """Get the selected save game index."""
        selection = self.save_game_listbox.curselection()
        return selection[0] if selection else None

    def set_selected_save_game_index(self, index: int):
        """Set the selected save game index."""
        print(f"[DEBUG_VIEW] Setting save game selection to index: {index}, listbox size: {self.save_game_listbox.size()}")
        if 0 <= index < self.save_game_listbox.size():
            self.save_game_listbox.selection_clear(0, tk.END)
            self.save_game_listbox.selection_set(index)
            self.save_game_listbox.see(index)  # Ensure the item is visible
            print(f"[DEBUG_VIEW] Save game selection set successfully")
        else:
            print(f"[DEBUG_VIEW] Invalid save game index: {index}")

    def clear_timeline_info(self):
        """Clear the timeline info display."""
        self.timeline_info_text.config(state=tk.NORMAL)
        self.timeline_info_text.delete(1.0, tk.END)
        self.timeline_info_text.config(state=tk.DISABLED)

    def set_timeline_info(self, info_text: str):
        """Set the timeline info display."""
        self.timeline_info_text.config(state=tk.NORMAL)
        self.timeline_info_text.delete(1.0, tk.END)
        self.timeline_info_text.insert(1.0, info_text)
        self.timeline_info_text.config(state=tk.DISABLED)

    def clear_checkpoints_list(self):
        """Clear the checkpoints list."""
        self.checkpoint_listbox.delete(0, tk.END)

    def add_checkpoint_to_list(self, checkpoint_text: str):
        """Add a checkpoint to the list."""
        self.checkpoint_listbox.insert(tk.END, checkpoint_text)

    def get_selected_checkpoint_index(self) -> Optional[int]:
        """Get the selected checkpoint index."""
        selection = self.checkpoint_listbox.curselection()
        return selection[0] if selection else None

    def set_selected_checkpoint_index(self, index: int):
        """Set the selected checkpoint index."""
        print(f"[DEBUG_VIEW] Setting checkpoint selection to index: {index}, listbox size: {self.checkpoint_listbox.size()}")
        print(f"[DEBUG_VIEW] Save game listbox current selection before: {self.save_game_listbox.curselection()}")

        if 0 <= index < self.checkpoint_listbox.size():
            self.checkpoint_listbox.selection_clear(0, tk.END)
            self.checkpoint_listbox.selection_set(index)
            self.checkpoint_listbox.see(index)  # Ensure the item is visible
            print(f"[DEBUG_VIEW] Checkpoint selection set successfully")
        else:
            print(f"[DEBUG_VIEW] Invalid checkpoint index: {index}")

        print(f"[DEBUG_VIEW] Save game listbox current selection after: {self.save_game_listbox.curselection()}")

    def clear_checkpoint_details(self):
        """Clear the checkpoint details display."""
        self.checkpoint_details_text.config(state=tk.NORMAL)
        self.checkpoint_details_text.delete(1.0, tk.END)
        self.checkpoint_details_text.config(state=tk.DISABLED)

    def set_checkpoint_details(self, details_text: str):
        """Set the checkpoint details display."""
        self.checkpoint_details_text.config(state=tk.NORMAL)
        self.checkpoint_details_text.delete(1.0, tk.END)
        self.checkpoint_details_text.insert(1.0, details_text)
        self.checkpoint_details_text.config(state=tk.DISABLED)

    def set_current_branch(self, branch_name: str):
        """Set the current branch display."""
        self.current_branch_label.config(text=branch_name)

    def set_branches(self, branches: List[str]):
        """Set the available branches in the combobox."""
        self.branch_combobox['values'] = branches

    def get_checkpoint_message(self) -> str:
        """Get the checkpoint message from the entry."""
        return self.checkpoint_message_var.get().strip()

    def clear_checkpoint_message(self):
        """Clear the checkpoint message entry."""
        self.checkpoint_message_var.set("")

    def get_selected_branch(self) -> str:
        """Get the selected branch from the combobox."""
        return self.branch_combobox.get()

    def enable_timeline_operations(self, enabled: bool = True):
        """Enable or disable timeline operation buttons."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.create_checkpoint_button.config(state=state)
        self.restore_checkpoint_button.config(state=state)
        self.create_branch_button.config(state=state)
        self.switch_branch_button.config(state=state)

    def enable_checkpoint_operations(self, enabled: bool = True):
        """Enable or disable checkpoint-specific operations."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.restore_checkpoint_button.config(state=state)
        self.create_branch_button.config(state=state)

    def enable_create_timeline_button(self, enabled: bool = True):
        """Enable or disable the create timeline button."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.create_timeline_button.config(state=state)

    def show_timeline_creation_mode(self, show: bool = True):
        """Show or hide timeline creation mode UI elements."""
        if show:
            # Show create timeline button, hide timeline operations
            self.create_timeline_button.config(state=tk.NORMAL)
            self.enable_timeline_operations(False)
        else:
            # Hide create timeline button, show timeline operations
            self.create_timeline_button.config(state=tk.DISABLED)
            self.enable_timeline_operations(True)
