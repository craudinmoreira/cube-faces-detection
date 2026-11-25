import sys
import types

import pytest
from rubik.cube import Cube

from solver_utils import solve_cube, solve_cube_kociemba

SOLVED = 'OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR'


def scrambled(sequence='R U Ri F D L B'):
    cube = Cube(SOLVED)
    cube.sequence(sequence)
    return cube.flat_str()


def test_layer_by_layer_solution_solves_the_cube():
    state = scrambled()
    moves = solve_cube(state)

    assert isinstance(moves, list) and moves
    cube = Cube(state)
    cube.sequence(' '.join(moves))
    assert cube.is_solved()


def test_layer_by_layer_reports_invalid_state_as_error():
    assert solve_cube('xyz').startswith('Error solving cube')


@pytest.fixture
def fake_optimal(monkeypatch):
    """Substitui o RubikOptimal: o real gera tabelas de poda por minutos."""
    package = types.ModuleType('optimal')
    solver = types.ModuleType('optimal.solver')
    package.solver = solver
    monkeypatch.setitem(sys.modules, 'optimal', package)
    monkeypatch.setitem(sys.modules, 'optimal.solver', solver)
    return solver


def test_kociemba_returns_solver_output(fake_optimal):
    fake_optimal.solve = lambda state: f'R U (2f) for {state[:3]}'

    assert solve_cube_kociemba('UUUxxx') == 'R U (2f) for UUU'


def test_kociemba_reports_solver_exception(fake_optimal):
    def explode(_state):
        raise ValueError('invalid cube')

    fake_optimal.solve = explode

    assert solve_cube_kociemba('bad') == 'Error solving cube with Kociemba: invalid cube'


def test_kociemba_explains_missing_package(monkeypatch):
    monkeypatch.setitem(sys.modules, 'optimal.solver', None)

    assert 'not installed' in solve_cube_kociemba('UUU')
