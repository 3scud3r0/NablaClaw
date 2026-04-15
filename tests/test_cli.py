from nablaclaw.cli import build_parser


def test_cli_parser_accepts_chat_defaults() -> None:
    parser = build_parser()
    args = parser.parse_args(["chat"])
    assert args.command == "chat"
    assert args.provider == "echo"


def test_cli_parser_accepts_openrouter_args() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["chat", "--provider", "openrouter", "--model", "openai/gpt-4o-mini", "--api-key", "k"]
    )
    assert args.provider == "openrouter"
    assert args.model == "openai/gpt-4o-mini"
    assert args.api_key == "k"


def test_cli_parser_accepts_web_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(["web", "--host", "0.0.0.0", "--port", "9000"])
    assert args.command == "web"
    assert args.host == "0.0.0.0"
    assert args.port == 9000


def test_cli_parser_accepts_web_open_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(["web-open", "--host", "127.0.0.1", "--port", "8010"])
    assert args.command == "web-open"
    assert args.port == 8010


def test_cli_parser_accepts_desktop_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(["desktop", "--provider", "echo"])
    assert args.command == "desktop"
    assert args.provider == "echo"


def test_cli_parser_accepts_doctor_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(["doctor", "--json"])
    assert args.command == "doctor"
    assert args.json is True


def test_cli_parser_accepts_status_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(["status", "--provider", "echo"])
    assert args.command == "status"


def test_cli_parser_accepts_packet_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(["packet", "--file", "workflow.json", "--provider", "echo"])
    assert args.command == "packet"
    assert args.file == "workflow.json"
