import unittest

import numpy as np

from vision import CubeDetector


class DebugStateTests(unittest.TestCase):
    def test_records_candidate_count_and_rejection_reason(self):
        detector = CubeDetector(debug=True)

        _, colors, _ = detector.process_frame(np.zeros((100, 100, 3), dtype=np.uint8))

        debug_state = detector.get_debug_state()
        self.assertIsNone(colors)
        self.assertIn('candidate_count', debug_state)
        self.assertIn('rejection_reason', debug_state)

    def test_debug_views_are_disabled_when_not_requested(self):
        detector = CubeDetector(debug=False)
        detector.process_frame(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual({}, detector.debug_views)


if __name__ == '__main__':
    unittest.main()
