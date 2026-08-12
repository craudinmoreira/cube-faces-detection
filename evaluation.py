"""Evaluate color preprocessing modes against sessions from --collect-data."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import cv2

from annotations import grid_matches
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


def load_annotations(path='data/annotations.json'):
    annotation_path = Path(path)
    if not annotation_path.exists():
        return []
    data = json.loads(annotation_path.read_text(encoding='utf-8'))
    records = data.get('records', {})
    if not isinstance(records, dict):
        raise ValueError('Arquivo de anotações inválido.')
    return list(records.values())


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


def evaluate_annotations(records, image_root, detector_factory=CubeDetector):
    """Measure face presence, grid location and color against manual labels."""
    results = {}
    for mode in MODES:
        detector = detector_factory(color_preprocess=mode)
        totals = defaultdict(int)
        for record in records:
            frame = cv2.imread(str(Path(image_root) / record['path']))
            if frame is None:
                continue
            _, detected_colors, _ = detector.process_frame(frame)
            predicted_centers = detector.last_grid_centers
            predicted_face = len(predicted_centers) == 9
            expected_face = record['has_face']
            totals['samples'] += 1
            if expected_face:
                totals['positive_samples'] += 1
                expected_colors = record.get('expected_colors')
                if expected_colors:
                    totals['total_stickers'] += len(expected_colors)
                if predicted_face:
                    totals['true_positive'] += 1
                    grid_correct = grid_matches(record['centers'], predicted_centers)
                    totals['grid_correct'] += int(grid_correct)
                    if expected_colors:
                        if grid_correct and detected_colors is not None:
                            totals['correct_stickers'] += sum(
                                actual == expected
                                for actual, expected in zip(detected_colors, expected_colors)
                            )
                else:
                    totals['false_negative'] += 1
            elif predicted_face:
                totals['false_positive'] += 1
        results[mode] = _manual_metrics(totals)
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


def _manual_metrics(totals):
    def rate(numerator, denominator):
        return numerator / denominator if denominator else 0.0

    return {
        'samples': totals['samples'],
        'positive_samples': totals['positive_samples'],
        'face_precision': rate(totals['true_positive'], totals['true_positive'] + totals['false_positive']),
        'face_recall': rate(totals['true_positive'], totals['positive_samples']),
        'grid_accuracy': rate(totals['grid_correct'], totals['positive_samples']),
        'color_accuracy': rate(totals['correct_stickers'], totals['total_stickers']),
    }


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


def write_report(results, output_dir='data/reports', manual_results=None):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    recommendation, reason = recommend_preprocessing(results)
    report = {
        'results': results,
        'manual_annotations': manual_results or {},
        'recommendation': recommendation,
        'reason': reason,
    }
    (output_path / 'evaluation.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    with (output_path / 'evaluation.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=['source', 'mode', 'color', 'samples', 'face_detection_rate', 'grid_detection_rate', 'face_precision', 'face_recall', 'grid_accuracy', 'color_accuracy'],
        )
        writer.writeheader()
        for mode, metrics in results.items():
            writer.writerow({'source': 'automatic', 'mode': mode, 'color': 'all', **{key: metrics[key] for key in ('samples', 'face_detection_rate', 'grid_detection_rate', 'color_accuracy')}})
            for color, values in metrics['by_color'].items():
                writer.writerow({'source': 'automatic', 'mode': mode, 'color': color, **values})
        for mode, metrics in (manual_results or {}).items():
            writer.writerow({'source': 'manual', 'mode': mode, 'color': 'all', **metrics})
    return report


def main():
    parser = argparse.ArgumentParser(description='Evaluate collected Rubik face samples')
    parser.add_argument('--data', default='data/collected', help='Directory containing collection sessions')
    parser.add_argument('--output', default='data/reports', help='Directory for CSV and JSON reports')
    parser.add_argument('--annotations', default='data/annotations.json', help='Manual annotation JSON')
    parser.add_argument('--annotated-data', default='data/to_annotate', help='Directory containing annotated images')
    args = parser.parse_args()
    manual_records = load_annotations(args.annotations)
    records = load_records(args.data)
    if not records and not manual_records:
        raise SystemExit('Nenhuma amostra encontrada. Use --collect-data ou annotation.py primeiro.')
    report = write_report(
        evaluate_records(records),
        args.output,
        evaluate_annotations(manual_records, args.annotated_data) if manual_records else None,
    )
    print(report['reason'])
    print(f"Relatórios salvos em {args.output}")


if __name__ == '__main__':
    main()
