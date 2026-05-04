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
        min_pixels_required = (hsv_roi.shape[0] * hsv_roi.shape[1]) * 0.2
        if max_count < min_pixels_required:
            return 'U'
            
        return detected_color

class CubeDetector:
    def __init__(self):
        self.color_detector = ColorDetector()

    def process_frame(self, frame, calibration_mode=False):
        """
        Process the frame to find a 3x3 Rubik's cube face.
        Returns:
            annotated_frame: Frame with drawings
            face_colors: List of 9 color strings ('R', 'G', etc.) if detected, else None.
            hsv_rois: List of the 9 HSV numpy arrays corresponding to the center of each square.
        """
        annotated_frame = frame.copy()
        
        # Apply blur directly on the color image instead of grayscale.
        # This helps detect edges between colors with similar luminance.
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # Lower thresholds to catch the faint plastic creases of stickerless cubes
        edges = cv2.Canny(blurred, 20, 50)
        
        # Dilate edges to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        square_contours = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            
            # Check if it's a quadrilateral
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                # Filter by area to remove noise and huge bounding boxes
                if 1000 < area < 20000:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h
                    # Check if it's roughly square
                    if 0.8 <= aspect_ratio <= 1.2:
                        square_contours.append((approx, area, (x, y, w, h)))

        # Group contours of similar area
        if len(square_contours) >= 9:
            # Sort by area descending
            square_contours.sort(key=lambda x: x[1], reverse=True)
            
            # Find a group of 9 contours with similar areas
            # We use a sliding window approach over the sorted areas
            found_group = None
            for i in range(len(square_contours) - 8):
                group = square_contours[i:i+9]
                max_area = group[0][1]
                min_area = group[-1][1]
                
                # If the smallest area is at least 60% of the largest area, consider it a valid group
                if min_area > max_area * 0.6:
                    found_group = group
                    break
            
            if found_group:
                # We have our 9 squares. Now sort them top-to-bottom, left-to-right.
                # First, extract centers.
                centers = []
                for approx, area, bbox in found_group:
                    x, y, w, h = bbox
                    cx, cy = x + w//2, y + h//2
                    centers.append({
                        'approx': approx,
                        'bbox': bbox,
                        'cx': cx,
                        'cy': cy
                    })
                
                # Sort by Y-coordinate to separate into rows
                centers.sort(key=lambda item: item['cy'])
                
                # Split into 3 rows and sort each row by X-coordinate
                sorted_faces = []
                for row_idx in range(3):
                    row = centers[row_idx*3:(row_idx+1)*3]
                    row.sort(key=lambda item: item['cx'])
                    sorted_faces.extend(row)
                
                # Extract colors and draw
                hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                face_colors = []
                hsv_rois = []
                
                for idx, face_data in enumerate(sorted_faces):
                    approx = face_data['approx']
                    x, y, w, h = face_data['bbox']
                    
                    # Define a smaller ROI inside the square to avoid edges
                    offset_x = int(w * 0.2)
                    offset_y = int(h * 0.2)
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
                        
                        # Draw bounding box and color text
                        bgr_color = self.color_detector.color_bgr.get(detected_color, (255,255,255))
                        cv2.drawContours(annotated_frame, [approx], -1, bgr_color, 3)
                        
                        # Inner center circle
                        cv2.circle(annotated_frame, (cx, cy), 5, bgr_color, -1)
                        cv2.putText(annotated_frame, detected_color, (x, y - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, bgr_color, 2)
                    else:
                        face_colors.append('U')
                        cv2.drawContours(annotated_frame, [approx], -1, (255, 255, 255), 3)
                        cv2.circle(annotated_frame, (cx, cy), 5, (255, 255, 255), -1)
                    
                # If we couldn't detect some colors reliably, we might return None or let caller handle it.
                if 'U' in face_colors and not calibration_mode:
                    pass
                
                return annotated_frame, face_colors, hsv_rois

        return annotated_frame, None, None
