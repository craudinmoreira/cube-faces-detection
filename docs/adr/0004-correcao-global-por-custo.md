# ADR 0004: corrigir cores com restrição global

## Status

Aceita.

## Contexto

A classificação LAB decide cada adesivo isoladamente. Sob iluminação difícil,
duas cores próximas, especialmente vermelho e laranja, podem ser confundidas;
o resultado pode conter mais ou menos de nove adesivos de uma cor.

## Decisão

Após capturar as seis faces, o sistema usa as distâncias LAB de cada adesivo
para atribuir exatamente oito posições não centrais a cada cor. Os seis centros
permanecem fixos. A atribuição de menor custo é aplicada apenas se for única e
o cubo resultante for fisicamente válido.

Em falhas ou empates, nenhuma captura é alterada. O programa mostra as duas
faces com maior custo de classificação como sugestão de recaptura. Em sucesso,
informa os adesivos que foram ajustados; o detalhe permanece acessível no modo
`--debug`.

## Consequências

- Erros de classificação isolada podem ser corrigidos automaticamente.
- A correção não inventa um estado: ambiguidade e impossibilidade bloqueiam o
  solver.
- Cada captura estável conserva os custos LAB medianos necessários para a
  decisão global.
