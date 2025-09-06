"""
File Operations Utilities for YACL

This module provides cross-platform file operations including zip/unzip functionality,
directory management, and file copying equivalent to Godot's filesystem_helper.gd
"""

import logging
import os
import shutil
import zipfile
import tarfile
import threading
from typing import Optional, Callable, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Status module removed - using logging instead

def _safe_post_status(message: str, message_type: str = "INFO"):
    """Safely post a status message, handling cases where status manager is not initialized."""
    try:
        # Just log to console since status module is removed
        logging.getLogger("YACL").info(f"[{message_type.upper()}] {message}")
    except Exception as e:
        logging.getLogger("YACL").warning(f"Failed to log message: {e}")


class FileOperationError(Exception):
    """Custom exception for file operation errors."""
    pass


class FileOperations:
    """
    File operations utility class for YACL.
    
    This class handles:
    - Cross-platform file operations
    - Archive extraction (zip, tar.gz)
    - Directory operations (copy, move, remove)
    - Threaded operations for UI responsiveness
    """
    
    def __init__(self):
        """Initialize the file operations manager."""
        self.logger = logging.getLogger("YACL")
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="FileOps")
        
        # Operation results
        self.last_extract_result = 0
        self.last_operation_error: Optional[str] = None
        
    def extract_archive(self, archive_path: str, dest_dir: str, 
                       progress_callback: Optional[Callable] = None) -> bool:
        """
        Extract a zip or tar.gz archive.
        
        Args:
            archive_path: Path to the archive file
            dest_dir: Destination directory for extraction
            progress_callback: Optional progress callback function
            
        Returns:
            bool: True if extraction was successful
        """
        try:
            archive_path = Path(archive_path)
            dest_dir = Path(dest_dir)
            
            if not archive_path.exists():
                raise FileOperationError(f"Archive not found: {archive_path}")
            
            # Create destination directory if it doesn't exist
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            _safe_post_status(f"Extracting {archive_path.name}...", "INFO")
            
            if archive_path.suffix.lower() == '.zip':
                return self._extract_zip(archive_path, dest_dir, progress_callback)
            elif archive_path.name.lower().endswith('.tar.gz'):
                return self._extract_tar_gz(archive_path, dest_dir, progress_callback)
            else:
                raise FileOperationError(f"Unsupported archive format: {archive_path.suffix}")
                
        except Exception as e:
            self.logger.error(f"Failed to extract archive {archive_path}: {e}")
            self.last_operation_error = str(e)
            _safe_post_status(f"Extraction failed: {e}", "ERROR")
            return False
    
    def _extract_zip(self, archive_path: Path, dest_dir: Path,
                     progress_callback: Optional[Callable] = None) -> bool:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                members = zip_ref.infolist()
                total_files = len(members)
                last_reported_progress = -1

                for i, member in enumerate(members):
                    zip_ref.extract(member, dest_dir)

                    if progress_callback and total_files > 0:
                        progress = (i + 1) / total_files * 100
                        # Only report progress every 5% or on significant files
                        if (int(progress) % 5 == 0 and int(progress) != last_reported_progress) or i == total_files - 1:
                            progress_callback(progress, f"Extracting files... ({i + 1}/{total_files})")
                            last_reported_progress = int(progress)

            self.last_extract_result = 0
            _safe_post_status("Archive extracted successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.last_extract_result = 1
            raise FileOperationError(f"ZIP extraction failed: {e}")
    
    def _extract_tar_gz(self, archive_path: Path, dest_dir: Path,
                        progress_callback: Optional[Callable] = None) -> bool:
        """Extract a TAR.GZ archive."""
        try:
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                members = tar_ref.getmembers()
                total_files = len(members)
                last_reported_progress = -1

                for i, member in enumerate(members):
                    tar_ref.extract(member, dest_dir)

                    if progress_callback and total_files > 0:
                        progress = (i + 1) / total_files * 100
                        # Only report progress every 5% or on significant files
                        if (int(progress) % 5 == 0 and int(progress) != last_reported_progress) or i == total_files - 1:
                            progress_callback(progress, f"Extracting files... ({i + 1}/{total_files})")
                            last_reported_progress = int(progress)

            self.last_extract_result = 0
            _safe_post_status("Archive extracted successfully", "SUCCESS")
            return True

        except Exception as e:
            self.last_extract_result = 1
            raise FileOperationError(f"TAR.GZ extraction failed: {e}")

    def copy_directory(self, src_dir: str, dest_dir: str,
                      progress_callback: Optional[Callable] = None) -> bool:
        """
        Copy a directory recursively.

        Args:
            src_dir: Source directory path
            dest_dir: Destination directory path
            progress_callback: Optional progress callback function

        Returns:
            bool: True if copy was successful
        """
        try:
            src_path = Path(src_dir)
            dest_path = Path(dest_dir)

            if not src_path.exists():
                raise FileOperationError(f"Source directory not found: {src_path}")

            _safe_post_status(f"Copying directory {src_path.name}...", "INFO")

            # Create destination parent directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the directory
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

            _safe_post_status("Directory copied successfully", "SUCCESS")
            return True

        except Exception as e:
            self.logger.error(f"Failed to copy directory {src_dir} to {dest_dir}: {e}")
            self.last_operation_error = str(e)
            _safe_post_status(f"Copy failed: {e}", "ERROR")
            return False
    
    def move_directory(self, src_dir: str, dest_dir: str) -> bool:
        """
        Move a directory.
        
        Args:
            src_dir: Source directory path
            dest_dir: Destination directory path
            
        Returns:
            bool: True if move was successful
        """
        try:
            src_path = Path(src_dir)
            dest_path = Path(dest_dir)
            
            if not src_path.exists():
                raise FileOperationError(f"Source directory not found: {src_path}")

            _safe_post_status(f"Moving directory {src_path.name}...", "INFO")

            # Create destination parent directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the directory
            shutil.move(str(src_path), str(dest_path))

            _safe_post_status("Directory moved successfully", "SUCCESS")
            return True

        except Exception as e:
            self.logger.error(f"Failed to move directory {src_dir} to {dest_dir}: {e}")
            self.last_operation_error = str(e)
            _safe_post_status(f"Move failed: {e}", "ERROR")
            return False
    
    def remove_directory(self, dir_path: str) -> bool:
        """
        Remove a directory recursively.
        
        Args:
            dir_path: Directory path to remove
            
        Returns:
            bool: True if removal was successful
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                self.logger.warning(f"Directory not found: {path}")
                return True  # Consider it successful if already gone

            _safe_post_status(f"Removing directory {path.name}...", "INFO")

            # Remove the directory
            shutil.rmtree(path)

            _safe_post_status("Directory removed successfully", "SUCCESS")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove directory {dir_path}: {e}")
            self.last_operation_error = str(e)
            _safe_post_status(f"Removal failed: {e}", "ERROR")
            return False
    
    def list_directory(self, dir_path: str) -> list:
        """
        List contents of a directory.
        
        Args:
            dir_path: Directory path to list
            
        Returns:
            list: List of directory contents
        """
        try:
            path = Path(dir_path)
            
            if not path.exists() or not path.is_dir():
                return []
            
            return [item.name for item in path.iterdir()]
            
        except Exception as e:
            self.logger.error(f"Failed to list directory {dir_path}: {e}")
            return []
    
    def get_extracted_root_dir(self, extract_dir: str) -> Optional[str]:
        """
        Get the root directory of extracted content.

        This method intelligently determines the actual game root directory
        by looking for common game files and directory structures.

        Args:
            extract_dir: Directory where archive was extracted

        Returns:
            str: Path to the actual game root directory
        """
        try:
            extract_path = Path(extract_dir)
            contents = list(extract_path.iterdir())

            if not contents:
                self.logger.warning(f"Extract directory is empty: {extract_dir}")
                return None

            # If there's only one directory, check if it's the game root
            if len(contents) == 1 and contents[0].is_dir():
                single_dir = contents[0]

                # Check if this directory contains game files
                if self._is_game_root_directory(single_dir):
                    return str(single_dir)

                # If not, check one level deeper
                sub_contents = list(single_dir.iterdir())
                if len(sub_contents) == 1 and sub_contents[0].is_dir():
                    if self._is_game_root_directory(sub_contents[0]):
                        return str(sub_contents[0])

                # Default to the single directory
                return str(single_dir)

            # Multiple items - check if current directory is game root
            if self._is_game_root_directory(extract_path):
                return str(extract_path)

            # Look for a subdirectory that might be the game root
            for item in contents:
                if item.is_dir() and self._is_game_root_directory(item):
                    return str(item)

            # Fallback to the extract directory
            self.logger.warning(f"Could not determine game root, using extract directory: {extract_dir}")
            return str(extract_path)

        except Exception as e:
            self.logger.error(f"Failed to determine extracted root directory: {e}")
            return None

    def _is_game_root_directory(self, directory: Path) -> bool:
        """
        Check if a directory appears to be a game root directory.

        Args:
            directory: Directory to check

        Returns:
            bool: True if directory appears to be a game root
        """
        try:
            if not directory.is_dir():
                return False

            # Common game files and directories to look for
            game_indicators = [
                "cataclysm-tiles",  # Main executable (Linux)
                "cataclysm-tiles.exe",  # Main executable (Windows)
                "cataclysm-launcher",  # Launcher executable (Linux)
                "cataclysm",  # Alternative executable name
                "cataclysm.exe",  # Alternative executable (Windows)
                "cataclysm-bn-tiles.exe",  # Bright Nights executable (Windows)
                "data",  # Game data directory
                "gfx",  # Graphics directory
                "config",  # Config directory
                "doc",  # Documentation directory
                "lang",  # Language files directory
            ]

            # Check for presence of game indicators
            found_indicators = 0
            for item in directory.iterdir():
                if item.name.lower() in [indicator.lower() for indicator in game_indicators]:
                    found_indicators += 1

            # Consider it a game root if we find at least 2 indicators
            return found_indicators >= 2

        except Exception as e:
            self.logger.debug(f"Error checking if directory is game root: {e}")
            return False

    def get_directory_size(self, directory: str) -> int:
        """
        Get the total size of a directory in bytes.

        Args:
            directory: Directory path

        Returns:
            int: Total size in bytes
        """
        try:
            total_size = 0
            dir_path = Path(directory)

            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size

            return total_size

        except Exception as e:
            self.logger.error(f"Failed to calculate directory size: {e}")
            return 0

    def validate_archive(self, archive_path: str) -> bool:
        """
        Validate that an archive file is not corrupted.

        Args:
            archive_path: Path to the archive file

        Returns:
            bool: True if archive is valid
        """
        try:
            archive_file = Path(archive_path)

            if not archive_file.exists():
                return False

            if archive_file.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # Test the archive
                    bad_file = zip_ref.testzip()
                    return bad_file is None

            elif archive_file.name.lower().endswith('.tar.gz'):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    # Basic validation - try to get member list
                    members = tar_ref.getmembers()
                    return len(members) > 0

            return False

        except Exception as e:
            self.logger.error(f"Archive validation failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the file operations manager."""
        # Don't wait for completion to avoid blocking shutdown
        self.executor.shutdown(wait=False)


# Global instance
_file_operations: Optional[FileOperations] = None


def get_file_operations() -> FileOperations:
    """Get the global file operations instance."""
    global _file_operations
    if _file_operations is None:
        _file_operations = FileOperations()
    return _file_operations


def shutdown_file_operations():
    """Shutdown the global file operations instance."""
    global _file_operations
    if _file_operations is not None:
        _file_operations.shutdown()
        _file_operations = None
