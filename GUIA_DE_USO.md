# Guia de uso

## 1. Instalação

No diretório do projeto, crie o ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Iniciar a câmera

```powershell
python main.py
```

Escolha a calibração no menu. Para uma calibração nova, mostre uma face
**resolvida** de cada cor; mantenha-a estável por cerca de um segundo. O
programa guarda o centro LAB e medidas de variabilidade em `calibration.json`.

## 3. Capturar um cubo para resolver

Mostre uma face por vez. A captura é automática após 15 frames consistentes,
em pelo menos 0,5 segundo. O centro identifica a face canônica:

| Cor do centro | Face | Posição |
| --- | --- | --- |
| Branco | `U` | topo |
| Amarelo | `D` | baixo |
| Verde | `F` | frente |
| Azul | `B` | trás |
| Vermelho | `R` | direita |
| Laranja | `L` | esquerda |

Depois das seis faces, o programa verifica contagens, corrige pequenas
ambiguidades de cor apenas quando houver uma solução única e válida, resolve a
orientação das faces e chama o solver. Se algo falhar, ele preserva as capturas
e indica o que recapturar.

## 4. Recapturar uma face

Use `u`, `r`, `f`, `d`, `l` ou `b` para escolher a face. A captura antiga só é
substituída quando a nova ficar estável. `Esc` cancela a recaptura pendente.

## 5. Diagnóstico

```powershell
python main.py --debug
```

O modo mostra a quantidade de quadriláteros candidatos, pontuação da grade,
motivos de rejeição e janelas com candidatos e face retificada. Também detalha
quais adesivos foram ajustados por uma correção global.

## 6. Coletar imagens para avaliação

Use um cubo resolvido e execute:

```powershell
python main.py --collect-data
```

O modo grava automaticamente somente faces estáveis cujas nove leituras são
iguais ao centro. Cada sessão é criada em `data/collected/<data-hora>/` e
contém o frame original, a face retificada e `manifest.json` com rótulo,
previsão e metadados.

Cada cor aceita até 10 exemplos por sessão. Faces quase idênticas são ignoradas;
por isso, altere iluminação, distância e inclinação entre amostras. Fora de
`--collect-data`, o programa não grava imagens.

## 7. Comparar técnicas de pré-processamento

Depois de coletar sessões, execute:

```powershell
python evaluation.py
```

O comando compara pixels originais, balanço de branco *gray-world* e o realce
HSV atual. Ele grava `data/reports/evaluation.csv` e `evaluation.json`, com
métricas de candidatos de face, grade 3×3 e cores por técnica e por cor.

O relatório só recomenda outra técnica quando houver pelo menos 30 exemplos de
cada cor, ganho mínimo de cinco pontos percentuais em cores e nenhuma piora de
detecção ou grade. A recomendação não altera o programa: uma troca futura será
revisada e versionada em commit próprio.

## 8. Anotar imagens difíceis manualmente

Copie imagens inclinadas, com reflexos, com fundos quadrados ou sem cubo para
`data/to_annotate/`. Depois execute:

```powershell
python annotation.py
```

A previsão da grade aparece em amarelo apenas como referência. Para cada
imagem, pressione `n` se não houver uma face de cubo. Se houver, pressione `y`,
clique os nove centros em ordem de leitura (esquerda para direita, de cima para
baixo) e informe as nove cores com `w`, `y`, `g`, `b`, `r` e `o`.

`r` reinicia somente a imagem atual; `q` encerra e mantém o progresso. As
anotações ficam em `data/annotations.json`, e imagens já anotadas são ignoradas
na próxima execução.

Para incluir essas métricas no relatório, execute novamente:

```powershell
python evaluation.py
```

O JSON passa a mostrar precisão e recall de presença de face, acerto de grade e
acerto de cor das anotações manuais. Esses números complementam, mas não
substituem, a comparação automática das faces resolvidas.
