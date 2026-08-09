# ADR 0001: resolver orientação por validação do estado

## Status

Aceita.

## Contexto

O centro identifica a face canônica, mas não informa a rotação da matriz 3×3
observada. Capturas feitas com o cubo em orientações diferentes podem preservar
as contagens de cores e ainda descrever um estado incorreto.

## Decisão

Após capturar seis faces, o sistema testará as quatro rotações possíveis de
cada face (`4⁶ = 4096` combinações). A combinação será aceita somente se houver
exatamente um estado fisicamente válido segundo a validação de cubies.

Se não houver nenhuma combinação válida ou houver mais de uma, o solver será
bloqueado e o usuário deverá recapturar uma face.

## Consequências

- Elimina a exigência de o usuário manter uma orientação física rígida.
- Mantém a decisão baseada em regras do domínio, sem modelo visual adicional.
- Exige uma interface clara de recaptura para resolver estados ausentes ou
  ambíguos. A face anterior é preservada até a nova captura estável confirmá-la.
- A busca é pequena o suficiente para execução local síncrona.
