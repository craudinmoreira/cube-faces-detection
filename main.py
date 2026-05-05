import cv2
import argparse
import time
import numpy as np
from vision import CubeDetector
from cube_state import CubeState
from ui import FaceDisplay
from solver_utils import solve_cube

def calibrate_colors(cap, detector):
    """
    Guides the user to calibrate the 6 colors using a solved cube.
    """
    colors_to_calibrate = [
        ('W', 'White'),
        ('Y', 'Yellow'),
        ('G', 'Green'),
        ('B', 'Blue'),
        ('O', 'Orange'),
        ('R', 'Red')
    ]
    
    calibrated_ranges = {}
    current_idx = 0
    
    log_file = "calibration_log.txt"
    import datetime
    with open(log_file, "a") as f:
        f.write(f"\n--- Calibration Session: {datetime.datetime.now()} ---\n")

    def log_msg(msg):
        print(msg)
        with open(log_file, "a") as f:
            f.write(msg + "\n")

    log_msg("\n--- Color Calibration Mode ---")
    log_msg("Please show a SOLVED face of the cube to the camera.")
    
    while current_idx < len(colors_to_calibrate):
        color_code, color_name = colors_to_calibrate[current_idx]
        
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, hsv_rois = detector.process_frame(frame, calibration_mode=True)
        
        instructions = f"Show SOLVED {color_name} face. Press 'c' to capture."
        cv2.putText(annotated_frame, instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(annotated_frame, "Press 'q' to skip calibration.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        cv2.imshow('Rubik Cube Detection', annotated_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') and hsv_rois and len(hsv_rois) == 9:
            # Calculate min and max HSV for the 9 ROIs
            all_hsv_pixels = []
            for roi in hsv_rois:
                if roi is not None and roi.size > 0:
                    # Reshape to a list of pixels
                    pixels = roi.reshape(-1, 3)
                    all_hsv_pixels.append(pixels)
            
            if all_hsv_pixels:
                all_hsv_pixels = np.vstack(all_hsv_pixels)
                
                # Use percentiles to ignore outliers
                min_hsv = np.percentile(all_hsv_pixels, 5, axis=0)
                max_hsv = np.percentile(all_hsv_pixels, 95, axis=0)
                
                # Add padding
                min_hsv[0] = max(0, min_hsv[0] - 5)   # H padding
                min_hsv[1] = max(50, min_hsv[1] - 30) # S padding
                min_hsv[2] = max(50, min_hsv[2] - 30) # V padding
                
                max_hsv[0] = min(179, max_hsv[0] + 5) # H padding
                max_hsv[1] = min(255, max_hsv[1] + 30)# S padding
                max_hsv[2] = min(255, max_hsv[2] + 30)# V padding
                
                calibrated_ranges[color_code] = [(np.array(min_hsv, dtype=np.uint8), np.array(max_hsv, dtype=np.uint8))]
                print(f"[{color_name}] Calibrated: Min {min_hsv} Max {max_hsv}")
                
                current_idx += 1
                time.sleep(0.5) # small pause
                
        elif key == ord('q'):
            print("Calibration skipped.")
            return False
            
    # Apply calibrated ranges
    detector.color_detector.color_ranges = calibrated_ranges
    print("\nCalibration Complete!")
    print("Scramble your cube. Press 's' to start scanning.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        cv2.putText(frame, "Calibration Complete! Scramble cube.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Press 's' to start scanning.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('Rubik Cube Detection', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            break
        elif key == ord('q'):
            print("Exiting...")
            return False
            
    print("\nTransitioning to Scan Mode...\n")
    return True

import re
import os

def load_calibration_from_log(detector):
    """
    Parses the calibration_log.txt to find the most recent calibration bounds.
    """
    log_file = "calibration_log.txt"
    if not os.path.exists(log_file):
        print("No calibration_log.txt found. Using default colors.")
        return False
        
    color_map = {
        'White': 'W',
        'Yellow': 'Y',
        'Green': 'G',
        'Blue': 'B',
        'Orange': 'O',
        'Red': 'R'
    }
    
    calibrated_ranges = {}
    
    # Read all lines and reverse to find the latest calibration
    with open(log_file, "r") as f:
        lines = f.readlines()
        
    print("Searching for latest calibration in log...")
    
    # Regex to match: [Color] Calibrated: Min [ 67.  50. 127.] Max [ 86.  96. 215.]
    # Handle optional spaces and dots
    pattern = re.compile(r'\[(.*?)\] Calibrated: Min \[\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*\] Max \[\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*\]')
    
    for line in reversed(lines):
        match = pattern.search(line)
        if match:
            color_name = match.group(1)
            if color_name in color_map:
                code = color_map[color_name]
                if code not in calibrated_ranges:
                    min_hsv = np.array([float(match.group(2)), float(match.group(3)), float(match.group(4))], dtype=np.uint8)
                    max_hsv = np.array([float(match.group(5)), float(match.group(6)), float(match.group(7))], dtype=np.uint8)
                    calibrated_ranges[code] = [(min_hsv, max_hsv)]
                    print(f"Found {color_name}: Min {min_hsv} Max {max_hsv}")
                    
        # Stop if we found all 6
        if len(calibrated_ranges) == 6:
            break
            
    if len(calibrated_ranges) > 0:
        detector.color_detector.color_ranges.update(calibrated_ranges)
        print("Successfully loaded calibration from log!")
        return True
    else:
        print("Could not parse calibration data from log. Using defaults.")
        return False

def run_camera(skip_calibration=False):
    cap = cv2.VideoCapture(0)
    detector = CubeDetector()
    state = CubeState()
    ui = FaceDisplay()
    
    if not skip_calibration:
        print("\n==================================")
        print("Rubik's Cube Solver - Startup Menu")
        print("==================================")
        print("1. Run New Color Calibration (Recommended)")
        print("2. Load Last Calibration from Log")
        print("3. Skip Calibration (Use default hardcoded ranges)")
        print("==================================")
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == '1':
            calibrate_colors(cap, detector)
        elif choice == '2':
            load_calibration_from_log(detector)
        else:
            print("Using default hardcoded color ranges.")
    
    # Stability tracking
    history = []
    STABILITY_FRAMES = 5
    
    print("Hold the SCRAMBLED cube to the camera. Face capturing is automatic.")
    print("Press 'q' to quit at any time.")
    
    solution_moves = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, _ = detector.process_frame(frame, calibration_mode=False)
        
        if face_colors and 'U' not in face_colors:
            # Add to history
            history.append(face_colors)
            if len(history) > STABILITY_FRAMES:
                history.pop(0)
                
            # Check stability
            if len(history) == STABILITY_FRAMES and all(x == history[0] for x in history):
                # Face is stable
                center_color = face_colors[4]
                if center_color in state.center_to_face:
                    face_name = state.center_to_face[center_color]
                    if face_name not in state.faces:
                        print(f"Captured {face_name} face!")
                        state.add_face(face_colors)
                        history.clear() # Reset history after capture
                        
                        if state.is_complete() and not solution_moves:
                            print("All faces captured! Solving...")
                            state_str = state.to_54_string()
                            print(f"State String: {state_str}")
                            solution_moves = solve_cube(state_str)
                            print(f"Solution: {' '.join(solution_moves) if isinstance(solution_moves, list) else solution_moves}")
        else:
            history.clear()

        # Display UI
        ui_img = ui.draw(state)
        
        # Display instructions or status on camera feed
        if state.is_complete():
            if isinstance(solution_moves, list):
                sol_str = " ".join(solution_moves)
                # Split long solutions
                if len(sol_str) > 50:
                    cv2.putText(annotated_frame, sol_str[:50], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(annotated_frame, sol_str[50:], (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(annotated_frame, sol_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(annotated_frame, "Solving Failed", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            missing = ", ".join(state.get_missing_faces())
            cv2.putText(annotated_frame, f"Missing: {missing}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow('Rubik Cube Detection', annotated_frame)
        cv2.imshow('Cube Faces', ui_img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def run_image(image_path):
    print(f"Processing image: {image_path}")
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not read image.")
        return
        
    detector = CubeDetector()
    state = CubeState()
    ui = FaceDisplay()
    
    annotated_frame, face_colors, _ = detector.process_frame(frame, calibration_mode=False)
    
    if face_colors:
        print(f"Detected Colors: {face_colors}")
        face_name = state.add_face(face_colors)
        if face_name:
            print(f"Added as {face_name} face.")
    else:
        print("Could not detect a 3x3 face in the image.")
        
    ui_img = ui.draw(state)
    
    cv2.imshow('Rubik Cube Detection', annotated_frame)
    cv2.imshow('Cube Faces', ui_img)
    print("Press any key to exit.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rubik's Cube Solver with OpenCV")
    parser.add_argument("--image", type=str, help="Path to an image to process (optional)")
    parser.add_argument("--skip-calibration", action="store_true", help="Skip color calibration and use default ranges")
    args = parser.parse_args()
    
    if args.image:
        run_image(args.image)
    else:
        run_camera(skip_calibration=args.skip_calibration)
