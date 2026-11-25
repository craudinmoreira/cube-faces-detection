# Testes e orçamentos

## Rodar

```bash
uv run pytest                      # suíte completa, ~1 s
uv run pytest --cov                # com cobertura; falha abaixo do piso
uv run python scripts/bench_pipeline.py   # orçamento de tempo por frame
```

Nenhum teste usa câmera. Cada teste roda num diretório temporário vazio
(`tests/conftest.py`), para não ler nem gravar o `calibration.json` da máquina.
O `RubikOptimal` é substituído por um módulo falso nos testes, porque o real
gera tabelas de poda por minutos na primeira execução.

## Cobertura

O piso fica em `[tool.coverage.report] fail_under`, no `pyproject.toml`, e
funciona como catraca: quando a cobertura subir, suba o piso no mesmo PR, e
nunca o baixe para fazer o CI passar. A cobertura conta ramos
(`branch = true`).

O ponto fraco conhecido é o `main.py` (laço da câmera e do teclado OpenCV), que
só tem os helpers cobertos. Extrair a lógica do laço para funções puras é o
caminho para testá-lo.

## Regressão do pipeline de visão

`scripts/bench_pipeline.py` gera 20 frames sintéticos fixos de 640×480
(semente fixa): uma face 3×3 com cores conhecidas sobre fundo com ruído, em
posição e tamanho variáveis.

- `tests/test_pipeline_regression.py` exige que todas as faces e todas as cores
  sejam reconhecidas. Não mede tempo.
- O script mede o tempo de `process_frame` (3 frames de aquecimento e
  5 repetições) e falha se a mediana passar de **33 ms**, que é um frame a
  30 fps, ou se o p95 passar de **50 ms**. A medida local fica em torno de
  12 ms.

Se uma mudança intencional alterar o pipeline, ajuste os frames ou o orçamento
no mesmo PR e explique o motivo na descrição.
