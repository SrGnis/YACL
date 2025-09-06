"""
Installation Progress Dialog for YACL

This module provides a modal dialog for displaying both download and installation progress
with separate progress bars, status text, and cancel functionality.
"""

import logging
from typing import Optional, Callable
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.base_dialog import BaseDialog
from yacl.services.downloader import get_download_manager
from yacl.services.events import EventManager, Events


class InstallationProgressDialog(BaseDialog):
    """
    Modal dialog for displaying download and installation progress.

    This dialog provides:
    - Separate progress bars for download and installation phases
    - Status text for each phase (speed, size, extraction progress, etc.)
    - Cancel button to abort the process
    - Automatic closure on completion
    - Event-driven updates from download and installation managers
    """

    def __init__(self, parent_window: tk.Widget, event_manager: EventManager,
                filename: str, on_complete: Optional[Callable[[bool, Optional[str]], None]] = None):
        """
        Initialize the installation progress dialog.

        Args:
            parent_window: Parent window for the modal dialog
            event_manager: Event manager for listening to download and installation events
            filename: Name of the file being downloaded and installed
            on_complete: Callback when the entire process completes (success, file_path)
        """
        super().__init__(parent_window, f"Installing {filename}")

        self.event_manager = event_manager
        self.filename = filename
        self.on_complete = on_complete

        # UI components for download progress
        self.download_progress_var: tk.DoubleVar
        self.download_progress_bar: ttk.Progressbar
        self.download_status_label: ttk.Label

        # UI components for installation progress
        self.installation_progress_var: tk.DoubleVar
        self.installation_progress_bar: ttk.Progressbar
        self.installation_status_label: ttk.Label

        # Control components
        self.cancel_button: ttk.Button

        # Process state
        self.process_cancelled = False
        self.download_completed = False
        self.installation_completed = False

        self.logger.debug(f"Initialized installation progress dialog for: {filename}")
    
    def show(self, width: int = 600, height: int = 500, resizable: bool = True,
            use_scrolling: bool = False) -> tk.Toplevel:
        """
        Show the installation progress dialog.

        Returns:
            The created modal window
        """

        self._subscribe_to_events()

        return super().show(width=width, height=height, resizable=resizable, use_scrolling=use_scrolling)
    
    def _create_content(self):
        """Create the installation progress dialog content."""

        try:
            title_label = ttk.Label(
                self.content_frame,
                text=f"Installing: {self.filename}",
                font=("TkDefaultFont", 10, "bold")
            )
            title_label.pack(pady=(0, 20))

            # Download
            download_section = self.create_section_frame(title="Download Progress", padding=10)

            self.download_progress_var = tk.DoubleVar()
            self.download_progress_bar = ttk.Progressbar(
                download_section,
                variable=self.download_progress_var,
                maximum=100,
                length=500,
                mode='determinate'
            )
            self.download_progress_bar.pack(pady=(0, 5))

            self.download_status_label = ttk.Label(
                download_section,
                text="Preparing download...",
                wraplength=500
            )
            self.download_status_label.pack(pady=(0, 10))

            # Installation
            installation_section = self.create_section_frame(title="Installation Progress", padding=10)

            self.installation_progress_var = tk.DoubleVar()
            self.installation_progress_bar = ttk.Progressbar(
                installation_section,
                variable=self.installation_progress_var,
                maximum=100,
                length=500,
                mode='determinate'
            )
            self.installation_progress_bar.pack(pady=(0, 5))

            self.installation_status_label = ttk.Label(
                installation_section,
                text="Waiting for download to complete...",
                wraplength=500
            )
            self.installation_status_label.pack(pady=(0, 10))

            # Cancel button
            button_frame = self.create_button_frame()

            self.cancel_button = ttk.Button(
                button_frame,
                text="Cancel",
                command=self._on_cancel_clicked
            )
            self.cancel_button.pack(side=tk.RIGHT)

        except Exception as e:
            self.logger.error(f"Error creating installation progress dialog content: {e}")
    
    def _subscribe_to_events(self):
        """Subscribe to download and installation events."""
        try:
            # Download events
            self.event_manager.subscribe(Events.DOWNLOAD_STARTED, self._on_download_started)
            self.event_manager.subscribe(Events.DOWNLOAD_PROGRESS, self.update_download_progress)
            self.event_manager.subscribe(Events.DOWNLOAD_FINISHED, self._on_download_finished)

            # Installation events
            self.event_manager.subscribe(Events.INSTALLATION_STARTED, self._on_installation_started)
            self.event_manager.subscribe(Events.INSTALLATION_PROGRESS, self.update_installation_progress)
            self.event_manager.subscribe(Events.INSTALLATION_FINISHED, self._on_installation_finished)

        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")

    def _unsubscribe_from_events(self):
        """Unsubscribe from download and installation events."""
        try:
            # Download events
            self.event_manager.unsubscribe(Events.DOWNLOAD_STARTED, self._on_download_started)
            self.event_manager.unsubscribe(Events.DOWNLOAD_PROGRESS, self.update_download_progress)
            self.event_manager.unsubscribe(Events.DOWNLOAD_FINISHED, self._on_download_finished)

            # Installation events
            self.event_manager.unsubscribe(Events.INSTALLATION_STARTED, self._on_installation_started)
            self.event_manager.unsubscribe(Events.INSTALLATION_PROGRESS, self.update_installation_progress)
            self.event_manager.unsubscribe(Events.INSTALLATION_FINISHED, self._on_installation_finished)

        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")
    
    def _on_download_started(self, sender, **kwargs):
        """Handle download started event."""
        try:
            filename = kwargs.get('filename', '')
            if filename == self.filename:
                self._update_download_status("Download started...")

        except Exception as e:
            self.logger.error(f"Error handling download started event: {e}")

    def _on_download_finished(self, sender, **kwargs):
        """Handle download finished event."""
        try:
            filename = kwargs.get('filename', '')
            success = kwargs.get('success', False)
            file_path = kwargs.get('file_path')

            if filename == self.filename:
                self.download_completed = True

                if success:
                    self._update_download_progress(100)
                    self._update_download_status("Download completed successfully!")
                else:
                    self._update_download_status("Download failed or was cancelled.")

                    self._complete_process(False, file_path)

        except Exception as e:
            self.logger.error(f"Error handling download finished event: {e}")

    def _on_installation_started(self, sender, **kwargs):
        """Handle installation started event."""
        try:
            self._update_installation_status("Installation started...")

        except Exception as e:
            self.logger.error(f"Error handling installation started event: {e}")

    def _on_installation_finished(self, sender, **kwargs):
        """Handle installation finished event."""
        try:
            success = kwargs.get('success', False)
            installation_path = kwargs.get('installation_path')
            error_message = kwargs.get('error_message')

            self.installation_completed = True

            if success:
                self._update_installation_progress(100)
                self._update_installation_status("Installation completed successfully!")
            else:
                self._update_installation_status(f"Installation failed: {error_message or 'Unknown error'}")

            self._complete_process(success, installation_path)

        except Exception as e:
            self.logger.error(f"Error handling installation finished event: {e}")
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        try:
            if not self.download_completed and not self.installation_completed:

                download_manager = get_download_manager()
                download_manager.cancel_download()
                self.process_cancelled = True
                self._update_download_status("Cancelling...")
                self._update_installation_status("Cancelled")

                self.cancel_button.config(state=tk.DISABLED)
            else:
                self.close()

        except Exception as e:
            self.logger.error(f"Error cancelling process: {e}")

    def _complete_process(self, success: bool, file_path: Optional[str]):
        """Complete the entire process and update UI."""
        try:

            self.cancel_button.config(text="Close", command=self.close)

            if self.on_complete:
                self.on_complete(success, file_path)

        except Exception as e:
            self.logger.error(f"Error completing process: {e}")

    def _update_download_progress(self, percentage: float):
        """Update the download progress bar."""
        try:
            self.modal_window.after(0, lambda: self.download_progress_var.set(percentage))

        except Exception as e:
            self.logger.error(f"Error updating download progress: {e}")

    def _update_installation_progress(self, percentage: float):
        """Update the installation progress bar."""
        try:
            self.modal_window.after(0, lambda: self.installation_progress_var.set(percentage))

        except Exception as e:
            self.logger.error(f"Error updating installation progress: {e}")

    def _update_download_status(self, status_text: str):
        """Update the download status label."""
        try:
            self.modal_window.after(0, lambda: self.download_status_label.config(text=status_text))

        except Exception as e:
            self.logger.error(f"Error updating download status: {e}")

    def _update_installation_status(self, status_text: str):
        """Update the installation status label."""
        try:
            self.modal_window.after(0, lambda: self.installation_status_label.config(text=status_text))

        except Exception as e:
            self.logger.error(f"Error updating installation status: {e}")
    
    def update_download_progress(self, sender, **kwargs):
        """
        Update download progress from download manager callback.

        Args:
            sender: The event sender (EventManager)
            **kwargs: Event data containing:
                - downloaded: Bytes downloaded so far
                - total: Total bytes to download (0 if unknown)
                - message: Progress message
        """
        try:
            downloaded = kwargs.get('downloaded', 0)
            total = kwargs.get('total', 0)
            message = kwargs.get('message', '')

            # Calculate percentage
            if total > 0:
                percentage = (downloaded / total) * 100
                self._update_download_progress(percentage)

            # Update status message
            self._update_download_status(message)

        except Exception as e:
            self.logger.error(f"Error updating download progress from callback: {e}")

    def update_installation_progress(self, sender, **kwargs):
        """
        Update installation progress from installation manager callback.

        Args:
            sender: The event sender (EventManager)
            **kwargs: Event data containing:
                - progress: Progress percentage (0-100)
                - message: Progress message
        """
        try:
            progress = kwargs.get('progress', 0)

            # Update progress bar
            self._update_installation_progress(progress)

            # Create a clean status message - just show "Extracting..." with percentage
            if progress > 0:
                clean_message = f"Installing... {progress:.1f}%"
            else:
                clean_message = "Preparing installation..."

            # Update status message with clean text
            self._update_installation_status(clean_message)

        except Exception as e:
            self.logger.error(f"Error updating installation progress from callback: {e}")
    
    def close(self):
        try:
            self._unsubscribe_from_events()

            self.modal_window.destroy()

        except Exception as e:
            self.logger.error(f"Error closing installation progress dialog: {e}")

    def _on_window_close(self):
        if not self.download_completed and not self.installation_completed and not self.process_cancelled:
            self._on_cancel_clicked()
        else:
            self.close()
