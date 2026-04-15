import json
from tempfile import TemporaryDirectory

from nablaclaw.core.skills import SkillRegistry
from nablaclaw.skills import register_system_skills


def test_system_skills_register_and_execute_read_write() -> None:
    registry = SkillRegistry()
    register_system_skills(registry)

    with TemporaryDirectory() as tmp:
        target = f"{tmp}/a.txt"
        write_payload = json.dumps({"path": target, "content": "hello"})
        assert registry.execute("write_file", write_payload) == "ok"

        read_payload = json.dumps({"path": target})
        assert registry.execute("read_file", read_payload) == "hello"


def test_system_skill_shell_exec() -> None:
    registry = SkillRegistry()
    register_system_skills(registry)
    payload = json.dumps({"cmd": "echo hi"})
    result = json.loads(registry.execute("shell_exec", payload))
    assert result["returncode"] == 0
    assert "hi" in result["stdout"]
