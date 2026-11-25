#!/usr/bin/env bash
# Instala o gitleaks (versão de .gitleaks-version) em ~/.local/bin, conferindo o checksum.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
VERSION="$(cat .gitleaks-version)"
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)  platform=linux_x64 ;;
  Linux-aarch64) platform=linux_arm64 ;;
  Darwin-arm64)  platform=darwin_arm64 ;;
  Darwin-x86_64) platform=darwin_x64 ;;
  *) echo "Plataforma não suportada: $(uname -sm)" >&2; exit 1 ;;
esac
file="gitleaks_${VERSION}_${platform}.tar.gz"
base="https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/$file" "$base/$file"
curl -fsSL -o "$tmp/checksums.txt" "$base/gitleaks_${VERSION}_checksums.txt"
(cd "$tmp" && grep " $file\$" checksums.txt | sha256sum -c -)
mkdir -p "$HOME/.local/bin"
tar -xzf "$tmp/$file" -C "$tmp" gitleaks
install -m 0755 "$tmp/gitleaks" "$HOME/.local/bin/gitleaks"
echo "✔ gitleaks $VERSION em ~/.local/bin/gitleaks"
