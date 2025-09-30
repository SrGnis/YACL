"""
Input Dialog Utilities for YACL

This module provides simple dialog utilities for user input including text input
and confirmation dialogs using tkinter's built-in dialogs.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional


def show_text_input_dialog(parent: tk.Widget, title: str, prompt: str, 
                          initial_value: str = "") -> Optional[str]:
    """
    Show a text input dialog to get user input.
    
    Args:
        parent: Parent window for the dialog
        title: Dialog title
        prompt: Prompt text to show to user
        initial_value: Initial value for the text field
        
    Returns:
        User input string or None if cancelled
    """
    try:
        result = simpledialog.askstring(
            title=title,
            prompt=prompt,
            initialvalue=initial_value,
            parent=parent
        )
        return result
    except Exception:
        return None


def show_confirmation_dialog(parent: tk.Widget, title: str, message: str) -> bool:
    """
    Show a yes/no confirmation dialog.
    
    Args:
        parent: Parent window for the dialog
        title: Dialog title
        message: Message to show to user
        
    Returns:
        True if user clicked Yes, False otherwise
    """
    try:
        result = messagebox.askyesno(title, message, parent=parent)
        return result
    except Exception:
        return False


def show_error_dialog(parent: tk.Widget, title: str, message: str):
    """
    Show an error message dialog.
    
    Args:
        parent: Parent window for the dialog
        title: Dialog title
        message: Error message to show
    """
    try:
        messagebox.showerror(title, message, parent=parent)
    except Exception:
        pass


def show_info_dialog(parent: tk.Widget, title: str, message: str):
    """
    Show an information message dialog.
    
    Args:
        parent: Parent window for the dialog
        title: Dialog title
        message: Information message to show
    """
    try:
        messagebox.showinfo(title, message, parent=parent)
    except Exception:
        pass


def show_warning_dialog(parent: tk.Widget, title: str, message: str):
    """
    Show a warning message dialog.
    
    Args:
        parent: Parent window for the dialog
        title: Dialog title
        message: Warning message to show
    """
    try:
        messagebox.showwarning(title, message, parent=parent)
    except Exception:
        pass


def validate_branch_name(branch_name: str, save_name: str) -> Optional[str]:
    """
    Validate and format a branch name according to YACL conventions.

    Args:
        branch_name: The branch name to validate
        save_name: The save game name to use as prefix

    Returns:
        Formatted branch name or None if invalid
    """
    if not branch_name or not branch_name.strip():
        return None

    # Clean the branch name (replace spaces with underscores, convert to lowercase)
    clean_branch = branch_name.strip().replace(" ", "_").lower()

    # Remove invalid characters for git branch names
    import re
    clean_branch = re.sub(r'[^a-zA-Z0-9\-_]', '', clean_branch)

    if not clean_branch:
        return None

    # Clean the save name as well (replace spaces with underscores, convert to lowercase)
    # This matches the pattern used in timeline_manager.py
    clean_save_name = save_name.replace(' ', '_').lower()

    # Format according to YACL convention: save_name-branch_name
    formatted_name = f"{clean_save_name}-{clean_branch}"

    return formatted_name


def show_branch_name_dialog(parent: tk.Widget, save_name: str) -> Optional[str]:
    """
    Show a dialog to get a branch name from the user with validation.

    Args:
        parent: Parent window for the dialog
        save_name: The save game name to use as prefix

    Returns:
        Validated branch name or None if cancelled/invalid
    """
    # Format the save name for display (same as what will be used)
    clean_save_name = save_name.replace(' ', '_').lower()

    while True:
        branch_name = show_text_input_dialog(
            parent,
            "Create New Branch",
            f"Enter branch name (will be formatted as '{clean_save_name}-<name>'):"
        )
        
        if branch_name is None:  # User cancelled
            return None
        
        validated_name = validate_branch_name(branch_name, save_name)
        if validated_name:
            return validated_name
        else:
            show_error_dialog(
                parent,
                "Invalid Branch Name",
                "Branch name must contain only letters, numbers, hyphens, and underscores."
            )
