from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PermissionPolicy:
    """RBAC com allow/deny explícito e suporte a curingas por prefixo."""

    grants: dict[str, set[str]] = field(default_factory=dict)
    denies: dict[str, set[str]] = field(default_factory=dict)

    def grant(self, role: str, action: str) -> None:
        self.grants.setdefault(role, set()).add(action)

    def deny(self, role: str, action: str) -> None:
        self.denies.setdefault(role, set()).add(action)

    def _match(self, patterns: set[str], action: str) -> bool:
        if action in patterns or "*" in patterns:
            return True
        for pattern in patterns:
            if pattern.endswith("*") and action.startswith(pattern[:-1]):
                return True
        return False

    def allowed(self, role: str, action: str) -> bool:
        role_denies = self.denies.get(role, set())
        if self._match(role_denies, action):
            return False
        role_grants = self.grants.get(role, set())
        return self._match(role_grants, action)

    def require(self, role: str, action: str) -> None:
        if not self.allowed(role, action):
            msg = f"Role '{role}' não possui permissão para '{action}'."
            raise PermissionError(msg)
