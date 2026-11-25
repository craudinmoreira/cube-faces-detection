"""Orçamento de performance do pipeline de visão.

Gera um conjunto fixo de frames sintéticos (semente fixa, sem câmera), roda
`CubeDetector.process_frame` em cada um e falha se a mediana ou o p95 do tempo
por frame passarem do orçamento, ou se alguma face ou cor deixar de ser
reconhecida.

    uv run python scripts/bench_pipeline.py            # verifica o orçamento
    uv run python scripts/bench_pipeline.py --json     # só imprime as métricas

A mediana tem de caber num frame a 30 fps (33 ms). A medida local fica em
torno de 12 ms, e a folga cobre runners de CI mais lentos e ruidosos. O
orçamento existe para pegar regressões grandes, como um laço O(n²) novo ou um
filtro caro por frame, e não variações de 10%.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vision import CubeDetector  # noqa: E402

BUDGET_MEDIAN_MS = 33.0
BUDGET_P95_MS = 50.0
FRAMES = 20
REPEATS = 5
WARMUP = 3

# BGR saturados, próximos dos centros padrão do ColorDetector.
STICKERS = {
    'W': (255, 255, 255),
    'Y': (0, 255, 255),
    'G': (0, 255, 0),
    'B': (255, 0, 0),
    'O': (0, 165, 255),
    'R': (0, 0, 255),
}


def synthetic_frame(seed, width=640, height=480):
    """Uma face 3x3 sobre fundo com ruído, em posição e tamanho variáveis."""
    rng = np.random.default_rng(seed)
    frame = np.full((height, width, 3), 150, np.uint8)
    frame = cv2.add(frame, rng.integers(0, 25, frame.shape, dtype=np.uint8))
    step = int(rng.integers(60, 85))
    sticker = int(step * 0.82)
    x0 = int(rng.integers(20, width - 3 * step - 20))
    y0 = int(rng.integers(20, height - 3 * step - 20))
    cv2.rectangle(frame, (x0 - 8, y0 - 8), (x0 + 3 * step, y0 + 3 * step), (25, 25, 25), -1)
    colors = list(STICKERS)
    expected = []
    for row in range(3):
        for column in range(3):
            name = colors[int(rng.integers(len(colors)))]
            expected.append(name)
            x, y = x0 + column * step, y0 + row * step
            cv2.rectangle(frame, (x, y), (x + sticker, y + sticker), STICKERS[name], -1)
    return frame, expected


def measure():
    detector = CubeDetector()
    frames = [synthetic_frame(seed) for seed in range(FRAMES)]
    for frame, _ in frames[:WARMUP]:
        detector.process_frame(frame.copy())

    timings = []
    for _ in range(REPEATS):
        detected = correct = 0
        for frame, expected in frames:
            start = time.perf_counter()
            _, colors, _ = detector.process_frame(frame.copy())
            timings.append((time.perf_counter() - start) * 1000)
            detected += colors is not None
            correct += sum(a == b for a, b in zip(colors or [], expected))
    timings.sort()
    return {
        'frames': FRAMES,
        'samples': len(timings),
        'detected': detected,
        'correct_stickers': correct,
        'median_ms': round(statistics.median(timings), 2),
        'p95_ms': round(timings[int(len(timings) * 0.95) - 1], 2),
        'budget_median_ms': BUDGET_MEDIAN_MS,
        'budget_p95_ms': BUDGET_P95_MS,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true', help='só imprime as métricas, sem verificar')
    args = parser.parse_args()
    result = measure()
    print(json.dumps(result, indent=2))
    if args.json:
        return 0

    failures = []
    if result['detected'] < FRAMES:
        failures.append(f"face detectada em {result['detected']}/{FRAMES} frames")
    if result['correct_stickers'] < FRAMES * 9:
        failures.append(f"cores corretas: {result['correct_stickers']}/{FRAMES * 9}")
    if result['median_ms'] > BUDGET_MEDIAN_MS:
        failures.append(f"mediana {result['median_ms']} ms > {BUDGET_MEDIAN_MS} ms")
    if result['p95_ms'] > BUDGET_P95_MS:
        failures.append(f"p95 {result['p95_ms']} ms > {BUDGET_P95_MS} ms")
    for failure in failures:
        print(f'✖ {failure}', file=sys.stderr)
    if not failures:
        print('✔ dentro do orçamento')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
