import csv
from collections import defaultdict
import json
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

import evaluation
from annotation import AnnotationController, _draw_annotation


class FakeDetector:
    """Devolve sempre a mesma leitura, sem depender de visão computacional."""

    def __init__(self, colors, color_preprocess=None):
        self.colors = colors
        self.debug_state = {}
        self.last_grid_centers = []

    def process_frame(self, frame):
        self.debug_state = {'candidate_count': 9 if self.colors else 0}
        self.last_grid_centers = [(10 + 20 * c, 10 + 20 * r) for r in range(3) for c in range(3)] if self.colors else []
        return frame, self.colors, None


def write_session(root, name, records):
    session = root / name
    session.mkdir()
    for record in records:
        cv2.imwrite(str(session / record['frame']), np.zeros((8, 8, 3), np.uint8))
    (session / 'manifest.json').write_text(json.dumps({'records': records}), encoding='utf-8')
    return session


def test_load_records_reads_every_session_manifest(tmp_path):
    write_session(tmp_path, 's1', [{'frame': 'a.png', 'color': 'W', 'expected_colors': ['W'] * 9}])
    write_session(tmp_path, 's2', [{'frame': 'b.png', 'color': 'R', 'expected_colors': ['R'] * 9}])

    records = evaluation.load_records(tmp_path)

    assert [r['frame'] for r in records] == ['a.png', 'b.png']
    assert records[0]['_directory'] == tmp_path / 's1'


def test_load_annotations_handles_missing_valid_and_invalid_files(tmp_path):
    path = tmp_path / 'annotations.json'
    assert evaluation.load_annotations(path) == []

    path.write_text(json.dumps({'records': {'a.png': {'path': 'a.png', 'has_face': False}}}), encoding='utf-8')
    assert evaluation.load_annotations(path) == [{'path': 'a.png', 'has_face': False}]

    path.write_text(json.dumps({'records': []}), encoding='utf-8')
    with pytest.raises(ValueError):
        evaluation.load_annotations(path)


def test_evaluate_records_scores_colors_and_skips_unreadable_frames(tmp_path):
    session = write_session(tmp_path, 's1', [{'frame': 'a.png', 'color': 'W', 'expected_colors': ['W'] * 9}])
    records = evaluation.load_records(tmp_path)
    records.append({'frame': 'missing.png', 'color': 'W', 'expected_colors': ['W'] * 9, '_directory': session})
    detected = ['W'] * 8 + ['Y']

    results = evaluation.evaluate_records(records, lambda **kw: FakeDetector(detected, **kw))

    metrics = results['hsv_enhanced']
    assert metrics['samples'] == 1
    assert metrics['grid_detection_rate'] == 1.0
    assert metrics['color_accuracy'] == pytest.approx(8 / 9)
    assert metrics['by_color']['W']['color_accuracy'] == pytest.approx(8 / 9)


def test_evaluate_annotations_counts_false_positives_and_negatives(tmp_path):
    cv2.imwrite(str(tmp_path / 'neg.png'), np.zeros((8, 8, 3), np.uint8))
    records = [{'path': 'neg.png', 'has_face': False}]

    with_face = evaluation.evaluate_annotations(records, tmp_path, lambda **kw: FakeDetector(['W'] * 9, **kw))
    without_face = evaluation.evaluate_annotations(
        [{'path': 'neg.png', 'has_face': True, 'centers': []}], tmp_path, lambda **kw: FakeDetector(None, **kw)
    )

    assert with_face['hsv_enhanced']['face_precision'] == 0.0
    assert without_face['hsv_enhanced']['face_recall'] == 0.0


def test_write_report_saves_json_and_csv(tmp_path):
    results = {'hsv_enhanced': evaluation._metrics(defaultdict(int, samples=1), {})}
    manual = {'hsv_enhanced': evaluation._manual_metrics(defaultdict(int, samples=2))}

    report = evaluation.write_report(results, tmp_path / 'out', manual)

    saved = json.loads((tmp_path / 'out' / 'evaluation.json').read_text(encoding='utf-8'))
    assert saved['reason'] == report['reason']
    rows = list(csv.DictReader((tmp_path / 'out' / 'evaluation.csv').open(encoding='utf-8')))
    assert [row['source'] for row in rows] == ['automatic', 'manual']


def test_main_without_samples_exits_with_message(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.argv', ['evaluation.py', '--data', str(tmp_path), '--annotations', str(tmp_path / 'none.json')])

    with pytest.raises(SystemExit, match='Nenhuma amostra'):
        evaluation.main()


def test_annotation_overlay_marks_predictions_and_clicks():
    controller = AnnotationController('a.png', SimpleNamespace(save=lambda *a, **k: None))
    controller.start_positive()
    controller.add_center((30, 40))
    frame = np.zeros((100, 300, 3), np.uint8)

    view = _draw_annotation(frame, controller, [(70, 80)], 1, 3)

    assert view is not frame and not np.array_equal(view, frame)
    assert tuple(view[40, 30]) == (0, 255, 0)
    assert controller.stage == 'Clique centros: 1/9.'
