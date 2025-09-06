"""
ScrollableFrame Widget for YACL

This module provides a reusable scrollable frame component that encapsulates
the canvas-scrollbar-frame composition pattern with automatic mousewheel binding.
"""

import logging
from typing import Optional, Union, Callable
import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """
    A reusable scrollable frame widget that inherits from ttk.Frame and provides scrolling functionality.

    This class encapsulates the common pattern of creating a scrollable area with:
    - Canvas widget for scrolling content
    - Configurable vertical or horizontal scrolling
    - Inner frame for content
    - Automatic scroll region updates
    - Dynamic sizing with callback support
    - Recursive mousewheel binding for all child widgets
    - Auto-hide scrollbar functionality

    Usage:
        scrollable = ScrollableFrame(parent)
        scrollable.pack(fill="both", expand=True)
        content = scrollable.get_content_frame()
        # Add widgets to content frame
    """

    def __init__(self,
                parent: Union[tk.Widget, ttk.Widget],
                get_size: Optional[Callable[[], int]] = None,
                is_scroll_vertical: bool = True,
                auto_hide_scrollbar: bool = True,
                 **kwargs):
        """
        Initialize the scrollable frame.

        Args:
            parent: The parent widget to create the scrollable frame in
            get_size: Optional callback that returns the size for the scrollable dimension.
                    If None, uses parent size. For vertical scrolling, should return height.
                    For horizontal scrolling, should return width.
            is_scroll_vertical: True for vertical scrolling, False for horizontal
            auto_hide_scrollbar: True to auto-hide scrollbar when not needed
            **kwargs: Additional arguments passed to the frame
        """
        # Initialize the parent Frame
        super().__init__(parent, **kwargs)

        self.logger = logging.getLogger("YACL")

        # Configuration
        self._get_size = get_size
        self._is_scroll_vertical = is_scroll_vertical
        self.auto_hide_scrollbar = auto_hide_scrollbar

        # Configure grid weights for proper expansion
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        if not self._is_scroll_vertical:
            # For horizontal scrolling, also configure row 1 for scrollbar
            self.rowconfigure(1, weight=0)

        # Scrolling components
        self.canvas: Optional[tk.Canvas] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None
        self.content_frame: Optional[ttk.Frame] = None
        self.canvas_window: Optional[int] = None

        # Auto-hide scrollbar state
        self.scrollbar_visible = True

        # Scrolling behavior state
        self.scrolling_enabled = True
        self._bound_widgets = set()  # Track widgets with mousewheel bindings

        # Resize debouncing
        self._resize_after_id = None

        # Create the scrollable infrastructure
        self._create_scrollable_infrastructure()

        self.logger.debug(f"ScrollableFrame created (vertical={self._is_scroll_vertical}, auto_hide={self.auto_hide_scrollbar})")
    
    def _create_scrollable_infrastructure(self):
        """Create the canvas, scrollbar, and content frame with improved layout."""
        try:
            # Determine orientation-specific settings
            if self._is_scroll_vertical:
                scrollbar_orient = "vertical"
                scrollbar_grid_config = {"row": 0, "column": 1, "sticky": "nse"}
                canvas_grid_config = {"row": 0, "column": 0, "sticky": "nswe"}
            else:
                scrollbar_orient = "horizontal"
                scrollbar_grid_config = {"row": 1, "column": 0, "sticky": "swe"}
                canvas_grid_config = {"row": 0, "column": 0, "sticky": "nswe"}

            # Create canvas and scrollbar
            self.canvas = tk.Canvas(
                self,
                highlightthickness=0,
            )

            # Create scrollbar with proper command binding
            if self._is_scroll_vertical:
                self.scrollbar = ttk.Scrollbar(
                    self,
                    orient=scrollbar_orient,
                    command=self.canvas.yview,
                )
            else:
                self.scrollbar = ttk.Scrollbar(
                    self,
                    orient=scrollbar_orient,
                    command=self.canvas.xview,
                )

            self.content_frame = ttk.Frame(self.canvas)

            # Connect canvas to scrollbar
            if self._is_scroll_vertical:
                self.canvas.configure(yscrollcommand=self.scrollbar.set)
            else:
                self.canvas.configure(xscrollcommand=self.scrollbar.set)

            # Create window in canvas for content frame
            self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

            # Setup resize handling with improved logic from tk-components
            self._setup_resize_handling()

            # Use grid layout for better control (inspired by tk-components)
            self.canvas.grid(**canvas_grid_config)
            if self.auto_hide_scrollbar:
                # Initially hide scrollbar if auto-hide is enabled
                self.scrollbar_visible = False
                # Don't setup scrolling initially when auto-hide is enabled
                # It will be setup when scrollbar becomes visible
            else:
                self.scrollbar.grid(**scrollbar_grid_config)
                self.scrollbar_visible = True
                # Setup mousewheel scrolling immediately for always-visible scrollbar
                self._setup_scrolling()

            # Schedule initial canvas window configuration
            self.after_idle(self._configure_initial_canvas_window)

            # Schedule initial scrollbar visibility check for auto-hide mode
            if self.auto_hide_scrollbar:
                self.after_idle(self._check_scrollbar_visibility)

        except Exception as e:
            self.logger.error(f"Error creating scrollable infrastructure: {e}")
            raise

    def _configure_initial_canvas_window(self):
        """Configure the initial canvas window size and perform initial stretch on render."""
        if not self.canvas or not self.canvas_window or not self.content_frame:
            return

        try:
            # Wait for canvas to be properly sized
            self.canvas.update_idletasks()

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Only configure if canvas has been properly sized
            if canvas_width > 1 and canvas_height > 1:
                if self._is_scroll_vertical:
                    # For vertical scrolling, content should fill canvas width
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                else:
                    # For horizontal scrolling, content should fill canvas height
                    self.canvas.itemconfig(self.canvas_window, height=canvas_height)

                # Perform initial stretch on render
                # This prevents the scroll region from having a tiny border until the first resize
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                # Check scrollbar visibility
                self._check_scrollbar_visibility()
            else:
                # If canvas isn't sized yet, try again later
                self.after(10, self._configure_initial_canvas_window)

        except Exception as e:
            self.logger.debug(f"Error in initial canvas window configuration: {e}")

    def _setup_resize_handling(self):
        """Setup resize handling using"""
        def on_canvas_configure(event):
            """Reset the canvas window to encompass inner frame when required."""
            # Only handle events for our canvas
            if event.widget != self.canvas:
                return

            if not self.canvas or not self.canvas_window:
                return

            # Cancel any pending resize operation
            if self._resize_after_id:
                self.canvas.after_cancel(self._resize_after_id)

            # Schedule the resize operation with a small delay to debounce rapid events
            self._resize_after_id = self.canvas.after(5, lambda: self._handle_canvas_resize(event.width, event.height))



        def on_content_configure(event):
            """Reset the scroll region to encompass the inner frame."""
            # Only handle events for our content frame
            if event.widget != self.content_frame:
                return

            if not self.canvas:
                return

            try:
                # Update scroll region when content changes
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                # Check if scrollbar visibility needs updating
                self._check_scrollbar_visibility()
            except tk.TclError:
                # Canvas might be destroyed during shutdown
                pass

        # Bind resize events
        if self.canvas:
            self.canvas.bind("<Configure>", on_canvas_configure)
        if self.content_frame:
            self.content_frame.bind("<Configure>", on_content_configure)

    def _handle_canvas_resize(self, canvas_width, canvas_height):
        """Handle the actual canvas resize operation."""
        self._resize_after_id = None

        if not self.canvas or not self.canvas_window:
            return

        try:
            # Configure the canvas window size based on orientation
            if self._is_scroll_vertical:
                # For vertical scrolling, content width should match canvas width
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            else:
                # For horizontal scrolling, content height should match canvas height
                self.canvas.itemconfig(self.canvas_window, height=canvas_height)

            # Force update to ensure changes are applied
            self.canvas.update_idletasks()

            # Update scroll region after canvas resize
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # Check if scrollbar visibility needs updating after resize
            self._check_scrollbar_visibility()

        except tk.TclError:
            # Canvas might be destroyed during shutdown
            pass

    def _check_scrollbar_visibility(self):
        """Check if scrollbar should be visible and update accordingly."""
        if not self.auto_hide_scrollbar or not self.canvas or not self.scrollbar:
            return

        try:
            # Get the scroll region and canvas dimensions
            self.canvas.update_idletasks()
            scroll_region = self.canvas.cget("scrollregion")

            if scroll_region:
                # Parse scroll region: "x1 y1 x2 y2"
                _, y1, _, y2 = map(float, scroll_region.split())

                # Determine if scrolling is needed based on orientation
                if self._is_scroll_vertical:
                    content_size = y2 - y1
                    canvas_size = self.canvas.winfo_height()
                else:
                    # For horizontal scrolling, use x coordinates
                    x1, _, x2, _ = map(float, scroll_region.split())
                    content_size = x2 - x1
                    canvas_size = self.canvas.winfo_width()

                scrolling_needed = content_size > canvas_size

                if scrolling_needed and not self.scrollbar_visible:
                    self._show_scrollbar()
                elif not scrolling_needed and self.scrollbar_visible:
                    self._hide_scrollbar()
                elif not scrolling_needed and not self.scrollbar_visible and self.scrolling_enabled:
                    self._disable_scrolling()

        except Exception as e:
            self.logger.debug(f"Error checking scrollbar visibility: {e}")

    def _show_scrollbar(self):
        """Show the scrollbar, adjust canvas layout, and enable scrolling."""
        try:
            if not self.scrollbar_visible and self.scrollbar and self.canvas:
                if self._is_scroll_vertical:
                    scrollbar_grid_config = {"row": 0, "column": 1, "sticky": "nse"}
                else:
                    scrollbar_grid_config = {"row": 1, "column": 0, "sticky": "swe"}

                self.scrollbar.grid(**scrollbar_grid_config)
                self.scrollbar_visible = True

                # Setup scrolling when scrollbar becomes visible
                self._setup_scrolling()

                self.logger.debug("Scrollbar shown and scrolling enabled")

        except Exception as e:
            self.logger.error(f"Error showing scrollbar: {e}")

    def _hide_scrollbar(self):
        """Hide the scrollbar, expand canvas to full area, and disable scrolling."""
        try:
            if self.scrollbar_visible and self.scrollbar and self.canvas:
                # Disable scrolling behavior first
                self._disable_scrolling()

                # Hide scrollbar using grid_remove
                self.scrollbar.grid_remove()
                self.scrollbar_visible = False

                self.logger.debug("Scrollbar hidden and scrolling disabled")

        except Exception as e:
            self.logger.error(f"Error hiding scrollbar: {e}")

    def _disable_scrolling(self):
        """Disable mousewheel scrolling on canvas and all child widgets."""
        if not self.scrolling_enabled:
            return

        try:
            self.scrolling_enabled = False

            if self.canvas:
                self.canvas.unbind("<MouseWheel>")
                self.canvas.unbind("<Button-4>")
                self.canvas.unbind("<Button-5>")

            self._unbind_mousewheel_from_children(self.content_frame) # type: ignore

            self.logger.debug("Scrolling disabled")

        except Exception as e:
            self.logger.error(f"Error disabling scrolling: {e}")

    def _setup_canvas_scrolling(self):
        if not self.canvas:
            return

        try:
            if self._is_scroll_vertical:
                canvas_scroll_function = self.canvas.yview_scroll
            else:
                canvas_scroll_function = self.canvas.xview_scroll

            def on_mousewheel(event):
                if self.canvas and self.scrolling_enabled:
                    scroll_direction = self._get_scroll_direction(event.delta)
                    canvas_scroll_function(scroll_direction, "units")

            # Bind scroll events to canvas
            self.canvas.bind("<MouseWheel>", on_mousewheel)

            # Linux scroll bindings
            if self._is_scroll_vertical:
                self.canvas.bind("<Button-4>", lambda _e: self.canvas and self.scrolling_enabled and self.canvas.yview_scroll(-1, "units"))  # Linux scroll up
                self.canvas.bind("<Button-5>", lambda _e: self.canvas and self.scrolling_enabled and self.canvas.yview_scroll(1, "units"))   # Linux scroll down
            else:
                self.canvas.bind("<Button-4>", lambda _e: self.canvas and self.scrolling_enabled and self.canvas.xview_scroll(-1, "units"))  # Linux scroll left
                self.canvas.bind("<Button-5>", lambda _e: self.canvas and self.scrolling_enabled and self.canvas.xview_scroll(1, "units"))   # Linux scroll right

        except Exception as e:
            self.logger.error(f"Error setting up canvas scrolling: {e}")

    @staticmethod
    def _get_scroll_direction(event_delta):
        """
        Calculate scroll direction from event delta.

        Args:
            event_delta: The delta value from the scroll event

        Returns:
            int: 1 for scroll down/right, -1 for scroll up/left
        """
        return int(-1 * (event_delta / abs(event_delta)))

    def _unbind_mousewheel_from_children(self, widget: tk.Widget):
        """
        Recursively unbind mousewheel events from all child widgets.

        Args:
            widget: The widget to unbind events from and search for children
        """
        if not widget:
            return

        try:
            # Unbind mousewheel events from this widget
            try:
                widget.unbind("<MouseWheel>")
                widget.unbind("<Button-4>")
                widget.unbind("<Button-5>")
                self._bound_widgets.discard(widget)
            except tk.TclError:
                # Widget might not have bindings or might be destroyed
                pass

            # Recursively unbind from all children
            try:
                children = widget.winfo_children()
                for child in children:
                    self._unbind_mousewheel_from_children(child)
            except tk.TclError:
                pass

        except Exception as e:
            self.logger.debug(f"Error unbinding mousewheel from widget {widget}: {e}")

    def _setup_scrolling(self):
        """Setup mousewheel scrolling for the canvas and all child widgets."""
        if not self.canvas or not self.content_frame:
            return

        try:
            if not self.scrolling_enabled:
                self.scrolling_enabled = True

                self._setup_canvas_scrolling()

                self._bind_mousewheel_to_children(self.content_frame, self.canvas)

                self.logger.debug("Scrolling setup completed")

        except Exception as e:
            self.logger.error(f"Error setting up scrolling: {e}")
    
    def _bind_mousewheel_to_children(self, widget: tk.Widget, canvas: tk.Canvas):
        """
        Recursively bind mousewheel events to all child widgets that should forward scroll events.

        Args:
            widget: The widget to bind events to and search for children
            canvas: The canvas to forward scroll events to
        """
        try:
            # Define widgets that should NOT have scroll events bound to them
            # These are widgets that have their own scrolling behavior
            scrollable_widget_types = (
                tk.Text,      # Text widgets with scrollbars
                tk.Listbox,   # Listboxes with scrollbars
                tk.Canvas,    # Canvas widgets (already have scroll bindings)
                ttk.Treeview  # Treeview widgets with scrollbars
            )

            # Check if this widget should have scroll events bound
            if not isinstance(widget, scrollable_widget_types):
                # Determine scroll function based on orientation
                if self._is_scroll_vertical:
                    canvas_scroll_function = canvas.yview_scroll
                else:
                    canvas_scroll_function = canvas.xview_scroll

                # Define the scroll event handlers that check if scrolling is enabled
                def on_mousewheel(event):
                    if self.scrolling_enabled:
                        scroll_direction = self._get_scroll_direction(event.delta)
                        canvas_scroll_function(scroll_direction, "units")
                    return "break"  # Prevent event propagation

                def on_scroll_up(_event):
                    if self.scrolling_enabled:
                        canvas_scroll_function(-1, "units")
                    return "break"

                def on_scroll_down(_event):
                    if self.scrolling_enabled:
                        canvas_scroll_function(1, "units")
                    return "break"

                # Bind the scroll events to this widget
                widget.bind("<MouseWheel>", on_mousewheel, add=True)
                widget.bind("<Button-4>", on_scroll_up, add=True)    # Linux scroll up/left
                widget.bind("<Button-5>", on_scroll_down, add=True)  # Linux scroll down/right

                # Track this widget as having bindings
                self._bound_widgets.add(widget)

            # Recursively bind to all children
            try:
                children = widget.winfo_children()
                for child in children:
                    self._bind_mousewheel_to_children(child, canvas)
            except tk.TclError:
                pass

        except Exception as e:
            self.logger.error(f"Error binding mousewheel to widget {widget}: {e}")
    

    
    def get_content_frame(self) -> ttk.Frame:
        """
        Get the content frame where widgets should be added.
        """
        if not self.content_frame:
            raise RuntimeError("ScrollableFrame not properly initialized")
        return self.content_frame
    
    def refresh_bindings(self):
        """
        Refresh mousewheel bindings for all child widgets.

        This should be called after dynamically adding widgets to ensure
        they receive proper mousewheel events.
        """
        try:
            if self.canvas and self.content_frame:
                self._bind_mousewheel_to_children(self.content_frame, self.canvas)

            # Also check scrollbar visibility after refreshing bindings
            self._check_scrollbar_visibility()
        except Exception as e:
            self.logger.error(f"Error refreshing bindings: {e}")

