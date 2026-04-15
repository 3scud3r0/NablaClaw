from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SocietyRole:
    name: str
    tier: int
    responsibilities: tuple[str, ...]


@dataclass
class AgentSociety:
    """Hierarquia de agentes com relação líder->subordinados."""

    roles: dict[str, SocietyRole] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)

    def add_role(self, role: SocietyRole) -> None:
        self.roles[role.name] = role
        self.edges.setdefault(role.name, [])

    def link(self, leader: str, subordinate: str) -> None:
        if leader not in self.roles or subordinate not in self.roles:
            raise KeyError("Papéis precisam existir antes do vínculo")
        current = self.edges.setdefault(leader, [])
        if subordinate not in current:
            current.append(subordinate)

    def subordinates_of(self, leader: str) -> list[str]:
        return list(self.edges.get(leader, []))

    def chain_of_command(self) -> list[str]:
        return [
            name
            for name, _ in sorted(
                self.roles.items(),
                key=lambda item: (item[1].tier, item[0]),
            )
        ]

    def describe(self) -> str:
        lines: list[str] = []
        for role_name in self.chain_of_command():
            role = self.roles[role_name]
            subs = ", ".join(self.subordinates_of(role_name)) or "nenhum"
            lines.append(
                f"[{role.tier}] {role.name}: responsabilidades={';'.join(role.responsibilities)} | subordinados={subs}"
            )
        return "\n".join(lines)
