"""Evaluate color preprocessing modes against sessions from --collect-data."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import cv2

from vision import CubeDetector


MODES = CubeDetector.COLOR_PREPROCESSING_MODES
MIN_SAMPLES_PER_COLOR = 30
MIN_ACCURACY_GAIN = 0.05


def load_records(data_root):
    records = []
    for manifest_path in sorted(Path(data_root).glob('*/manifest.json')):
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for record in manifest.get('records', []):
            record = dict(record)
            record['_directory'] = manifest_path.parent
            records.append(record)
    return records


def evaluate_records(records, detector_factory=CubeDetector):
    """Return aggregate detection, grid and per-sticker color metrics per mode."""
    results = {}
    for mode in MODES:
        detector = detector_factory(color_preprocess=mode)
        totals = defaultdict(int)
        by_color = defaultdict(lambda: defaultdict(int))
        for record in records:
            expected = record['expected_colors']
            color = record['color']
            frame = cv2.imread(str(record['_directory'] / record['frame']))
            if frame is None:
                continue
            _, detected_colors, _ = detector.process_frame(frame)
            candidate_found = detector.debug_state.get('candidate_count', 0) >= 9
            totals['samples'] += 1
            totals['face_detected'] += int(candidate_found)
            by_color[color]['samples'] += 1
            by_color[color]['face_detected'] += int(candidate_found)
            grid_found = detected_colors is not None and len(detected_colors) == 9
            totals['grid_detected'] += int(grid_found)
            by_color[color]['grid_detected'] += int(grid_found)
            totals['total_stickers'] += len(expected)
            by_color[color]['total_stickers'] += len(expected)
            if grid_found:
                correct = sum(actual == wanted for actual, wanted in zip(detected_colors, expected))
                totals['correct_stickers'] += correct
                by_color[color]['correct_stickers'] += correct

        results[mode] = _metrics(totals, by_color)
    return results


def _metrics(totals, by_color):
    def rate(numerator, denominator):
        return numerator / denominator if denominator else 0.0

    summary = {
        'samples': totals['samples'],
        'face_detection_rate': rate(totals['face_detected'], totals['samples']),
        'grid_detection_rate': rate(totals['grid_detected'], totals['samples']),
        'color_accuracy': rate(totals['correct_stickers'], totals['total_stickers']),
        'by_color': {},
    }
    for color, values in sorted(by_color.items()):
        summary['by_color'][color] = {
            'samples': values['samples'],
            'face_detection_rate': rate(values['face_detected'], values['samples']),
            'grid_detection_rate': rate(values['grid_detected'], values['samples']),
            'color_accuracy': rate(values['correct_stickers'], values['total_stickers']),
        }
    return summary


def recommend_preprocessing(results):
    """Recommend a mode only when the approved evidence threshold is met."""
    baseline = results['hsv_enhanced']
    colors = ('W', 'Y', 'G', 'B', 'R', 'O')
    if any(baseline['by_color'].get(color, {}).get('samples', 0) < MIN_SAMPLES_PER_COLOR for color in colors):
        return None, 'Dados insuficientes: são necessárias 30 amostras por cor.'
    candidates = []
    for mode, metrics in results.items():
        if mode == 'hsv_enhanced':
            continue
        if (
            metrics['color_accuracy'] >= baseline['color_accuracy'] + MIN_ACCURACY_GAIN
            and metrics['face_detection_rate'] >= baseline['face_detection_rate']
            and metrics['grid_detection_rate'] >= baseline['grid_detection_rate']
        ):
            candidates.append((metrics['color_accuracy'], mode))
    if not candidates:
        return None, 'Nenhuma técnica supera o realce atual pelos critérios aprovados.'
    return max(candidates)[1], 'Recomendação baseada em métricas; a troca do padrão requer commit explícito.'


def write_report(results, output_dir='data/reports'):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    recommendation, reason = recommend_preprocessing(results)
    report = {'results': results, 'recommendation': recommendation, 'reason': reason}
    (output_path / 'evaluation.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    with (output_path / 'evaluation.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=['mode', 'color', 'samples', 'face_detection_rate', 'grid_detection_rate', 'color_accuracy'],
        )
        writer.writeheader()
        for mode, metrics in results.items():
            writer.writerow({'mode': mode, 'color': 'all', **{key: metrics[key] for key in writer.fieldnames[2:]}})
            for color, values in metrics['by_color'].items():
                writer.writerow({'mode': mode, 'color': color, **values})
    return report


def main():
    parser = argparse.ArgumentParser(description='Evaluate collected Rubik face samples')
    parser.add_argument('--data', default='data/collected', help='Directory containing collection sessions')
    parser.add_argument('--output', default='data/reports', help='Directory for CSV and JSON reports')
    args = parser.parse_args()
    records = load_records(args.data)
    if not records:
        raise SystemExit('Nenhuma amostra encontrada. Use python main.py --collect-data primeiro.')
    report = write_report(evaluate_records(records), args.output)
    print(report['reason'])
    print(f"Relatórios salvos em {args.output}")


if __name__ == '__main__':
    main()
