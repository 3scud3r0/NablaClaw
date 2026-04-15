import json
from tempfile import NamedTemporaryFile

from nablaclaw.adapters.algorithmic import AlgorithmEngine
from nablaclaw.core import AdvancedHarness, AgentRuntime, PermissionPolicy, Skill, SkillMatrix, SkillRegistry, TaskPacket


def make_harness() -> AdvancedHarness:
    policy = PermissionPolicy()
    policy.grant("assistant", "run_algorithm")
    policy.grant("assistant", "use_model")
    policy.grant("assistant", "skill:normalize")

    skills = SkillRegistry()
    skills.register(
        Skill(name="normalize", description="norm", actions=["transform"], handler=lambda x: x.lower())
    )

    algorithms = AlgorithmEngine()
    algorithms.register("keyword_route", lambda text: "algorithm")
    algorithms.register("deterministic_router", lambda text: "ok")

    runtime = AgentRuntime(
        role="assistant",
        permission_policy=policy,
        skills=skills,
        algorithms=algorithms,
        skill_matrix=SkillMatrix(proficiency={"normalize": 1.0}, cooldowns={"normalize": 0}, base_cooldowns={"normalize": 0}),
    )
    return AdvancedHarness(root_agent=runtime)


def test_run_packet_skill_and_task_steps() -> None:
    harness = make_harness()
    packet = TaskPacket.from_json(
        json.dumps(
            {
                "id": "p1",
                "objective": "demo",
                "requester_role": "assistant",
                "steps": [
                    {"name": "normalize", "mode": "skill", "payload": "ABC", "actor_role": "assistant"},
                    {"name": "draft", "mode": "task", "payload": "texto", "actor_role": "assistant"},
                ],
            }
        )
    )
    result = harness.run_packet(packet)
    assert result.packet_id == "p1"
    assert len(result.outputs) == 2


def test_packet_cli_payload_file_shape() -> None:
    packet = {
        "id": "p2",
        "objective": "x",
        "requester_role": "assistant",
        "steps": [],
    }
    with NamedTemporaryFile("w+", suffix=".json") as f:
        f.write(json.dumps(packet))
        f.flush()
        loaded = TaskPacket.from_json(open(f.name, "r", encoding="utf-8").read())
        assert loaded.id == "p2"
