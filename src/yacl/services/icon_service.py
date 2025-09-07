"""
SVG Icon Service for YACL

This module provides SVG to PNG conversion and caching functionality for tkinter applications.
Since tkinter doesn't natively support SVG files, this service converts SVG icons to PNG format
at runtime and caches them for efficient reuse.
"""

import logging
from pathlib import Path
from typing import Optional, Dict
import tkinter as tk

import cairosvg

from yacl.services.paths import get_paths
from yacl.utils.helpers import get_resource_base_path


class IconService:
    """
    SVG icon service for converting and caching SVG icons as PNG files.
    
    This service handles:
    - Converting SVG files to PNG format using cairosvg
    - Caching converted PNG files to avoid repeated conversions
    - Managing cache directory and file organization
    - Providing PNG file paths for tkinter image loading
    """
    
    def __init__(self):
        """Initialize the icon service."""
        self.logger = logging.getLogger("YACL")

        self.paths = get_paths()

        # Icon directories
        self.svg_icons_dir = get_resource_base_path() / "assets" / "lucide-icons" / "icons" # TODO: Make this configurable
        self.cache_dir = self.paths.cache_dir / "icons"

        self._image_cache: Dict[str, tk.PhotoImage] = {}

        self._is_initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the icon service and create cache directory.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Initializing icon service...")
            
            # Create cache directory if it doesn't exist
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify SVG icons directory exists
            if not self.svg_icons_dir.exists():
                self.logger.error(f"SVG icons directory not found: {self.svg_icons_dir}")
                return False
            
            self._is_initialized = True
            self.logger.info("Icon service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize icon service: {e}")
            return False
    
    def get_icon_png_path(self, icon_name: str, size: int = 24) -> Optional[Path]:
        """
        Get the PNG file path for an SVG icon, converting if necessary.
        
        Args:
            icon_name: Name of the icon (without .svg extension)
            size: Size in pixels for the PNG conversion (default: 24)
            
        Returns:
            Optional[Path]: Path to the PNG file, or None if conversion failed
        """
        try:
            if not self._is_initialized:
                self.logger.warning("Icon service not initialized")
                return None
            
            # Generate cache filename based on icon name and size
            cache_filename = f"{icon_name}_{size}.png"
            cache_file_path = self.cache_dir / cache_filename
            
            # Check if cached PNG already exists
            if cache_file_path.exists():
                self.logger.debug(f"Using cached icon: {cache_file_path}")
                return cache_file_path
            
            # Find the SVG file
            svg_file_path = self.svg_icons_dir / f"{icon_name}.svg"
            if not svg_file_path.exists():
                self.logger.error(f"SVG icon not found: {svg_file_path}")
                return None
            
            # Convert SVG to PNG
            return self._convert_svg_to_png(svg_file_path, cache_file_path, size)

        except Exception as e:
            self.logger.error(f"Failed to get icon PNG path for '{icon_name}': {e}")
            return None

    def get_icon_image(self, icon_name: str, size: int = 24) -> Optional[tk.PhotoImage]:
        """
        Get a PhotoImage object for an SVG icon, with caching to prevent garbage collection.

        Args:
            icon_name: Name of the icon (without .svg extension)
            size: Size in pixels for the PNG conversion (default: 24)

        Returns:
            Optional[tk.PhotoImage]: Cached PhotoImage object, or None if loading failed
        """
        try:
            if not self._is_initialized:
                self.logger.warning("Icon service not initialized")
                return None

            # Generate cache key
            cache_key = f"{icon_name}_{size}"

            # Check if PhotoImage is already cached
            if cache_key in self._image_cache:
                self.logger.debug(f"Using cached PhotoImage: {cache_key}")
                return self._image_cache[cache_key]

            # Get PNG file path (this handles SVG conversion and PNG caching)
            png_path = self.get_icon_png_path(icon_name, size)
            if not png_path:
                return None

            # Create PhotoImage and cache it
            photo_image = tk.PhotoImage(file=str(png_path))
            self._image_cache[cache_key] = photo_image

            self.logger.debug(f"Created and cached PhotoImage: {cache_key}")
            return photo_image

        except Exception as e:
            self.logger.error(f"Failed to get icon image for '{icon_name}': {e}")
            return None
    
    def _convert_svg_to_png(self, svg_path: Path, png_path: Path, size: int) -> Optional[Path]:
        """
        Convert an SVG file to PNG format.
        
        Args:
            svg_path: Path to the source SVG file
            png_path: Path where the PNG file should be saved
            size: Size in pixels for the PNG conversion
            
        Returns:
            Optional[Path]: Path to the converted PNG file, or None if conversion failed
        """
        try:
            self.logger.debug(f"Converting SVG to PNG: {svg_path} -> {png_path}")
            
            # Convert SVG to PNG using cairosvg
            cairosvg.svg2png(
                url=str(svg_path),
                write_to=str(png_path),
                output_width=size,
                output_height=size,
                negate_colors=True # TODO: Set this based on theme
            )
            
            # Verify the PNG file was created
            if png_path.exists():
                self.logger.debug(f"Successfully converted icon: {png_path}")
                return png_path
            else:
                self.logger.error(f"PNG file was not created: {png_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to convert SVG to PNG: {e}")
            return None
    
    def clear_cache(self) -> bool:
        """
        Clear all cached PNG icons and PhotoImage objects.

        Returns:
            bool: True if cache was cleared successfully
        """
        try:
            if not self._is_initialized:
                self.logger.warning("Icon service not initialized")
                return False

            # Clear PhotoImage cache
            cached_images = len(self._image_cache)
            self._image_cache.clear()

            # Remove all PNG files in cache directory
            png_files = list(self.cache_dir.glob("*.png"))
            for png_file in png_files:
                png_file.unlink()

            self.logger.info(f"Cleared {len(png_files)} cached PNG files and {cached_images} cached PhotoImages")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear icon cache: {e}")
            return False
    
    def get_cache_size(self) -> int:
        """
        Get the number of cached PNG icons.

        Returns:
            int: Number of cached PNG files
        """
        try:
            if not self._is_initialized or not self.cache_dir.exists():
                return 0

            return len(list(self.cache_dir.glob("*.png")))

        except Exception as e:
            self.logger.error(f"Failed to get cache size: {e}")
            return 0

    def get_image_cache_size(self) -> int:
        """
        Get the number of cached PhotoImage objects.

        Returns:
            int: Number of cached PhotoImage objects
        """
        try:
            return len(self._image_cache)
        except Exception as e:
            self.logger.error(f"Failed to get image cache size: {e}")
            return 0
    
    def shutdown(self):
        """Shutdown the icon service."""
        try:
            self.logger.debug("Shutting down icon service...")

            # Clear PhotoImage cache to free memory
            cached_images = len(self._image_cache)
            self._image_cache.clear()
            if cached_images > 0:
                self.logger.debug(f"Cleared {cached_images} cached PhotoImages during shutdown")

            self._is_initialized = False
            self.logger.debug("Icon service shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during icon service shutdown: {e}")


