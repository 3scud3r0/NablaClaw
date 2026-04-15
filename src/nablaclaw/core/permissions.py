from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PermissionPolicy:
    """RBAC com allow/deny explícito, curingas e herança de papéis."""

    grants: dict[str, set[str]] = field(default_factory=dict)
    denies: dict[str, set[str]] = field(default_factory=dict)
    role_parents: dict[str, set[str]] = field(default_factory=dict)

    def grant(self, role: str, action: str) -> None:
        self.grants.setdefault(role, set()).add(action)

    def deny(self, role: str, action: str) -> None:
        self.denies.setdefault(role, set()).add(action)

    def grant_role(self, role: str, parent_role: str) -> None:
        self.role_parents.setdefault(role, set()).add(parent_role)

    def _match(self, patterns: set[str], action: str) -> bool:
        if action in patterns or "*" in patterns:
            return True
        for pattern in patterns:
            if pattern.endswith("*") and action.startswith(pattern[:-1]):
                return True
        return False

    def _expand_roles(self, role: str) -> set[str]:
        seen: set[str] = set()
        stack = [role]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.role_parents.get(current, set()))
        return seen

    def allowed(self, role: str, action: str) -> bool:
        roles = self._expand_roles(role)
        for r in roles:
            if self._match(self.denies.get(r, set()), action):
                return False
        return any(self._match(self.grants.get(r, set()), action) for r in roles)

    def require(self, role: str, action: str) -> None:
        if not self.allowed(role, action):
            msg = f"Role '{role}' não possui permissão para '{action}'."
            raise PermissionError(msg)
