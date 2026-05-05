import cv2
import numpy as np

class ColorDetector:
    def __init__(self):
        # Define HSV color ranges for the Rubik's cube standard colors.
        # These may need calibration depending on lighting.
        # OpenCV uses H: 0-179, S: 0-255, V: 0-255
        self.color_ranges = {
            'R': [
                (np.array([0, 100, 100]), np.array([3, 255, 255])),
                (np.array([170, 100, 100]), np.array([179, 255, 255]))
            ],
            'O': [
                (np.array([4, 100, 100]), np.array([25, 255, 255]))
            ],
            'Y': [
                (np.array([26, 100, 100]), np.array([35, 255, 255]))
            ],
            'G': [
                (np.array([36, 100, 100]), np.array([85, 255, 255]))
            ],
            'B': [
                (np.array([86, 100, 100]), np.array([130, 255, 255]))
            ],
            'W': [
                (np.array([0, 0, 150]), np.array([179, 60, 255]))
            ]
        }
        
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

    def detect_color(self, hsv_roi):
        # Calculate the median HSV value of the ROI
        median_hsv = np.median(hsv_roi, axis=(0, 1))
        
        # Alternative: mean
        mean_hsv = np.mean(hsv_roi, axis=(0, 1))
        
        # Check against ranges using a more robust method: count pixels in range
        max_count = 0
        detected_color = 'U'
        
        for color, ranges in self.color_ranges.items():
            count = 0
            for lower, upper in ranges:
                mask = cv2.inRange(hsv_roi, lower, upper)
                count += cv2.countNonZero(mask)
            
            if count > max_count:
                max_count = count
                detected_color = color
                
        # If no color is significantly present, return 'U'
        # Lowered to 10% to be more forgiving with noise/glare after calibration
        min_pixels_required = (hsv_roi.shape[0] * hsv_roi.shape[1]) * 0.1
        if max_count < min_pixels_required:
            return 'U'
            
        return detected_color

class CubeDetector:
    def __init__(self):
        self.color_detector = ColorDetector()

    def _find_squares(self, frame):
        blurred = cv2.GaussianBlur(frame, (7, 7), 0)
        edges = cv2.Canny(blurred, 15, 40)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        square_contours = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if 500 < area < 25000:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h
                    if 0.75 <= aspect_ratio <= 1.3:
                        square_contours.append((approx, area, (x, y, w, h)))
        return square_contours

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
        
        sorted_faces = []
        for row_idx in range(3):
            row = centers[row_idx*3:(row_idx+1)*3]
            row.sort(key=lambda item: item['cx'])
            sorted_faces.extend(row)
            
        return sorted_faces

    def _extract_colors_and_draw(self, frame, annotated_frame, sorted_faces, calibration_mode):
        color_smooth = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv_frame = cv2.cvtColor(color_smooth, cv2.COLOR_BGR2HSV)
        face_colors = []
        hsv_rois = []
        
        for face_data in sorted_faces:
            approx = face_data['approx']
            x, y, w, h = face_data['bbox']
            
            offset_x = int(w * 0.3)
            offset_y = int(h * 0.3)
            roi = hsv_frame[y+offset_y:y+h-offset_y, x+offset_x:x+w-offset_x]
            
            if roi.size == 0:
                face_colors.append('U')
                hsv_rois.append(None)
                continue
                
            hsv_rois.append(roi)
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
                
        return face_colors, hsv_rois

    def process_frame(self, frame, calibration_mode=False):
        """
        Process the frame to find a 3x3 Rubik's cube face.
        """
        annotated_frame = frame.copy()
        
        square_contours = self._find_squares(frame)
        sorted_faces = self._group_and_sort_squares(square_contours)
        
        if sorted_faces:
            face_colors, hsv_rois = self._extract_colors_and_draw(
                frame, annotated_frame, sorted_faces, calibration_mode
            )
            return annotated_frame, face_colors, hsv_rois

        return annotated_frame, None, None
