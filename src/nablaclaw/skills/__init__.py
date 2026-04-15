"""Namespace para skills customizadas."""

from .library import LocalSkillLibrary, SkillSpec
from .system import register_system_skills

__all__ = ["LocalSkillLibrary", "SkillSpec", "register_system_skills"]
