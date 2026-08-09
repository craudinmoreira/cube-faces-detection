# ADR 0003: retificar a face antes de medir cores

## Status

Aceita.

## Contexto

Regiões de cor extraídas dos retângulos originais variam com perspectiva,
tamanho e inclinação. Bordas e fundo podem contaminar a medição.

## Decisão

Os nove centros da grade aceita são mapeados para uma imagem canônica de
300×300 pixels por homografia. A cor é medida no quadrado central de 50×50
pixels de cada uma das nove células de 100×100.

Uma homografia deve explicar os nove centros dentro do erro máximo configurado.
Se não explicar, o frame é rejeitado; o sistema não volta às ROIs originais.

## Consequências

- A classificação recebe ROIs de mesma escala e posição previsível.
- O frame pode ser rejeitado quando a geometria estiver inconsistente.
- A calibração e a inferência usam a mesma representação retificada.
