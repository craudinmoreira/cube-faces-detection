# cube-faces-detection

Projeto experimental e de estudo. O objetivo não é entregar um resolvedor de
Cubo Mágico pronto para uso, e sim entender, passo a passo, o que acontece
entre uma imagem de câmera e uma sequência de movimentos que resolve o cubo.

Cada parte do caminho é tratada como uma pergunta a investigar:

1. **Ver o cubo:** como encontrar uma face 3×3 em um frame, mesmo em cubos
   *stickerless*, sem confundir o fundo ou a mão com peças?
2. **Ler as cores:** como classificar seis cores sob iluminações diferentes,
   onde laranja e vermelho, ou branco e amarelo, se misturam com facilidade?
3. **Montar o estado:** como juntar seis fotos de faces, cada uma em uma
   rotação desconhecida, em um único estado de 54 adesivos que exista de fato
   em um cubo físico?
4. **Resolver:** o que os algoritmos de resolução fazem com esse estado, e por
   que um método camada por camada gera dezenas de movimentos a mais que o
   algoritmo de Kociemba?

O código é o registro dessas experiências: algumas decisões estão
documentadas em [ADRs](docs/adr/), há ferramentas para coletar e anotar
imagens, e um avaliador compara abordagens com dados reais antes de adotá-las.

## O que já foi explorado

### Visão: da imagem à face

- Detecção de quadriláteros candidatos com filtros de borda e contornos.
- Seleção da grade 3×3 pela geometria: linhas, colunas, espaçamento e tamanho
  coerentes, com uma pontuação mínima para aceitar o frame
  ([ADR 0002](docs/adr/0002-selecionar-grade-por-geometria.md)).
- Retificação da face por perspectiva antes de medir a cor
  ([ADR 0003](docs/adr/0003-retificar-face-antes-de-medir-cor.md)).
- Observação estável: uma leitura só conta quando se mantém consistente por
  vários frames.

### Cor: calibração e classificação

- Classificação no espaço LAB, a partir de centros calibrados com uma face
  resolvida de cada cor.
- Perfil de calibração versionado, com variabilidade e percentis de distância
  ([ADR 0005](docs/adr/0005-perfil-versionado-de-calibracao.md)).
- Comparação de modos de pré-processamento de cor com o avaliador.

### Estado: de seis faces a um cubo válido

- Cada face é identificada pela cor do centro, seguindo um esquema fixo
  (branco=U, amarelo=D, verde=F, azul=B, vermelho=R, laranja=L).
- A orientação das faces é resolvida testando as 4⁶ combinações de rotação e
  aceitando apenas uma que produza um estado fisicamente possível
  ([ADR 0001](docs/adr/0001-resolver-orientacao-por-validacao.md)).
- Correção global por custo: se a leitura não tem nove adesivos de cada cor, o
  programa procura a correção mais barata e só a aplica quando ela é única e
  válida ([ADR 0004](docs/adr/0004-correcao-global-por-custo.md)).

### Resolução

- Método camada por camada, via biblioteca
  [rubik-cube](https://pypi.org/project/rubik-cube/).
- Algoritmo de Kociemba, via `RubikOptimal`, para comparar o tamanho das
  soluções.

O vocabulário do domínio (face capturada, recaptura, estado válido etc.) está
em [CONTEXT.md](CONTEXT.md).

## Estrutura

| Arquivo | Papel |
| --- | --- |
| `main.py` | Ponto de entrada: câmera, ciclo de captura e chamada ao solver |
| `vision.py` | Candidatos geométricos, seleção de grade, retificação e cor |
| `calibration.py` | Calibração e perfil de cores |
| `stability.py` | Critério de observação estável |
| `cube_state.py` | Estado do cubo, orientação das faces e validação |
| `solver_utils.py` | Integração com os solvers camada por camada e Kociemba |
| `ui.py` | Janela com o cubo planificado |
| `data_collection.py` | Coleta de observações para avaliação |
| `annotation.py`, `annotations.py` | Anotação manual de casos difíceis |
| `evaluation.py` | Comparação de abordagens com os dados coletados |
| `tests/` | Testes automatizados |

## Como rodar

Requer Python 3 e uma webcam.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Com a câmera:

```bash
python main.py
```

Com uma imagem estática:

```bash
python main.py --image caminho/para/foto.png
```

Para ver os candidatos geométricos, a face retificada e o motivo de cada
rejeição:

```bash
python main.py --debug
```

Para rodar os testes:

```bash
python -m pytest
```

O [guia de uso](GUIA_DE_USO.md) detalha calibração, captura, recaptura,
coleta de dados, anotação e avaliação.

## Limitações

Este é um laboratório, não um produto. A leitura depende bastante da
iluminação e da câmera, a calibração precisa ser refeita quando o ambiente
muda, e várias partes ainda estão sendo testadas e ajustadas.
