# view_overlay.py - Viewport overlay for VLM-friendly visualization

import omni.ui as ui
import carb
from omni.kit.viewport.utility import get_active_viewport_window


class TimeTravelViewportOverlay:
    """Viewport overlay for displaying time information."""
    
    def __init__(self, core):
        """Initialize the viewport overlay.
        
        Args:
            core: TimeTravelCore instance for accessing time data
        """
        self._core = core
        self._is_visible = True
        self._time_frame = None
        self._date_label = None
        self._time_label = None
        
        # Create time overlay
        self._create_time_overlay()
        
        carb.log_info("[ViewOverlay] Time overlay initialized")
    
    def _create_time_overlay(self):
        """Create time display overlay in bottom-right corner."""
        # Get active viewport
        viewport_window = get_active_viewport_window()
        
        if not viewport_window:
            carb.log_warn("[ViewOverlay] No active viewport found")
            return
        
        carb.log_info(f"[ViewOverlay] Active viewport found: {viewport_window}")
        
        # Create overlay frame in viewport
        try:
            with viewport_window.get_frame("timetravel_time_overlay"):
                # Create frame that fills the viewport
                self._time_frame = ui.Frame(separate_window=False)
                
                with self._time_frame:
                    # Use absolute positioning for bottom-right corner
                    with ui.HStack():
                        ui.Spacer()
                        with ui.VStack(width=220):  # Fixed width container
                            ui.Spacer()
                            # Time display box at bottom
                            with ui.ZStack(width=200, height=80):
                                # Background rectangle
                                ui.Rectangle(
                                    style={
                                        "background_color": 0xFF1A1A1A,
                                        "border_color": 0xFF00FF00,
                                        "border_width": 2,
                                        "border_radius": 5
                                    }
                                )
                                
                                # Date and Time text - centered
                                with ui.VStack(spacing=3):
                                    ui.Spacer(height=10)  # Top padding
                                    # Date label
                                    with ui.HStack():
                                        ui.Spacer(width=50)  # Small left space
                                        self._date_label = ui.Label(
                                            "2025-01-01",
                                            style={
                                                "font_size": 24,
                                                "color": 0xFFCCCCCC,
                                                "font_weight": "normal"
                                            }
                                        )
                                        ui.Spacer()  # Larger right space (pushes text left)
                                    # Time label
                                    with ui.HStack():
                                        ui.Spacer(width=50)  # Small left space
                                        self._time_label = ui.Label(
                                            "00:00:00",
                                            style={
                                                "font_size": 28,
                                                "color": 0xFFFFFFFF,
                                                "font_weight": "bold"
                                            }
                                        )
                                        ui.Spacer()  # Larger right space (pushes text left)
                                    ui.Spacer(height=10)  # Bottom padding
                            ui.Spacer(height=10)  # Bottom margin
                
                self._time_frame.visible = self._is_visible
                carb.log_info("[ViewOverlay] Time display created successfully")
        except Exception as e:
            carb.log_error(f"[ViewOverlay] Failed to create time display: {e}")
            import traceback
            carb.log_error(traceback.format_exc())
    
    def update(self):
        """Update overlay display (called every frame)."""
        if not self._is_visible:
            return
        
        if not self._time_label or not self._date_label:
            return
        
        try:
            # Update date and time text
            current_time = self._core.get_current_time()
            date_str = current_time.strftime("%Y-%m-%d")
            time_str = current_time.strftime("%H:%M:%S")
            self._date_label.text = date_str
            self._time_label.text = time_str
        except Exception as e:
            carb.log_error(f"[ViewOverlay] Error updating time: {e}")
    
    def set_visible(self, visible: bool):
        """Show or hide the overlay."""
        self._is_visible = visible
        
        # Control time frame visibility
        if self._time_frame:
            self._time_frame.visible = visible
        
        carb.log_info(f"[ViewOverlay] Visibility set to: {visible}")
    
    def is_visible(self) -> bool:
        """Get current visibility state."""
        return self._is_visible
    
    def destroy(self):
        """Clean up overlay resources."""
        if self._time_frame:
            self._time_frame.clear()
            self._time_frame = None
        
        self._date_label = None
        self._time_label = None
        carb.log_info("[ViewOverlay] Overlay destroyed")
