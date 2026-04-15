from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from nablaclaw.core.types import ExecutionContext, Task, TaskKind


@dataclass
class WorkflowStep:
    name: str
    mode: str  # skill|task
    payload: str
    actor_role: str


@dataclass
class TaskPacket:
    id: str
    objective: str
    requester_role: str
    steps: list[WorkflowStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_json(raw: str) -> "TaskPacket":
        data = json.loads(raw)
        steps = [WorkflowStep(**item) for item in data.get("steps", [])]
        return TaskPacket(
            id=data["id"],
            objective=data["objective"],
            requester_role=data["requester_role"],
            steps=steps,
            metadata=data.get("metadata", {}),
        )


@dataclass
class WorkflowResult:
    packet_id: str
    outputs: list[dict[str, str]]


class WorkflowEngine:
    def __init__(self, harness) -> None:  # AdvancedHarness
        self.harness = harness

    def run_packet(self, packet: TaskPacket) -> WorkflowResult:
        outputs: list[dict[str, str]] = []
        self.harness.telemetry.publish("packet_started", packet_id=packet.id, objective=packet.objective)
        for step in packet.steps:
            if step.mode == "skill":
                actor = self.harness.registry[step.actor_role]
                out = actor.execute_skill(step.name, step.payload)
                outputs.append({"step": step.name, "mode": step.mode, "output": out})
                self.harness.telemetry.publish("packet_step", packet_id=packet.id, step=step.name, mode="skill")
                continue

            task = Task(id=f"{packet.id}:{step.name}", kind=TaskKind.GENERAL, content=step.payload)
            ctx = ExecutionContext(task=task, requester_role=step.actor_role)
            result = self.harness.run(ctx)
            outputs.append({"step": step.name, "mode": step.mode, "output": result.output})
            self.harness.telemetry.publish("packet_step", packet_id=packet.id, step=step.name, mode="task")

        self.harness.telemetry.publish("packet_finished", packet_id=packet.id, steps=len(packet.steps))
        return WorkflowResult(packet_id=packet.id, outputs=outputs)
