from tempfile import TemporaryDirectory

from nablaclaw.adapters.algorithmic import AlgorithmEngine
from nablaclaw.core import AdvancedHarness, AgentRuntime, PermissionPolicy, SkillMatrix, SkillRegistry
from nablaclaw.desktop import DesktopRuntime
from nablaclaw.skills import LocalSkillLibrary


def build_runtime() -> DesktopRuntime:
    policy = PermissionPolicy()
    policy.grant("assistant", "run_algorithm")
    policy.grant("assistant", "use_model")
    policy.grant("assistant", "spawn_agent")
    policy.grant("assistant", "create_agent:user")
    policy.grant("assistant", "create_agent:agent")
    policy.grant("assistant", "create_skill")

    skills = SkillRegistry()
    algorithms = AlgorithmEngine()
    algorithms.register("keyword_route", lambda text: "algorithm")
    algorithms.register("deterministic_router", lambda text: "ok")

    agent = AgentRuntime(
        role="assistant",
        permission_policy=policy,
        skills=skills,
        algorithms=algorithms,
        skill_matrix=SkillMatrix(),
    )

    return DesktopRuntime(harness=AdvancedHarness(root_agent=agent))


def test_desktop_runtime_process_returns_reply_and_trace() -> None:
    runtime = build_runtime()
    reply, trace = runtime.process("teste")
    assert reply.startswith("🤖 Assistente:")
    assert len(trace) > 0


def test_desktop_runtime_agent_and_skill_commands() -> None:
    runtime = build_runtime()
    with TemporaryDirectory() as tmp:
        runtime.harness.skill_library = LocalSkillLibrary(f"{tmp}/skills.json")
        reply1, _ = runtime.process("/agent create user worker1")
        assert "worker1" in reply1

        reply2, _ = runtime.process("/skill create assistant shout uppercase")
        assert "shout" in reply2

        names = runtime.harness.root_agent.skills.list_names()
        assert "shout" in names
        assert runtime.harness.root_agent.skills.execute("shout", "abc") == "ABC"
