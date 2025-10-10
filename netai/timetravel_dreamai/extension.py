# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary

import omni.ext
import omni.ui as ui
import omni.usd
from pxr import Usd, UsdGeom, Gf
import carb
from .window import TimeTravelWindow
from .core import TimeTravelCore


class NetAITimetravelDreamAI(omni.ext.IExt):
    """Time Travel Extension for visualizing object movements over time."""
    
    def on_startup(self, ext_id):
        """Initialize the extension."""
        print("[netai.timetravel_dreamai] Extension startup")
        
        # Initialize core logic
        self._core = TimeTravelCore()
        
        # Load configuration and data
        if self._core.load_config("./data/config.json"):
            self._core.load_data()
        
        # Create UI window
        self._window = TimeTravelWindow(self._core)
        
        # Start update loop
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="timetravel_update"
        )
        
        # Set initial time to earliest timestamp
        if self._core.has_data():
            self._core.set_to_earliest_time()
    
    def _on_update(self, e):
        """Update loop for playback and UI updates."""
        dt = e.payload.get("dt", 0)
        
        # Update core logic (handles playback)
        self._core.update(dt)
        
        # Update UI
        if self._window:
            self._window.update_ui()
    
    def on_shutdown(self):
        """Clean up the extension."""
        print("[netai.timetravel_dreamai] Extension shutdown")
        
        # Clean up subscription
        if hasattr(self, '_update_sub'):
            self._update_sub = None
        
        # Clean up window
        if hasattr(self, '_window') and self._window:
            self._window.destroy()
            self._window = None
        
        # Clean up core
        if hasattr(self, '_core'):
            self._core = None