# Política de segurança

## Reportar uma vulnerabilidade

Não abra uma issue pública. Use o **[reporte privado de vulnerabilidade](https://github.com/craudinmoreira/cube-faces-detection/security/advisories/new)** do GitHub. Respondo em até 7 dias.

## Escopo

O cube-faces-detection é um estudo experimental que roda localmente: lê a
webcam com OpenCV, detecta as faces do cubo e chama solvers em Python. Ele não
tem servidor, não cria contas e não envia dados para fora da máquina. O que
importa aqui:

- Segredos ou dados pessoais versionados, como fotos da câmera ou caminhos da
  máquina.
- Comprometimento da cadeia de dependências (PyPI) e do CI (GitHub Actions).
- Leitura insegura de arquivos locais (calibração, anotações, manifestos).

## Medidas em vigor

| Camada | Medida |
|---|---|
| Commits | gitleaks com `.gitleaks.toml` (`scripts/gitleaks.sh`); secret scanning e push protection do GitHub |
| Dados locais | `calibration.json` e as pastas de coleta em `data/` ficam fora do git (`.gitignore`) |
| Dependências | Versões fixadas em `uv.lock`; `requirements.txt` exportado com hashes; `pip-audit` |

## Histórico

- [Auditoria de 2026-11](docs/security/audit-2026-11.md)
