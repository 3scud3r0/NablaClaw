from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetManager:
    """Controle simples de orçamento (tokens/custo relativo)."""

    remaining: int

    def reserve(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount deve ser >= 0")
        if amount > self.remaining:
            raise RuntimeError(
                f"Orçamento insuficiente: pedido={amount}, restante={self.remaining}"
            )
        self.remaining -= amount

    def can_afford(self, amount: int) -> bool:
        return amount <= self.remaining
