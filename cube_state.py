from collections import Counter


class CubeState:
    FACE_ORDER = ('U', 'R', 'F', 'D', 'L', 'B')

    # Facelet positions and colors follow the URFDLB convention used by
    # Kociemba-compatible solvers.
    CORNER_FACELETS = (
        (8, 9, 20),    # URF
        (6, 18, 38),   # UFL
        (0, 36, 47),   # ULB
        (2, 45, 11),   # UBR
        (29, 26, 15),  # DFR
        (27, 44, 24),  # DLF
        (33, 53, 42),  # DBL
        (35, 17, 51),  # DRB
    )
    CORNER_COLORS = (
        ('U', 'R', 'F'),
        ('U', 'F', 'L'),
        ('U', 'L', 'B'),
        ('U', 'B', 'R'),
        ('D', 'F', 'R'),
        ('D', 'L', 'F'),
        ('D', 'B', 'L'),
        ('D', 'R', 'B'),
    )
    EDGE_FACELETS = (
        (5, 10),   # UR
        (7, 19),   # UF
        (3, 37),   # UL
        (1, 46),   # UB
        (32, 16),  # DR
        (28, 25),  # DF
        (30, 43),  # DL
        (34, 52),  # DB
        (23, 12),  # FR
        (21, 41),  # FL
        (50, 39),  # BL
        (48, 14),  # BR
    )
    EDGE_COLORS = (
        ('U', 'R'),
        ('U', 'F'),
        ('U', 'L'),
        ('U', 'B'),
        ('D', 'R'),
        ('D', 'F'),
        ('D', 'L'),
        ('D', 'B'),
        ('F', 'R'),
        ('F', 'L'),
        ('B', 'L'),
        ('B', 'R'),
    )

    def __init__(self):
        # Maps face standard name (U, D, F, B, L, R) to a list of 9 color strings
        self.faces = {}
        
        # Default western color scheme
        self.center_to_face = {
            'W': 'U',
            'Y': 'D',
            'G': 'F',
            'B': 'B',
            'R': 'R',
            'O': 'L'
        }
        
    def add_face(self, colors):
        """
        Takes a list of 9 colors representing a face.
        The center color (index 4) determines which face it is.
        """
        if len(colors) != 9:
            return False
            
        center_color = colors[4]
        if center_color not in self.center_to_face:
            return False
            
        face_name = self.center_to_face[center_color]
        self.faces[face_name] = colors
        return face_name

    def is_complete(self):
        return len(self.faces) == 6

    def validate_counts(self):
        """
        Validate the structural and color-count invariants of a captured cube.

        Returns a tuple ``(is_valid, errors)`` so callers can present useful
        feedback without relying on solver exceptions.
        """
        errors = []
        expected_faces = set(self.FACE_ORDER)
        actual_faces = set(self.faces)

        missing_faces = sorted(expected_faces - actual_faces)
        unexpected_faces = sorted(actual_faces - expected_faces)
        if missing_faces:
            errors.append(f"Faces ausentes: {', '.join(missing_faces)}.")
        if unexpected_faces:
            errors.append(f"Faces desconhecidas: {', '.join(unexpected_faces)}.")

        allowed_colors = set(self.center_to_face)
        all_colors = []
        centers = []

        for face_name in self.FACE_ORDER:
            colors = self.faces.get(face_name)
            if colors is None:
                continue
            if len(colors) != 9:
                errors.append(
                    f"A face {face_name} tem {len(colors)} peças; esperado: 9."
                )
                continue

            all_colors.extend(colors)
            center_color = colors[4]
            centers.append(center_color)
            expected_face = self.center_to_face.get(center_color)
            if expected_face != face_name:
                errors.append(
                    f"Centro da face {face_name} é {center_color!r}, "
                    f"que identifica {expected_face or 'nenhuma face'}."
                )

        unknown_colors = sorted(set(all_colors) - allowed_colors)
        if unknown_colors:
            errors.append(
                f"Cores desconhecidas: {', '.join(repr(c) for c in unknown_colors)}."
            )

        counts = Counter(all_colors)
        for color in self.center_to_face:
            count = counts[color]
            if count != 9:
                errors.append(f"Cor {color}: {count} peças; esperado: 9.")

        if len(centers) == 6 and len(set(centers)) != 6:
            errors.append("As seis faces devem possuir centros de cores diferentes.")

        return not errors, errors

    @staticmethod
    def _permutation_parity(permutation):
        inversions = sum(
            permutation[i] > permutation[j]
            for i in range(len(permutation))
            for j in range(i + 1, len(permutation))
        )
        return inversions % 2

    def validate_solvability(self):
        """
        Validate whether the captured facelets describe a physically legal cube.

        Besides counts and centers, this checks that every corner and edge occurs
        exactly once, corner twists sum to zero, edge flips sum to zero, and edge
        and corner permutations have matching parity.
        """
        counts_valid, errors = self.validate_counts()
        if not counts_valid:
            return False, errors

        facelets = self.to_kociemba_string()
        corner_permutation = []
        corner_orientations = []

        for position, indexes in enumerate(self.CORNER_FACELETS):
            colors = tuple(facelets[index] for index in indexes)
            orientation = next(
                (index for index, color in enumerate(colors) if color in ('U', 'D')),
                None,
            )
            if orientation is None:
                errors.append(
                    f"Canto na posição {position} não contém uma cor U/D: {colors}."
                )
                continue

            side_1 = colors[(orientation + 1) % 3]
            side_2 = colors[(orientation + 2) % 3]
            cubie = next(
                (
                    index
                    for index, expected in enumerate(self.CORNER_COLORS)
                    if expected[1] == side_1 and expected[2] == side_2
                ),
                None,
            )
            if cubie is None:
                errors.append(f"Canto impossível na posição {position}: {colors}.")
                continue

            corner_permutation.append(cubie)
            corner_orientations.append(orientation % 3)

        edge_permutation = []
        edge_orientations = []
        for position, indexes in enumerate(self.EDGE_FACELETS):
            colors = tuple(facelets[index] for index in indexes)
            match = next(
                (
                    (index, 0)
                    for index, expected in enumerate(self.EDGE_COLORS)
                    if colors == expected
                ),
                None,
            )
            if match is None:
                match = next(
                    (
                        (index, 1)
                        for index, expected in enumerate(self.EDGE_COLORS)
                        if colors == expected[::-1]
                    ),
                    None,
                )
            if match is None:
                errors.append(f"Aresta impossível na posição {position}: {colors}.")
                continue

            cubie, orientation = match
            edge_permutation.append(cubie)
            edge_orientations.append(orientation)

        if len(corner_permutation) == 8:
            if len(set(corner_permutation)) != 8:
                errors.append("Há cantos duplicados ou ausentes.")
            if sum(corner_orientations) % 3 != 0:
                errors.append("A orientação dos cantos é fisicamente impossível.")

        if len(edge_permutation) == 12:
            if len(set(edge_permutation)) != 12:
                errors.append("Há arestas duplicadas ou ausentes.")
            if sum(edge_orientations) % 2 != 0:
                errors.append("A orientação das arestas é fisicamente impossível.")

        corners_complete = (
            len(corner_permutation) == 8 and len(set(corner_permutation)) == 8
        )
        edges_complete = len(edge_permutation) == 12 and len(set(edge_permutation)) == 12
        if corners_complete and edges_complete:
            if self._permutation_parity(corner_permutation) != self._permutation_parity(
                edge_permutation
            ):
                errors.append("A paridade das permutações de cantos e arestas não coincide.")

        return not errors, errors
        
    def get_missing_faces(self):
        all_faces = set(self.center_to_face.values())
        return list(all_faces - set(self.faces.keys()))

    def to_54_string(self):
        """
        Converts the captured 6 faces into the 54-character string format
        required by pglass/cube (rubik-cube python package).
        
        Layout:
                     UP (U)
                     0  1  2
                     3  4  5
                     6  7  8
        LEFT (L)   FRONT (F)  RIGHT (R)   BACK (B)
         9 10 11   12 13 14   15 16 17   18 19 20
        21 22 23   24 25 26   27 28 29   30 31 32
        33 34 35   36 37 38   39 40 41   42 43 44
                    DOWN (D)
                    45 46 47
                    48 49 50
                    51 52 53
        """
        if not self.is_complete():
            raise ValueError("Cube state is not complete.")
            
        result = [''] * 54
        
        # UP face
        for i in range(9):
            result[i] = self.faces['U'][i]
            
        # DOWN face
        for i in range(9):
            result[45 + i] = self.faces['D'][i]
            
        # Middle band (L, F, R, B)
        # Row 1
        result[9:12] = self.faces['L'][0:3]
        result[12:15] = self.faces['F'][0:3]
        result[15:18] = self.faces['R'][0:3]
        result[18:21] = self.faces['B'][0:3]
        
        # Row 2
        result[21:24] = self.faces['L'][3:6]
        result[24:27] = self.faces['F'][3:6]
        result[27:30] = self.faces['R'][3:6]
        result[30:33] = self.faces['B'][3:6]
        
        # Row 3
        result[33:36] = self.faces['L'][6:9]
        result[36:39] = self.faces['F'][6:9]
        result[39:42] = self.faces['R'][6:9]
        result[42:45] = self.faces['B'][6:9]
        
        return "".join(result)

    def to_kociemba_string(self):
        """
        Converts the captured 6 faces into the 54-character string format
        required by Kociemba's algorithm.
        
        Layout order: U, R, F, D, L, B.
        Characters must be the face identifiers ('U', 'R', 'F', 'D', 'L', 'B').
        """
        if not self.is_complete():
            raise ValueError("Cube state is not complete.")
            
        result = ""
        for face_name in ['U', 'R', 'F', 'D', 'L', 'B']:
            for color in self.faces[face_name]:
                result += self.center_to_face[color]
        return result
