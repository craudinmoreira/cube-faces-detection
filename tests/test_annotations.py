import json
import tempfile
import unittest
from pathlib import Path

from annotations import AnnotationStore, grid_matches
from annotation import AnnotationController


class AnnotationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.input_dir = self.root / 'to_annotate'
        self.input_dir.mkdir()
        (self.input_dir / 'hard.png').write_bytes(b'image')
        (self.input_dir / 'new.png').write_bytes(b'image')
        self.store = AnnotationStore(self.root / 'annotations.json')

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pending_images_skips_a_previously_saved_annotation(self):
        self.store.save('hard.png', has_face=False)

        self.assertEqual(['new.png'], self.store.pending_images(self.input_dir))

    def test_positive_annotation_requires_nine_centers_and_allowed_colors(self):
        with self.assertRaisesRegex(ValueError, 'nove centros'):
            self.store.save('hard.png', has_face=True, centers=[(1, 1)], expected_colors=['W'])

        with self.assertRaisesRegex(ValueError, 'cor inválida'):
            self.store.save(
                'hard.png',
                has_face=True,
                centers=[(index, index) for index in range(9)],
                expected_colors=['W'] * 8 + ['U'],
            )

    def test_rejects_absolute_or_parent_relative_paths(self):
        with self.assertRaisesRegex(ValueError, 'caminho relativo'):
            self.store.save('../outside.png', has_face=False)
        with self.assertRaisesRegex(ValueError, 'caminho relativo'):
            self.store.save(str(self.root / 'outside.png'), has_face=False)

    def test_persists_a_relative_positive_record(self):
        centers = [(column * 10, row * 10) for row in range(3) for column in range(3)]
        self.store.save('hard.png', has_face=True, centers=centers, expected_colors=['W'] * 9)

        saved = json.loads((self.root / 'annotations.json').read_text(encoding='utf-8'))
        self.assertEqual('hard.png', saved['records']['hard.png']['path'])
        self.assertEqual(
            [[0, 0], [10, 0], [20, 0], [0, 10], [10, 10], [20, 10], [0, 20], [10, 20], [20, 20]],
            saved['records']['hard.png']['centers'],
        )


class GridMatchingTests(unittest.TestCase):
    def setUp(self):
        self.centers = [
            (column * 10, row * 10)
            for row in range(3)
            for column in range(3)
        ]

    def test_accepts_predictions_within_forty_percent_of_grid_spacing(self):
        predicted = [(x + 4, y) for x, y in self.centers]

        self.assertTrue(grid_matches(self.centers, predicted))

    def test_rejects_predictions_outside_forty_percent_of_grid_spacing(self):
        predicted = [(x + 5, y) for x, y in self.centers]

        self.assertFalse(grid_matches(self.centers, predicted))


class AnnotationControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = AnnotationStore(Path(self.temp_dir.name) / 'annotations.json')
        self.controller = AnnotationController('hard.png', self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_positive_annotation_saves_after_nine_centers_and_colors(self):
        self.controller.start_positive()
        for row in range(3):
            for column in range(3):
                self.controller.add_center((column * 10, row * 10))
        for color in 'WYGBROWYG':
            self.controller.add_color(color)

        record = self.store.records['hard.png']
        self.assertTrue(record['has_face'])
        self.assertEqual(list('WYGBROWYG'), record['expected_colors'])

    def test_negative_annotation_saves_without_centers(self):
        self.controller.mark_negative()

        self.assertEqual({'path': 'hard.png', 'has_face': False}, self.store.records['hard.png'])

    def test_reset_discards_the_current_incomplete_annotation(self):
        self.controller.start_positive()
        self.controller.add_center((10, 10))
        self.controller.reset_current()

        self.assertEqual([], self.controller.centers)
        self.assertEqual([], self.controller.colors)
        self.assertFalse(self.controller.positive_started)


if __name__ == '__main__':
    unittest.main()
