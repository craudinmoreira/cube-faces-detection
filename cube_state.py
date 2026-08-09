from collections import Counter, deque
from itertools import product


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
        # Per-sticker LAB distances collected during a stable camera observation.
        self.face_color_costs = {}
        
        # Default western color scheme
        self.center_to_face = {
            'W': 'U',
            'Y': 'D',
            'G': 'F',
            'B': 'B',
            'R': 'R',
            'O': 'L'
        }
        
    def add_face(self, colors, color_costs=None):
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
        self.faces[face_name] = list(colors)
        if color_costs is not None and len(color_costs) == 9:
            self.face_color_costs[face_name] = color_costs
        else:
            self.face_color_costs.pop(face_name, None)
        return face_name

    def apply_global_color_correction(self):
        """Apply the unique, minimum-cost 9-per-color assignment when legal.

        Centers are fixed. The original capture is never mutated unless the
        assignment is unique and the resulting cube passes physical validation.
        """
        if not self.is_complete():
            return False, None, ["A correção global exige as seis faces capturadas."]
        colors = tuple(self.center_to_face)
        if any(
            face not in self.face_color_costs
            or len(self.face_color_costs[face]) != 9
            for face in self.FACE_ORDER
        ):
            return False, None, ["Dados de confiança das cores estão ausentes; recapture as faces."]

        stickers = []
        for face_name in self.FACE_ORDER:
            for position, costs in enumerate(self.face_color_costs[face_name]):
                if position == 4:
                    continue
                if not all(color in costs for color in colors):
                    return False, None, ["Dados de confiança das cores estão incompletos; recapture as faces."]
                stickers.append((face_name, position, costs))

        assignment, best_cost = self._minimum_cost_assignment(stickers, colors)
        if assignment is None:
            return False, None, ["Não foi possível equilibrar nove adesivos por cor."]
        if not self._assignment_is_unique(stickers, colors, assignment, best_cost):
            return False, None, ["A correção global é ambígua; recapture as faces sugeridas."]

        candidate_faces = {face: list(values) for face, values in self.faces.items()}
        changes = []
        for (face_name, position, _), color in zip(stickers, assignment):
            previous = candidate_faces[face_name][position]
            candidate_faces[face_name][position] = color
            if previous != color:
                changes.append((face_name, position, previous, color))

        candidate = CubeState()
        candidate.faces = candidate_faces
        is_valid, errors = candidate.validate_solvability()
        if not is_valid:
            suspect_faces = self._suspect_faces(stickers)
            return False, None, errors + [
                "Faces mais suspeitas para recaptura: " + ", ".join(suspect_faces) + "."
            ]

        self.faces = candidate_faces
        return True, {"changes": changes, "cost": best_cost}, []

    def _minimum_cost_assignment(self, stickers, colors, forbidden=None):
        """Assign eight non-center stickers to each color with min-cost flow."""
        forbidden = forbidden or set()
        source = 0
        sticker_offset = 1
        color_offset = sticker_offset + len(stickers)
        sink = color_offset + len(colors)
        graph = [[] for _ in range(sink + 1)]

        def add_edge(start, end, capacity, cost):
            graph[start].append([end, len(graph[end]), capacity, cost])
            graph[end].append([start, len(graph[start]) - 1, 0, -cost])

        for sticker_index, (_, _, costs) in enumerate(stickers):
            sticker_node = sticker_offset + sticker_index
            add_edge(source, sticker_node, 1, 0)
            for color_index, color in enumerate(colors):
                if (sticker_index, color) not in forbidden:
                    add_edge(sticker_node, color_offset + color_index, 1, int(round(costs[color] * 1000)))
        for color_index in range(len(colors)):
            add_edge(color_offset + color_index, sink, 8, 0)

        total_cost = 0
        for _ in stickers:
            previous_node = [-1] * len(graph)
            previous_edge = [-1] * len(graph)
            distance = [None] * len(graph)
            distance[source] = 0
            queue = deque([source])
            in_queue = [False] * len(graph)
            in_queue[source] = True
            while queue:
                node = queue.popleft()
                in_queue[node] = False
                for edge_index, edge in enumerate(graph[node]):
                    end, _, capacity, cost = edge
                    if capacity <= 0:
                        continue
                    candidate_cost = distance[node] + cost
                    if distance[end] is None or candidate_cost < distance[end]:
                        distance[end] = candidate_cost
                        previous_node[end] = node
                        previous_edge[end] = edge_index
                        if not in_queue[end]:
                            queue.append(end)
                            in_queue[end] = True
            if distance[sink] is None:
                return None, None
            total_cost += distance[sink]
            node = sink
            while node != source:
                start = previous_node[node]
                edge = graph[start][previous_edge[node]]
                edge[2] -= 1
                graph[node][edge[1]][2] += 1
                node = start

        assignment = []
        for sticker_index in range(len(stickers)):
            sticker_node = sticker_offset + sticker_index
            selected_color = next(
                (
                    colors[edge[0] - color_offset]
                    for edge in graph[sticker_node]
                    if color_offset <= edge[0] < sink and edge[2] == 0
                ),
                None,
            )
            assignment.append(selected_color)
        return assignment, total_cost

    def _assignment_is_unique(self, stickers, colors, assignment, best_cost):
        for sticker_index, color in enumerate(assignment):
            _, alternative_cost = self._minimum_cost_assignment(
                stickers, colors, forbidden={(sticker_index, color)}
            )
            if alternative_cost == best_cost:
                return False
        return True

    def _suspect_faces(self, stickers):
        totals = Counter()
        for face_name, position, costs in stickers:
            observed = self.faces[face_name][position]
            totals[face_name] += costs.get(observed, min(costs.values()))
        return [face for face, _ in totals.most_common(2)]

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

    @staticmethod
    def rotate_face_clockwise(colors):
        """Return a 3x3 face rotated clockwise by 90 degrees."""
        if len(colors) != 9:
            raise ValueError("A face must contain exactly 9 colors.")
        return [colors[6], colors[3], colors[0], colors[7], colors[4], colors[1], colors[8], colors[5], colors[2]]

    @classmethod
    def _rotate_face(cls, colors, quarter_turns):
        rotated = list(colors)
        for _ in range(quarter_turns % 4):
            rotated = cls.rotate_face_clockwise(rotated)
        return rotated

    def resolve_orientations(self):
        """
        Rotate captured faces until exactly one legal cube state is found.

        Faces with rotationally identical layouts can produce several equivalent
        rotation vectors, so candidates are deduplicated by their 54 facelets.
        The state is updated only after an unambiguous result is found.
        """
        counts_valid, errors = self.validate_counts()
        if not counts_valid:
            return False, errors, None

        valid_states = {}
        for rotations in product(range(4), repeat=len(self.FACE_ORDER)):
            candidate = CubeState()
            candidate.faces = {
                face_name: self._rotate_face(self.faces[face_name], turns)
                for face_name, turns in zip(self.FACE_ORDER, rotations)
            }
            is_valid, _ = candidate.validate_solvability()
            if is_valid:
                state_string = candidate.to_kociemba_string()
                valid_states.setdefault(state_string, (candidate.faces, rotations))

        if not valid_states:
            return False, ["Nenhuma orientação das faces forma um cubo válido."], None
        if len(valid_states) > 1:
            return (
                False,
                ["Mais de uma orientação válida foi encontrada; recapture uma face."],
                None,
            )

        resolved_faces, rotations = next(iter(valid_states.values()))
        self.faces = {face_name: list(colors) for face_name, colors in resolved_faces.items()}
        return True, [], dict(zip(self.FACE_ORDER, rotations))
        
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
