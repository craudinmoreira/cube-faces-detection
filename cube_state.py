class CubeState:
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
