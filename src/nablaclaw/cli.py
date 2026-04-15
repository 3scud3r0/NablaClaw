from __future__ import annotations

import argparse
import webbrowser

from nablaclaw.adapters.algorithmic import AlgorithmEngine
from nablaclaw.adapters.providers import OllamaAdapter, OpenRouterAdapter
from nablaclaw.chat import TextChatSession
from nablaclaw.core import AdvancedHarness, AgentRuntime, PermissionPolicy, SkillMatrix, SkillRegistry
from nablaclaw.desktop import run_desktop_window
from nablaclaw.web import WebRuntime, run_server


def _build_runtime(provider: str, model: str, api_key: str | None) -> AgentRuntime:
    policy = PermissionPolicy()
    policy.grant("assistant", "run_algorithm")
    policy.grant("assistant", "use_model")
    policy.grant("assistant", "spawn_agent")
    policy.grant("assistant", "create_agent:user")
    policy.grant("assistant", "create_agent:agent")
    policy.grant("assistant", "create_skill")

    skills = SkillRegistry()
    algorithms = AlgorithmEngine()
    algorithms.register("keyword_route", lambda text: "algorithm" if len(text) < 90 else "model")
    algorithms.register("deterministic_router", lambda text: f"size={len(text.split())}")

    skill_matrix = SkillMatrix()

    adapter = None
    if provider == "ollama":
        adapter = OllamaAdapter(model=model)
    elif provider == "openrouter":
        if not api_key:
            raise SystemExit("--api-key é obrigatório para provider=openrouter")
        adapter = OpenRouterAdapter(model=model, api_key=api_key)

    runtime = AgentRuntime(
        role="assistant",
        permission_policy=policy,
        skills=skills,
        algorithms=algorithms,
        model=adapter,
        skill_matrix=skill_matrix,
    )
    return runtime


def _build_harness_and_session(args: argparse.Namespace) -> tuple[AdvancedHarness, TextChatSession]:
    runtime = _build_runtime(provider=args.provider, model=args.model, api_key=args.api_key)
    harness = AdvancedHarness(root_agent=runtime)
    harness.load_local_skills(runtime.skills)
    session = TextChatSession(harness=harness, user_id=args.user_id, locale=args.locale)
    return harness, session


def _run_chat(args: argparse.Namespace) -> int:
    _, session = _build_harness_and_session(args)

    print("NablaClaw chat iniciado. Digite 'sair' para encerrar.")
    while True:
        user_text = input("Você: ").strip()
        if user_text.lower() in {"sair", "exit", "quit"}:
            print("Encerrado.")
            return 0
        if not user_text:
            continue
        response = session.ask(user_text, requester_role="assistant")
        print(response)


def _run_web(args: argparse.Namespace, open_browser: bool = False) -> int:
    harness, session = _build_harness_and_session(args)
    runtime = WebRuntime(harness=harness, session=session)
    if open_browser:
        webbrowser.open(f"http://{args.host}:{args.port}")
    run_server(runtime=runtime, host=args.host, port=args.port)
    return 0


def _run_desktop(args: argparse.Namespace) -> int:
    harness, _ = _build_harness_and_session(args)
    run_desktop_window(harness)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nablaclaw")
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="Inicia chat textual local")
    chat.add_argument("--provider", choices=["echo", "ollama", "openrouter"], default="echo")
    chat.add_argument("--model", default="llama3")
    chat.add_argument("--api-key", default=None)
    chat.add_argument("--user-id", default="local-user")
    chat.add_argument("--locale", default="pt-BR")

    web = sub.add_parser("web", help="Inicia interface web estilo chat + painel de atividade")
    web.add_argument("--provider", choices=["echo", "ollama", "openrouter"], default="echo")
    web.add_argument("--model", default="llama3")
    web.add_argument("--api-key", default=None)
    web.add_argument("--user-id", default="local-user")
    web.add_argument("--locale", default="pt-BR")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8000)

    web_open = sub.add_parser("web-open", help="Abre navegador automaticamente com a interface web")
    web_open.add_argument("--provider", choices=["echo", "ollama", "openrouter"], default="echo")
    web_open.add_argument("--model", default="llama3")
    web_open.add_argument("--api-key", default=None)
    web_open.add_argument("--user-id", default="local-user")
    web_open.add_argument("--locale", default="pt-BR")
    web_open.add_argument("--host", default="127.0.0.1")
    web_open.add_argument("--port", type=int, default=8000)

    desktop = sub.add_parser("desktop", help="Abre janela desktop nativa (Tkinter)")
    desktop.add_argument("--provider", choices=["echo", "ollama", "openrouter"], default="echo")
    desktop.add_argument("--model", default="llama3")
    desktop.add_argument("--api-key", default=None)
    desktop.add_argument("--user-id", default="local-user")
    desktop.add_argument("--locale", default="pt-BR")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "chat":
        return _run_chat(args)
    if args.command == "web":
        return _run_web(args, open_browser=False)
    if args.command == "web-open":
        return _run_web(args, open_browser=True)
    if args.command == "desktop":
        return _run_desktop(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
