import unittest

import numpy as np

from vision import ColorDetector


class ColorDetectorConfidenceTests(unittest.TestCase):
    def setUp(self):
        self.detector = ColorDetector(calibration_path='missing-calibration.json')

    def test_accepts_an_exact_reference_color(self):
        result = self.detector.classify_lab(self.detector.color_centers_lab['R'])

        self.assertEqual('R', result)

    def test_rejects_a_color_between_red_and_orange(self):
        ambiguous = (
            self.detector.color_centers_lab['R']
            + self.detector.color_centers_lab['O']
        ) / 2

        result = self.detector.classify_lab(ambiguous)

        self.assertEqual('U', result)

    def test_rejects_a_color_far_from_all_references(self):
        result = self.detector.classify_lab(np.array([0, 0, 0]))

        self.assertEqual('U', result)

    def test_detect_color_uses_the_lab_classifier(self):
        roi = np.full((20, 20, 3), (0, 0, 255), dtype=np.uint8)

        self.assertEqual('R', self.detector.detect_color(roi))

    def test_color_measurement_exposes_cost_for_every_reference(self):
        label, distances = self.detector.detect_color_with_distances(
            np.full((20, 20, 3), (0, 0, 255), dtype=np.uint8)
        )

        self.assertEqual('R', label)
        self.assertEqual(set(self.detector.color_centers_lab), set(distances))
        self.assertLess(distances['R'], distances['O'])


if __name__ == '__main__':
    unittest.main()
