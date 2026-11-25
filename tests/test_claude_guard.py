"""Testes do hook PreToolUse do Claude Code (.claude/hooks/guard.py)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / '.claude' / 'hooks' / 'guard.py'
sys.path.insert(0, str(GUARD.parent))

from guard import check  # noqa: E402


def bash(command):
    return check({'tool_name': 'Bash', 'tool_input': {'command': command}})


@pytest.mark.parametrize(
    'command',
    [
        'git commit --no-verify -m "x"',
        'git commit -n -m x',
        'git push --no-verify',
        'SKIP=gitleaks git commit -m x',
        'uv run pre-commit uninstall',
        'git config core.hooksPath /dev/null',
        'git push --force origin feat/x',
        'git push -f',
        'git push origin +feat/x',
        'git push origin master',
        'git push origin HEAD:master',
        'gh pr merge 3 --squash',
        'git tag v1.2.0',
        'git filter-repo --path example.png --invert-paths',
        'gh secret set TOKEN --body x',
        'gh variable set SELF_HOSTED_RUNNER --body true',
        'cat .env',
        'cat .env.local',
        'head -n 3 ./config/.env.production',
        'cp service-account.json /tmp/',
        'cat key.pem',
        'cat ~/.pypirc',
        'python -c "print(open(\'.env\').read())"',
    ],
)
def test_blocks_command(command):
    assert bash(command)


@pytest.mark.parametrize(
    'command',
    [
        'uv run pytest --cov',
        'uv run ruff check .',
        'git push -u origin feat/novo-modo',
        'git push --force-with-lease origin feat/x',
        'git commit -m "feat(vision): add x"',
        'cat .env.example',
        'gh pr view 3',
        'gh pr create --base master --body-file /tmp/pr.md',
        'gh variable get SELF_HOSTED_RUNNER',
        'grep -rn "env" vision.py',
        'git log --oneline',
        'git tag --list',
    ],
)
def test_allows_command(command):
    assert bash(command) is None


SECRET_PATHS = [
    '.env',
    '/repo/.env.local',
    'certs/server.pem',
    'id.key',
    'gcp-service-account.json',
    'github-credentials.json',
    '/home/x/.pypirc',
]


@pytest.mark.parametrize('path', SECRET_PATHS)
@pytest.mark.parametrize('tool', ['Read', 'Write', 'Edit'])
def test_blocks_secret_files(tool, path):
    assert check({'tool_name': tool, 'tool_input': {'file_path': path}})


@pytest.mark.parametrize(
    'path',
    [
        '.env.example',
        'vision.py',
        'docs/ci.md',
        'keyboard.py',
        'environment.py',
        'calibration.json',
    ],
)
def test_allows_regular_files(path):
    assert check({'tool_name': 'Read', 'tool_input': {'file_path': path}}) is None


def test_blocks_grep_on_secret_path():
    assert check({'tool_name': 'Grep', 'tool_input': {'pattern': 'x', 'path': '.env'}})


def run_hook(payload):
    return subprocess.run(  # noqa: S603 - executa o próprio hook com o Python atual
        [sys.executable, str(GUARD)], input=payload, capture_output=True, text=True, check=False
    )


def test_hook_exits_2_with_reason_on_stderr():
    result = run_hook(json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git push -f'}}))

    assert result.returncode == 2
    assert 'Bloqueado pelo guard do projeto' in result.stderr


def test_hook_allows_and_ignores_invalid_input():
    allowed = run_hook(json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git status'}}))

    assert allowed.returncode == 0
    assert run_hook('not json').returncode == 0
