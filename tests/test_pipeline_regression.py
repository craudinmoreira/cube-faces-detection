"""Regressão funcional do pipeline com frames sintéticos fixos.

O tempo por frame é verificado à parte, em scripts/bench_pipeline.py, porque
medir tempo dentro da suíte de testes deixa os testes instáveis.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

from bench_pipeline import FRAMES, synthetic_frame  # noqa: E402
from vision import CubeDetector  # noqa: E402


@pytest.mark.parametrize('seed', range(FRAMES))
def test_detects_face_and_colors_in_synthetic_frame(seed):
    frame, expected = synthetic_frame(seed)

    _, colors, rois = CubeDetector().process_frame(frame)

    assert colors == expected
    assert len(rois) == 9
