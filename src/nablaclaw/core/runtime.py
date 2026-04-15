from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from nablaclaw.adapters.algorithmic import AlgorithmEngine
from nablaclaw.adapters.base import ModelAdapter
from nablaclaw.core.lifecycle import AgentNode
from nablaclaw.core.permissions import PermissionPolicy
from nablaclaw.core.personality import EmotionState, PersonalityProfile, SkillMatrix
from nablaclaw.core.skills import SkillRegistry
from nablaclaw.core.types import Task, TaskKind


class EchoModel(ModelAdapter):
    """Stub para desenvolvimento local inicial."""

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        prefix = f"[{system}] " if system else ""
        return f"{prefix}MODEL::{prompt}"


@dataclass
class AgentRuntime:
    role: str
    permission_policy: PermissionPolicy
    skills: SkillRegistry
    algorithms: AlgorithmEngine
    model: ModelAdapter | None = None
    max_spawn_depth: int = 3
    personality: PersonalityProfile = field(default_factory=PersonalityProfile)
    emotions: EmotionState = field(default_factory=EmotionState)
    skill_matrix: SkillMatrix = field(default_factory=SkillMatrix)
    node: AgentNode | None = None
    _depth: int = field(default=0, repr=False)

    def _route(self, task: Task) -> str:
        if task.kind in {TaskKind.CLASSIFY, TaskKind.EXTRACT} and self.algorithms.has(
            "deterministic_router"
        ):
            return "algorithm"
        if len(task.content) < 120 and self.algorithms.has("keyword_route"):
            return "algorithm"
        return "model"

    def _ensure_awake(self) -> None:
        if self.node is not None and not self.node.is_awake():
            raise RuntimeError(f"Agente '{self.role}' está dormindo")

    def advance_cycle(self) -> None:
        """Avança o ciclo interno (cooldowns, estados temporais)."""
        self.skill_matrix.tick()

    def handle_task(self, task: Task | str) -> str:
        self._ensure_awake()
        if isinstance(task, str):
            task = Task(id="adhoc", kind=TaskKind.GENERAL, content=task)

        route = self._route(task)
        if route == "algorithm":
            self.permission_policy.require(self.role, "run_algorithm")
            algorithm = (
                "deterministic_router"
                if self.algorithms.has("deterministic_router")
                else "keyword_route"
            )
            decision = self.algorithms.run(algorithm, task.content)
            self.emotions.update(focus_delta=0.03)
            self.advance_cycle()
            return f"ALG::{decision}"

        self.permission_policy.require(self.role, "use_model")
        active_model = self.model or EchoModel()
        style = self.personality.style_prefix(self.emotions)
        self.emotions.update(arousal_delta=0.05)
        self.advance_cycle()
        return active_model.generate(
            task.content,
            system=f"role={self.role};kind={task.kind.value};{style}",
        )

    def execute_skill(self, skill_name: str, payload: str) -> str:
        self._ensure_awake()
        self.permission_policy.require(self.role, f"skill:{skill_name}")
        self.skill_matrix.consume(skill_name)
        return self.skills.execute(skill_name, payload)

    def spawn_agent(self, role: str) -> "AgentRuntime":
        self.permission_policy.require(self.role, "spawn_agent")
        if self._depth + 1 > self.max_spawn_depth:
            raise RuntimeError(
                f"Spawn depth excedida para '{self.role}' (max={self.max_spawn_depth})"
            )
        return AgentRuntime(
            role=role,
            permission_policy=self.permission_policy,
            skills=self.skills,
            algorithms=self.algorithms,
            model=self.model,
            max_spawn_depth=self.max_spawn_depth,
            personality=deepcopy(self.personality),
            emotions=EmotionState(),
            skill_matrix=deepcopy(self.skill_matrix),
            _depth=self._depth + 1,
        )
