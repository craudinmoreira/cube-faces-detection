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
