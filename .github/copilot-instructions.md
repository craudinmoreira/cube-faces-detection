# Instruções para o GitHub Copilot

As regras do projeto estão no [`AGENTS.md`](../AGENTS.md), a fonte única para
todos os agentes. Leia esse arquivo antes de sugerir mudanças. O essencial:

- Commits e títulos de PR em Conventional Commits, **em inglês**. A nota de
  versão vai em **pt-BR**, no bloco `BEGIN_COMMIT_OVERRIDE` da descrição do PR.
- Teste junto com o código (pytest, sem câmera, com imagens sintéticas). Mudança
  no pipeline de visão precisa manter `tests/test_pipeline_regression.py` e o
  orçamento de `scripts/bench_pipeline.py`.
- Use o vocabulário do `CONTEXT.md`. Decisão de arquitetura vira ADR em
  `docs/adr/`.
- Nunca leia nem commite `.env*`, chaves, credenciais, `calibration.json`,
  `data/` ou fotos de câmera. Nunca pule hooks (`--no-verify`, `SKIP=`).
- Nada de `pickle`, `eval`, `exec` ou `subprocess` com `shell=True`.
  Dependências só pelo uv, com versão fixada.
