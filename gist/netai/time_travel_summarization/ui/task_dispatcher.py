from queue import Empty, SimpleQueue
from typing import Callable

import omni.kit.app


class UiTaskDispatcher:
    """Dispatch UI mutations onto Kit's main update loop."""

    def __init__(self, subscription_name: str):
        self._queue = SimpleQueue()
        self._active = True
        self._subscription = (
            omni.kit.app.get_app_interface()
            .get_update_event_stream()
            .create_subscription_to_pop(self._drain, name=subscription_name)
        )

    def submit(self, callback: Callable[[], None]):
        if self._active:
            self._queue.put(callback)

    def shutdown(self):
        self._active = False
        self._subscription = None

        while True:
            try:
                self._queue.get_nowait()
            except Empty:
                break

    def _drain(self, _event):
        if not self._active:
            return

        while True:
            try:
                callback = self._queue.get_nowait()
            except Empty:
                break

            callback()
