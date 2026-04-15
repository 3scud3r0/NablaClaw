from __future__ import annotations

from dataclasses import dataclass, field

from nablaclaw.core.harness import AdvancedHarness
from nablaclaw.core.types import ExecutionContext, Task, TaskKind


@dataclass
class TextChatSession:
    """Interface amigável de chat textual para usuário final."""

    harness: AdvancedHarness
    user_id: str
    locale: str = "pt-BR"
    history: list[tuple[str, str]] = field(default_factory=list)

    def _friendly_prefix(self) -> str:
        if self.locale.startswith("pt"):
            return "🤖 Assistente"
        return "🤖 Assistant"

    def ask(
        self,
        text: str,
        *,
        requester_role: str,
        kind: TaskKind = TaskKind.GENERAL,
        max_cost: int = 0,
    ) -> str:
        task = Task(id=f"msg-{len(self.history)+1}", kind=kind, content=text)
        ctx = ExecutionContext(task=task, requester_role=requester_role, max_cost=max_cost)
        result = self.harness.run(ctx)

        response = (
            f"{self._friendly_prefix()}: {result.output}\n"
            f"(rota={result.route}, custo={result.consumed_budget}, passos={len(result.trace)})"
        )
        self.history.append((text, response))
        return response
