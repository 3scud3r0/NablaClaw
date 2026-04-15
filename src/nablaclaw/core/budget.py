from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BudgetManager:
    """Controle de orçamento (tokens/custo relativo) com histórico de consumo."""

    remaining: int
    initial: int | None = None
    ledger: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.initial is None:
            self.initial = self.remaining

    def reserve(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount deve ser >= 0")
        if amount > self.remaining:
            raise RuntimeError(
                f"Orçamento insuficiente: pedido={amount}, restante={self.remaining}"
            )
        self.remaining -= amount
        self.ledger.append(amount)

    def can_afford(self, amount: int) -> bool:
        return amount <= self.remaining

    @property
    def spent(self) -> int:
        return (self.initial or 0) - self.remaining

    def as_dict(self) -> dict[str, object]:
        return {
            "initial": self.initial,
            "remaining": self.remaining,
            "spent": self.spent,
            "ledger": self.ledger,
        }
