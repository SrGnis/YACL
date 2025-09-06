"""
Download Manager for YACL

This module provides HTTP download functionality with progress tracking.
"""

import logging
import time
import threading
from typing import Optional
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from yacl.services.settings import get_settings
from yacl.services.events import EventManager, Events


class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass


class DownloadManager:
    """
    Download management system for YACL.
    
    This class handles:
    - HTTP downloads with progress tracking
    - File management and directory creation
    - Progress reporting with speed calculation
    - Event emission for UI coordination
    - Threading for non-blocking downloads
    """
    
    # Progress update thresholds (matching original)
    PROGRESS_AFTER_MSECS = 2000  # 2 seconds
    PROGRESS_AFTER_BYTES = 1024 * 1024 * 5  # 5 MB
    
    def __init__(self, event_manager: EventManager):
        """
        Initialize the download manager.

        TODO: Concurrent downloads, have a download queue and return 
        a download id on download_file, on download_finished event, return the download id. 
        
        Args:
            event_manager: Event manager for UI communication
        """
        self.logger = logging.getLogger("YACL")
        self.event_manager = event_manager
        
        # Download state
        self.current_filename = ""
        self.current_file_path = ""
        self.download_ongoing = False
        self.download_thread: Optional[threading.Thread] = None
        self.cancel_requested = False
        
        # HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info("Download manager initialized")
    
    def download_file(self, url: str, target_dir: str, target_filename: str) -> bool:
        """
        Download a file from URL to target directory.
        
        Args:
            url: URL to download from
            target_dir: Target directory path
            target_filename: Target filename
            
        Returns:
            bool: True if download was successful
        """
        try:
            
            # Prepare target directory and file path
            target_path = Path(target_dir)
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {target_path}")
            
            self.current_filename = target_filename
            self.current_file_path = str(target_path / target_filename)
            
            # Start download in background thread
            self.download_thread = threading.Thread(
                target=self._download_worker,
                args=(url, self.current_file_path),
                daemon=True
            )
            
            self.cancel_requested = False
            self.download_ongoing = True
            
            # Emit download started event
            if self.event_manager:
                self.event_manager.emit(Events.DOWNLOAD_STARTED, filename=target_filename)
            

            self.logger.info(f"Starting download: {target_filename}")
            
            self.download_thread.start()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start download: {e}")
            self._finish_download(False)
            return False
    
    def cancel_download(self) -> None:
        """Cancel the current download."""
        if self.download_ongoing:
            self.cancel_requested = True
            self.logger.info("Download cancellation requested")
    
    def is_downloading(self) -> bool:
        """Check if a download is currently in progress."""
        return self.download_ongoing
    
    def shutdown(self) -> None:
        """Shutdown the download manager and cleanup resources."""
        self.cancel_download()
        if self.download_thread:
            self.download_thread.join(timeout=5.0)
        self.logger.info("Download manager shutdown")

    def _download_worker(self, url: str, file_path: str) -> None:
        """
        Worker method that performs the actual download in a background thread.

        Args:
            url: URL to download from
            file_path: Full path where to save the file
        """
        success = False
        try:
            self.logger.info(f"Starting download from {url}")

            # Start the download with streaming
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Get content length for progress tracking
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Progress tracking variables
            last_progress_time = time.time() * 1000  # Convert to milliseconds
            last_progress_bytes = 0

            # Download the file in chunks
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancel_requested:
                        self.logger.info("Download cancelled by user")
                        break

                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Check if we should update progress
                        current_time = time.time() * 1000
                        delta_time = current_time - last_progress_time
                        delta_bytes = downloaded - last_progress_bytes

                        if (delta_time >= self.PROGRESS_AFTER_MSECS or
                            delta_bytes >= self.PROGRESS_AFTER_BYTES):

                            # Generate progress message
                            progress_msg = self._get_progress_string(
                                downloaded, total_size, delta_time, delta_bytes
                            )

                            # Log progress
                            self.logger.debug(progress_msg)

                            # Emit progress event
                            self.event_manager.emit(
                                Events.DOWNLOAD_PROGRESS,
                                downloaded=downloaded,
                                total=total_size,
                                message=progress_msg
                            )

                            # Update tracking variables
                            last_progress_time = current_time
                            last_progress_bytes = downloaded

            # Check if download was completed successfully
            if not self.cancel_requested and Path(file_path).exists():
                success = True
                self.logger.info(f"Download completed: {file_path}")
            else:
                # Clean up partial file
                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to cleanup partial file: {cleanup_error}")

                if self.cancel_requested:
                    self.logger.info(f"Download cancelled: {self.current_filename}")
                else:
                    self.logger.error(f"Download failed: {self.current_filename}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP error during download: {e}")

        except Exception as e:
            self.logger.error(f"Unexpected error during download: {e}")

        finally:
            self._finish_download(success)

    def _get_progress_string(self, downloaded: int, total: int,
                        delta_time: float, delta_bytes: int) -> str:
        """
        Generate a progress string

        Args:
            downloaded: Total bytes downloaded
            total: Total file size (0 if unknown)
            delta_time: Time since last update in milliseconds
            delta_bytes: Bytes downloaded since last update

        Returns:
            str: Formatted progress string
        """
        # Format downloaded amount
        if downloaded > 1024 * 1024:
            amount_str = f"{downloaded / (1024 * 1024):.1f} MB"
        else:
            amount_str = f"{downloaded // 1024} KB"

        # Format percentage if total size is known
        percent_str = ""
        if total > 0:
            percent = (downloaded / total) * 100
            percent_str = f" ({percent:.1f}%)"

        # Calculate and format download speed
        speed_str = " at "
        if delta_time > 0:
            speed_bps = (delta_bytes / delta_time) * 1000.0  # Convert to bytes per second
            if speed_bps > 1024 * 1024:
                speed_str += f"{speed_bps / (1024 * 1024):.1f} MB/s"
            else:
                speed_str += f"{speed_bps / 1024:.0f} KB/s"
        else:
            speed_str += "calculating..."

        return f"Download progress: {amount_str}{percent_str}{speed_str}"

    def _finish_download(self, success: bool) -> None:
        """
        Finish the download process and emit completion event.

        Args:
            success: Whether the download was successful
        """
        self.download_ongoing = False

        # Emit download finished event
        if self.event_manager:
            self.event_manager.emit(
                Events.DOWNLOAD_FINISHED,
                filename=self.current_filename,
                success=success,
                file_path=self.current_file_path if success else None
            )

        # Log completion
        if success:
            self.logger.info(f"Download completed successfully: {self.current_filename}")
        else:
            self.logger.warning(f"Download failed or was cancelled: {self.current_filename}")


# Global download manager instance (will be initialized by the application)
download_manager: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """
    Get the global download manager instance.

    Returns:
        DownloadManager: Global download manager instance

    Raises:
        RuntimeError: If download manager hasn't been initialized
    """
    if download_manager is None:
        raise RuntimeError("Download manager not initialized")
    return download_manager


def initialize_download_manager(event_manager: EventManager) -> bool:
    """
    Initialize the global download manager instance.

    Args:
        event_manager: Event manager for UI communication

    Returns:
        bool: True if initialization was successful
    """
    global download_manager
    try:
        download_manager = DownloadManager(event_manager)
        return True
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global download manager: {e}")
        return False


def shutdown_download_manager():
    """Shutdown the global download manager instance."""
    global download_manager
    if download_manager:
        download_manager.shutdown()
        download_manager = None
