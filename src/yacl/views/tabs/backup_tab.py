"""
Backup Tab Implementation for YACL

This module provides the backup management tab UI components with backup listing,
details display, and backup operations using Tkinter.
This is the View component in the MVC pattern - it only handles UI rendering and layout.
"""

from typing import Optional, List
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.base_tab import BaseTab
from yacl.services.events import EventManager
from yacl.services.icon_service import load_icon


class BackupTab(BaseTab):
    """
    Backup management tab view for YACL using Tkinter.

    This view provides UI components for:
    - Backup listing for current game type
    - Backup details display
    - Backup operations (create, delete, restore)
    - Backup name input for creation
    """

    def __init__(self, parent_frame: ttk.Frame, event_manager: EventManager):
        """
        Initialize the backup tab view.

        Args:
            parent_frame: The parent frame to create content in
            event_manager: Event manager for component communication
        """
        # Initialize the base tab
        super().__init__(parent_frame, event_manager)

        # UI widget references
        self.backup_listbox: Optional[tk.Listbox] = None
        self.details_text: Optional[tk.Text] = None
        self.refresh_button: Optional[ttk.Button] = None
        self.delete_button: Optional[ttk.Button] = None
        self.restore_button: Optional[ttk.Button] = None
        self.backup_name_entry: Optional[ttk.Entry] = None
        self.create_button: Optional[ttk.Button] = None
        self.backup_name_var: Optional[tk.StringVar] = None

    def _create_tab_content(self):
        """Create the backup tab specific content."""
        if not self.scrollable_frame:
            return

        # Main container
        main_container = ttk.Frame(self.scrollable_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the two-column top section
        self._create_top_section(main_container)

        # Create action buttons row
        self._create_action_buttons(main_container)

        # Create backup creation form
        self._create_backup_form(main_container)

    def _create_top_section(self, parent: ttk.Frame):
        """Create the two-column top section with backup list and details."""
        # Top section frame
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configure grid weights for equal columns
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        # Left column: Backup list
        self._create_backup_list_section(top_frame)

        # Right column: Backup details
        self._create_backup_details_section(top_frame)

    def _create_backup_list_section(self, parent: ttk.Frame):
        """Create the backup list section."""
        # Left column frame
        left_frame = ttk.LabelFrame(parent, text="Backups", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Backup listbox with scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.backup_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.SINGLE,
            height=15,
            font=('TkDefaultFont', 10)
        )
        self.backup_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for backup listbox
        backup_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.backup_listbox.config(yscrollcommand=backup_scrollbar.set)
        backup_scrollbar.config(command=self.backup_listbox.yview)

    def _create_backup_details_section(self, parent: ttk.Frame):
        """Create the backup details section."""
        # Right column frame
        right_frame = ttk.LabelFrame(parent, text="Backup Details", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Details text widget with scrollbar
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)

        self.details_text = tk.Text(
            details_frame,
            wrap=tk.WORD,
            height=15,
            width=40,
            font=('TkDefaultFont', 10),
            state=tk.DISABLED
        )
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for details text
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text.config(yscrollcommand=details_scrollbar.set)
        details_scrollbar.config(command=self.details_text.yview)

    def _create_action_buttons(self, parent: ttk.Frame):
        """Create the action buttons row."""
        # Action buttons frame
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        # Refresh button
        self.refresh_button = ttk.Button(
            action_frame,
            text="Refresh",
            width=12
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))

        # Delete button
        self.delete_button = ttk.Button(
            action_frame,
            text="Delete",
            width=12,
            state=tk.DISABLED
        )
        self.delete_button.pack(side=tk.LEFT, padx=(0, 5))

        # Restore button
        self.restore_button = ttk.Button(
            action_frame,
            text="Restore",
            width=12,
            state=tk.DISABLED
        )
        self.restore_button.pack(side=tk.LEFT, padx=(0, 5))

    def _create_backup_form(self, parent: ttk.Frame):
        """Create the backup creation form."""
        # Backup form frame
        form_frame = ttk.LabelFrame(parent, text="Create New Backup", padding=10)
        form_frame.pack(fill=tk.X)

        # Input row
        input_frame = ttk.Frame(form_frame)
        input_frame.pack(fill=tk.X)

        # Backup name label and entry
        ttk.Label(input_frame, text="Backup Name:").pack(side=tk.LEFT, padx=(0, 5))

        self.backup_name_var = tk.StringVar()
        self.backup_name_entry = ttk.Entry(
            input_frame,
            textvariable=self.backup_name_var,
            width=30
        )
        self.backup_name_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        # Create button
        self.create_button = ttk.Button(
            input_frame,
            text="Create Backup",
            width=15
        )
        self.create_button.pack(side=tk.RIGHT)

    def get_selected_backup_index(self) -> Optional[int]:
        """Get the index of the currently selected backup."""
        try:
            selection = self.backup_listbox.curselection()
            return selection[0] if selection else None
        except (IndexError, AttributeError):
            return None

    def get_backup_name_input(self) -> str:
        """Get the backup name from the input field."""
        return self.backup_name_var.get().strip() if self.backup_name_var else ""

    def clear_backup_name_input(self):
        """Clear the backup name input field."""
        if self.backup_name_var:
            self.backup_name_var.set("")

    def update_backup_list(self, backup_names: List[str]):
        """Update the backup listbox with new backup names."""
        if not self.backup_listbox:
            return

        # Clear current list
        self.backup_listbox.delete(0, tk.END)

        # Add new backup names
        for name in backup_names:
            self.backup_listbox.insert(tk.END, name)

    def update_backup_details(self, details: str):
        """Update the backup details text widget."""
        if not self.details_text:
            return

        # Enable text widget for editing
        self.details_text.config(state=tk.NORMAL)
        
        # Clear current content
        self.details_text.delete(1.0, tk.END)
        
        # Insert new details
        self.details_text.insert(1.0, details)
        
        # Disable text widget to prevent editing
        self.details_text.config(state=tk.DISABLED)

    def update_button_states(self, has_selection: bool):
        """Update the state of action buttons based on selection."""
        state = tk.NORMAL if has_selection else tk.DISABLED
        
        if self.delete_button:
            self.delete_button.config(state=state)
        if self.restore_button:
            self.restore_button.config(state=state)
