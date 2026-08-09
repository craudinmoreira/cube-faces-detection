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
    GRID_SCORE_THRESHOLD = 0.78
    RECTIFIED_FACE_SIZE = 300
    RECTIFIED_CELL_SIZE = RECTIFIED_FACE_SIZE // 3
    RECTIFIED_ROI_SIZE = 50
    MAX_HOMOGRAPHY_ERROR = 4.0

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

    @staticmethod
    def _candidate_center(candidate):
        x, y, width, height = candidate[2]
        return np.array([x + width / 2, y + height / 2], dtype=float)

    def _score_grid(self, group, seed_center):
        """Score an ordered, near-frontal 3x3 candidate grid from 0 to 1."""
        ordered_by_y = sorted(group, key=lambda item: self._candidate_center(item)[1])
        rows = [
            sorted(ordered_by_y[index:index + 3], key=lambda item: self._candidate_center(item)[0])
            for index in range(0, 9, 3)
        ]
        centers = np.array(
            [[self._candidate_center(candidate) for candidate in row] for row in rows]
        )
        areas = np.array([candidate[1] for row in rows for candidate in row], dtype=float)
        widths = np.array([candidate[2][2] for row in rows for candidate in row], dtype=float)
        heights = np.array([candidate[2][3] for row in rows for candidate in row], dtype=float)
        tile_width = np.median(widths)
        tile_height = np.median(heights)

        row_alignment_error = np.mean(np.std(centers[:, :, 1], axis=1)) / tile_height
        column_alignment_error = np.mean(np.std(centers[:, :, 0], axis=0)) / tile_width
        row_alignment = np.exp(-4 * row_alignment_error)
        column_alignment = np.exp(-4 * column_alignment_error)

        row_means = np.mean(centers[:, :, 1], axis=1)
        column_means = np.mean(centers[:, :, 0], axis=0)
        vertical_gaps = np.diff(row_means)
        horizontal_gaps = np.diff(column_means)
        if min(vertical_gaps) <= tile_height * 0.75 or min(horizontal_gaps) <= tile_width * 0.75:
            return 0.0, None

        vertical_regular = min(vertical_gaps) / max(vertical_gaps)
        horizontal_regular = min(horizontal_gaps) / max(horizontal_gaps)
        spacing_score = (vertical_regular + horizontal_regular) / 2
        area_score = min(areas) / max(areas)

        grid_center = centers[1, 1]
        seed_distance = np.linalg.norm(seed_center - grid_center)
        center_score = np.exp(-seed_distance / max(tile_width, tile_height))
        score = (
            0.25 * row_alignment
            + 0.25 * column_alignment
            + 0.20 * spacing_score
            + 0.15 * area_score
            + 0.15 * center_score
        )
        return float(score), [candidate for row in rows for candidate in row]

    def _select_best_grid(self, square_contours):
        if len(square_contours) < 9:
            return None, 0.0

        candidate_centers = [self._candidate_center(candidate) for candidate in square_contours]
        best_group = None
        best_score = 0.0
        for seed_index, seed_center in enumerate(candidate_centers):
            distances = [
                (np.linalg.norm(center - seed_center), index)
                for index, center in enumerate(candidate_centers)
            ]
            nearest_indexes = [index for _, index in sorted(distances)[:9]]
            group = [square_contours[index] for index in nearest_indexes]
            score, ordered_group = self._score_grid(group, seed_center)
            if ordered_group is not None and score > best_score:
                best_group = ordered_group
                best_score = score

        return best_group, best_score

    def _group_and_sort_squares(self, square_contours):
        best_group, best_score = self._select_best_grid(square_contours)
        if best_group is None or best_score < self.GRID_SCORE_THRESHOLD:
            return None

        centers = []
        for approx, area, bbox in best_group:
            x, y, w, h = bbox
            centers.append({
                'approx': approx,
                'bbox': bbox,
                'cx': x + w//2,
                'cy': y + h//2
            })
            
        return centers

    def _rectify_face(self, frame, sorted_faces):
        """Warp a detected 3x3 face to a square, front-facing image."""
        if len(sorted_faces) != 9:
            return None

        source_points = np.float32(
            [[face['cx'], face['cy']] for face in sorted_faces]
        )
        target_points = np.float32(
            [
                [
                    column * self.RECTIFIED_CELL_SIZE + self.RECTIFIED_CELL_SIZE / 2,
                    row * self.RECTIFIED_CELL_SIZE + self.RECTIFIED_CELL_SIZE / 2,
                ]
                for row in range(3)
                for column in range(3)
            ]
        )
        homography, inliers = cv2.findHomography(source_points, target_points, cv2.RANSAC, 3.0)
        if homography is None or inliers is None or int(inliers.sum()) != 9:
            return None

        projected_points = cv2.perspectiveTransform(source_points.reshape(-1, 1, 2), homography)
        errors = np.linalg.norm(projected_points.reshape(-1, 2) - target_points, axis=1)
        if float(np.max(errors)) > self.MAX_HOMOGRAPHY_ERROR:
            return None

        return cv2.warpPerspective(
            frame,
            homography,
            (self.RECTIFIED_FACE_SIZE, self.RECTIFIED_FACE_SIZE),
        )

    def _extract_colors_and_draw(self, frame, annotated_frame, sorted_faces, calibration_mode):
        color_smooth = cv2.GaussianBlur(frame, (11, 11), 0)
        rectified_face = self._rectify_face(color_smooth, sorted_faces)
        if rectified_face is None:
            return None, None

        face_colors = []
        rois = []
        roi_offset = (self.RECTIFIED_CELL_SIZE - self.RECTIFIED_ROI_SIZE) // 2

        for index, face_data in enumerate(sorted_faces):
            approx = face_data['approx']
            x, y, w, h = face_data['bbox']
            row, column = divmod(index, 3)
            roi_x = column * self.RECTIFIED_CELL_SIZE + roi_offset
            roi_y = row * self.RECTIFIED_CELL_SIZE + roi_offset
            roi = rectified_face[
                roi_y:roi_y + self.RECTIFIED_ROI_SIZE,
                roi_x:roi_x + self.RECTIFIED_ROI_SIZE,
            ]
            rois.append(roi)
            cx = int(round(face_data['cx']))
            cy = int(round(face_data['cy']))
            
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
            if face_colors is not None:
                return annotated_frame, face_colors, rois

        return annotated_frame, None, None
