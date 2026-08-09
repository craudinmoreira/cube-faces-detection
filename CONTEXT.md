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

### Candidato geométrico

Quadrilátero detectado no frame que pode representar uma peça, mas ainda não
foi aceito como parte de uma face do cubo.

### Grade candidata

Conjunto ordenado de nove candidatos geométricos que pode representar uma face
3×3.

### Pontuação de grade

Medida de coerência espacial de uma grade candidata. Ela considera a formação
de três linhas e três colunas, espaçamento e tamanho consistentes. Somente a
melhor grade acima do limiar é aceita.

### Frame geométrico rejeitado

Frame no qual nenhum conjunto de candidatos forma uma grade com confiança
suficiente. Nenhuma cor é classificada nesse frame.

### Grade frontal

Grade candidata observada com linhas e colunas aproximadamente paralelas aos
eixos da imagem. A primeira etapa geométrica aceita apenas grades frontais;
perspectiva forte é tratada posteriormente por retificação.

### Supressão de sobreposição

Processo que mantém um único candidato geométrico quando múltiplos contornos
se sobrepõem à mesma peça. A decisão usa a razão entre a interseção e a união
das caixas delimitadoras, não uma distância fixa em pixels.

### Homografia da face

Transformação que usa os centros das nove peças de uma grade candidata para
converter a face observada em uma visão quadrada e frontal.

### Face retificada

Imagem canônica produzida pela homografia. As cores são medidas em nove regiões
internas, fixas e de mesmo tamanho nessa imagem, não nos retângulos originais.

### Frame de retificação rejeitado

Frame cuja homografia é geometricamente inconsistente. Ele não usa as regiões
originais como alternativa e aguarda uma nova observação.

### Decisão de cor

Resultado da comparação entre a cor observada de uma ROI e os seis centros de
cor calibrados. Uma decisão aceita exige proximidade suficiente e separação
suficiente da segunda cor mais próxima.

### Cor ambígua

Cor cuja melhor e segunda melhor referência estão muito próximas. Ela é
representada por `U` e impede a captura estável da face.

### Amostra de calibração

Conjunto das nove medianas LAB observadas em uma face resolvida durante a
calibração.

### Centro de cor calibrado

Mediana robusta de pelo menos 30 amostras de calibração obtidas ao longo de no
mínimo um segundo para uma cor do cubo.
