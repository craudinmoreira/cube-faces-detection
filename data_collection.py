from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

import cv2
import numpy as np


class DataCollectionSession:
    """Persist a small, deduplicated set of labeled solved-face observations."""

    MAX_SAMPLES_PER_COLOR = 10
    DUPLICATE_DIFFERENCE_THRESHOLD = 6.0

    def __init__(self, root='data/collected', max_samples_per_color=None):
        self.created_at = datetime.now(timezone.utc)
        self.directory = Path(root) / self.created_at.strftime('%Y%m%dT%H%M%SZ')
        self.directory.mkdir(parents=True, exist_ok=False)
        self.max_samples_per_color = (
            self.MAX_SAMPLES_PER_COLOR
            if max_samples_per_color is None
            else max_samples_per_color
        )
        self._samples_by_color = Counter()
        self._fingerprints = {}
        self._records = []
        self._write_manifest()

    def observe(self, face_name, colors, frame, rectified_face, metadata=None):
        """Save a labeled solved face, or return why it was not saved."""
        center = colors[4] if colors and len(colors) == 9 else None
        if center is None or any(color != center for color in colors):
            return False, 'A face não parece resolvida; amostra ignorada.'
        if self._samples_by_color[center] >= self.max_samples_per_color:
            return False, f'Cota da cor {center} atingida.'
        if frame is None or rectified_face is None:
            return False, 'Imagem incompleta; amostra ignorada.'

        fingerprint = self._fingerprint(rectified_face)
        if self._is_duplicate(center, fingerprint):
            return False, 'Amostra quase idêntica; ignorada.'

        sequence = self._samples_by_color[center] + 1
        prefix = f'{center}_{sequence:02d}'
        frame_path = self.directory / f'{prefix}_frame.png'
        rectified_path = self.directory / f'{prefix}_rectified.png'
        if not cv2.imwrite(str(frame_path), frame) or not cv2.imwrite(str(rectified_path), rectified_face):
            return False, 'Não foi possível gravar a amostra.'

        self._samples_by_color[center] += 1
        self._fingerprints.setdefault(center, []).append(fingerprint)
        self._records.append(
            {
                'color': center,
                'face': face_name,
                'expected_colors': [center] * 9,
                'observed_colors': list(colors),
                'frame': frame_path.name,
                'rectified_face': rectified_path.name,
                'captured_at': datetime.now(timezone.utc).isoformat(),
                'metadata': metadata or {},
            }
        )
        self._write_manifest()
        return True, f'Amostra {center} salva ({self._samples_by_color[center]}/{self.max_samples_per_color}).'

    def progress(self):
        return dict(self._samples_by_color)

    def _fingerprint(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.resize(gray, (16, 16), interpolation=cv2.INTER_AREA).astype(float)

    def _is_duplicate(self, color, fingerprint):
        return any(
            float(np.mean(np.abs(fingerprint - previous)))
            < self.DUPLICATE_DIFFERENCE_THRESHOLD
            for previous in self._fingerprints.get(color, [])
        )

    def _write_manifest(self):
        manifest = {
            'schema_version': 1,
            'created_at': self.created_at.isoformat(),
            'max_samples_per_color': self.max_samples_per_color,
            'samples_by_color': dict(self._samples_by_color),
            'records': self._records,
        }
        with (self.directory / 'manifest.json').open('w', encoding='utf-8') as file:
            json.dump(manifest, file, indent=2, ensure_ascii=False)
