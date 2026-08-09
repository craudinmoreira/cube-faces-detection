# Contexto do domínio

## Glossário

### Face capturada

Uma matriz ordenada de 3×3 adesivos observada pela câmera e associada à face
canônica cujo centro possui aquela cor.

### Esquema canônico de cores

O projeto usa a convenção fixa: branco=`U` (topo), amarelo=`D` (baixo),
verde=`F` (frente), azul=`B` (trás), vermelho=`R` (direita) e laranja=`L`
(esquerda).

### Orientação da face

Uma das quatro rotações de 90° possíveis para a matriz de uma face capturada.
A identidade da face não determina sua orientação.

### Resolução de orientação

Processo que testa as 4⁶ combinações de rotação das seis faces capturadas e
aceita uma orientação apenas se ela produzir um único estado fisicamente válido.

### Observação estável

Uma leitura de 3×3 que se mantém consistente por pelo menos 15 frames, com ao
menos 80% de concordância por adesivo e duração mínima de 500 ms.

### Recaptura

Substituição explícita de uma face armazenada por uma nova face capturada. Uma
falha de validação nunca apaga automaticamente uma face anterior. A face
anterior é preservada até que a substituição seja confirmada.

### Recaptura pendente

Modo ativado pelas teclas `u`, `r`, `f`, `d`, `l` ou `b`, que identifica a face
a substituir. Uma legenda visível informa o mapeamento e `Esc` cancela o modo
sem alterar o estado armazenado.

### Legenda de captura

Ajuda persistente sobreposta à câmera que mostra cada tecla, a letra canônica,
a cor central e a posição da face. Durante uma recaptura, destaca a face
pendente.

### Resultado ambíguo de orientação

Situação em que nenhuma ou mais de uma combinação de rotações produz um estado
válido. O solver não pode ser chamado até que o usuário recapture uma face.

### Estado válido

Estado com nove adesivos de cada cor, seis centros coerentes e uma configuração
de cantos e arestas que pode existir em um cubo físico.
