"""
Checkpoint Creation Dialog for YACL

This module provides a dialog for creating timeline checkpoints with custom messages
and optional branch creation.
"""

from typing import Optional, Callable, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from yacl.ui.widgets.base_dialog import BaseDialog


class CheckpointDialog(BaseDialog):
    """
    Dialog for creating timeline checkpoints.
    
    This dialog provides:
    - Checkpoint message input
    - Optional branch creation
    - Validation and confirmation
    """
    
    def __init__(self, parent_window: tk.Widget, save_game_name: str,
                 on_checkpoint_created: Callable[[Optional[Dict[str, Any]]], None]):
        """
        Initialize the checkpoint creation dialog.

        Args:
            parent_window: Parent window for the modal dialog
            save_game_name: Name of the save game for context
            on_checkpoint_created: Callback function called when checkpoint is created or dialog is cancelled
        """
        # Initialize base dialog
        super().__init__(parent_window, f"Create Checkpoint - {save_game_name}")

        self.save_game_name = save_game_name
        self.on_checkpoint_created = on_checkpoint_created

        # Dialog state
        self.result: Optional[Dict[str, Any]] = None
        
        # UI components
        self.message_var: tk.StringVar
        self.create_branch_var: tk.BooleanVar
        self.branch_name_var: tk.StringVar
        self.message_entry: ttk.Entry
        self.branch_name_entry: ttk.Entry
        self.create_button: ttk.Button

    def _create_content(self):
        """Create the dialog content - required by BaseDialog."""
        self._create_dialog_content()

    def _create_dialog_content(self):
        """Create the dialog content."""
        # Main content frame
        content_frame = ttk.Frame(self.content_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(
            content_frame,
            text=f"Create a new checkpoint for '{self.save_game_name}'",
            font=("TkDefaultFont", 10, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Checkpoint message section
        self._create_message_section(content_frame)

        # Branch creation section
        self._create_branch_section(content_frame)

        # Buttons
        self._create_buttons(content_frame)

        # Set default focus
        self.message_entry.focus_set()

    def _create_message_section(self, parent: ttk.Frame):
        """Create the checkpoint message input section."""
        # Message frame
        message_frame = ttk.LabelFrame(parent, text="Checkpoint Message", padding=10)
        message_frame.pack(fill=tk.X, pady=(0, 15))

        # Message entry
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(
            message_frame,
            textvariable=self.message_var,
            width=50,
            font=("TkDefaultFont", 10)
        )
        self.message_entry.pack(fill=tk.X, pady=(0, 5))

        # Auto-populate with timestamp
        default_message = f"Checkpoint {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.message_var.set(default_message)

        # Help text
        help_label = ttk.Label(
            message_frame,
            text="Enter a descriptive message for this checkpoint",
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        help_label.pack(anchor=tk.W)

    def _create_branch_section(self, parent: ttk.Frame):
        """Create the branch creation section."""
        # Branch frame
        branch_frame = ttk.LabelFrame(parent, text="Branch Options", padding=10)
        branch_frame.pack(fill=tk.X, pady=(0, 15))

        # Create branch checkbox
        self.create_branch_var = tk.BooleanVar()
        create_branch_check = ttk.Checkbutton(
            branch_frame,
            text="Create new branch from this checkpoint",
            variable=self.create_branch_var,
            command=self._on_create_branch_toggled
        )
        create_branch_check.pack(anchor=tk.W, pady=(0, 5))

        # Branch name entry
        branch_name_frame = ttk.Frame(branch_frame)
        branch_name_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(branch_name_frame, text="Branch name:").pack(side=tk.LEFT)

        self.branch_name_var = tk.StringVar()
        self.branch_name_entry = ttk.Entry(
            branch_name_frame,
            textvariable=self.branch_name_var,
            width=30,
            state=tk.DISABLED
        )
        self.branch_name_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)

    def _create_buttons(self, parent: ttk.Frame):
        """Create the dialog buttons."""
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        # Create button
        self.create_button = ttk.Button(
            button_frame,
            text="Create Checkpoint",
            command=self._on_create_clicked,
            width=15
        )
        self.create_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=15
        )
        cancel_button.pack(side=tk.RIGHT)

    def _on_create_branch_toggled(self):
        """Handle create branch checkbox toggle."""
        if self.create_branch_var.get():
            self.branch_name_entry.config(state=tk.NORMAL)
            # Auto-populate branch name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.branch_name_var.set(f"{self.save_game_name}_branch_{timestamp}")
            self.branch_name_entry.focus_set()
        else:
            self.branch_name_entry.config(state=tk.DISABLED)
            self.branch_name_var.set("")

    def _on_create_clicked(self):
        """Handle create button click."""
        # Validate input
        message = self.message_var.get().strip()
        if not message:
            messagebox.showerror("Error", "Please enter a checkpoint message.")
            self.message_entry.focus_set()
            return

        create_branch = self.create_branch_var.get()
        branch_name = self.branch_name_var.get().strip() if create_branch else None

        if create_branch and not branch_name:
            messagebox.showerror("Error", "Please enter a branch name.")
            self.branch_name_entry.focus_set()
            return

        # Validate branch name format
        if branch_name and not self._is_valid_branch_name(branch_name):
            messagebox.showerror(
                "Error",
                "Branch name can only contain letters, numbers, hyphens, and underscores."
            )
            self.branch_name_entry.focus_set()
            return

        # Create result
        self.result = {
            "message": message,
            "create_branch": create_branch,
            "branch_name": branch_name
        }

        self._close_dialog()

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.result = None
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog and call the callback."""
        self.close()
        if self.on_checkpoint_created:
            self.on_checkpoint_created(self.result)

    def _is_valid_branch_name(self, name: str) -> bool:
        """
        Validate branch name format.
        
        Args:
            name: Branch name to validate
            
        Returns:
            bool: True if valid
        """
        if not name:
            return False
        
        # Basic validation - alphanumeric, hyphens, underscores
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

    def show_modal(self) -> Optional[Dict[str, Any]]:
        """
        Show the dialog modally and return the result.

        Returns:
            Dictionary with checkpoint data or None if cancelled
        """
        # Show the dialog
        self.show(width=500, height=350, resizable=False, use_scrolling=False)

        # Wait for dialog to close
        self.modal_window.wait_window()

        return self.result


class BranchDialog(BaseDialog):
    """
    Dialog for creating new branches.
    
    This dialog provides:
    - Branch name input
    - Source checkpoint selection
    - Validation and confirmation
    """
    
    def __init__(self, parent_window: tk.Widget, save_game_name: str, current_checkpoint: str,
                 on_branch_created: Callable[[Optional[str]], None]):
        """
        Initialize the branch creation dialog.

        Args:
            parent_window: Parent window for the modal dialog
            save_game_name: Name of the save game for context
            current_checkpoint: Current checkpoint hash for context
            on_branch_created: Callback function called when branch is created or dialog is cancelled
        """
        # Initialize base dialog
        super().__init__(parent_window, f"Create Branch - {save_game_name}")

        self.save_game_name = save_game_name
        self.current_checkpoint = current_checkpoint
        self.on_branch_created = on_branch_created

        # Dialog state
        self.result: Optional[str] = None
        
        # UI components
        self.branch_name_var: tk.StringVar
        self.branch_name_entry: ttk.Entry
        self.create_button: ttk.Button

    def _create_content(self):
        """Create the dialog content - required by BaseDialog."""
        self._create_dialog_content()

    def _create_dialog_content(self):
        """Create the dialog content."""
        # Main content frame
        content_frame = ttk.Frame(self.content_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(
            content_frame,
            text=f"Create a new branch for '{self.save_game_name}'",
            font=("TkDefaultFont", 10, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Current checkpoint info
        info_label = ttk.Label(
            content_frame,
            text=f"Branch will be created from current checkpoint: {self.current_checkpoint[:8]}",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        info_label.pack(pady=(0, 15))

        # Branch name section
        self._create_branch_name_section(content_frame)

        # Buttons
        self._create_buttons(content_frame)

        # Set default focus
        self.branch_name_entry.focus_set()

    def _create_branch_name_section(self, parent: ttk.Frame):
        """Create the branch name input section."""
        # Branch name frame
        name_frame = ttk.LabelFrame(parent, text="Branch Name", padding=10)
        name_frame.pack(fill=tk.X, pady=(0, 15))

        # Branch name entry
        self.branch_name_var = tk.StringVar()
        self.branch_name_entry = ttk.Entry(
            name_frame,
            textvariable=self.branch_name_var,
            width=40,
            font=("TkDefaultFont", 10)
        )
        self.branch_name_entry.pack(fill=tk.X, pady=(0, 5))

        # Auto-populate with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"{self.save_game_name}_branch_{timestamp}"
        self.branch_name_var.set(default_name)

        # Help text
        help_label = ttk.Label(
            name_frame,
            text="Enter a unique name for the new branch (letters, numbers, hyphens, underscores only)",
            font=("TkDefaultFont", 8),
            foreground="gray"
        )
        help_label.pack(anchor=tk.W)

    def _create_buttons(self, parent: ttk.Frame):
        """Create the dialog buttons."""
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        # Create button
        self.create_button = ttk.Button(
            button_frame,
            text="Create Branch",
            command=self._on_create_clicked,
            width=15
        )
        self.create_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=15
        )
        cancel_button.pack(side=tk.RIGHT)

    def _on_create_clicked(self):
        """Handle create button click."""
        # Validate input
        branch_name = self.branch_name_var.get().strip()
        if not branch_name:
            messagebox.showerror("Error", "Please enter a branch name.")
            self.branch_name_entry.focus_set()
            return

        # Validate branch name format
        if not self._is_valid_branch_name(branch_name):
            messagebox.showerror(
                "Error",
                "Branch name can only contain letters, numbers, hyphens, and underscores."
            )
            self.branch_name_entry.focus_set()
            return

        self.result = branch_name
        self._close_dialog()

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.result = None
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog and call the callback."""
        self.close()
        if self.on_branch_created:
            self.on_branch_created(self.result)

    def _is_valid_branch_name(self, name: str) -> bool:
        """
        Validate branch name format.
        
        Args:
            name: Branch name to validate
            
        Returns:
            bool: True if valid
        """
        if not name:
            return False
        
        # Basic validation - alphanumeric, hyphens, underscores
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

    def show_modal(self) -> Optional[str]:
        """
        Show the dialog modally and return the result.

        Returns:
            Branch name or None if cancelled
        """
        # Show the dialog
        self.show(width=450, height=300, resizable=False, use_scrolling=False)

        # Wait for dialog to close
        self.modal_window.wait_window()

        return self.result
