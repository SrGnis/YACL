"""
Timeline Creation Dialog for YACL

This module provides a dialog for creating new timelines for save games
that don't have timeline management yet.
"""

from typing import Optional, Callable, List
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from yacl.ui.widgets.base_dialog import BaseDialog


class TimelineCreationDialog(BaseDialog):
    """
    Dialog for creating new timelines for save games.
    
    This dialog provides:
    - Save game selection from available saves without timelines
    - Initial commit message input
    - Timeline creation confirmation
    """
    
    def __init__(self, parent_window: tk.Widget, available_saves: List[str],
                 on_timeline_created: Callable[[Optional[str]], None]):
        """
        Initialize the timeline creation dialog.

        Args:
            parent_window: Parent window for the modal dialog
            available_saves: List of save game names that don't have timelines
            on_timeline_created: Callback function called when timeline is created or dialog is cancelled
        """
        # Initialize base dialog
        super().__init__(parent_window, "Create Timeline")

        self.available_saves = available_saves
        self.on_timeline_created = on_timeline_created

        # Dialog state
        self.result: Optional[str] = None
        
        # UI components
        self.save_listbox: tk.Listbox
        self.message_var: tk.StringVar
        self.message_entry: ttk.Entry
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
            text="Create Timeline for Save Game",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        if not self.available_saves:
            # No saves available
            self._create_no_saves_content(content_frame)
        else:
            # Save selection section
            self._create_save_selection_section(content_frame)

            # Initial message section
            self._create_message_section(content_frame)

            # Buttons
            self._create_buttons(content_frame)

    def _create_no_saves_content(self, parent: ttk.Frame):
        """Create content when no saves are available."""
        # Info message
        info_label = ttk.Label(
            parent,
            text="No save games found that need timeline management.",
            font=("TkDefaultFont", 10),
            foreground="gray"
        )
        info_label.pack(pady=(20, 10))

        detail_label = ttk.Label(
            parent,
            text="All existing save games already have timelines, or no save games exist yet.",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        detail_label.pack(pady=(0, 20))

        # Close button
        close_button = ttk.Button(
            parent,
            text="Close",
            command=self._on_cancel_clicked,
            width=15
        )
        close_button.pack()

    def _create_save_selection_section(self, parent: ttk.Frame):
        """Create the save game selection section."""
        # Save selection frame
        selection_frame = ttk.LabelFrame(parent, text="Select Save Game", padding=10)
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Info text
        info_label = ttk.Label(
            selection_frame,
            text="Select a save game to create a timeline for:",
            font=("TkDefaultFont", 9)
        )
        info_label.pack(anchor=tk.W, pady=(0, 5))

        # Save games listbox with scrollbar
        listbox_frame = ttk.Frame(selection_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.save_listbox = tk.Listbox(
            listbox_frame,
            height=6,
            selectmode=tk.SINGLE,
            font=("Consolas", 10)
        )
        self.save_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for save list
        save_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.save_listbox.yview)
        save_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.save_listbox.config(yscrollcommand=save_scrollbar.set)

        # Populate the listbox
        for save_name in self.available_saves:
            self.save_listbox.insert(tk.END, save_name)

        # Select first item by default
        if self.available_saves:
            self.save_listbox.selection_set(0)

        # Bind selection event
        self.save_listbox.bind('<<ListboxSelect>>', self._on_save_selected)

    def _create_message_section(self, parent: ttk.Frame):
        """Create the initial commit message section."""
        # Message frame
        message_frame = ttk.LabelFrame(parent, text="Initial Commit Message", padding=10)
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

        # Auto-populate with default message
        default_message = f"Initial timeline commit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.message_var.set(default_message)

        # Help text
        help_label = ttk.Label(
            message_frame,
            text="This message will be used for the initial commit when creating the timeline",
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
            text="Create Timeline",
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

        # Update button state
        self._update_create_button_state()

    def _on_save_selected(self, event):
        """Handle save game selection."""
        _ = event  # Unused parameter
        self._update_create_button_state()

    def _update_create_button_state(self):
        """Update the create button state based on selection."""
        if hasattr(self, 'create_button'):
            selection = self.save_listbox.curselection()
            if selection:
                self.create_button.config(state=tk.NORMAL)
            else:
                self.create_button.config(state=tk.DISABLED)

    def _on_create_clicked(self):
        """Handle create button click."""
        # Get selected save
        selection = self.save_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a save game.")
            return

        selected_save = self.available_saves[selection[0]]

        # Validate message
        message = self.message_var.get().strip()
        if not message:
            messagebox.showerror("Error", "Please enter an initial commit message.")
            self.message_entry.focus_set()
            return

        # Confirm creation
        confirm = messagebox.askyesno(
            "Confirm Timeline Creation",
            f"Create timeline for save game '{selected_save}'?\n\n"
            f"This will initialize Git tracking for this save game and create "
            f"an initial commit with all current save files."
        )

        if confirm:
            # Actually create the timeline
            success = self._create_timeline(selected_save, message)
            if success:
                self.result = selected_save
                self._close_dialog()
            # If creation failed, dialog stays open for user to try again

    def _create_timeline(self, save_game_name: str, initial_message: str) -> bool:
        """
        Actually create the timeline for the save game.

        Args:
            save_game_name: Name of the save game
            initial_message: Initial commit message

        Returns:
            True if timeline creation succeeded, False otherwise
        """
        try:
            # Import timeline manager
            from yacl.models.timeline_manager import get_timeline_manager
            from yacl.models.installation_manager import get_installation_manager
            from yacl.models.backup import SaveGame
            from yacl.services.paths import get_paths

            timeline_manager = get_timeline_manager()
            installation_manager = get_installation_manager()

            # Get the current game type and active installation
            current_game_type = installation_manager.current_game_type
            if not current_game_type:
                messagebox.showerror("Error", "No game type is currently selected.")
                return False

            current_installation = installation_manager.get_active_installation(current_game_type)
            if not current_installation:
                messagebox.showerror("Error", "No installation is currently active.")
                return False

            # Build save game path
            paths = get_paths()
            save_path = paths.get_saves_dir(current_game_type.name) / save_game_name

            if not save_path.exists():
                messagebox.showerror("Error", f"Save game directory not found: {save_path}")
                return False

            # Create SaveGame object
            save_game = SaveGame(
                name=save_game_name,
                game=current_game_type,
                path=save_path
            )

            # Create the timeline (this method only takes save_game parameter)
            timeline = timeline_manager.create_timeline(save_game)

            if not timeline:
                messagebox.showerror("Error", "Failed to create timeline. Check logs for details.")
                return False

            # Create initial checkpoint with the custom message
            checkpoint = timeline_manager.create_checkpoint(save_game, initial_message)

            if not checkpoint:
                messagebox.showerror("Error", "Timeline created but failed to create initial checkpoint.")
                return False

            messagebox.showinfo(
                "Timeline Created",
                f"Timeline successfully created for '{save_game_name}'!\n\n"
                f"Initial commit: {initial_message}"
            )

            return True

        except Exception as e:
            messagebox.showerror(
                "Timeline Creation Failed",
                f"Failed to create timeline for '{save_game_name}':\n\n{str(e)}"
            )
            return False

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.result = None
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog and call the callback."""
        self.close()
        if self.on_timeline_created:
            self.on_timeline_created(self.result)

    def show_modal(self) -> Optional[str]:
        """
        Show the dialog modally and return the result.

        Returns:
            Selected save game name or None if cancelled
        """
        # Show the dialog
        self.show(width=500, height=800, resizable=False, use_scrolling=False)

        # Wait for dialog to close
        self.modal_window.wait_window()

        return self.result


class RestoreConfirmationDialog(BaseDialog):
    """
    Dialog for confirming checkpoint restoration.
    
    This dialog provides:
    - Checkpoint details display
    - Warning about unsaved changes
    - Restoration confirmation
    """
    
    def __init__(self, parent_window: tk.Widget, checkpoint_hash: str, checkpoint_message: str,
                 checkpoint_date: str, on_restore_confirmed: Callable[[bool], None]):
        """
        Initialize the restore confirmation dialog.

        Args:
            parent_window: Parent window for the modal dialog
            checkpoint_hash: Hash of the checkpoint to restore
            checkpoint_message: Message of the checkpoint
            checkpoint_date: Date of the checkpoint
            on_restore_confirmed: Callback function called with confirmation result
        """
        # Initialize base dialog
        super().__init__(parent_window, "Confirm Checkpoint Restoration")

        self.checkpoint_hash = checkpoint_hash
        self.checkpoint_message = checkpoint_message
        self.checkpoint_date = checkpoint_date
        self.on_restore_confirmed = on_restore_confirmed

        # Dialog state
        self.result: bool = False

    def _create_content(self):
        """Create the dialog content - required by BaseDialog."""
        self._create_dialog_content()

    def _create_dialog_content(self):
        """Create the dialog content."""
        # Main content frame
        content_frame = ttk.Frame(self.content_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Warning icon and title
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(
            title_frame,
            text="⚠️ Restore Checkpoint",
            font=("TkDefaultFont", 12, "bold"),
            foreground="orange"
        )
        title_label.pack()

        # Checkpoint details
        self._create_checkpoint_details(content_frame)

        # Warning message
        self._create_warning_message(content_frame)

        # Buttons
        self._create_buttons(content_frame)

    def _create_checkpoint_details(self, parent: ttk.Frame):
        """Create the checkpoint details section."""
        # Details frame
        details_frame = ttk.LabelFrame(parent, text="Checkpoint Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 15))

        # Checkpoint info
        info_text = f"Hash: {self.checkpoint_hash}\n"
        info_text += f"Date: {self.checkpoint_date}\n"
        info_text += f"Message: {self.checkpoint_message}"

        info_label = ttk.Label(
            details_frame,
            text=info_text,
            font=("Consolas", 9),
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)

    def _create_warning_message(self, parent: ttk.Frame):
        """Create the warning message section."""
        # Warning frame
        warning_frame = ttk.LabelFrame(parent, text="Warning", padding=10)
        warning_frame.pack(fill=tk.X, pady=(0, 15))

        warning_text = (
            "Restoring this checkpoint will:\n\n"
            "• Replace all current save files with the checkpoint version\n"
            "• Any unsaved changes will be lost permanently\n"
            "• The current state will not be automatically saved\n\n"
            "Make sure you have created a checkpoint of your current progress "
            "if you want to keep it."
        )

        warning_label = ttk.Label(
            warning_frame,
            text=warning_text,
            font=("TkDefaultFont", 9),
            justify=tk.LEFT,
            foreground="red"
        )
        warning_label.pack(anchor=tk.W)

    def _create_buttons(self, parent: ttk.Frame):
        """Create the dialog buttons."""
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        # Restore button
        restore_button = ttk.Button(
            button_frame,
            text="Restore Checkpoint",
            command=self._on_restore_clicked,
            width=18
        )
        restore_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=15
        )
        cancel_button.pack(side=tk.RIGHT)

    def _on_restore_clicked(self):
        """Handle restore button click."""
        self.result = True
        self._close_dialog()

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.result = False
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog and call the callback."""
        self.close()
        if self.on_restore_confirmed:
            self.on_restore_confirmed(self.result)

    def show_modal(self) -> bool:
        """
        Show the dialog modally and return the result.

        Returns:
            True if restore confirmed, False if cancelled
        """
        # Show the dialog
        self.show(width=450, height=300, resizable=False, use_scrolling=False)

        # Wait for dialog to close
        self.modal_window.wait_window()

        return self.result
