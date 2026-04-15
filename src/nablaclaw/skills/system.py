from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib import request

from nablaclaw.core.skills import Skill, SkillRegistry


def _shell_exec(payload: str) -> str:
    """payload json: {"cmd": "...", "timeout": 15}"""
    data = json.loads(payload)
    cmd = data["cmd"]
    timeout = int(data.get("timeout", 15))
    completed = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return json.dumps(
        {
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        },
        ensure_ascii=False,
    )


def _read_file(payload: str) -> str:
    data = json.loads(payload)
    path = Path(data["path"])
    max_chars = int(data.get("max_chars", 4000))
    return path.read_text(encoding="utf-8")[:max_chars]


def _write_file(payload: str) -> str:
    data = json.loads(payload)
    path = Path(data["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    content = data.get("content", "")
    path.write_text(content, encoding="utf-8")
    return "ok"


def _web_fetch(payload: str) -> str:
    data = json.loads(payload)
    url = data["url"]
    with request.urlopen(url, timeout=int(data.get("timeout", 15))) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    return body[: int(data.get("max_chars", 4000))]


def register_system_skills(registry: SkillRegistry) -> None:
    registry.register(
        Skill(
            name="shell_exec",
            description="Executa comando shell controlado",
            actions=["system"],
            handler=_shell_exec,
            owner="system",
        )
    )
    registry.register(
        Skill(
            name="read_file",
            description="Lê arquivo local",
            actions=["system"],
            handler=_read_file,
            owner="system",
        )
    )
    registry.register(
        Skill(
            name="write_file",
            description="Escreve arquivo local",
            actions=["system"],
            handler=_write_file,
            owner="system",
        )
    )
    registry.register(
        Skill(
            name="web_fetch",
            description="Baixa conteúdo HTTP",
            actions=["system"],
            handler=_web_fetch,
            owner="system",
        )
    )
