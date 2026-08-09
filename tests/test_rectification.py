import unittest

import cv2
import numpy as np

from vision import CubeDetector


CELL_COLORS = [
    (10, 20, 230), (20, 220, 20), (220, 20, 20),
    (20, 140, 240), (230, 230, 230), (20, 230, 230),
    (100, 40, 220), (40, 220, 100), (220, 100, 40),
]


def make_canonical_face():
    face = np.zeros((300, 300, 3), dtype=np.uint8)
    for index, color in enumerate(CELL_COLORS):
        row, column = divmod(index, 3)
        cv2.rectangle(
            face,
            (column * 100, row * 100),
            ((column + 1) * 100, (row + 1) * 100),
            color,
            -1,
        )
    return face


def faces_from_source_points(source_points):
    faces = []
    for center_x, center_y in source_points:
        x = int(center_x - 15)
        y = int(center_y - 15)
        faces.append(
            {
                'cx': float(center_x),
                'cy': float(center_y),
                'approx': np.array(
                    [[[x, y]], [[x + 30, y]], [[x + 30, y + 30]], [[x, y + 30]]],
                    dtype=np.int32,
                ),
                'bbox': (x, y, 30, 30),
            }
        )
    return faces


class FaceRectificationTests(unittest.TestCase):
    def setUp(self):
        self.detector = CubeDetector()
        self.target_corners = np.float32([[0, 0], [299, 0], [299, 299], [0, 299]])
        self.source_corners = np.float32([[45, 70], [330, 35], [350, 345], [65, 320]])
        self.target_centers = np.float32(
            [[50 + column * 100, 50 + row * 100] for row in range(3) for column in range(3)]
        )
        self.to_source = cv2.getPerspectiveTransform(self.target_corners, self.source_corners)
        self.source_centers = cv2.perspectiveTransform(
            self.target_centers.reshape(-1, 1, 2), self.to_source
        ).reshape(-1, 2)
        self.source_face = cv2.warpPerspective(make_canonical_face(), self.to_source, (400, 400))
        self.faces = faces_from_source_points(self.source_centers)

    def test_rectifies_a_projected_face(self):
        rectified = self.detector._rectify_face(self.source_face, self.faces)

        self.assertIsNotNone(rectified)
        self.assertEqual((300, 300, 3), rectified.shape)
        for index, expected_color in enumerate(CELL_COLORS):
            row, column = divmod(index, 3)
            pixel = rectified[row * 100 + 50, column * 100 + 50]
            np.testing.assert_allclose(expected_color, pixel, atol=3)

    def test_rejects_inconsistent_correspondences(self):
        inconsistent_faces = faces_from_source_points(self.source_centers.copy())
        inconsistent_faces[4]['cx'] += 50

        rectified = self.detector._rectify_face(self.source_face, inconsistent_faces)

        self.assertIsNone(rectified)

    def test_extracts_equal_sized_inner_rois_after_rectification(self):
        annotated = self.source_face.copy()

        colors, rois = self.detector._extract_colors_and_draw(
            self.source_face, annotated, self.faces, calibration_mode=True
        )

        self.assertEqual(['U'] * 9, colors)
        self.assertEqual(9, len(rois))
        self.assertTrue(all(roi.shape == (50, 50, 3) for roi in rois))


if __name__ == '__main__':
    unittest.main()
