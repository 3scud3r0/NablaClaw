from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from nablaclaw.chat import TextChatSession
from nablaclaw.core import AdvancedHarness, ExecutionContext, Task, TaskKind
from nablaclaw.web.screen import ScreenCapture

HTML_PAGE = """<!doctype html>
<html lang='pt-BR'>
<head>
  <meta charset='utf-8'/>
  <meta name='viewport' content='width=device-width, initial-scale=1'/>
  <title>NablaClaw Desktop Console</title>
  <style>
    body { margin:0; font-family: Inter, system-ui, sans-serif; background:#0f172a; color:#e2e8f0; }
    .app { display:grid; grid-template-columns: 1.7fr 1fr; height:100vh; }
    .chat, .monitor { padding:20px; }
    .chat { border-right:1px solid #1e293b; display:flex; flex-direction:column; }
    .messages { flex:1; overflow:auto; display:flex; flex-direction:column; gap:12px; }
    .bubble { padding:12px 14px; border-radius:12px; max-width:85%; line-height:1.4; white-space:pre-wrap; }
    .user { align-self:flex-end; background:#2563eb; color:#fff; }
    .assistant { align-self:flex-start; background:#1e293b; }
    .composer { display:flex; gap:10px; margin-top:12px; }
    .composer textarea { flex:1; border-radius:10px; border:1px solid #334155; background:#020617; color:#fff; padding:10px; min-height:56px; }
    .composer button { border:0; border-radius:10px; background:#10b981; color:#022c22; padding:10px 14px; font-weight:700; cursor:pointer; }
    .monitor { display:grid; grid-template-rows: 1fr 1fr; gap:12px; }
    .card { background:#020617; border:1px solid #1e293b; border-radius:12px; padding:12px; overflow:hidden; }
    .card h3 { margin:0 0 8px; font-size:14px; }
    .log { height:100%; overflow:auto; }
    .event { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:12px; padding:6px 0; border-bottom:1px dashed #1e293b; }
    #screen { width:100%; height:calc(100% - 26px); object-fit:contain; background:#000; border-radius:8px; }
    .hint { font-size:12px; opacity:.8; margin-top:6px; }
  </style>
</head>
<body>
<div class='app'>
  <section class='chat'>
    <h2>NablaClaw Chat</h2>
    <div class='messages' id='messages'></div>
    <div class='composer'>
      <textarea id='input' placeholder='Digite sua mensagem...'></textarea>
      <button id='send'>Enviar</button>
    </div>
  </section>
  <aside class='monitor'>
    <div class='card'>
      <h3>Atividade dos Agentes (tempo real)</h3>
      <div class='log' id='log'></div>
    </div>
    <div class='card'>
      <h3>Vídeo em tempo real (desktop do agente)</h3>
      <img id='screen' src='/api/screen' alt='screen stream'/>
      <div class='hint' id='screenHint'>Se a stream falhar, instale: pip install mss</div>
    </div>
  </aside>
</div>
<script>
  const messages = document.getElementById('messages');
  const log = document.getElementById('log');
  const input = document.getElementById('input');
  const screen = document.getElementById('screen');
  const screenHint = document.getElementById('screenHint');

  function addMessage(text, klass) {
    const el = document.createElement('div');
    el.className = `bubble ${klass}`;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  function addEvent(text) {
    const el = document.createElement('div');
    el.className = 'event';
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  document.getElementById('send').addEventListener('click', async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage(text, 'user');

    const resp = await fetch('/api/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ message: text })
    });
    const data = await resp.json();
    addMessage(data.reply, 'assistant');
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      document.getElementById('send').click();
    }
  });

  const es = new EventSource('/api/events');
  es.onmessage = (evt) => addEvent(evt.data);

  screen.addEventListener('error', () => {
    screenHint.textContent = 'Stream indisponível (verifique mss e permissão de captura de tela).';
  });
</script>
</body>
</html>
"""


@dataclass
class EventBus:
    events: list[str] = field(default_factory=list)

    def publish(self, message: str) -> None:
        now = time.strftime("%H:%M:%S")
        self.events.append(f"[{now}] {message}")

    def read_from(self, index: int) -> tuple[list[str], int]:
        if index < 0:
            index = 0
        items = self.events[index:]
        return items, len(self.events)


@dataclass
class WebRuntime:
    harness: AdvancedHarness
    session: TextChatSession
    bus: EventBus = field(default_factory=EventBus)
    screen: ScreenCapture = field(default_factory=ScreenCapture)

    def process_message(self, text: str) -> str:
        self.bus.publish(f"user_message len={len(text)}")
        task = Task(id=f"web-{len(self.session.history)+1}", kind=TaskKind.GENERAL, content=text)
        ctx = ExecutionContext(task=task, requester_role="assistant")
        result = self.harness.run(ctx)
        self.bus.publish(f"route={result.route} cost={result.consumed_budget}")
        for item in result.trace:
            self.bus.publish(f"trace::{item}")
        reply = (
            f"🤖 Assistente: {result.output}\n"
            f"(rota={result.route}, custo={result.consumed_budget}, passos={len(result.trace)})"
        )
        self.session.history.append((text, reply))
        return reply


def build_handler(runtime: WebRuntime) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _json_response(self, payload: dict[str, str], status: int = 200) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                data = HTML_PAGE.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            if self.path == "/api/events":
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                idx = 0
                try:
                    while True:
                        items, idx = runtime.bus.read_from(idx)
                        for item in items:
                            self.wfile.write(f"data: {item}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        time.sleep(0.5)
                except (BrokenPipeError, ConnectionResetError):
                    return

            if self.path == "/api/screen":
                if not runtime.screen.available():
                    self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "capture de tela indisponível")
                    return
                self.send_response(HTTPStatus.OK)
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                try:
                    for png in runtime.screen.frames():
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/png\r\n\r\n")
                        self.wfile.write(png)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
                return

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/chat":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8") or "{}")
            msg = str(payload.get("message", "")).strip()
            if not msg:
                self._json_response({"error": "message vazio"}, status=400)
                return
            reply = runtime.process_message(msg)
            self._json_response({"reply": reply})

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def run_server(runtime: WebRuntime, host: str = "127.0.0.1", port: int = 8000) -> None:
    runtime.bus.publish("web_server_start")
    httpd = ThreadingHTTPServer((host, port), build_handler(runtime))
    print(f"NablaClaw Web disponível em http://{host}:{port}")
    httpd.serve_forever()
