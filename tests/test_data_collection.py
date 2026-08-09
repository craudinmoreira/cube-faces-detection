import json
import tempfile
import unittest

import numpy as np

from data_collection import DataCollectionSession


class DataCollectionSessionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.frame = np.full((40, 40, 3), 50, dtype=np.uint8)
        self.rectified = np.full((30, 30, 3), 90, dtype=np.uint8)

    def tearDown(self):
        self.directory.cleanup()

    def test_saves_a_labeled_solved_face_and_manifest(self):
        session = DataCollectionSession(root=self.directory.name)

        saved, message = session.observe('U', ['W'] * 9, self.frame, self.rectified)

        self.assertTrue(saved)
        self.assertIn('1/10', message)
        manifest = json.loads((session.directory / 'manifest.json').read_text())
        self.assertEqual('W', manifest['records'][0]['color'])
        self.assertEqual(['W'] * 9, manifest['records'][0]['expected_colors'])
        self.assertEqual(['W'] * 9, manifest['records'][0]['observed_colors'])
        self.assertTrue((session.directory / manifest['records'][0]['frame']).exists())

    def test_rejects_unsolved_and_duplicate_faces(self):
        session = DataCollectionSession(root=self.directory.name)

        saved, _ = session.observe('U', ['W'] * 8 + ['R'], self.frame, self.rectified)
        duplicate_saved, _ = session.observe('U', ['W'] * 9, self.frame, self.rectified)
        duplicate_saved_again, message = session.observe('U', ['W'] * 9, self.frame, self.rectified)

        self.assertFalse(saved)
        self.assertTrue(duplicate_saved)
        self.assertFalse(duplicate_saved_again)
        self.assertIn('idêntica', message)

    def test_enforces_the_per_color_quota(self):
        session = DataCollectionSession(root=self.directory.name, max_samples_per_color=1)

        self.assertTrue(session.observe('U', ['W'] * 9, self.frame, self.rectified)[0])
        varied = self.rectified + 20
        saved, message = session.observe('U', ['W'] * 9, self.frame + 20, varied)

        self.assertFalse(saved)
        self.assertIn('Cota', message)


if __name__ == '__main__':
    unittest.main()
