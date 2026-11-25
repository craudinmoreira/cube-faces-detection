#!/usr/bin/env bash
# Roda o gitleaks com a config do repo. Usa o binário local se existir;
# senão, a imagem Docker oficial. Sem nenhum dos dois, falha: segredo não
# passa despercebido por falta de ferramenta. Instale com scripts/install-gitleaks.sh.
#   scripts/gitleaks.sh staged   → só o que está no stage (pre-commit)
#   scripts/gitleaks.sh history  → todo o histórico (varredura retroativa)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
VERSION="$(cat .gitleaks-version)"
mode="${1:-staged}"

case "$mode" in
  staged)  args=(git --staged --no-banner --redact --config .gitleaks.toml .) ;;
  history) args=(git --log-opts=--all --no-banner --redact --config .gitleaks.toml .) ;;
  *) echo "uso: $0 [staged|history]" >&2; exit 2 ;;
esac

if command -v gitleaks >/dev/null 2>&1; then
  exec gitleaks "${args[@]}"
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  exec docker run --rm -v "$PWD:/repo" -w /repo "zricethezav/gitleaks:v${VERSION}" "${args[@]}"
else
  echo "✖ gitleaks não encontrado. Rode scripts/install-gitleaks.sh (ou instale o Docker)." >&2
  exit 1
fi