# Global icon service instance (will be initialized by the application)
icon_service: Optional[IconService] = None

@staticmethod
def load_icon(icon_name: str, size: int = 16) -> Optional[tk.PhotoImage]:
        """
        Load an icon from the icon service with automatic caching.

        Args:
            icon_name: Name of the icon (without .svg extension)
            size: Size in pixels for the icon (default: 16)

        Returns:
            Optional[tk.PhotoImage]: Cached PhotoImage object or None if loading failed
        """
        try:
            icon_service = get_icon_service()
            return icon_service.get_icon_image(icon_name, size)
        except Exception as e:
            logging.getLogger("YACL").error(f"Error loading icon '{icon_name}': {e}")
            return None

@staticmethod
def get_icon_service() -> IconService:
    """
    Get the global icon service instance.
    
    Returns:
        IconService: Global icon service instance
        
    Raises:
        RuntimeError: If icon service hasn't been initialized
    """
    if icon_service is None:
        raise RuntimeError("Icon service not initialized")
    return icon_service

@staticmethod
def initialize_icon_service() -> bool:
    """
    Initialize the global icon service instance.
    
    Returns:
        bool: True if initialization was successful
    """
    global icon_service
    try:
        icon_service = IconService()
        return icon_service.initialize()
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global icon service: {e}")
        return False

@staticmethod
def shutdown_icon_service():
    """Shutdown the global icon service instance."""
    global icon_service
    if icon_service:
        icon_service.shutdown()
        icon_service = None
