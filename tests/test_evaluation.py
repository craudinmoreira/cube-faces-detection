import unittest

import numpy as np

from evaluation import recommend_preprocessing
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


if __name__ == '__main__':
    unittest.main()
