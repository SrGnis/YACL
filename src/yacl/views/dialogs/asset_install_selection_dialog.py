"""
Asset Installation Selection Dialog for YACL

This module provides a dialog for selecting which asset variant to install
from a game release, with platform detection and user-friendly descriptions.
"""

import platform
import logging
from typing import Optional, Dict, Any, List, Callable
import tkinter as tk
from tkinter import ttk

from yacl.ui.widgets.base_dialog import BaseDialog
from yacl.models.release import GameRelease, AssetPlatform, ReleaseAsset


class AssetInstallSelectionDialog(BaseDialog):
    """
    Dialog for selecting which asset variant to install from a game release.
    
    This dialog provides:
    - Platform detection and recommendation
    - Asset grouping by platform
    - Asset selection and confirmation
    """
    
    def __init__(self, parent_window: tk.Widget, release: GameRelease,
                on_asset_selected: Callable[[Optional[ReleaseAsset]], None]):
        """
        Initialize the asset selection dialog.

        Args:
            parent_window: Parent window for the modal dialog
            release: The game release containing assets to choose from
            on_asset_selected: Callback function called when an asset is selected or dialog is cancelled
        """
        # Initialize base dialog
        super().__init__(parent_window, f"Select Installation Variant - {release.name}")

        self.release = release
        self.on_asset_selected = on_asset_selected

        # Dialog state
        self.selected_asset_ref: Dict[str, Any] = {"asset": None}
        self.install_btn: Optional[ttk.Button] = None

        # Detect user's platform and group assets
        self.user_platform = self._detect_user_platform()
        self.grouped_assets = self._group_assets_by_platform(release.assets)

        self.logger.debug(f"Initialized asset selection dialog for release: {release.name}")
    
    def show(self, width: int = 600, height: int = 500, resizable: bool = True,
             use_scrolling: bool = True) -> tk.Toplevel:
        """
        Show the asset selection dialog.

        Args:
            width: Width of the dialog window
            height: Height of the dialog window
            resizable: Whether the window should be resizable
            use_scrolling: Whether to create a scrollable content area

        Returns:
            The created modal window
        """
        return super().show(width=width, height=height, resizable=resizable, use_scrolling=use_scrolling)
    
    def _create_content(self):
        """Create the complete dialog content within the scrollable frame."""
        try:
            if not self.content_frame:
                raise ValueError("Content frame not available")

            # Header info
            header_frame = ttk.Frame(self.content_frame)
            header_frame.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(header_frame, text=f"Release: {self.release.name}",
                     font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
            ttk.Label(header_frame, text=f"Channel: {self.release.channel.display_name()}").pack(anchor=tk.W)

            self.add_separator()

            ttk.Label(self.content_frame, text="Select the variant you want to install:",
                     font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W, pady=(0, 10))

            # Variable to track selected asset
            self.selected_asset_var = tk.StringVar()

            # Create asset selection interface
            self._create_asset_selection_interface()

            # Create buttons using BaseDialog utility
            buttons_frame = self.create_button_frame()

            # Cancel button
            cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=self._on_cancel)
            cancel_btn.pack(side=tk.LEFT)

            # Install button
            self.install_btn = ttk.Button(
                buttons_frame,
                text="Install Selected",
                state=tk.DISABLED,
                command=self._on_install
            )
            self.install_btn.pack(side=tk.RIGHT)

        except Exception as e:
            self.logger.error(f"Error creating dialog content: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_window_close(self):
        """Handle window close event by calling cancel."""
        self._on_cancel()

    def _on_cancel(self):
        """Handle cancel button click or window close."""
        try:
            super().close()
            self.on_asset_selected(None)
        except Exception as e:
            self.logger.error(f"Error handling cancel: {e}")

    def _on_install(self):
        """Handle install button click."""
        try:
            selected_asset = self.selected_asset_ref.get("asset")
            super().close()
            self.on_asset_selected(selected_asset)
        except Exception as e:
            self.logger.error(f"Error handling install: {e}")

    def _detect_user_platform(self) -> AssetPlatform:
        """
        Detect the user's current platform.

        Returns:
            AssetPlatform: The detected platform
        """
        system = platform.system().lower()

        if system == "windows":
            return AssetPlatform.WINDOWS
        elif system == "linux":
            return AssetPlatform.LINUX
        elif system == "darwin":
            return AssetPlatform.MACOS
        else:
            return AssetPlatform.UNKNOWN

    def _group_assets_by_platform(self, assets: List[ReleaseAsset]) -> Dict[AssetPlatform, List[ReleaseAsset]]:
        """
        Group assets by platform for organized display.
        """
        grouped = {}

        for asset in assets:
            platform = asset.platform or AssetPlatform.UNKNOWN
            if platform in [AssetPlatform.WINDOWS, AssetPlatform.LINUX]:
                if platform not in grouped:
                    grouped[platform] = []
                grouped[platform].append(asset)

        # Sort assets within each platform by graphics/sound options
        for platform_assets in grouped.values():
            platform_assets.sort(key=lambda a: (not a.graphics, not a.sounds, a.name))

        return grouped

    def _create_asset_selection_interface(self):
        """Create the asset selection interface within the scrollable frame."""
        try:
            if not self.content_frame:
                raise ValueError("Content frame not available")
            # Platform priority order (user's platform first)
            platform_order = [self.user_platform]
            for platform in AssetPlatform:
                if platform != self.user_platform and platform != AssetPlatform.UNKNOWN:
                    platform_order.append(platform)
            if AssetPlatform.UNKNOWN in self.grouped_assets:
                platform_order.append(AssetPlatform.UNKNOWN)

            # Create platform sections
            for platform in platform_order:
                if platform not in self.grouped_assets:
                    continue

                assets = self.grouped_assets[platform]
                if not assets:
                    continue

                # Platform header
                platform_name = platform.value.title()
                is_recommended = platform == self.user_platform
                header_text = f"{platform_name}"
                if is_recommended:
                    header_text += " (Recommended for your system)"

                # Platform frame
                platform_frame = self.create_section_frame(title=header_text)

                # Create radio buttons for each asset variant
                for i, asset in enumerate(assets):

                    radio_btn = ttk.Radiobutton(
                        platform_frame,
                        text=asset.name,
                        variable=self.selected_asset_var,
                        value=f"{platform.value}_{i}",
                        command=lambda a=asset: self._on_asset_radio_selected(a)
                    )
                    radio_btn.pack(anchor=tk.W, pady=2)

        except Exception as e:
            self.logger.error(f"Error creating asset selection interface: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_asset_radio_selected(self, selected_asset: ReleaseAsset):
        """
        Handle asset radio button selection.

        Args:
            selected_asset: The selected asset
        """
        try:
            # Store the selected asset
            self.selected_asset_ref["asset"] = selected_asset
            self.logger.debug(f"Asset selected: {selected_asset.name}")

            # Update install button state directly
            if self.install_btn:
                if self.selected_asset_ref.get("asset"):
                    self.install_btn.config(state=tk.NORMAL)
                else:
                    self.install_btn.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Error handling asset selection: {e}")
