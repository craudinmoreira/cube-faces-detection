# CI e hooks locais

## Hooks locais (pre-commit)

Instale uma vez por clone:

```bash
uv sync
uv run pre-commit install
```

| Quando | Hook | O que barra |
|---|---|---|
| commit | `gitleaks` | segredos no que está no stage |
| commit | `forbid-sensitive-files` | `calibration.json`, `.env*`, qualquer coisa em `data/`, imagens e vídeos (fora de `docs/`), arrays e pickles |
| commit | `check-added-large-files`, `detect-private-key` | arquivos acima de 500 KB e chaves privadas |
| commit | `ruff-check`, `ruff-format` | lint (inclui as regras de segurança do bandit) e formatação |
| commit | `uv-lock`, `uv-export` | `uv.lock` e `requirements.txt` fora de sincronia com o `pyproject.toml` |
| mensagem | `conventional-pre-commit` | mensagem fora do Conventional Commits |
| push | `pytest` | testes falhando ou cobertura abaixo do piso |

## Workflows

`ci.yml` roda em todo PR e em push na `master`:

| Job | O que faz |
|---|---|
| Lint e hooks | `pre-commit run --all-files` (os mesmos hooks, exceto gitleaks e pytest) |
| Testes | pytest com cobertura em Python 3.12 e 3.14; tabela de cobertura no resumo |
| Orçamento do pipeline de visão | `scripts/bench_pipeline.py` (ver [testing.md](testing.md)) |
| Segredos e dependências | gitleaks no histórico inteiro, `pip-audit` sobre o lock (com hashes) e dependency review |
| Conventional Commits | cada commit do PR e o título do PR, que vira o commit no squash |
| **CI ok** | agregador: o único check exigido pelo ruleset da `master` |

`codeql.yml` roda a suíte `security-and-quality` para Python e para os
próprios workflows (`actions`) em PRs, na `master` e toda segunda-feira.

Regras dos workflows: actions fixadas por SHA, com a versão em comentário;
`permissions: contents: read` por padrão; `persist-credentials: false`; PRs
antigos do mesmo branch são cancelados por `concurrency`.

## Dependabot

Todo semana o Dependabot abre PRs agrupados para `uv`, hooks do pre-commit e
Actions. O Dependabot atualiza o `uv.lock`, mas não o `requirements.txt`
exportado. Se o job "Lint e hooks" falhar num PR dele por causa do
`uv-export`, rode `uv run pre-commit run uv-export --all-files` na branch e
faça push.
