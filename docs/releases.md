# Releases e notas de versão

O CHANGELOG é escrito para quem usa o programa e vira a nota da GitHub Release,
no espírito do fluxo do menew. Este projeto não tem deploy nem pacote: **a
entrega é a release**, ou seja, a tag `vX.Y.Z`, as notas e o código daquela tag.
`python main.py --version` mostra a versão.

## Fluxo

```
PR (título em inglês: feat(vision): …)          ← CI barra fora do Conventional Commits
 └─ descrição com BEGIN_COMMIT_OVERRIDE em pt-BR ← o texto que entra no CHANGELOG
      │ squash merge
      ▼
master ──► release-please atualiza o Release PR "chore(release): vX.Y.Z"
                │  (versão calculada: feat → minor, fix/perf → patch, ! → major)
                │  revise o CHANGELOG no PR
                ▼ merge
          tag vX.Y.Z + GitHub Release com as notas
```

O release-please atualiza a versão no `pyproject.toml`, no `uv.lock` e no
`.release-please-manifest.json`, e escreve o `CHANGELOG.md`.

| Tipo do commit | Seção no CHANGELOG | Versão |
|---|---|---|
| `feat` | Novidades | minor |
| `fix` | Correções | patch |
| `perf` | Desempenho | patch |
| `feat!` ou `BREAKING CHANGE:` | (na seção do tipo) | major |
| `docs`, `test`, `ci`, `chore`, `refactor`, `build`, `style` | não aparecem | — |

## Commits em inglês, notas em português

O título do PR, que vira o commit do squash, segue o Conventional Commits em
**inglês**. A nota para quem usa vai em **pt-BR** na descrição do PR, no bloco
que o release-please usa no lugar da mensagem do commit:

```
BEGIN_COMMIT_OVERRIDE
feat(capture): **Recaptura guiada.** A legenda mostra qual face falta e onde ela fica.
fix(color): O laranja deixa de ser confundido com o vermelho sob luz amarela.
END_COMMIT_OVERRIDE
```

- Uma linha por item, no formato `tipo(escopo): texto`. Um PR pode gerar vários itens ou nenhum.
- Mudança invisível para quem usa (CI, testes, docs): use um tipo oculto (`chore: …`) ou omita o bloco.
- Esqueceu? Edite a descrição do PR **depois do merge**: o release-please relê o bloco na próxima execução.

## Configuração

- `release-please-config.json`:
  - `bootstrap-sha` é o último commit antes do hardening, e o histórico anterior não entra no CHANGELOG;
  - a primeira versão é forçada como `1.0.0` (`release-as`). **Remova `release-as` no PR seguinte à 1.0.0**, senão toda release tenta ser 1.0.0.
- `.github/workflows/release.yml` roda a cada push na `master`, sempre no GitHub,
  porque escreve no repo.
- **`RELEASE_PLEASE_TOKEN` (recomendado):** um PAT fine-grained só deste repo,
  com *Contents* e *Pull requests* em leitura e escrita. PRs abertos com o
  `GITHUB_TOKEN` não disparam workflows. Sem esse PAT, o Release PR não roda o
  CI, e o check obrigatório "CI ok" não aparece: seria preciso fechar e reabrir
  o PR, ou dar push nele, para destravar.
