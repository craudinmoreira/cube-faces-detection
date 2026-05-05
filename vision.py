import cv2
import numpy as np
import json
import os

class ColorDetector:
    def __init__(self, calibration_path='calibration.json'):
        # Define LAB color centers for the Rubik's cube standard colors.
        # L: 0-255, a: 0-255, b: 0-255 (OpenCV's representation of LAB)
        self.color_centers_lab = {
            'R': np.array([136, 208, 195]),
            'O': np.array([171, 171, 202]),
            'Y': np.array([248, 106, 223]),
            'G': np.array([224, 42, 211]),
            'B': np.array([82, 207, 20]),
            'W': np.array([255, 128, 128])
        }

        if os.path.exists(calibration_path):
            try:
                with open(calibration_path) as f:
                    data = json.load(f)
                for color, values in data.items():
                    self.color_centers_lab[color] = np.array(values)
            except Exception:
                pass
        
        # Used for drawing UI
        self.color_bgr = {
            'R': (0, 0, 255),
            'O': (0, 165, 255),
            'Y': (0, 255, 255),
            'G': (0, 255, 0),
            'B': (255, 0, 0),
            'W': (255, 255, 255),
            'U': (128, 128, 128) # Unknown
        }

    def detect_color(self, bgr_roi):
        if bgr_roi.size == 0:
            return 'U'
            
        lab_roi = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2LAB)
        
        # Use median to ignore noise/glare
        pixels = lab_roi.reshape(-1, 3)
        median_lab = np.median(pixels, axis=0)
        
        min_dist = float('inf')
        detected_color = 'U'
        weights = np.array([0.5, 1.0, 1.0])
        
        for color, center in self.color_centers_lab.items():
            dist = np.linalg.norm((median_lab - center) * weights)
            if dist < min_dist:
                min_dist = dist
                detected_color = color
                
        # Optional: threshold to prevent completely random colors from matching
        if min_dist > 80:
            return 'U'
            
        return detected_color

class CubeDetector:
    def __init__(self):
        self.color_detector = ColorDetector()

    def _find_squares(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        # Lowered thresholds for Canny to detect color boundaries without black lines
        edges = cv2.Canny(blurred, 10, 30)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        square_contours = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
            
            if len(approx) == 4 and cv2.isContourConvex(approx):
                area = cv2.contourArea(contour)
                if 500 < area < 25000:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h
                    if 0.75 <= aspect_ratio <= 1.3:
                        square_contours.append((approx, area, (x, y, w, h)))
        return self._deduplicate(square_contours)

    def _deduplicate(self, square_contours, min_dist=20):
        unique = []
        for item in square_contours:
            x, y, w, h = item[2]
            cx, cy = x + w // 2, y + h // 2
            if not any(
                abs(cx - (u[2][0] + u[2][2] // 2)) < min_dist and
                abs(cy - (u[2][1] + u[2][3] // 2)) < min_dist
                for u in unique
            ):
                unique.append(item)
        return unique

    def _group_and_sort_squares(self, square_contours):
        if len(square_contours) < 9:
            return None
            
        square_contours.sort(key=lambda x: x[1], reverse=True)
        
        found_group = None
        for i in range(len(square_contours) - 8):
            group = square_contours[i:i+9]
            max_area = group[0][1]
            min_area = group[-1][1]
            
            if min_area > max_area * 0.5:
                found_group = group
                break
        
        if not found_group:
            return None
            
        centers = []
        for approx, area, bbox in found_group:
            x, y, w, h = bbox
            centers.append({
                'approx': approx,
                'bbox': bbox,
                'cx': x + w//2,
                'cy': y + h//2
            })
            
        centers.sort(key=lambda item: item['cy'])

        avg_tile_h = int(np.median([c['bbox'][3] for c in centers]))
        row_tolerance = max(10, avg_tile_h // 2)

        rows = []
        current_row = [centers[0]]
        for c in centers[1:]:
            if abs(c['cy'] - current_row[-1]['cy']) < row_tolerance:
                current_row.append(c)
            else:
                rows.append(sorted(current_row, key=lambda i: i['cx']))
                current_row = [c]
        rows.append(sorted(current_row, key=lambda i: i['cx']))

        if len(rows) != 3 or any(len(r) != 3 for r in rows):
            return None

        return [item for row in rows for item in row]

    def _extract_colors_and_draw(self, frame, annotated_frame, sorted_faces, calibration_mode):
        color_smooth = cv2.GaussianBlur(frame, (11, 11), 0)
        face_colors = []
        rois = []
        
        for face_data in sorted_faces:
            approx = face_data['approx']
            x, y, w, h = face_data['bbox']
            
            offset_x = int(w * 0.3)
            offset_y = int(h * 0.3)
            roi = color_smooth[y+offset_y:y+h-offset_y, x+offset_x:x+w-offset_x]
            
            if roi.size == 0:
                face_colors.append('U')
                rois.append(None)
                continue
                
            rois.append(roi)
            cx, cy = face_data['cx'], face_data['cy']
            
            if not calibration_mode:
                detected_color = self.color_detector.detect_color(roi)
                face_colors.append(detected_color)
                
                bgr_color = self.color_detector.color_bgr.get(detected_color, (255,255,255))
                cv2.drawContours(annotated_frame, [approx], -1, bgr_color, 3)
                cv2.circle(annotated_frame, (cx, cy), 5, bgr_color, -1)
                cv2.putText(annotated_frame, detected_color, (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, bgr_color, 2)
            else:
                face_colors.append('U')
                cv2.drawContours(annotated_frame, [approx], -1, (255, 255, 255), 3)
                cv2.circle(annotated_frame, (cx, cy), 5, (255, 255, 255), -1)
                
        return face_colors, rois

    def _enhance_image(self, frame):
        """
        Artificially boosts the saturation of the image to help distinguish pale/washed-out colors.
        """
        # Convert to HSV (using float32 to prevent overflow during multiplication)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Boost saturation by 40%
        hsv[:, :, 1] = hsv[:, :, 1] * 1.4
        
        # Slightly boost value (brightness/contrast) to make colors pop
        hsv[:, :, 2] = hsv[:, :, 2] * 1.1
        
        # Clip values to ensure they stay within the valid 0-255 range
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        
        # Convert back to BGR
        enhanced_frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        return enhanced_frame

    def process_frame(self, frame, calibration_mode=False):
        """
        Process the frame to find a 3x3 Rubik's cube face.
        """
        # Boost saturation before any processing happens
        enhanced_frame = self._enhance_image(frame)
        annotated_frame = enhanced_frame.copy()
        
        square_contours = self._find_squares(frame)
        sorted_faces = self._group_and_sort_squares(square_contours)
        
        if sorted_faces:
            face_colors, rois = self._extract_colors_and_draw(
                enhanced_frame, annotated_frame, sorted_faces, calibration_mode
            )
            return annotated_frame, face_colors, rois

        return annotated_frame, None, None
