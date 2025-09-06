"""
Settings Management System for YACL

This module provides settings management with JSON-based configuration storage,
default values, and runtime settings management with dual-settings architecture.
"""

import logging
import json
import sys
from typing import Any, Dict, Optional, List
from pathlib import Path
from yacl.models.game_type import GameType
from yacl.utils.helpers import get_resource_base_path

class SettingsManager:
    """
    Settings management system for YACL with dual-settings architecture.

    This class handles:
    - Loading and saving settings to JSON files
    - Dual settings management (core and user)
    - Default value management from configuration files
    - Runtime settings access and modification
    - Settings validation
    """

    USER_SETTINGS_FILE = "user_settings.json"
    CORE_SETTINGS_FILE = "core_settings.json"
    CORE_DEFAULTS_FILE = "core_defaults.json"
    USER_DEFAULTS_FILE = "user_defaults.json"

    def __init__(self):
        """Initialize the settings manager."""
        self.logger = logging.getLogger("YACL")
        self.user_settings_file: Optional[Path] = None
        self.core_settings_file: Optional[Path] = None
        self.current_user_settings: Dict[str, Any] = {}
        self.current_core_settings: Dict[str, Any] = {}
        self._is_loaded = False

        self.logger.info("Settings manager initialized")

    def _load_default_config(self, config_filename: str) -> Dict[str, Any]:
        """
        Load default configuration from resources.

        Args:
            config_filename: Name of the configuration file to load

        Returns:
            Dict[str, Any]: Default configuration data
        """
        try:
            base_path = get_resource_base_path()
            config_path = base_path / "config" / config_filename
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Default config file not found: {config_filename}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load default config {config_filename}: {e}")
            return {}

    def _get_default_user_settings(self) -> Dict[str, Any]:
        """Get default user settings from configuration file."""
        return self._load_default_config(self.USER_DEFAULTS_FILE)

    def _get_default_core_settings(self) -> Dict[str, Any]:
        """Get default core settings from configuration file."""
        return self._load_default_config(self.CORE_DEFAULTS_FILE)

    def initialize(self, settings_dir: Path) -> bool:
        """
        Initialize the settings manager and load settings.

        Args:
            settings_dir: Directory where settings file should be stored

        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info("Initializing settings manager...")

            # Set up settings file paths
            settings_dir.mkdir(parents=True, exist_ok=True)
            self.user_settings_file = settings_dir / self.USER_SETTINGS_FILE
            self.core_settings_file = settings_dir / self.CORE_SETTINGS_FILE

            # Load settings
            self._load_user_settings()
            self._load_core_settings()

            self._is_loaded = True

            self.logger.info("Settings manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize settings manager: {e}")
            return False
    
    def read_user(self, setting_name: str, default: Any = None) -> Any:
        """
        Read a user setting value.

        Args:
            setting_name: Name of the setting to read
            default: Default value if setting doesn't exist

        Returns:
            Any: Setting value or default
        """
        try:
            if not self._is_loaded:
                self.logger.warning("Settings not loaded, using defaults")
                return self._get_default_user_settings().get(setting_name, default)

            if setting_name in self.current_user_settings:
                return self.current_user_settings[setting_name]
            else:
                return default

        except Exception as e:
            self.logger.error(f"Error reading user setting '{setting_name}': {e}")
            return default

    def read_core(self, setting_name: str, default: Any = None) -> Any:
        """
        Read a core setting value.

        Args:
            setting_name: Name of the setting to read
            default: Default value if setting doesn't exist

        Returns:
            Any: Setting value or default
        """
        try:
            if not self._is_loaded:
                self.logger.warning("Settings not loaded, using defaults")
                return self._get_default_core_settings().get(setting_name, default)

            if setting_name in self.current_core_settings:
                return self.current_core_settings[setting_name]
            else:
                return default

        except Exception as e:
            self.logger.error(f"Error reading core setting '{setting_name}': {e}")
            return default

    def read(self, setting_name: str, default: Any = None) -> Any:
        """
        Read a setting value (backward compatibility - defaults to user settings).

        Args:
            setting_name: Name of the setting to read
            default: Default value if setting doesn't exist

        Returns:
            Any: Setting value or default
        """
        return self.read_user(setting_name, default)
    
    def store_user(self, setting_name: str, value: Any) -> bool:
        """
        Store a user setting value.

        Args:
            setting_name: Name of the setting to store
            value: Value to store

        Returns:
            bool: True if setting was stored successfully
        """
        try:
            if not self._is_loaded:
                self.logger.warning("Settings not loaded, cannot store setting")
                return False

            self.current_user_settings[setting_name] = value
            self.logger.debug(f"User setting '{setting_name}' = {value}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing user setting '{setting_name}': {e}")
            return False

    def store_core(self, setting_name: str, value: Any) -> bool:
        """
        Store a core setting value.

        Args:
            setting_name: Name of the setting to store
            value: Value to store

        Returns:
            bool: True if setting was stored successfully
        """
        try:
            if not self._is_loaded:
                self.logger.warning("Settings not loaded, cannot store setting")
                return False

            self.current_core_settings[setting_name] = value
            self.logger.debug(f"Core setting '{setting_name}' = {value}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing core setting '{setting_name}': {e}")
            return False

    def store(self, setting_name: str, value: Any) -> bool:
        """
        Store a setting value (backward compatibility - defaults to user settings).

        Args:
            setting_name: Name of the setting to store
            value: Value to store

        Returns:
            bool: True if setting was stored successfully
        """
        return self.store_user(setting_name, value)
    
    def save_user(self) -> bool:
        """
        Save current user settings to file.

        Returns:
            bool: True if settings were saved successfully
        """
        try:
            if not self.user_settings_file:
                self.logger.error("User settings file not set")
                return False

            self.logger.debug(f"Saving user settings to {self.user_settings_file}")
            with open(self.user_settings_file, 'w') as f:
                json.dump(self.current_user_settings, f, indent=2)

            self.logger.debug(f"User settings saved to {self.user_settings_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save user settings: {e}")
            return False

    def save_core(self) -> bool:
        """
        Save current core settings to file.

        Returns:
            bool: True if settings were saved successfully
        """
        try:
            if not self.core_settings_file:
                self.logger.error("Core settings file not set")
                return False

            self.logger.debug(f"Saving core settings to {self.core_settings_file}")
            with open(self.core_settings_file, 'w') as f:
                json.dump(self.current_core_settings, f, indent=2)

            self.logger.debug(f"Core settings saved to {self.core_settings_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save core settings: {e}")
            return False

    def save(self) -> bool:
        """
        Save both user and core settings to files.

        Returns:
            bool: True if both settings were saved successfully
        """
        user_saved = self.save_user()
        core_saved = self.save_core()
        return user_saved and core_saved

    def _load_user_settings(self):
        """Load user settings from file."""
        try:
            if not self.user_settings_file:
                raise ValueError("User settings file not set")

            self.current_user_settings = self._get_default_user_settings().copy()

            if self.user_settings_file.exists():
                self.logger.info(f"Loading user settings from {self.user_settings_file}")
                with open(self.user_settings_file, 'r') as f:
                    loaded_settings = json.load(f)

                # Update with loaded settings
                self.current_user_settings.update(loaded_settings)

            else:
                self.logger.info("No user settings file found, using defaults")
                # Save defaults to create the file
                self.save_user()

        except Exception as e:
            self.logger.error(f"Failed to load user settings: {e}")
            # Use defaults on error
            self.current_user_settings = self._get_default_user_settings().copy()

    def _load_core_settings(self):
        """Load core settings from file."""
        try:
            if not self.core_settings_file:
                raise ValueError("Core settings file not set")

            self.current_core_settings = self._get_default_core_settings().copy()

            if self.core_settings_file.exists():
                self.logger.info(f"Loading core settings from {self.core_settings_file}")
                with open(self.core_settings_file, 'r') as f:
                    loaded_settings = json.load(f)

                # Update with loaded settings
                self.current_core_settings.update(loaded_settings)

            else:
                self.logger.info("No core settings file found, using defaults")
                # Save defaults to create the file
                self.save_core()

            # Initialize game types
            self._initialize_game_types()

        except Exception as e:
            self.logger.error(f"Failed to load core settings: {e}")
            # Use defaults on error
            self.current_core_settings = self._get_default_core_settings().copy()

    def _initialize_game_types(self):
        """Initialize game types from core settings."""
        try:
            game_types_data = self.read_core("game_types", [])
            for gt in game_types_data:
                GameType.add_game_type(GameType.from_dict(gt))
        except Exception as e:
            self.logger.error(f"Failed to initialize game types: {e}")


    def get_all_user_settings(self) -> Dict[str, Any]:
        """
        Get all current user settings.

        Returns:
            Dict[str, Any]: Copy of all current user settings
        """
        return self.current_user_settings.copy()

    def get_all_core_settings(self) -> Dict[str, Any]:
        """
        Get all current core settings.

        Returns:
            Dict[str, Any]: Copy of all current core settings
        """
        return self.current_core_settings.copy()

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all current settings (backward compatibility - returns user settings).

        Returns:
            Dict[str, Any]: Copy of all current user settings
        """
        return self.get_all_user_settings()

    def reset_user_to_defaults(self) -> bool:
        """
        Reset user settings to default values.

        Returns:
            bool: True if reset was successful
        """
        try:
            self.current_user_settings = self._get_default_user_settings().copy()
            self.logger.info("User settings reset to defaults")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset user settings: {e}")
            return False

    def reset_core_to_defaults(self) -> bool:
        """
        Reset core settings to default values.

        Returns:
            bool: True if reset was successful
        """
        try:
            self.current_core_settings = self._get_default_core_settings().copy()
            self.logger.info("Core settings reset to defaults")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset core settings: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to default values.

        Returns:
            bool: True if reset was successful
        """
        user_reset = self.reset_user_to_defaults()
        core_reset = self.reset_core_to_defaults()
        return user_reset and core_reset

    def shutdown(self):
        """Shutdown the settings manager and save settings."""
        try:
            self.logger.info("Shutting down settings manager...")
            if self._is_loaded:
                self.logger.info("Saving settings before shutdown")
                self.save()  # This saves both user and core settings
                self.logger.info("Settings saved")
            self.logger.info("Settings manager shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during settings manager shutdown: {e}")


# Global settings instance (will be initialized by the application)
settings: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """
    Get the global settings instance.
    
    Returns:
        SettingsManager: Global settings instance
        
    Raises:
        RuntimeError: If settings haven't been initialized
    """
    if settings is None:
        raise RuntimeError("Settings manager not initialized")
    return settings


def initialize_settings(settings_dir: Path) -> bool:
    """
    Initialize the global settings instance.
    
    Args:
        settings_dir: Directory where settings should be stored
        
    Returns:
        bool: True if initialization was successful
    """
    global settings
    try:
        settings = SettingsManager()
        return settings.initialize(settings_dir)
    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize global settings: {e}")
        return False


def shutdown_settings():
    """Shutdown the global settings instance."""
    global settings
    if settings:
        settings.shutdown()
        settings = None
