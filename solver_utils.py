from rubik.cube import Cube
from rubik.solve import Solver

def solve_cube(state_string):
    """
    Solves the Rubik's cube given a 54-character state string.
    Returns a list of move strings or an error message.
    """
    try:
        # The library expects the string to use certain characters, but it's flexible
        # as long as the color characters are internally consistent.
        # However, to be safe, standard strings are used.
        c = Cube(state_string)
        solver = Solver(c)
        solver.solve()
        
        # Moves are returned as a list of strings like ['U', 'R', "F'", ...]
        return solver.moves
    except Exception as e:
        return f"Error solving cube: {str(e)}"

def solve_cube_kociemba(state_string):
    """
    Solves the Rubik's cube using Kociemba's algorithm.
    Expects a 54-character state string (U, R, F, D, L, B).
    Returns a string of moves or an error message.
    """
    try:
        import optimal.solver as sv
        solution = sv.solve(state_string)
        return solution
    except ImportError:
        return "Error: 'RubikOptimal' package not installed. Run pip install RubikOptimal"
    except Exception as e:
        return f"Error solving cube with Kociemba: {str(e)}"
