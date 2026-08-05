import copy
import unittest

from cube_state import CubeState


SOLVED_FACES = {
    'U': ['W'] * 9,
    'R': ['R'] * 9,
    'F': ['G'] * 9,
    'D': ['Y'] * 9,
    'L': ['O'] * 9,
    'B': ['B'] * 9,
}


def solved_state():
    state = CubeState()
    state.faces = copy.deepcopy(SOLVED_FACES)
    return state


def state_from_flat_string(flat):
    state = CubeState()
    state.faces = {
        'U': list(flat[0:9]),
        'L': list(flat[9:12] + flat[21:24] + flat[33:36]),
        'F': list(flat[12:15] + flat[24:27] + flat[36:39]),
        'R': list(flat[15:18] + flat[27:30] + flat[39:42]),
        'B': list(flat[18:21] + flat[30:33] + flat[42:45]),
        'D': list(flat[45:54]),
    }
    return state


class CubeStateCountValidationTests(unittest.TestCase):
    def test_solved_cube_has_valid_counts(self):
        valid, errors = solved_state().validate_counts()

        self.assertTrue(valid)
        self.assertEqual([], errors)

    def test_incomplete_cube_reports_missing_faces(self):
        state = CubeState()
        state.faces['U'] = ['W'] * 9

        valid, errors = state.validate_counts()

        self.assertFalse(valid)
        self.assertTrue(any('Faces ausentes' in error for error in errors))

    def test_wrong_color_count_is_rejected(self):
        state = solved_state()
        state.faces['U'][0] = 'R'

        valid, errors = state.validate_counts()

        self.assertFalse(valid)
        self.assertTrue(any('Cor W: 8' in error for error in errors))
        self.assertTrue(any('Cor R: 10' in error for error in errors))

    def test_center_must_match_face_name(self):
        state = solved_state()
        state.faces['U'][4], state.faces['F'][4] = (
            state.faces['F'][4],
            state.faces['U'][4],
        )

        valid, errors = state.validate_counts()

        self.assertFalse(valid)
        self.assertTrue(any('Centro da face U' in error for error in errors))


class CubeStateSolvabilityTests(unittest.TestCase):
    def test_solved_cube_is_solvable(self):
        valid, errors = solved_state().validate_solvability()

        self.assertTrue(valid)
        self.assertEqual([], errors)

    def test_legal_scrambled_cube_is_solvable(self):
        flat = 'RRYRWYBBOWWOWOGWGRGBBWOGWGWBRRGBOBBGWRYOOBYYYRYGYYGOOR'

        valid, errors = state_from_flat_string(flat).validate_solvability()

        self.assertTrue(valid)
        self.assertEqual([], errors)

    def test_single_flipped_edge_is_rejected(self):
        state = solved_state()
        state.faces['U'][7], state.faces['F'][1] = (
            state.faces['F'][1],
            state.faces['U'][7],
        )

        valid, errors = state.validate_solvability()

        self.assertFalse(valid)
        self.assertTrue(any('orientação das arestas' in error for error in errors))

    def test_single_twisted_corner_is_rejected(self):
        state = solved_state()
        upper, right, front = (
            state.faces['U'][8],
            state.faces['R'][0],
            state.faces['F'][2],
        )
        state.faces['U'][8] = front
        state.faces['R'][0] = upper
        state.faces['F'][2] = right

        valid, errors = state.validate_solvability()

        self.assertFalse(valid)
        self.assertTrue(any('orientação dos cantos' in error for error in errors))

    def test_two_swapped_edges_are_rejected_by_parity(self):
        state = solved_state()
        state.faces['R'][1], state.faces['F'][1] = (
            state.faces['F'][1],
            state.faces['R'][1],
        )

        valid, errors = state.validate_solvability()

        self.assertFalse(valid)
        self.assertTrue(any('paridade' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
