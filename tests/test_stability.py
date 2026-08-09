import unittest

from stability import FaceStabilityTracker


FACE = ['R'] * 9


class FaceStabilityTrackerTests(unittest.TestCase):
    def test_requires_frame_count_and_minimum_duration(self):
        tracker = FaceStabilityTracker(
            min_frames=3,
            min_duration_seconds=1.0,
            min_agreement=0.8,
        )

        self.assertIsNone(tracker.observe(FACE, timestamp=0.0))
        self.assertIsNone(tracker.observe(FACE, timestamp=0.4))
        self.assertIsNone(tracker.observe(FACE, timestamp=0.9))
        self.assertEqual(FACE, tracker.observe(FACE, timestamp=1.0))

    def test_requires_agreement_for_every_sticker(self):
        tracker = FaceStabilityTracker(
            min_frames=5,
            min_duration_seconds=0.4,
            min_agreement=0.8,
        )
        observations = [
            ['R'] * 9,
            ['G'] + ['R'] * 8,
            ['G'] + ['R'] * 8,
            ['R'] * 9,
            ['R'] * 9,
        ]

        for index, colors in enumerate(observations):
            result = tracker.observe(colors, timestamp=index * 0.1)

        self.assertIsNone(result)

    def test_sliding_window_recovers_after_noisy_frames(self):
        tracker = FaceStabilityTracker(
            min_frames=5,
            min_duration_seconds=0.4,
            min_agreement=0.8,
            max_history_frames=5,
        )
        for index, color in enumerate(['G', 'B', 'G', 'B', 'G']):
            tracker.observe([color] + ['R'] * 8, timestamp=index * 0.1)

        result = None
        for index in range(5, 10):
            result = tracker.observe(FACE, timestamp=index * 0.1)

        self.assertEqual(FACE, result)

    def test_high_frame_rate_still_reaches_minimum_duration(self):
        tracker = FaceStabilityTracker(
            min_frames=15,
            min_duration_seconds=0.5,
            history_window_seconds=0.6,
        )

        result = None
        for frame_index in range(121):
            result = tracker.observe(FACE, timestamp=frame_index / 240)

        self.assertEqual(FACE, result)

    def test_center_change_resets_the_observation(self):
        tracker = FaceStabilityTracker(min_frames=2, min_duration_seconds=0)

        tracker.observe(FACE, timestamp=0.0)
        new_center_face = ['G'] * 9
        result = tracker.observe(new_center_face, timestamp=0.1)

        self.assertIsNone(result)
        self.assertEqual(1, tracker.frame_count)

    def test_unknown_sticker_prevents_consensus(self):
        tracker = FaceStabilityTracker(min_frames=3, min_duration_seconds=0)
        unknown = ['U'] + ['R'] * 8

        for index in range(3):
            result = tracker.observe(unknown, timestamp=float(index))

        self.assertIsNone(result)

    def test_progress_requires_frames_and_duration(self):
        tracker = FaceStabilityTracker(min_frames=4, min_duration_seconds=1.0)

        tracker.observe(FACE, timestamp=0.0)
        tracker.observe(FACE, timestamp=0.5)

        self.assertEqual(0.5, tracker.progress(timestamp=0.5))

    def test_returns_median_color_costs_for_a_stable_observation(self):
        tracker = FaceStabilityTracker(min_frames=2, min_duration_seconds=0)
        first = [{'R': 1.0, 'O': 9.0} for _ in range(9)]
        second = [{'R': 3.0, 'O': 7.0} for _ in range(9)]

        tracker.observe(FACE, timestamp=0.0, color_costs=first)
        self.assertEqual(FACE, tracker.observe(FACE, timestamp=0.1, color_costs=second))

        self.assertEqual(2.0, tracker.consensus_color_costs()[0]['R'])
        self.assertEqual(8.0, tracker.consensus_color_costs()[0]['O'])


if __name__ == '__main__':
    unittest.main()
