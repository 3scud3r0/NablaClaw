from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


SkillHandler = Callable[[str], str]


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    actions: list[str]
    handler: SkillHandler | None = None
    owner: str = "system"


@dataclass
class SkillRegistry:
    skills: dict[str, Skill] = field(default_factory=dict)

    def register(self, skill: Skill) -> None:
        self.skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        if name not in self.skills:
            raise KeyError(f"Skill '{name}' não encontrada")
        return self.skills[name]

    def list_names(self) -> list[str]:
        return sorted(self.skills.keys())

    def execute(self, name: str, payload: str) -> str:
        skill = self.get(name)
        if skill.handler is None:
            raise RuntimeError(f"Skill '{name}' não possui handler configurado")
        return skill.handler(payload)
