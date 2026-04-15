# NablaClaw

Framework multiagente com foco em execução local, economia de tokens e controle operacional.

## Conserto extremo aplicado (gap OpenClaw / Claude Code)

- Criação dinâmica de agentes por usuário e por agentes.
- Criação dinâmica de skills por usuário/agentes com persistência local.
- Biblioteca local de skills (`~/.nablaclaw/skills.json`).
- Skills de sistema reais (execução shell, leitura/escrita de arquivo, web fetch).
- Adaptadores multicanal reais (Discord webhook, Telegram bot API, Twilio WhatsApp API).
- Comandos desktop no-code para criação/listagem de agentes/skills.

## Comandos desktop

No modo `nablaclaw desktop`, você pode usar no chat:

- `/agent list`
- `/agent create <user|role> <novo_role>`
- `/skill list`
- `/skill create <role> <name> <mode> [replace_from] [replace_to]`

`mode` suportados: `identity`, `lowercase`, `uppercase`, `strip`, `replace`.

## CLI avançado

No `nablaclaw chat`:

- `/skills` lista skills disponíveis
- `/run-skill <name> <json_payload>` executa skill diretamente

Exemplos:

```bash
/run-skill shell_exec {"cmd":"ls -la"}
/run-skill web_fetch {"url":"https://example.com"}
```

## Execução

```bash
pip install -e .
pytest -q
nablaclaw desktop --provider echo
```


## Observabilidade e diagnóstico

- `nablaclaw doctor --json` roda checklist de ambiente (python, home writable, DNS, screen capture lib).
- `nablaclaw status --provider echo` imprime estado operacional (session state, agentes e skills carregadas).


## Avanços de arquitetura

- Máquina de estados de sessão (`spawning`, `ready`, `running`, `finished`, etc.).
- Telemetria estruturada em memória com eventos de execução.
- Adaptadores HTTP com retry/backoff para OpenRouter/Ollama.
- ChannelHub com entrega resiliente (`send_with_retry`) e broadcast com resultado estruturado.
- RBAC com herança de papéis (`grant_role`).


## Workflow avançado com TaskPacket

Também é possível executar workflows declarativos em JSON:

```bash
nablaclaw packet --provider echo --file workflow.json
```

Formato base:

```json
{
  "id": "pkt-1",
  "objective": "objetivo",
  "requester_role": "assistant",
  "steps": [
    {"name":"normalize","mode":"skill","payload":"ABC","actor_role":"assistant"},
    {"name":"draft","mode":"task","payload":"escreva algo","actor_role":"assistant"}
  ]
}
```
