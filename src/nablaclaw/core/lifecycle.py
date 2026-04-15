from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SleepCycle:
    """Janela diária de atividade em UTC [wake_hour, sleep_hour)."""

    wake_hour_utc: int = 0
    sleep_hour_utc: int = 24

    def is_awake(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        hour = now.hour
        if self.wake_hour_utc <= self.sleep_hour_utc:
            return self.wake_hour_utc <= hour < self.sleep_hour_utc
        return hour >= self.wake_hour_utc or hour < self.sleep_hour_utc


@dataclass
class AgentNode:
    role: str
    tags: set[str] = field(default_factory=set)
    cycle: SleepCycle = field(default_factory=SleepCycle)
    awake_override: bool | None = None

    def is_awake(self, now: datetime | None = None) -> bool:
        if self.awake_override is not None:
            return self.awake_override
        return self.cycle.is_awake(now)

    def wake(self) -> None:
        self.awake_override = True

    def sleep(self) -> None:
        self.awake_override = False


@dataclass
class AgentMesh:
    """Teia de agentes com regras de invocação por trigger/tag."""

    nodes: dict[str, AgentNode] = field(default_factory=dict)
    triggers: dict[str, list[str]] = field(default_factory=dict)

    def register_node(self, node: AgentNode) -> None:
        self.nodes[node.role] = node

    def link_trigger(self, trigger: str, target_roles: list[str]) -> None:
        self.triggers[trigger] = target_roles

    def invoke(self, trigger: str, now: datetime | None = None) -> list[str]:
        roles = self.triggers.get(trigger, [])
        awakened: list[str] = []
        for role in roles:
            node = self.nodes.get(role)
            if node and node.is_awake(now):
                awakened.append(role)
        return awakened
