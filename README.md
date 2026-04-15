# NablaClaw

Framework multiagente com foco em execução local, economia de tokens e controle operacional.

## O que foi incorporado agora

- Criação dinâmica de agentes por:
  - usuário (`create_agent:user`);
  - agentes (`create_agent:agent`).
- Criação de skills por usuário/agentes (`create_skill`).
- Biblioteca local de skills (`~/.nablaclaw/skills.json`) com persistência.
- Carregamento/registro de skills da biblioteca local para runtime.
- Comandos no desktop para criar/listar agentes e skills sem codar.

## Comandos desktop

No modo `nablaclaw desktop`, você pode usar no chat:

- `/agent list`
- `/agent create <user|role> <novo_role>`
- `/skill list`
- `/skill create <role> <name> <mode> [replace_from] [replace_to]`

`mode` suportados: `identity`, `lowercase`, `uppercase`, `strip`, `replace`.

## Execução

```bash
pip install -e .
pytest -q
nablaclaw desktop --provider echo
```
