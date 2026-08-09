import unittest
from unittest.mock import mock_open, patch

import numpy as np

import main


class FakeColorDetector:
    def __init__(self):
        self.color_centers_lab = {}


class FakeDetector:
    def __init__(self):
        self.color_detector = FakeColorDetector()


class MainHelperTests(unittest.TestCase):
    def test_load_calibration_updates_detector(self):
        detector = FakeDetector()
        calibration = '{"R": [1.0, 2.0, 3.0]}'

        with patch('main.os.path.exists', return_value=True), patch(
            'builtins.open', mock_open(read_data=calibration)
        ):
            loaded = main.load_calibration_from_log(detector)

        self.assertTrue(loaded)
        np.testing.assert_array_equal(
            np.array([1.0, 2.0, 3.0]), detector.color_detector.color_centers_lab['R']
        )

    def test_legend_lists_each_recapture_key(self):
        self.assertEqual(
            {'U', 'R', 'F', 'D', 'L', 'B'}, set(main.CAPTURE_KEY_TO_FACE.values())
        )
        legend = ' '.join(main.CAPTURE_LEGEND).lower()
        for key in ('u', 'r', 'f', 'd', 'l', 'b'):
            self.assertIn(key, legend)

    def test_pending_recapture_adds_highlight(self):
        with patch('main.cv2.putText') as put_text:
            main.draw_capture_legend(np.zeros((200, 400, 3), dtype=np.uint8), 'F')

        self.assertEqual(3, put_text.call_count)


if __name__ == '__main__':
    unittest.main()
