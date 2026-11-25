@AGENTS.md

## Específico do Claude Code

- `.claude/settings.json` bloqueia a leitura de arquivos de segredo, e
  `.claude/hooks/guard.py` barra comandos que furam o gate: pular hooks,
  force push, push na master, `gh pr merge`, tags de versão, reescrita de
  histórico, `gh secret` e `gh variable`. Se o hook barrar algo, não contorne:
  explique à pessoa e, se for o caso, sugira que ela rode o comando com `!`.
- O guard analisa o texto inteiro do comando. Escreva arquivos com a
  ferramenta Write e passe descrições de PR via `--body-file`, não por
  heredoc.
- Skills do projeto:
  - `/feature`: mudança ponta a ponta até o PR;
  - `/release`: revisar o Release PR e as notas;
  - `/security-audit`: auditoria periódica.
- Antes de abrir o PR, rode `/code-review` sobre o diff e corrija o que for
  real.
