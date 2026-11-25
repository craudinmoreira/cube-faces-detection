# Contribuindo

Obrigado pelo interesse! As regras completas estão no [`AGENTS.md`](AGENTS.md),
que vale para pessoas e agentes de IA. O resumo:

## Preparar

```bash
uv sync                        # Python 3.12+ e dependências do uv.lock
uv run pre-commit install      # hooks do git
scripts/install-gitleaks.sh    # opcional: sem ele, o hook usa o Docker
uv run python main.py
```

## Fazer uma mudança

1. Crie uma branch a partir da `master`: `feat/…`, `fix/…`, `perf/…`, `docs/…`.
2. Teste junto com o código (`uv run pytest --cov`), sem câmera e com imagens
   sintéticas. Mudança no pipeline de visão: compare o
   `scripts/bench_pipeline.py` antes e depois.
3. Commits em [Conventional Commits](https://www.conventionalcommits.org), **em
   inglês**: `feat(capture): guide the pending recapture`.
4. Abra o PR pelo template. A **nota de versão em português** vai no bloco
   `BEGIN_COMMIT_OVERRIDE` (veja [`docs/releases.md`](docs/releases.md)).
5. O CI precisa ficar verde ("CI ok").

Os hooks barram commits com segredos, calibração local, dados de `data/`, fotos
de câmera, lint quebrado ou mensagem fora do padrão. Se um hook falhar, corrija a
causa e não o pule.

## Segurança

Vulnerabilidade? Não abra issue pública. Veja o [`SECURITY.md`](SECURITY.md).

## Mais

- [Testes e orçamentos](docs/testing.md)
- [CI e hooks](docs/ci.md)
- [Runner self-hosted](docs/runner.md)
- [Releases e notas de versão](docs/releases.md)
- [Desenvolvimento assistido por IA](docs/ai-workflow.md)
