from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskKind(str, Enum):
    CLASSIFY = "classify"
    EXTRACT = "extract"
    SUMMARIZE = "summarize"
    PLAN = "plan"
    GENERAL = "general"


@dataclass(slots=True)
class Task:
    """Unidade de trabalho para o harness multiagente."""

    id: str
    kind: TaskKind
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionContext:
    task: Task
    requester_role: str
    max_cost: int = 0
    trace: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExecutionResult:
    task_id: str
    output: str
    route: str
    consumed_budget: int
    trace: list[str]
