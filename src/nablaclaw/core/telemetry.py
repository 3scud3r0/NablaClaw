from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TelemetryEvent:
    name: str
    payload: dict[str, Any]
    ts: float = field(default_factory=time.time)


@dataclass
class TelemetryStore:
    events: list[TelemetryEvent] = field(default_factory=list)
    max_events: int = 2000

    def publish(self, name: str, **payload: Any) -> None:
        self.events.append(TelemetryEvent(name=name, payload=payload))
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

    def recent(self, n: int = 25) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.events[-n:]]
