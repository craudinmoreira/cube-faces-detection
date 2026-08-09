import unittest

import numpy as np

from calibration import CalibrationTracker


SAMPLE = np.tile(np.array([[100.0, 150.0, 200.0]]), (9, 1))


class CalibrationTrackerTests(unittest.TestCase):
    def test_requires_frames_and_duration(self):
        tracker = CalibrationTracker(min_frames=3, min_duration_seconds=1.0)

        self.assertIsNone(tracker.observe(SAMPLE, timestamp=0.0))
        self.assertIsNone(tracker.observe(SAMPLE, timestamp=0.5))
        self.assertIsNone(tracker.observe(SAMPLE, timestamp=0.9))
        np.testing.assert_array_equal(SAMPLE[0], tracker.observe(SAMPLE, timestamp=1.0))

    def test_uses_a_median_across_all_face_observations(self):
        tracker = CalibrationTracker(min_frames=3, min_duration_seconds=0)
        tracker.observe(SAMPLE, timestamp=0.0)
        tracker.observe(SAMPLE + 2, timestamp=0.1)
        result = tracker.observe(SAMPLE + 100, timestamp=0.2)

        np.testing.assert_array_equal(SAMPLE[0] + 2, result)

    def test_invalid_sample_resets_collection(self):
        tracker = CalibrationTracker(min_frames=2, min_duration_seconds=0)
        tracker.observe(SAMPLE, timestamp=0.0)

        self.assertIsNone(tracker.observe(np.zeros((8, 3)), timestamp=0.1))
        self.assertEqual(0, tracker.frame_count)

    def test_progress_requires_both_constraints(self):
        tracker = CalibrationTracker(min_frames=4, min_duration_seconds=1.0)
        tracker.observe(SAMPLE, timestamp=0.0)
        tracker.observe(SAMPLE, timestamp=0.5)

        self.assertEqual(0.5, tracker.progress(timestamp=0.5))

    def test_profile_records_variability_and_distance_percentiles(self):
        tracker = CalibrationTracker(min_frames=2, min_duration_seconds=0)
        tracker.observe(SAMPLE, timestamp=2.0)
        tracker.observe(SAMPLE + 4, timestamp=3.5)

        profile = tracker.profile()

        self.assertEqual([102.0, 152.0, 202.0], profile['center_lab'])
        self.assertEqual(18, profile['sample_count'])
        self.assertEqual(1.5, profile['duration_seconds'])
        self.assertGreater(profile['channel_std_lab'][0], 0)
        self.assertIn('p95', profile['distance_percentiles'])


if __name__ == '__main__':
    unittest.main()
