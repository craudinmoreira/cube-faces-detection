# Rubik's Cube OpenCV Solver 🧩🤖

Um projeto em Python que utiliza **Visão Computacional (OpenCV)** para detectar em tempo real o estado de um Cubo Mágico (Rubik's Cube) 3x3x3 através de uma webcam, e calcula os passos necessários para solucioná-lo.

O sistema é capaz de identificar as 6 faces do cubo automaticamente e gera a sequência de movimentos utilizando o algoritmo *Layer-by-Layer* (Camada por Camada).

![Screenshot de Exemplo](example.png) *(Coloque uma imagem do sistema em funcionamento aqui)*

## 🚀 Funcionalidades

*   **Detecção Automática:** Identifica os quadrados do cubo mesmo em cubos *stickerless* (sem bordas pretas), analisando vincos e contrastes de cor diretamente na imagem colorida.
*   **Mapeamento de Cores HSV:** Converte os pixels lidos pela câmera para a notação lógica de cores (Vermelho, Laranja, Amarelo, Verde, Azul, Branco) e permite ajustes finos.
*   **Interface 2D em Tempo Real:** Uma janela secundária desenha o "mapa" plano (planificado) do cubo conforme as faces vão sendo escaneadas.
*   **Solução Integrada:** Assim que o estado das 6 faces é capturado de forma estável, o algoritmo gera a notação padrão (U, D, R, L, F, B) necessária para montar o cubo.

## 📂 Arquitetura do Projeto

O código foi construído de forma modular para fácil manutenção e expansão:

*   `main.py`: O ponto de entrada. Orquestra a captura da câmera, gerencia o estado (loop de escaneamento) e chama o solver.
*   `vision.py`: O "cérebro" visual. Processa os frames, aplica os filtros (Blur e Canny), encontra os contornos (quadrados) e detecta a cor com base em limites HSV pré-definidos.
*   `cube_state.py`: Mantém o registro lógico do cubo na memória. Sabe interpretar qual face está sendo escaneada verificando a cor central (ex: Centro Branco = Face Up/Topo).
*   `ui.py`: Cuida da janela "Cube Faces", renderizando as peças detectadas em um layout de malha planificada.
*   `solver_utils.py`: O wrapper que se comunica com o pacote externo `rubik-cube` para calcular a solução.

## 🛠️ Como Instalar e Rodar

### Pré-requisitos
*   Python 3.7+ instalado no sistema.
*   Webcam.

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/cube-py.git
   cd cube-py
   ```

2. Crie e ative um ambiente virtual:
   * **Windows:**
     ```bash
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
   * **Linux/Mac:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Executando

Para utilizar com a **webcam** (modo principal):
```bash
python main.py
```
**Dica de uso:** Aponte o cubo para a câmera. Mantenha a face estável por cerca de 1 segundo para que o sistema registre a leitura com segurança. Gire o cubo e mostre as próximas faces. Quando todas as 6 forem detectadas, a solução aparecerá na tela de vídeo.

Para processar uma **imagem estática**:
```bash
python main.py --image caminho_para_sua_foto.png
```

## ⚙️ Calibração de Cores

A iluminação do ambiente (lâmpadas brancas, amarelas, luz natural) afeta drasticamente a leitura das cores pela câmera. Se o sistema estiver confundindo Laranja com Vermelho, ou Branco com Amarelo, você precisará calibrar os limiares.

Para ajustar, abra o arquivo `vision.py` e localize o dicionário `self.color_ranges` dentro da classe `ColorDetector`. Altere os limites inferiores e superiores (Hue, Saturation, Value) até que o sistema fique estável no seu ambiente.

---
Desenvolvido com Python, OpenCV e a biblioteca [rubik-cube](https://pypi.org/project/rubik-cube/).