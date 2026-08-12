import unittest

import numpy as np

from vision import CubeDetector


def candidate(center_x, center_y, size=30, area=None):
    area = float(size * size if area is None else area)
    x = int(center_x - size / 2)
    y = int(center_y - size / 2)
    corners = np.array(
        [[[x, y]], [[x + size, y]], [[x + size, y + size]], [[x, y + size]]],
        dtype=np.int32,
    )
    return corners, area, (x, y, size, size)


def regular_grid(origin_x=100, origin_y=120, spacing=45):
    return [
        candidate(origin_x + column * spacing, origin_y + row * spacing)
        for row in range(3)
        for column in range(3)
    ]


class GridSelectionTests(unittest.TestCase):
    def setUp(self):
        self.detector = CubeDetector()

    def test_selects_regular_grid_among_false_candidates(self):
        candidates = regular_grid()
        candidates.extend(
            [
                candidate(10, 10, size=50),
                candidate(420, 80, size=20),
                candidate(300, 360, size=45),
            ]
        )

        selected, score = self.detector._select_best_grid(candidates)

        self.assertIsNotNone(selected)
        self.assertGreaterEqual(score, self.detector.GRID_SCORE_THRESHOLD)
        centers = [self.detector._candidate_center(item) for item in selected]
        self.assertEqual(
            [(100.0, 120.0), (145.0, 120.0), (190.0, 120.0)],
            [tuple(point) for point in centers[:3]],
        )

    def test_rejects_irregular_grid(self):
        candidates = [
            candidate(100, 100), candidate(180, 105), candidate(260, 100),
            candidate(105, 150), candidate(185, 210), candidate(255, 160),
            candidate(95, 230), candidate(180, 280), candidate(275, 240),
        ]

        selected = self.detector._group_and_sort_squares(candidates)

        self.assertIsNone(selected)

    def test_returns_row_major_order_for_accepted_grid(self):
        selected = self.detector._group_and_sort_squares(regular_grid())

        self.assertIsNotNone(selected)
        self.assertEqual(
            [(100, 120), (145, 120), (190, 120), (100, 165), (145, 165)],
            [(item['cx'], item['cy']) for item in selected[:5]],
        )

    def test_records_predicted_centers_for_an_annotation_overlay(self):
        self.detector._group_and_sort_squares(regular_grid())

        self.assertEqual(
            [(100.0, 120.0), (145.0, 120.0), (190.0, 120.0)],
            self.detector.last_grid_centers[:3],
        )

    def test_suppresses_overlapping_candidates_by_iou(self):
        large = candidate(100, 100, size=40)
        overlapping = candidate(102, 102, size=36)
        distinct = candidate(200, 100, size=40)

        selected = self.detector._suppress_overlaps([overlapping, distinct, large])

        self.assertEqual(2, len(selected))
        self.assertEqual({large[2], distinct[2]}, {item[2] for item in selected})

    def test_area_screening_scales_with_frame_size(self):
        frame_area = 1000 * 1000

        self.assertTrue(self.detector._has_plausible_area(2_500, frame_area))
        self.assertFalse(self.detector._has_plausible_area(100, frame_area))
        self.assertFalse(self.detector._has_plausible_area(100_000, frame_area))


if __name__ == '__main__':
    unittest.main()
