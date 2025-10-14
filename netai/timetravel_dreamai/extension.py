# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary

import omni.ext
import omni.ui as ui
import omni.usd
from pxr import Usd, UsdGeom, Gf
import carb
import os
from pathlib import Path
from .window import TimeTravelWindow
from .core import TimeTravelCore


class NetAITimetravelDreamAI(omni.ext.IExt):
    """Time Travel Extension for visualizing object movements over time."""
    
    def on_startup(self, ext_id):
        """Initialize the extension."""
        print("[netai.timetravel_dreamai] Extension startup")
        
        # Print current working directory and extension path
        current_dir = os.getcwd()
        extension_file = Path(__file__).absolute()
        extension_dir = extension_file.parent
    
        
        # Initialize core logic
        self._core = TimeTravelCore() 
        
        # Load configuration and data
        config_path = extension_dir / "config.json"  # 익스텐션 디렉터리 기준
        
        if self._core.load_config(str(config_path)): # self._core._config, self._core._prim_map 생성됨
            self._core.load_data()  #self._core._data, self._core._timestamps 생성됨
        
        # Create UI window
        self._window = TimeTravelWindow(self._core)
        
        # Start update loop (Events 2.0)
        import omni.kit.app
        self._update_sub = (
            omni.kit.app.get_app_interface()
            .get_update_event_stream()
            .create_subscription_to_pop(self._on_update)
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