# Desenvolvimento assistido por IA

Como agentes (Claude Code, Codex, Cursor e Copilot) trabalham neste repositório
sem furar os gates de qualidade e segurança. A ideia central é que **o agente
acelera e os gates decidem**. Nenhuma regra depende só de o agente "lembrar":
cada uma é verificada por uma camada que roda de qualquer jeito.

## Camadas

```
            instrução                       verificação automática
┌─────────────────────────────┐   ┌───────────────────────────────────────────────┐
│ AGENTS.md (fonte única)     │   │ 1. Agente   .claude/hooks/guard.py            │
│  ├ CLAUDE.md  (@AGENTS.md)  │   │             permissions.deny (segredos)       │
│  ├ copilot-instructions.md  │   │ 2. Commit   pre-commit: gitleaks · arquivos   │
│  └ Codex/Cursor: nativo     │   │             sensíveis · ruff (+bandit) · lock │
│ Skills: /feature /release   │   │             · Conventional Commits            │
│         /security-audit     │   │ 3. Push     pytest com piso de cobertura      │
│ Template de PR e de issues  │   │ 4. PR       CI ok · CodeQL · pip-audit ·      │
│ CONTEXT.md · docs/adr/      │   │             orçamento de visão · título       │
└─────────────────────────────┘   │ 5. Merge    ruleset: PR + CI ok · só squash   │
                                  │ 6. Release  Release PR revisado pela pessoa   │
                                  └───────────────────────────────────────────────┘
```

| Regra | Onde está escrita | Quem garante |
|---|---|---|
| Sem segredo no repositório | AGENTS.md › Segurança | guard (agente), gitleaks (commit e CI), push protection (GitHub) |
| Sem calibração, `data/` ou fotos de câmera no git | AGENTS.md › Arquitetura | `.gitignore` + hook `forbid-sensitive-files` (commit e CI) |
| Sem pular hooks, force push, merge ou tag pelo agente | AGENTS.md | guard + `permissions.deny` + ruleset da master |
| Conventional Commits em inglês | AGENTS.md › Fluxo | `conventional-pre-commit` (commit-msg e CI, inclusive no título do PR) |
| Testes junto com o código | skill `/feature` | piso de cobertura (pre-push e CI) |
| Pipeline de visão não regride | AGENTS.md › Arquitetura | `test_pipeline_regression.py` + `bench_pipeline.py` (CI) |
| Nada de `pickle`, `eval` ou `shell=True` | AGENTS.md › Segurança | ruff `S` (bandit) + CodeQL |
| Dependências fixadas e sem CVE | AGENTS.md | `uv.lock` com hashes, `uv-lock`/`uv-export` (hooks), pip-audit e dependency review (CI), Dependabot |
| Actions por SHA, permissões mínimas, PR fora do self-hosted | AGENTS.md › Segurança | CodeQL (actions) + `runs-on` condicional + revisão |
| Nota de versão em pt-BR | template de PR, skill `/release` | revisão do Release PR |
| O guard funciona | este documento | `tests/test_claude_guard.py` (pytest, CI) |

## Ciclo típico com um agente

1. A pessoa descreve a mudança. O agente segue o `/feature`: branch, teste que
   falha, implementação, medição (se tocar o pipeline) e gate local.
2. O agente se auto-revisa com `/code-review`, e também com `/security-review`
   se a mudança tocar workflow, runner, leitura de arquivo ou dependência.
3. O agente abre o PR pelo template, com a nota de versão em pt-BR, e
   acompanha o CI.
4. **A pessoa** revisa e faz o merge. O agente não faz merge, e o guard barra
   `gh pr merge`.
5. Na hora de lançar, o `/release` revisa o Release PR, e **a pessoa** faz o
   merge.
6. De tempos em tempos (sugestão: mensal, ou depois de um alerta), rode o
   `/security-audit`.

Não há review por IA no CI. A auto-revisão acontece na sessão do agente, antes
do PR.

## Ferramentas

| Ferramenta | Lê |
|---|---|
| Claude Code | `CLAUDE.md` (que importa o `AGENTS.md`), `.claude/settings.json`, `.claude/hooks/`, `.claude/skills/` |
| Codex | `AGENTS.md` |
| Cursor | `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` (resumo, que aponta para o `AGENTS.md`) |

Configuração pessoal do Claude Code vai em `.claude/settings.local.json`, que
fica fora do git.

## Mudanças grandes

Uma tarefa que vira vários PRs vai **em stack**: cada PR tem como base a branch
do anterior, e todos são abertos de uma vez. Depois que um PR do meio da stack
for reescrito, rebaseie os seguintes com
`git rebase --onto <nova base> <tip antigo da base> <branch>` e
`git push --force-with-lease`. O rebase comum reaplica os commits antigos.

## Manutenção destas regras

- Regra nova que vale para todos os agentes vai no `AGENTS.md`. Regra
  específica do Claude vai no `CLAUDE.md` ou em `.claude/`.
- Toda regra importante precisa de uma verificação automática na tabela acima.
  Se não tiver, crie uma (teste, lint, hook ou check), ou conte que a regra vai
  ser quebrada.
- Ao mudar o guard, atualize os casos em `tests/test_claude_guard.py`.
