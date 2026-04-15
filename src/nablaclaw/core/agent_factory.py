from __future__ import annotations

from dataclasses import dataclass, field

from nablaclaw.core.runtime import AgentRuntime


@dataclass
class AgentFactory:
    """Registro/fábrica para criação dinâmica de agentes por usuário e por agentes."""

    agents: dict[str, AgentRuntime] = field(default_factory=dict)

    def register(self, agent: AgentRuntime) -> None:
        self.agents[agent.role] = agent

    def create_by_user(self, *, root: AgentRuntime, new_role: str) -> AgentRuntime:
        root.permission_policy.require(root.role, "create_agent:user")
        agent = root.spawn_agent(new_role)
        self.register(agent)
        return agent

    def create_by_agent(self, *, creator: AgentRuntime, new_role: str) -> AgentRuntime:
        creator.permission_policy.require(creator.role, "create_agent:agent")
        agent = creator.spawn_agent(new_role)
        self.register(agent)
        return agent

    def get(self, role: str) -> AgentRuntime:
        if role not in self.agents:
            raise KeyError(f"Agente '{role}' não encontrado")
        return self.agents[role]

    def list_roles(self) -> list[str]:
        return sorted(self.agents.keys())
