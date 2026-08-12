"""Persistent ground-truth annotations and relative 3x3 grid comparison."""

import json
from math import dist
from pathlib import Path

import numpy as np


ALLOWED_COLORS = frozenset(('W', 'Y', 'G', 'B', 'R', 'O'))
IMAGE_SUFFIXES = frozenset(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))


class AnnotationStore:
    """Read and write resumable annotations keyed by input-relative path."""

    def __init__(self, path='data/annotations.json'):
        self.path = Path(path)
        self.records = self._load_records()

    def pending_images(self, input_dir):
        root = Path(input_dir)
        if not root.exists():
            return []
        return [
            image.relative_to(root).as_posix()
            for image in sorted(root.rglob('*'))
            if image.is_file()
            and image.suffix.lower() in IMAGE_SUFFIXES
            and image.relative_to(root).as_posix() not in self.records
        ]

    def save(self, relative_path, has_face, centers=None, expected_colors=None):
        normalized_path = _validate_relative_path(relative_path)
        record = {'path': normalized_path, 'has_face': bool(has_face)}
        if has_face:
            if centers is None or expected_colors is None or len(centers) != 9 or len(expected_colors) != 9:
                raise ValueError('Anotações positivas exigem nove centros e nove cores.')
            if any(color not in ALLOWED_COLORS for color in expected_colors):
                raise ValueError('Anotação positiva contém cor inválida.')
            record['centers'] = [[int(x), int(y)] for x, y in centers]
            record['expected_colors'] = list(expected_colors)
        self.records[record['path']] = record
        self._write()

    def _load_records(self):
        if not self.path.exists():
            return {}
        with self.path.open(encoding='utf-8') as file:
            data = json.load(file)
        if not isinstance(data, dict) or not isinstance(data.get('records', {}), dict):
            raise ValueError('Arquivo de anotações inválido.')
        for path, record in data['records'].items():
            if _validate_relative_path(path) != record.get('path'):
                raise ValueError('Arquivo de anotações contém caminho relativo inválido.')
        return data['records']

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as file:
            json.dump({'schema_version': 1, 'records': self.records}, file, indent=2, ensure_ascii=False)


def grid_matches(annotated_centers, predicted_centers, tolerance_ratio=0.4):
    """Compare row-major grids using a tolerance relative to sticker spacing."""
    if len(annotated_centers) != 9 or len(predicted_centers) != 9:
        return False
    spacing = _median_grid_spacing(annotated_centers)
    if spacing <= 0:
        return False
    return all(
        dist(expected, actual) <= spacing * tolerance_ratio
        for expected, actual in zip(annotated_centers, predicted_centers)
    )


def _median_grid_spacing(centers):
    neighbor_distances = []
    for row in range(3):
        for column in range(2):
            index = row * 3 + column
            neighbor_distances.append(dist(centers[index], centers[index + 1]))
    for row in range(2):
        for column in range(3):
            index = row * 3 + column
            neighbor_distances.append(dist(centers[index], centers[index + 3]))
    return float(np.median(neighbor_distances))


def _validate_relative_path(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('A anotação exige um caminho relativo à pasta de entrada.')
    return path.as_posix()
