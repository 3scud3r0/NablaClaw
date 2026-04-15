from datetime import datetime, timezone
from tempfile import TemporaryDirectory

from nablaclaw.adapters.algorithmic import AlgorithmEngine
from nablaclaw.channels import ChannelHub, InMemoryChannelAdapter
from nablaclaw.chat import TextChatSession
from nablaclaw.core import (
    AdvancedHarness,
    AgentMesh,
    AgentNode,
    AgentRuntime,
    AgentSociety,
    ExecutionContext,
    PermissionPolicy,
    Skill,
    SkillMatrix,
    SkillRegistry,
    SleepCycle,
    SocietyRole,
    Task,
    TaskKind,
)
from nablaclaw.skills import LocalSkillLibrary, SkillSpec


def make_runtime() -> AgentRuntime:
    policy = PermissionPolicy()
    policy.grant("architect", "spawn_agent")
    policy.grant("architect", "run_algorithm")
    policy.grant("architect", "use_model")
    policy.grant("architect", "skill:normalize")
    policy.grant("architect", "create_agent:user")
    policy.grant("architect", "create_agent:agent")
    policy.grant("architect", "create_skill")
    policy.grant("researcher", "run_algorithm")
    policy.grant("researcher", "use_model")
    policy.grant("researcher", "skill:normalize")
    policy.grant("researcher", "create_agent:agent")
    policy.grant("researcher", "spawn_agent")
    policy.grant("researcher", "create_skill")

    skills = SkillRegistry()
    skills.register(
        Skill(
            name="normalize",
            description="normaliza",
            actions=["transform"],
            handler=lambda text: " ".join(text.lower().split()),
        )
    )

    algorithms = AlgorithmEngine()
    algorithms.register("keyword_route", lambda text: "algorithm" if len(text) < 120 else "model")
    algorithms.register("deterministic_router", lambda text: f"labels={len(text.split())}")

    skill_matrix = SkillMatrix()
    skill_matrix.set_skill("normalize", 0.9, cooldown=1)

    return AgentRuntime(
        role="architect",
        permission_policy=policy,
        skills=skills,
        algorithms=algorithms,
        max_spawn_depth=2,
        skill_matrix=skill_matrix,
    )


def test_structured_task_uses_algorithm() -> None:
    runtime = make_runtime()
    output = runtime.handle_task(Task(id="1", kind=TaskKind.CLASSIFY, content="texto curto"))
    assert output.startswith("ALG::labels=")


def test_long_general_task_uses_model_with_personality_style() -> None:
    runtime = make_runtime()
    long_task = Task(id="2", kind=TaskKind.GENERAL, content="x" * 240)
    output = runtime.handle_task(long_task)
    assert "tom=consultivo" in output
    assert output.startswith("[role=architect;kind=general;")


def test_skill_cooldown_enforced_and_released_after_cycle_tick() -> None:
    runtime = make_runtime()
    output = runtime.execute_skill("normalize", "  TEXTO   COM  ESPACOS ")
    assert output == "texto com espacos"

    try:
        runtime.execute_skill("normalize", "novo texto")
        raise AssertionError("esperava RuntimeError por cooldown")
    except RuntimeError as err:
        assert "cooldown" in str(err)

    runtime.advance_cycle()
    second_output = runtime.execute_skill("normalize", "  Mais  Um ")
    assert second_output == "mais um"


def test_spawned_agents_have_isolated_skill_matrix_state() -> None:
    runtime = make_runtime()
    child = runtime.spawn_agent("researcher")

    child.execute_skill("normalize", "A")
    parent_output = runtime.execute_skill("normalize", "B")
    assert parent_output == "b"


def test_harness_creates_agents_for_user_and_agents() -> None:
    runtime = make_runtime()
    harness = AdvancedHarness(root_agent=runtime)

    child_user = harness.create_agent_for_user("planner")
    assert child_user.role == "planner"

    researcher = runtime.spawn_agent("researcher")
    harness.register_agent(researcher)
    child_agent = harness.create_agent_for_agent("researcher", "analyst")
    assert child_agent.role == "analyst"


