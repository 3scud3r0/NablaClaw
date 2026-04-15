from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from nablaclaw.core.skills import Skill


@dataclass(frozen=True)
class SkillSpec:
    name: str
    description: str
    actions: list[str]
    mode: str = "identity"
    replace_from: str = ""
    replace_to: str = ""
    owner: str = "user"


class LocalSkillLibrary:
    """Biblioteca local de skills criada por usuário e agentes."""

    def __init__(self, path: str | Path | None = None) -> None:
        default_path = Path.home() / ".nablaclaw" / "skills.json"
        self.path = Path(path) if path else default_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list_specs(self) -> list[SkillSpec]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [SkillSpec(**item) for item in data]

    def save_spec(self, spec: SkillSpec) -> None:
        specs = {item.name: item for item in self.list_specs()}
        specs[spec.name] = spec
        payload = [asdict(item) for item in sorted(specs.values(), key=lambda s: s.name)]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def compile_skill(self, spec: SkillSpec) -> Skill:
        def handler(text: str) -> str:
            if spec.mode == "identity":
                return text
            if spec.mode == "lowercase":
                return text.lower()
            if spec.mode == "uppercase":
                return text.upper()
            if spec.mode == "strip":
                return " ".join(text.split())
            if spec.mode == "replace":
                return text.replace(spec.replace_from, spec.replace_to)
            raise ValueError(f"Modo de skill não suportado: {spec.mode}")

        return Skill(
            name=spec.name,
            description=spec.description,
            actions=spec.actions,
            handler=handler,
            owner=spec.owner,
        )
