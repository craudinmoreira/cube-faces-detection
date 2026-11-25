# Runner self-hosted

O repositório é **público**. Um runner self-hosted que rodasse PRs executaria
código de qualquer pessoa na sua máquina. Por isso o modelo é híbrido:

| Evento | Onde roda |
|---|---|
| PR (inclusive de fork e do Dependabot), merge queue | sempre no GitHub (`ubuntu-latest`) |
| push na `master`, `workflow_dispatch` | self-hosted, **se** `vars.SELF_HOSTED_RUNNER == 'true'`; senão, GitHub |
| CodeQL, Conventional Commits, "CI ok" | sempre no GitHub |

## Isolamento

`scripts/runner/runner.sh` sobe um container novo por job a partir de
`scripts/runner/Dockerfile`:

- **Efêmero:** registrado com `--ephemeral` e criado com `docker run --rm`.
  Quando o job termina, o runner se desregistra e o container é apagado.
- A imagem base é a oficial `ghcr.io/actions/actions-runner`, fixada por
  digest, com `libgl1` para o OpenCV. O usuário `runner` sai dos grupos
  `sudo` e `docker`, e o container roda com `no-new-privileges`.
- Sem `docker.sock` e sem volumes do host. CPU, memória e pids são limitados
  (`RUNNER_CPUS`, padrão 2, e `RUNNER_MEMORY`, padrão 4g).
- O token de registro dura 1 h, é pedido a cada job via `gh` e entra por
  stdin, então não aparece no `docker inspect`.

## Operação

```bash
scripts/runner/runner.sh start                    # constrói a imagem e sobe o loop
gh variable set SELF_HOSTED_RUNNER --body true    # workflows passam a usar
scripts/runner/runner.sh status                   # loop, registros e labels
gh variable set SELF_HOSTED_RUNNER --body false   # volta tudo para o GitHub
scripts/runner/runner.sh stop                     # para e apaga os registros desta máquina
```

Para manter o runner no ar depois de reiniciar a máquina, use a unit systemd
`scripts/runner/cube-faces-detection-runner.service`. As instruções estão no
próprio arquivo.

> Se a variável estiver `true` com o runner desligado, os jobs de push ficam na
> fila esperando. Desligue a variável antes de parar o runner por muito tempo.

## Armadilhas conhecidas

- Não use `--no-default-labels`. Ele remove `self-hosted`, `linux` e `x64`, e
  nenhum job casa com o runner.
- O `stop` apaga **todos** os registros com o prefixo desta máquina, inclusive
  os que estão online, porque o container já foi destruído.
- Para atualizar o runner, troque a tag e o digest no `Dockerfile` (o
  Dependabot não acompanha esse arquivo) e rode `runner.sh build`.
