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