def test_harness_create_and_load_local_skill_library() -> None:
    runtime = make_runtime()
    registry = runtime.skills
    with TemporaryDirectory() as tmp:
        harness = AdvancedHarness(root_agent=runtime, skill_library=LocalSkillLibrary(f"{tmp}/skills.json"))
        spec = SkillSpec(
            name="upperx",
            description="uppercase",
            actions=["transform"],
            mode="uppercase",
            owner="architect",
        )
        harness.create_skill(actor_role="architect", spec=spec, skill_registry=registry)
        assert "upperx" in registry.list_names()
        assert registry.execute("upperx", "abc") == "ABC"


def test_harness_delegate_and_trigger_invocation() -> None:
    runtime = make_runtime()
    harness = AdvancedHarness(root_agent=runtime, default_budget=120)

    researcher = runtime.spawn_agent("researcher")
    harness.register_agent(researcher)

    mesh = AgentMesh()
    mesh.register_node(AgentNode(role="architect", cycle=SleepCycle(0, 24)))
    mesh.register_node(AgentNode(role="researcher", cycle=SleepCycle(0, 24)))
    mesh.link_trigger("incident_high", ["architect", "researcher"])
    harness.mesh = mesh

    ctx = ExecutionContext(
        task=Task(id="4", kind=TaskKind.GENERAL, content="delegar pesquisa"),
        requester_role="architect",
    )

    delegated = harness.delegate(from_role="architect", child_role="researcher", context=ctx)
    assert delegated.task_id == "4"
    assert any(entry == "delegate:architect->researcher" for entry in delegated.trace)

    invocations = harness.invoke_by_trigger("incident_high", ctx)
    assert len(invocations) == 2


def test_channel_notifications_and_text_chat() -> None:
    runtime = make_runtime()
    channels = ChannelHub()
    channels.register(InMemoryChannelAdapter("whatsapp"))
    channels.register(InMemoryChannelAdapter("telegram"))
    channels.register(InMemoryChannelAdapter("discord"))
    harness = AdvancedHarness(root_agent=runtime, channels=channels)

    receipt = harness.notify_user(platform="telegram", user_id="u1", text="olá")
    assert receipt == "telegram:1"

    chat = TextChatSession(harness=harness, user_id="u1", locale="pt-BR")
    answer = chat.ask("resuma este texto", requester_role="architect", kind=TaskKind.SUMMARIZE)
    assert answer.startswith("🤖 Assistente:")


def test_sleep_cycle_blocks_sleeping_agent() -> None:
    runtime = make_runtime()
    runtime.node = AgentNode(role="architect", cycle=SleepCycle(8, 18))
    runtime.node.sleep()

    try:
        runtime.handle_task(Task(id="s1", kind=TaskKind.GENERAL, content="teste"))
        raise AssertionError("esperava RuntimeError")
    except RuntimeError as err:
        assert "dormindo" in str(err)

    assert SleepCycle(0, 24).is_awake(datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc))


def test_society_hierarchy_overview() -> None:
    runtime = make_runtime()
    harness = AdvancedHarness(root_agent=runtime)

    society = AgentSociety()
    society.add_role(SocietyRole("architect", tier=0, responsibilities=("coordenação", "segurança")))
    society.add_role(SocietyRole("researcher", tier=1, responsibilities=("análise",)))
    society.add_role(SocietyRole("executor", tier=2, responsibilities=("ação",)))
    society.link("architect", "researcher")
    society.link("architect", "researcher")
    society.link("researcher", "executor")

    harness.society = society
    overview = harness.society_overview()
    assert "architect" in overview
    assert "researcher" in overview
    assert "executor" in overview
    assert overview.count("researcher") >= 1
