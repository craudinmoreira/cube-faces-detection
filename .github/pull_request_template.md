## O que muda

<!-- O quê e por quê. Link da issue, se houver: "Closes #123". -->

## Como validei

<!-- Testes, cobertura, ms por frame (scripts/bench_pipeline.py), acurácia (evaluation.py), screenshot da janela se for visual. -->

## Nota de versão (pt-BR)

<!--
Vai para o CHANGELOG e para a GitHub Release. Escreva para quem usa o programa.
Mudança invisível para quem usa: apague o bloco.
Uma linha por item: tipo(escopo): texto. Ver docs/releases.md.
-->
BEGIN_COMMIT_OVERRIDE
feat(capture): **Título curto.** O que a pessoa ganha com isso.
END_COMMIT_OVERRIDE

## Checklist

- [ ] Título do PR em Conventional Commits, em inglês (`feat(vision): …`, `fix(color): …`).
- [ ] Testes cobrindo a mudança; `uv run pytest --cov` passa.
- [ ] Mudança no pipeline de visão: números de antes e depois do `scripts/bench_pipeline.py`.
- [ ] Sem segredo, `.env`, `calibration.json`, `data/` ou foto de câmera no diff.
- [ ] Sem dependência nova, ou justificada acima e fixada pelo uv.
- [ ] Decisão de arquitetura registrada em `docs/adr/`, se houver.
- [ ] Nota de versão preenchida, ou bloco removido se não houver mudança visível.
