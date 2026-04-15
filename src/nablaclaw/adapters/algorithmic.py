from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class AlgorithmEngine:
    """Registro de algoritmos locais para substituir modelos quando possível."""

    algorithms: dict[str, Callable[[str], str]] = field(default_factory=dict)

    def register(self, name: str, fn: Callable[[str], str]) -> None:
        self.algorithms[name] = fn

    def run(self, name: str, text: str) -> str:
        if name not in self.algorithms:
            raise KeyError(f"Algoritmo '{name}' não registrado")
        return self.algorithms[name](text)

    def has(self, name: str) -> bool:
        return name in self.algorithms
