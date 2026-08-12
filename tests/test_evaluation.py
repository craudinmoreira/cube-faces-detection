import unittest
import tempfile
from pathlib import Path

import numpy as np
import cv2

from evaluation import evaluate_annotations, recommend_preprocessing
from vision import CubeDetector


def metrics(samples=30, accuracy=0.8, face_rate=1.0, grid_rate=1.0):
    return {
        'samples': samples * 6,
        'face_detection_rate': face_rate,
        'grid_detection_rate': grid_rate,
        'color_accuracy': accuracy,
        'by_color': {
            color: {
                'samples': samples,
                'face_detection_rate': face_rate,
                'grid_detection_rate': grid_rate,
                'color_accuracy': accuracy,
            }
            for color in ('W', 'Y', 'G', 'B', 'R', 'O')
        },
    }


class EvaluationRecommendationTests(unittest.TestCase):
    def test_requires_thirty_samples_per_color(self):
        results = {mode: metrics(samples=29) for mode in CubeDetector.COLOR_PREPROCESSING_MODES}

        recommendation, reason = recommend_preprocessing(results)

        self.assertIsNone(recommendation)
        self.assertIn('30 amostras', reason)

    def test_recommends_a_meaningfully_better_mode_without_regression(self):
        results = {
            'hsv_enhanced': metrics(accuracy=0.80),
            'original': metrics(accuracy=0.86),
            'gray_world': metrics(accuracy=0.82),
        }

        recommendation, _ = recommend_preprocessing(results)

        self.assertEqual('original', recommendation)

    def test_rejects_a_mode_that_harms_grid_detection(self):
        results = {
            'hsv_enhanced': metrics(accuracy=0.80),
            'original': metrics(accuracy=0.90, grid_rate=0.90),
            'gray_world': metrics(accuracy=0.81),
        }

        recommendation, _ = recommend_preprocessing(results)

        self.assertIsNone(recommendation)


class ColorPreprocessingTests(unittest.TestCase):
    def test_original_preprocessing_preserves_pixels(self):
        frame = np.array([[[20, 60, 120]]], dtype=np.uint8)

        processed = CubeDetector(color_preprocess='original')._preprocess_color_frame(frame)

        np.testing.assert_array_equal(frame, processed)

    def test_gray_world_brings_channel_means_closer(self):
        frame = np.full((10, 10, 3), (20, 60, 120), dtype=np.uint8)

        processed = CubeDetector(color_preprocess='gray_world')._preprocess_color_frame(frame)

        self.assertLess(np.ptp(processed.mean(axis=(0, 1))), np.ptp(frame.mean(axis=(0, 1))))


class ManualAnnotationEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        cv2.imwrite(str(self.root / 'negative.png'), np.zeros((20, 20, 3), dtype=np.uint8))
        cv2.imwrite(str(self.root / 'positive.png'), np.zeros((20, 20, 3), dtype=np.uint8))
        self.centers = [
            [column * 10, row * 10]
            for row in range(3)
            for column in range(3)
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_negative_image_with_predicted_grid_is_a_false_positive(self):
        records = [{'path': 'negative.png', 'has_face': False}]

        metrics = evaluate_annotations(records, self.root, detector_factory=AlwaysGridDetector)

        self.assertEqual(0.0, metrics['hsv_enhanced']['face_precision'])
        self.assertEqual(0.0, metrics['hsv_enhanced']['face_recall'])

    def test_positive_image_scores_a_grid_by_relative_tolerance(self):
        records = [{
            'path': 'positive.png',
            'has_face': True,
            'centers': self.centers,
            'expected_colors': ['W'] * 9,
        }]

        metrics = evaluate_annotations(records, self.root, detector_factory=MatchingGridDetector)

        self.assertEqual(1.0, metrics['hsv_enhanced']['face_precision'])
        self.assertEqual(1.0, metrics['hsv_enhanced']['face_recall'])
        self.assertEqual(1.0, metrics['hsv_enhanced']['grid_accuracy'])
        self.assertEqual(1.0, metrics['hsv_enhanced']['color_accuracy'])


class AlwaysGridDetector:
    def __init__(self, **_):
        self.last_grid_centers = [(index, 0) for index in range(9)]

    def process_frame(self, _):
        return None, ['W'] * 9, None


class MatchingGridDetector:
    def __init__(self, **_):
        self.last_grid_centers = [
            (column * 10 + 3, row * 10)
            for row in range(3)
            for column in range(3)
        ]

    def process_frame(self, _):
        return None, ['W'] * 9, None


if __name__ == '__main__':
    unittest.main()
