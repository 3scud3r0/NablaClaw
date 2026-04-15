from __future__ import annotations

import base64
from dataclasses import dataclass, field
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Button, Frame, Label, Text, Tk
from tkinter.scrolledtext import ScrolledText

from nablaclaw.core import AdvancedHarness, ExecutionContext, Task, TaskKind
from nablaclaw.skills import SkillSpec
from nablaclaw.web import ScreenCapture


@dataclass
class DesktopRuntime:
    harness: AdvancedHarness
    history: list[tuple[str, str]] = field(default_factory=list)

    def _handle_command(self, text: str) -> str | None:
        parts = text.split()
        if not parts:
            return None

        if parts[:2] == ["/agent", "list"]:
            return "Agentes: " + ", ".join(self.harness.factory.list_roles())

        if len(parts) >= 4 and parts[:2] == ["/agent", "create"]:
            actor = parts[2]
            new_role = parts[3]
            if actor == "user":
                self.harness.create_agent_for_user(new_role)
            else:
                self.harness.create_agent_for_agent(actor, new_role)
            return f"Agente '{new_role}' criado por '{actor}'."

        if parts[:2] == ["/skill", "list"]:
            names = self.harness.root_agent.skills.list_names()
            return "Skills: " + ", ".join(names)

        if len(parts) >= 5 and parts[:2] == ["/skill", "create"]:
            # /skill create <actor_role> <name> <mode> [from] [to]
            actor_role = parts[2]
            name = parts[3]
            mode = parts[4]
            replace_from = parts[5] if len(parts) > 5 else ""
            replace_to = parts[6] if len(parts) > 6 else ""
            spec = SkillSpec(
                name=name,
                description=f"Skill {name} criada via UI",
                actions=["transform"],
                mode=mode,
                replace_from=replace_from,
                replace_to=replace_to,
                owner=actor_role,
            )
            self.harness.create_skill(actor_role=actor_role, spec=spec, skill_registry=self.harness.root_agent.skills)
            return f"Skill '{name}' criada por '{actor_role}'."

        return None

    def process(self, text: str, requester_role: str = "assistant") -> tuple[str, list[str]]:
        command_reply = self._handle_command(text)
        if command_reply is not None:
            reply = f"🤖 Assistente: {command_reply}"
            self.history.append((text, reply))
            return reply, ["command_executed"]

        task = Task(id=f"desktop-{len(self.history)+1}", kind=TaskKind.GENERAL, content=text)
        ctx = ExecutionContext(task=task, requester_role=requester_role)
        result = self.harness.run(ctx)
        reply = (
            f"🤖 Assistente: {result.output}\n"
            f"(rota={result.route}, custo={result.consumed_budget}, passos={len(result.trace)})"
        )
        self.history.append((text, reply))
        return reply, result.trace


class DesktopWindow:
    def __init__(self, runtime: DesktopRuntime, title: str = "NablaClaw Desktop") -> None:
        self.runtime = runtime
        self.capture = ScreenCapture(fps=1)
        self.root = Tk()
        self.root.title(title)
        self.root.geometry("1280x800")

        main = Frame(self.root)
        main.pack(fill=BOTH, expand=True)

        left = Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True)

        right = Frame(main)
        right.pack(side=RIGHT, fill=BOTH)

        self.messages = ScrolledText(left, wrap="word", height=28)
        self.messages.pack(side=TOP, fill=BOTH, expand=True)

        composer = Frame(left)
        composer.pack(side=TOP, fill=BOTH)

        self.input = Text(composer, height=4)
        self.input.pack(side=LEFT, fill=BOTH, expand=True)

        send = Button(composer, text="Enviar", command=self.on_send)
        send.pack(side=RIGHT)

        self.activity = ScrolledText(right, width=48, wrap="word")
        self.activity.pack(side=TOP, fill=BOTH, expand=True)
        self.activity.insert(END, "Atividade dos agentes em tempo real\n")

        self.screen_label = Label(right, text="Vídeo do desktop do agente (instale mss para habilitar)")
        self.screen_label.pack(side=TOP, fill=BOTH)
        self._screen_image = None

        self._add_assistant(
            "Interface desktop iniciada. Comandos: /agent list | /agent create <user|role> <novo_role> | /skill list | /skill create <role> <nome> <mode>"
        )
        self.root.after(1200, self.refresh_screen)

    def _add_user(self, text: str) -> None:
        self.messages.insert(END, f"\nVocê: {text}\n")
        self.messages.see(END)

    def _add_assistant(self, text: str) -> None:
        self.messages.insert(END, f"\n{text}\n")
        self.messages.see(END)

    def on_send(self) -> None:
        text = self.input.get("1.0", END).strip()
        if not text:
            return
        self.input.delete("1.0", END)
        self._add_user(text)
        reply, trace = self.runtime.process(text)
        self._add_assistant(reply)
        for item in trace:
            self.activity.insert(END, f"{item}\n")
        self.activity.see(END)

    def refresh_screen(self) -> None:
        try:
            if self.capture.available():
                png = self.capture.snapshot_png()
                encoded = base64.b64encode(png).decode("ascii")
                self._screen_image = __import__("tkinter").PhotoImage(data=encoded)
                self.screen_label.configure(image=self._screen_image, text="")
            else:
                self.screen_label.configure(text="Vídeo indisponível: instale mss para captura.", image="")
        except Exception:
            self.screen_label.configure(text="Falha ao capturar tela (verifique permissões).", image="")
        finally:
            self.root.after(1200, self.refresh_screen)

    def run(self) -> None:
        self.root.mainloop()


def run_desktop_window(harness: AdvancedHarness) -> None:
    runtime = DesktopRuntime(harness=harness)
    window = DesktopWindow(runtime=runtime)
    window.run()
