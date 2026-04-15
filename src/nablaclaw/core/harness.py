from __future__ import annotations

from dataclasses import dataclass, field

from nablaclaw.channels.multi import ChannelHub
from nablaclaw.core.agent_factory import AgentFactory
from nablaclaw.core.budget import BudgetManager
from nablaclaw.core.lifecycle import AgentMesh
from nablaclaw.core.runtime import AgentRuntime
from nablaclaw.core.session import SessionController, SessionState
from nablaclaw.core.telemetry import TelemetryStore
from nablaclaw.core.skills import SkillRegistry
from nablaclaw.core.society import AgentSociety
from nablaclaw.core.types import ExecutionContext, ExecutionResult
from nablaclaw.core.workflow import TaskPacket, WorkflowEngine, WorkflowResult
from nablaclaw.skills import LocalSkillLibrary, SkillSpec


@dataclass
class AdvancedHarness:
    """
    Harness avançado para coordenação multiagente.

    Recursos:
    - orçamento por execução;
    - trace auditável;
    - delegação entre agentes;
    - teia de agentes com invocação por trigger;
    - sociedade hierárquica;
    - criação dinâmica de agentes/skills por usuário e agentes.
    """

    root_agent: AgentRuntime
    default_budget: int = 1_000
    registry: dict[str, AgentRuntime] = field(default_factory=dict)
    mesh: AgentMesh = field(default_factory=AgentMesh)
    society: AgentSociety = field(default_factory=AgentSociety)
    channels: ChannelHub = field(default_factory=ChannelHub)
    factory: AgentFactory = field(default_factory=AgentFactory)
    skill_library: LocalSkillLibrary = field(default_factory=LocalSkillLibrary)
    session: SessionController = field(default_factory=SessionController)
    telemetry: TelemetryStore = field(default_factory=TelemetryStore)

    def __post_init__(self) -> None:
        if self.root_agent.role not in self.registry:
            self.registry[self.root_agent.role] = self.root_agent
        self.factory.register(self.root_agent)
        self.session.transition(SessionState.READY)
        self.telemetry.publish("session_ready", role=self.root_agent.role)

    def register_agent(self, agent: AgentRuntime) -> None:
        self.registry[agent.role] = agent
        self.factory.register(agent)
        self.telemetry.publish("agent_registered", role=agent.role)

    def create_agent_for_user(self, new_role: str) -> AgentRuntime:
        agent = self.factory.create_by_user(root=self.root_agent, new_role=new_role)
        self.register_agent(agent)
        return agent

    def create_agent_for_agent(self, creator_role: str, new_role: str) -> AgentRuntime:
        creator = self.registry[creator_role]
        agent = self.factory.create_by_agent(creator=creator, new_role=new_role)
        self.register_agent(agent)
        return agent

    def create_skill(self, *, actor_role: str, spec: SkillSpec, skill_registry: SkillRegistry) -> None:
        actor = self.registry[actor_role]
        actor.permission_policy.require(actor.role, "create_skill")
        self.skill_library.save_spec(spec)
        skill_registry.register(self.skill_library.compile_skill(spec))

    def load_local_skills(self, skill_registry: SkillRegistry) -> None:
        for spec in self.skill_library.list_specs():
            skill_registry.register(self.skill_library.compile_skill(spec))

    def run(self, context: ExecutionContext) -> ExecutionResult:
        self.session.transition(SessionState.RUNNING)
        self.telemetry.publish("task_started", requester=context.requester_role, task_id=context.task.id)
        budget = BudgetManager(context.max_cost or self.default_budget)
        actor = self.registry.get(context.requester_role, self.root_agent)

        context.trace.append(f"start:{actor.role}")

        route_cost = 10
        budget.reserve(route_cost)
        context.trace.append(f"budget:-{route_cost}")

        output = actor.handle_task(context.task)
        execution_cost = max(1, len(context.task.content) // 20)
        budget.reserve(execution_cost)
        context.trace.append(f"budget:-{execution_cost}")

        result = ExecutionResult(
            task_id=context.task.id,
            output=output,
            route="auto",
            consumed_budget=(context.max_cost or self.default_budget) - budget.remaining,
            trace=context.trace,
        )
        self.session.transition(SessionState.FINISHED)
        self.telemetry.publish("task_finished", task_id=context.task.id, spent=result.consumed_budget)
        return result

    def delegate(
        self,
        *,
        from_role: str,
        child_role: str,
        context: ExecutionContext,
    ) -> ExecutionResult:
        parent = self.registry[from_role]
        child = parent.spawn_agent(child_role)
        self.register_agent(child)
        context.trace.append(f"delegate:{from_role}->{child_role}")
        context.requester_role = child_role
        return self.run(context)

    def invoke_by_trigger(self, trigger: str, context: ExecutionContext) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []
        awakened_roles = self.mesh.invoke(trigger)
        for role in awakened_roles:
            local_context = ExecutionContext(
                task=context.task,
                requester_role=role,
                max_cost=context.max_cost,
                trace=[*context.trace, f"invoked:{trigger}:{role}"],
            )
            results.append(self.run(local_context))
        return results

    def notify_user(self, *, platform: str, user_id: str, text: str) -> str:
        return self.channels.send(platform=platform, user_id=user_id, text=text)

    def society_overview(self) -> str:
        return self.society.describe()


    def run_packet(self, packet: TaskPacket) -> WorkflowResult:
        engine = WorkflowEngine(self)
        return engine.run_packet(packet)

    def status(self) -> dict[str, object]:
        return {
            "session": self.session.as_dict(),
            "agents": self.factory.list_roles(),
            "skills": self.root_agent.skills.list_names(),
            "telemetry": self.telemetry.recent(20),
        }
