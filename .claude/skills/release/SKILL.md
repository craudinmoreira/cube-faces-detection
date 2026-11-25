---
name: release
description: Revisa o Release PR do release-please do cube-faces-detection antes do merge, conferindo versão, CHANGELOG em pt-BR, notas faltando e estado do CI, e confere a tag e a GitHub Release depois. Use quando a pessoa pedir para "lançar", "fazer release", "revisar as notas" ou "publicar a versão".
---

# Release

O fluxo completo está em `docs/releases.md`. Você **não** cria tags e **não** faz merge: o release-please cria a tag, e a pessoa aprova.

## 1. Achar o Release PR

```bash
gh pr list --label "autorelease: pending" --json number,title,url
```

Se não houver, não há nada visível para lançar desde a última versão (só `ci`, `docs`, `chore`…). Diga isso à pessoa.

## 2. Conferir a versão

```bash
git fetch --tags
git log "$(git describe --tags --abbrev=0 2>/dev/null || echo 1a29087)"..origin/master --oneline
```

`feat` sobe minor, `fix` e `perf` sobem patch, `!` ou `BREAKING CHANGE` sobe major. Se a versão parecer errada, aponte o commit que causou. Confira também se o Release PR muda a versão no `pyproject.toml` **e** no `uv.lock`.

## 3. Revisar as notas (pt-BR, para quem usa o programa)

Leia o diff do `CHANGELOG.md` no Release PR. Para cada item:

- Está em português, claro para quem não programa, e diz o que a pessoa ganha?
- Algum item ainda está em inglês, porque o PR não tinha `BEGIN_COMMIT_OVERRIDE`? Proponha o texto e **edite a descrição do PR de origem**, não o CHANGELOG. Salve a descrição atual num arquivo, acrescente o bloco com a ferramenta Edit e depois rode:

  ```bash
  gh pr edit <n> --body-file <arquivo>
  gh workflow run release.yml        # o release-please regenera o Release PR
  ```

- Alguma mudança visível para quem usa ficou de fora? Siga o mesmo caminho.

## 4. Pronto para lançar

- CI verde no Release PR (`gh pr checks <n>`). Sem `RELEASE_PLEASE_TOKEN`, o CI não dispara sozinho no Release PR (veja `docs/releases.md`).
- Primeira release: confira que `release-as` ainda está no config. Depois dela, abra um PR removendo a linha.

Resuma para a pessoa a versão, os itens das notas e o que você conferiu. Ela faz o merge.

## 5. Depois do merge

```bash
gh run list --workflow release.yml --limit 1
gh release view "$(gh release list --limit 1 --json tagName --jq '.[0].tagName')"
```

Confirme a tag `vX.Y.Z` e a GitHub Release com as notas. Num checkout da tag, `uv run python main.py --version` deve mostrar a mesma versão.
