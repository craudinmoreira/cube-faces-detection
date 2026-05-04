import cv2
import numpy as np
from vision import ColorDetector

class FaceDisplay:
    def __init__(self):
        self.square_size = 30
        self.face_size = self.square_size * 3
        self.pad = 20
        self.width = self.pad * 2 + self.face_size * 4
        self.height = self.pad * 2 + self.face_size * 3
        self.color_bgr = ColorDetector().color_bgr
        
        self.face_offsets = {
            'U': (self.pad + self.face_size, self.pad),
            'L': (self.pad, self.pad + self.face_size),
            'F': (self.pad + self.face_size, self.pad + self.face_size),
            'R': (self.pad + self.face_size * 2, self.pad + self.face_size),
            'B': (self.pad + self.face_size * 3, self.pad + self.face_size),
            'D': (self.pad + self.face_size, self.pad + self.face_size * 2)
        }

    def draw(self, cube_state):
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[:] = (40, 40, 40) # Dark gray background
        
        # Draw placeholder outlines for all faces
        for face_name, (offset_x, offset_y) in self.face_offsets.items():
            cv2.rectangle(img, (offset_x, offset_y), 
                          (offset_x + self.face_size, offset_y + self.face_size), 
                          (100, 100, 100), 1)
                          
        # Draw captured faces
        for face_name, colors in cube_state.faces.items():
            offset_x, offset_y = self.face_offsets[face_name]
            
            for i in range(9):
                row = i // 3
                col = i % 3
                
                color_str = colors[i]
                bgr = self.color_bgr.get(color_str, (128, 128, 128))
                
                x1 = offset_x + col * self.square_size
                y1 = offset_y + row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Draw filled square
                cv2.rectangle(img, (x1, y1), (x2, y2), bgr, -1)
                # Draw black border
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 2)
                
        return img
