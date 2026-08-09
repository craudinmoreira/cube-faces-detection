# ADR 0002: selecionar grade por geometria espacial

## Status

Aceita.

## Contexto

O detector anterior escolhia grupos de nove quadriláteros principalmente pela
área. Objetos de fundo ou contornos duplicados podiam satisfazer esse critério
sem formar uma face do cubo.

## Decisão

O detector avaliará grupos locais de nove candidatos por alinhamento em três
linhas e três colunas, regularidade de espaçamento, consistência de área e
proximidade ao centro do grupo. Apenas a grade de maior pontuação acima de um
limiar conservador será aceita.

A primeira versão aceita apenas grades aproximadamente frontais. A correção de
perspectiva será adicionada em uma etapa posterior, depois que esta seleção
puder ser testada isoladamente.

## Consequências

- Frames incertos são rejeitados antes da classificação de cores.
- A seleção deixa de depender da ordem e da área dos contornos.
- Faces muito inclinadas podem ser rejeitadas até a etapa de homografia.
