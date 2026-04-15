from __future__ import annotations

from abc import ABC, abstractmethod


class ModelAdapter(ABC):
    """Contrato para qualquer provider de modelo (local ou API)."""

    @abstractmethod
    def generate(self, prompt: str, *, system: str | None = None) -> str:
        raise NotImplementedError
