from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SessionState(str, Enum):
    SPAWNING = "spawning"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    FAILED = "failed"
    FINISHED = "finished"


@dataclass
class SessionController:
    state: SessionState = SessionState.SPAWNING
    history: list[SessionState] = field(default_factory=lambda: [SessionState.SPAWNING])

    def transition(self, new_state: SessionState) -> None:
        self.state = new_state
        self.history.append(new_state)

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "history": [item.value for item in self.history],
        }
