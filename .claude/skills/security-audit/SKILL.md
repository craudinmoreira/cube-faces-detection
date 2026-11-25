---
name: security-audit
description: Auditoria periódica de segurança e performance do cube-faces-detection, cobrindo segredos e dados pessoais no histórico (inclusive fotos de câmera), dependências, alertas do GitHub, workflows, runner e tempo por frame do pipeline de visão, registrada em docs/security/audit-AAAA-MM.md com um PR de correções. Use quando a pessoa pedir auditoria, revisão de segurança ou checagem de vazamento.
---

# Auditoria

O modelo é `docs/security/audit-2026-11.md`. Registre cada achado com severidade e o PR que o trata.

## 1. Segredos e dados pessoais

```bash
scripts/gitleaks.sh history
gh api "repos/{owner}/{repo}/secret-scanning/alerts?state=open" --jq '.[].secret_type'
# Mídia, calibração e dados que já entraram no histórico (mesmo se apagados depois):
git log --all --diff-filter=A --name-only --format= | sort -u \
  | grep -iE '\.(png|jpe?g|bmp|gif|webp|heic|mp4|avi|mov|npy|npz|pkl)$|calibration|^data/|\.env'
```

- Se achar um vazamento confirmado, **pare e avise a pessoa na hora**. Rotacionar a credencial vem antes de limpar o histórico, e reescrever o histórico exige aprovação explícita.
- Imagem nova no histórico: abra o arquivo e diga o que aparece nele (pessoas, ambiente, caminhos ou nomes de usuário). O `example.png` antigo já foi avaliado, e a decisão foi mantê-lo.

## 2. Dependências

```bash
uvx --from pip-audit pip-audit --strict --require-hashes --disable-pip -r requirements.txt
uv tree --outdated --depth 1
gh api "repos/{owner}/{repo}/dependabot/alerts?state=open" --jq '.[].security_advisory.summary'
```

## 3. Código e workflows

```bash
gh api "repos/{owner}/{repo}/code-scanning/alerts?state=open" --jq '.[] | "\(.rule.severity) \(.rule.id) \(.most_recent_instance.location.path)"'
grep -rn "uses:" .github/workflows | grep -vE '@[0-9a-f]{40}'          # actions sem SHA
grep -rn "pull_request_target\|secrets\.\|id-token\|self-hosted" .github/workflows
grep -rnE "pickle|eval\(|exec\(|shell=True|yaml\.load|allow_pickle" --include=*.py .
```

Confira contra o `AGENTS.md` e o `docs/runner.md`:
- permissões mínimas;
- código de PR nunca roda no self-hosted;
- a imagem do runner continua fixada por digest e sem sudo.

## 4. Performance

```bash
uv run python scripts/bench_pipeline.py --json
```

Compare com a auditoria anterior (12 ms de mediana local e 15 ms no CI, em 2026-11). Se precisar de perfil, use `cProfile` num script temporário fora do repo e nunca o commite.

## 5. Registrar e corrigir

1. Escreva `docs/security/audit-AAAA-MM.md` e acrescente a linha em `SECURITY.md › Histórico`.
2. Corrija o que for direto num PR (`fix(security): …`). O que precisar de decisão vai como pergunta à pessoa, com uma recomendação.
