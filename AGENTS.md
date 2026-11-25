# cube-faces-detection: regras do projeto para agentes de IA

Fonte única de instruções para qualquer agente (Claude Code, Codex, Cursor,
Copilot…). O `CLAUDE.md` e o `.github/copilot-instructions.md` apontam para cá.
Não duplique regras neles.

Projeto **experimental e de estudo** em Python: lê a webcam com OpenCV, encontra
uma face 3×3 do cubo mágico, classifica as cores, monta o estado de 54 adesivos e
chama solvers. Roda localmente, sem servidor e sem coleta de dados para fora da
máquina. O repositório é **público**.

## Comandos

| Para | Rode |
|---|---|
| Instalar (Python 3.12+) | `uv sync` e, uma vez por clone, `uv run pre-commit install` |
| Rodar com a câmera | `uv run python main.py` (`--debug`, `--image foto.png`, `--version`) |
| Gate rápido (o mesmo do pre-push) | `uv run pytest --cov` |
| Lint e formatação | `uv run ruff check . && uv run ruff format --check .` |
| Todos os hooks | `uv run pre-commit run --all-files` |
| Orçamento do pipeline de visão | `uv run python scripts/bench_pipeline.py` |
| Varredura de segredos no histórico | `scripts/gitleaks.sh history` |

Dependências só pelo uv: `uv add <pacote>` atualiza o `pyproject.toml` e o
`uv.lock`, e o hook `uv-export` regenera o `requirements.txt` (com hashes).

## Arquitetura

```
main.py            ponto de entrada: câmera, teclado, ciclo de captura, solver
vision.py          candidatos geométricos, seleção de grade, retificação, cor (LAB)
calibration.py     amostras e perfil de calibração de cores
stability.py       critério de observação estável (frames consistentes)
cube_state.py      estado do cubo, orientação das faces, validação, correção global
solver_utils.py    solver camada por camada (rubik-cube) e Kociemba (RubikOptimal)
ui.py              janela com o cubo planificado
data_collection.py, annotation.py, annotations.py, evaluation.py
                   coleta, anotação manual e avaliação de abordagens
version.py         versão lida do pyproject.toml
tests/             pytest, sem câmera
scripts/           gitleaks, orçamento do pipeline, runner self-hosted
docs/adr/          decisões de arquitetura (ADRs)
docs/              testes, CI, runner, releases, fluxo com IA, auditorias
CONTEXT.md         glossário do domínio
```

Regras que os testes e o CI defendem:

- **Vocabulário do domínio:** use os termos do `CONTEXT.md` (face capturada,
  observação estável, recaptura, estado válido…). Termo novo entra no glossário
  no mesmo PR.
- **Decisão de arquitetura vira ADR** em `docs/adr/NNNN-titulo.md`, em pt-BR,
  com Contexto, Decisão e Consequências. Siga os existentes.
- **Mudança de abordagem de visão ou cor se mede antes de adotar.** Use o
  `evaluation.py` com dados coletados, ou os frames sintéticos de
  `scripts/bench_pipeline.py`. O teste `tests/test_pipeline_regression.py` exige
  100% de faces e cores nos frames sintéticos, e o orçamento é de 33 ms por frame
  (mediana).
- **Testes sem câmera nem janela.** Use imagens sintéticas geradas com numpy e
  OpenCV. Cada teste roda num diretório temporário (`tests/conftest.py`). O
  `RubikOptimal` real gera tabelas de poda por minutos, então os testes usam um
  módulo falso.
- **Dados locais nunca entram no git:** `calibration.json`, `data/` (frames,
  anotações, relatórios), fotos e vídeos de câmera e as tabelas do RubikOptimal.
  Os hooks barram esses arquivos. Imagem de documentação vai em `docs/` e é
  revisada à mão, porque fotos de câmera mostram pessoas, mãos e ambientes.
- **Textos novos para quem usa o programa vão em pt-BR.**

## Fluxo de trabalho

```
pedido ──► branch (feat/…, fix/…, perf/…, refactor/…, docs/…, ci/…, chore/…)
  ──► teste que falha ──► implementação ──► gate local (hooks)
  ──► PR (template) ──► CI ok + CodeQL ──► revisão da pessoa ──► squash merge
  ──► Release PR (release-please) ──► tag vX.Y.Z + GitHub Release
```

1. **Nunca trabalhe na `master`.** Ela só recebe PR com o check "CI ok" verde.
   PRs dependentes podem ir em stack, com a base de cada PR na branch anterior.
2. **Teste junto com o código.** O piso de cobertura (`fail_under` no
   `pyproject.toml`) funciona como catraca: suba-o quando a cobertura subir e
   nunca o baixe para passar.
3. **Commits:** [Conventional Commits](https://www.conventionalcommits.org) em
   **inglês** (`feat(vision): …`, `fix(color): …`, `perf: …`). Comece o assunto
   com verbo em minúsculo. Escopos usuais: `vision, color, calibration, capture,
   state, solver, ui, eval, data, security, deps, ci, runner, release, ai, docs`.
4. **PR:** o título segue o Conventional Commits, porque vira o commit do
   squash. Na descrição vai a **nota de versão em pt-BR**, no bloco
   `BEGIN_COMMIT_OVERRIDE` (ver `docs/releases.md`), escrita para quem usa o
   programa. Mudança invisível para quem usa: apague o bloco.
5. **Release é automática:** não crie tags e não edite o `CHANGELOG.md` à mão
   fora do Release PR.
6. **O merge é da pessoa.** O agente abre o PR e acompanha o CI.

## Segurança: inegociável

- **Nunca leia, crie, imprima ou commite** `.env*`, chaves (`*.pem`, `*.key`,
  `*.p12`), `.pypirc`, JSON de service account ou tokens. Se precisar de uma
  credencial, peça à pessoa.
- **Nunca pule hooks:** nada de `--no-verify`, `SKIP=` ou
  `pre-commit uninstall`. Se um hook falhar, corrija a causa. Falso positivo
  do gitleaks vai como fingerprint em `.gitleaksignore`, com justificativa no
  PR.
- **Nunca reescreva histórico publicado** (force push sem lease, `filter-repo`,
  rebase de branch alheia) sem pedido explícito.
- **Configurações do GitHub** (ruleset, secrets, variáveis como
  `SELF_HOSTED_RUNNER`) são decisão da pessoa. Proponha e espere a aprovação.
- **Workflows:**
  - toda action fixada por SHA, com a versão em comentário;
  - `permissions` mínimas e `persist-credentials: false`;
  - nunca `pull_request_target`;
  - código de PR nunca roda no runner self-hosted (`docs/runner.md`).
- **Leitura de arquivos locais:** JSON com `json.load` e validação. Nunca
  `pickle`, `eval`, `exec`, `yaml.load` nem `subprocess` com `shell=True`. O
  ruff (regras `S`, do bandit) e o CodeQL verificam.
- **Dependência nova** só com motivo forte, explicado no PR. Fixe a versão pelo
  uv.
- Achou uma vulnerabilidade? Não abra issue pública: veja o `SECURITY.md`.
