from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EmotionState:
    """Estado emocional contínuo do agente."""

    valence: float = 0.0
    arousal: float = 0.0
    focus: float = 0.7

    def update(
        self,
        *,
        valence_delta: float = 0.0,
        arousal_delta: float = 0.0,
        focus_delta: float = 0.0,
    ) -> None:
        self.valence = max(-1.0, min(1.0, self.valence + valence_delta))
        self.arousal = max(0.0, min(1.0, self.arousal + arousal_delta))
        self.focus = max(0.0, min(1.0, self.focus + focus_delta))


@dataclass
class PersonalityProfile:
    """Traços de personalidade (estilo Big Five simplificado)."""

    openness: float = 0.7
    conscientiousness: float = 0.8
    extraversion: float = 0.6
    agreeableness: float = 0.8
    neuroticism: float = 0.2
    tone: str = "consultivo"

    def style_prefix(self, emotion: EmotionState) -> str:
        mood = "positivo" if emotion.valence > 0.15 else "neutro"
        if emotion.valence < -0.15:
            mood = "cauteloso"
        energy = "alto" if emotion.arousal > 0.6 else "estável"
        return f"tom={self.tone};humor={mood};energia={energy};foco={emotion.focus:.2f}"


@dataclass
class SkillMatrix:
    """Mapa de habilidades com nível de proficiência e cooldown lógico."""

    proficiency: dict[str, float] = field(default_factory=dict)
    cooldowns: dict[str, int] = field(default_factory=dict)
    base_cooldowns: dict[str, int] = field(default_factory=dict)

    def set_skill(self, name: str, level: float, cooldown: int = 0) -> None:
        self.proficiency[name] = max(0.0, min(1.0, level))
        cooldown_value = max(0, cooldown)
        self.cooldowns[name] = 0
        self.base_cooldowns[name] = cooldown_value

    def can_invoke(self, name: str) -> bool:
        return self.proficiency.get(name, 0.0) > 0 and self.cooldowns.get(name, 0) == 0

    def consume(self, name: str) -> None:
        if not self.can_invoke(name):
            raise RuntimeError(f"Skill '{name}' em cooldown ou sem proficiência")
        self.cooldowns[name] = self.base_cooldowns.get(name, 0)

    def tick(self) -> None:
        for name, cooldown in list(self.cooldowns.items()):
            self.cooldowns[name] = max(0, cooldown - 1)
