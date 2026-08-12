# Desenho: anotação manual de casos de visão

## Objetivo

Complementar a coleta automática de faces resolvidas com uma base pequena de
imagens difíceis e negativas. Essa base permitirá medir presença de face e
correção da grade 3×3 sem depender da previsão do próprio algoritmo.

## Escopo

`annotation.py` processará imagens colocadas em `data/to_annotate/`. A
ferramenta salvará anotações retomáveis em `data/annotations.json`. Imagens e
anotações não serão incluídas no Git.

## Fluxo de anotação

1. A ferramenta mostra a imagem e a sobreposição da grade prevista pelo
   detector, quando existir.
2. `n` registra uma imagem negativa: não há face de cubo visível.
3. `y` inicia uma anotação positiva. O usuário clica os nove centros em ordem
   de leitura (três linhas, da esquerda para a direita) e informa nove cores
   pelas teclas `w`, `y`, `g`, `b`, `r` e `o`.
4. `r` reinicia a anotação da imagem atual; `q` interrompe sem perder os
   registros de imagens anteriores.
5. Uma imagem já registrada é ignorada em execuções futuras.

## Modelo de dados

Cada registro contém um caminho relativo à pasta de entrada, `has_face`, e,
para positivos, `centers` e `expected_colors`. O caminho relativo permite mover
o projeto inteiro sem quebrar o manifesto.

## Avaliação

O avaliador combina duas fontes:

- sessões automáticas de faces resolvidas: acerto de cor em escala;
- anotações manuais: presença de face, correção de grade e, quando presente,
  acerto de cor.

Uma grade prevista é correta quando tem nove centros e cada centro, na ordem de
leitura, fica dentro de 40% do espaçamento mediano da grade anotada. Imagens
negativas alimentam falsos positivos; positivas sem grade prevista alimentam
falsos negativos.

## Limites

Esta etapa não troca o pré-processamento padrão nem treina um modelo. Ela cria
referências independentes e métricas reproduzíveis para embasar mudanças
posteriores.

## Testes

Os testes cobrirão a persistência e retomada da fila, registros positivos e
negativos, a tolerância geométrica relativa e as métricas de presença/grade.
