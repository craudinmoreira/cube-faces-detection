#!/usr/bin/env python3
"""Hook PreToolUse do Claude Code.

Barra o acesso a segredos e os atalhos que furam o gate: pular hooks do git,
force push, push direto na master, merge de PR, tags de versão, reescrita de
histórico e mudanças em secrets e variáveis do repositório.

Entrada: o JSON do evento no stdin. Saída 2 bloqueia, e a mensagem no stderr
volta para o agente. Só usa a biblioteca padrão.
"""

import json
import re
import sys

# Arquivos que um agente nunca deve ler nem escrever.
SECRET_FILE = re.compile(
    r'(^|[\\/])('
    r'\.env(\.(?!example$)[\w.-]+)?'
    r'|[^\\/]*\.(pem|key|p12|pfx)'
    r'|[^\\/]*service-account[^\\/]*\.json'
    r'|[^\\/]*-credentials\.json'
    r'|\.pypirc'
    r')$',
    re.IGNORECASE,
)

# Comandos que leem ou copiam conteúdo de arquivo.
READS_FILE = re.compile(
    r'\b(cat|less|more|head|tail|bat|nl|strings|xxd|base64|cp|scp|curl|source|python3?|uv\s+run)\b|(^|\s)\.\s'
)

# Um trecho de comando sem separadores de shell.
_ = r'[^\n|;&]*'

BLOCKED_COMMANDS = [
    (
        rf'\bgit\b{_}\s--no-verify\b|\bgit\s+commit\b{_}\s-n\b',
        'não pule os hooks do git (gitleaks, ruff, mensagem). Corrija a causa da falha.',
    ),
    (rf'\bSKIP=\S+{_}\bgit\b', 'não pule hooks do pre-commit com SKIP=.'),
    (r'\bpre-commit\s+uninstall\b', 'não desinstale os hooks do git.'),
    (rf'\bgit\s+config\b{_}core\.hooksPath', 'não altere o caminho dos hooks.'),
    (
        rf'\bgit\s+push\b{_}(\s--force(?!-with-lease)\b|\s-f\b|\s\+\S)',
        'force push reescreve histórico publicado. Use --force-with-lease na sua branch ou peça à pessoa.',
    ),
    (rf'\bgit\s+push\b{_}\s(origin\s+)?(HEAD:)?master\b', 'a master só recebe PR. Abra um PR.'),
    (r'\bgh\s+pr\s+merge\b', 'o merge é da pessoa, não do agente.'),
    (rf'\bgit\s+tag\b{_}\bv\d', 'tags de versão são criadas pelo release-please.'),
    (
        r'\bgit\s+(filter-repo|filter-branch)\b',
        'reescrever o histórico exige aprovação explícita da pessoa.',
    ),
    (r'\bgh\s+secret\s+(set|delete|remove)\b', 'secrets são geridos pela pessoa, não pelo agente.'),
    (
        r'\bgh\s+variable\s+(set|delete)\b',
        'variáveis do repo (ex.: SELF_HOSTED_RUNNER) são decisão da pessoa.',
    ),
]
BLOCKED_COMMANDS = [(re.compile(pattern), reason) for pattern, reason in BLOCKED_COMMANDS]

TOKEN_SPLIT = re.compile(r'''[\s'"=<>|;&()]+''')
FILE_TOOLS_PATH_KEYS = ('file_path', 'notebook_path', 'path')


def check(event):
    """Devolve o motivo do bloqueio, ou None se a ação é permitida."""
    tool = event.get('tool_name')
    args = event.get('tool_input') or {}

    if tool == 'Bash':
        command = str(args.get('command', ''))
        for pattern, reason in BLOCKED_COMMANDS:
            if pattern.search(command):
                return reason
        if READS_FILE.search(command):
            for token in TOKEN_SPLIT.split(command):
                if SECRET_FILE.search(token):
                    return f'acesso a arquivo de segredo ({token}).'
        return None

    for key in FILE_TOOLS_PATH_KEYS:
        path = str(args.get(key) or '')
        if path and SECRET_FILE.search(path):
            return f'arquivo de segredo ({path}). Peça à pessoa o que precisar.'
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    reason = check(event)
    if reason:
        print(f'Bloqueado pelo guard do projeto: {reason}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
