---
name: feature
description: Leva uma mudança no cube-faces-detection (feature, correção, ajuste de visão ou cor, melhoria de performance) do pedido ao PR aberto, passando por branch, teste que falha, gate local, medição quando o pipeline muda, auto-revisão e nota de versão em pt-BR. Use quando a pessoa pedir para implementar, corrigir ou melhorar algo no programa.
---

# Mudança ponta a ponta

Siga o `AGENTS.md` (regras, arquitetura e segurança). Este é o roteiro.

## 1. Entender e fatiar

- Releia o pedido e os termos do `CONTEXT.md`. Se faltar uma decisão (comportamento visível, texto da interface, critério de aceite de uma abordagem de visão), pergunte antes de codar.
- Uma mudança por PR. Se houver partes independentes, proponha PRs separados (em stack, se uma depender da outra).
- Decisão de arquitetura: proponha o ADR (`docs/adr/NNNN-…md`) junto.

## 2. Branch

```bash
git switch master && git pull --ff-only
git switch -c <tipo>/<descricao-curta>   # feat/, fix/, perf/, refactor/, docs/, ci/, chore/
uv sync
```

## 3. Teste primeiro

- Lógica pura (`cube_state`, `stability`, `calibration`, `annotations`): teste que falha antes do código.
- Visão e cor: imagem sintética gerada no teste (numpy e `cv2.rectangle`), como em `tests/test_grid_selection.py` e `scripts/bench_pipeline.py`. Nunca use câmera, janela, nem foto real versionada.
- Bug: reproduza num teste primeiro.

## 4. Implementar

- Respeite as regras do `AGENTS.md`: vocabulário do `CONTEXT.md`, dados locais fora do git, nada de `pickle`, `eval` ou `shell=True`, textos novos em pt-BR.
- Mudança no pipeline de visão: meça antes e depois.

  ```bash
  uv run python scripts/bench_pipeline.py --json   # antes (na master) e depois
  ```

  Se houver dados coletados localmente, rode também `uv run python evaluation.py` e cite os números no PR.

## 5. Gate local

```bash
uv run pre-commit run --all-files
uv run pytest --cov
uv run python scripts/bench_pipeline.py
```

Se algo falhar, corrija a causa. Nunca pule hooks nem baixe limites (cobertura, orçamento) para fazer passar. Se um limite precisar mudar, explique o motivo no PR. Se a cobertura subiu, suba o `fail_under`.

## 6. Commits

Conventional Commits em inglês, um assunto por commit, com verbo em minúsculo: `feat(capture): guide the pending recapture`. O hook roda gitleaks, o bloqueio de arquivos sensíveis, o ruff, a sincronia do lock e a checagem da mensagem.

## 7. Auto-revisão

Rode `/code-review` sobre o diff e corrija o que for real. Se a mudança tocar workflow, runner, leitura de arquivo ou dependência, rode também `/security-review`.

## 8. PR

Escreva a descrição num arquivo com a ferramenta Write, seguindo `.github/pull_request_template.md`. Depois:

```bash
git push -u origin HEAD
gh pr create --base master --title "<tipo>(<escopo>): <resumo em inglês>" --body-file <arquivo>
gh pr checks --watch
```

- **O que muda** e **Como validei**, com números (testes, cobertura, ms por frame, acurácia).
- **Nota de versão (pt-BR)** no bloco `BEGIN_COMMIT_OVERRIDE`, escrita para quem usa o programa: o que a pessoa ganha, não o que mudou no código. Mudança invisível: apague o bloco.

Não faça merge: isso é da pessoa.
