from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ScreenCapture:
    fps: int = 2

    def available(self) -> bool:
        try:
            import mss  # noqa: F401
            import mss.tools  # noqa: F401
        except Exception:
            return False
        return True

    def snapshot_png(self) -> bytes:
        import mss
        import mss.tools

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            return mss.tools.to_png(shot.rgb, shot.size)

    def frames(self):
        """Gera frames PNG para stream multipart."""
        frame_interval = 1 / max(1, self.fps)
        while True:
            yield self.snapshot_png()
            time.sleep(frame_interval)
