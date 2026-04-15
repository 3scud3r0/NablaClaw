from nablaclaw.adapters.algorithmic import AlgorithmEngine
from nablaclaw.chat import TextChatSession
from nablaclaw.core import AdvancedHarness, AgentRuntime, PermissionPolicy, SkillMatrix, SkillRegistry
from nablaclaw.web import EventBus, ScreenCapture, WebRuntime


def make_web_runtime() -> WebRuntime:
    policy = PermissionPolicy()
    policy.grant("assistant", "run_algorithm")
    policy.grant("assistant", "use_model")

    skills = SkillRegistry()
    algorithms = AlgorithmEngine()
    algorithms.register("keyword_route", lambda text: "algorithm")
    algorithms.register("deterministic_router", lambda text: "ok")
    runtime = AgentRuntime(
        role="assistant",
        permission_policy=policy,
        skills=skills,
        algorithms=algorithms,
        skill_matrix=SkillMatrix(),
    )
    harness = AdvancedHarness(root_agent=runtime)
    session = TextChatSession(harness=harness, user_id="u1")
    return WebRuntime(harness=harness, session=session)


def test_event_bus_publish_and_read() -> None:
    bus = EventBus()
    bus.publish("abc")
    items, idx = bus.read_from(0)
    assert idx == 1
    assert len(items) == 1
    assert "abc" in items[0]


def test_web_runtime_process_message_appends_history_and_events() -> None:
    wr = make_web_runtime()
    reply = wr.process_message("teste")
    assert reply.startswith("🤖 Assistente:")
    assert len(wr.session.history) == 1
    items, _ = wr.bus.read_from(0)
    assert any("trace::" in item for item in items)


def test_screen_capture_available_returns_bool() -> None:
    capture = ScreenCapture()
    assert isinstance(capture.available(), bool)
