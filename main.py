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
    
    roi_history = []
    CALIBRATION_FRAMES = 15
    
    while current_idx < len(colors_to_calibrate):
        color_code, color_name = colors_to_calibrate[current_idx]
        
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, hsv_rois = detector.process_frame(frame, calibration_mode=True)
        
        if hsv_rois and len(hsv_rois) == 9 and all(r is not None for r in hsv_rois):
            roi_history.append(hsv_rois)
        else:
            roi_history.clear()
            
        progress = int((len(roi_history) / CALIBRATION_FRAMES) * 100)
        instructions = f"Show SOLVED {color_name} face. Auto-capturing: {progress}%"
        cv2.putText(annotated_frame, instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(annotated_frame, "Press 'q' to skip calibration.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        cv2.imshow('Rubik Cube Detection', annotated_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if len(roi_history) >= CALIBRATION_FRAMES:
            # Calculate min and max HSV for the 9 ROIs across all accumulated frames
            all_hsv_pixels = []
            for history_rois in roi_history:
                for roi in history_rois:
                    if roi is not None and roi.size > 0:
                        pixels = roi.reshape(-1, 3)
                        all_hsv_pixels.append(pixels)
            
            if all_hsv_pixels:
                all_hsv_pixels = np.vstack(all_hsv_pixels)
                
                # Extract percentiles
                min_hsv = np.percentile(all_hsv_pixels, 5, axis=0)
                max_hsv = np.percentile(all_hsv_pixels, 95, axis=0)
                
                ranges_to_save = []
                
                if color_code == 'W':
                    # White: Hue doesn't matter. It's defined by very low Saturation.
                    # With saturation boost, white might reach up to 100 max, but we must cap it
                    # to prevent it from eating yellow/blue.
                    min_hsv[0] = 0
                    max_hsv[0] = 179
                    min_hsv[1] = 0
                    max_hsv[1] = min(100, max_hsv[1] + 20) # Cap saturation
                    min_hsv[2] = max(80, min_hsv[2] - 30)  # Must be bright
                    max_hsv[2] = 255
                    ranges_to_save.append((np.array(min_hsv, dtype=np.uint8), np.array(max_hsv, dtype=np.uint8)))
                    
                elif color_code == 'R':
                    # Red usually wraps around the 179/0 boundary.
                    # Instead of a single min/max which would span 0 to 179 (eating all colors),
                    # we check if it's wrapping.
                    hues = all_hsv_pixels[:, 0]
                    # If we have both very low hues and very high hues
                    if np.any(hues < 20) and np.any(hues > 160):
                        # Split into two ranges
                        hues_low = hues[hues < 80]
                        hues_high = hues[hues >= 80]
                        
                        min_s = max(0, min_hsv[1] - 30)
                        max_s = min(255, max_hsv[1] + 30)
                        min_v = max(0, min_hsv[2] - 30)
                        max_v = min(255, max_hsv[2] + 30)
                        
                        if len(hues_low) > 0:
                            h_min_low = max(0, np.percentile(hues_low, 5) - 3)
                            h_max_low = np.percentile(hues_low, 95) + 2
                            # Ensure low red doesn't eat orange (orange starts around 8-10 usually, 
                            # but with sat boost we must be careful. Let's cap low red hue at 5).
                            h_max_low = min(5, h_max_low)
                            ranges_to_save.append((
                                np.array([h_min_low, min_s, min_v], dtype=np.uint8),
                                np.array([h_max_low, max_s, max_v], dtype=np.uint8)
                            ))
                        
                        if len(hues_high) > 0:
                            h_min_high = max(165, np.percentile(hues_high, 5) - 4)
                            h_max_high = min(179, np.percentile(hues_high, 95) + 4)
                            ranges_to_save.append((
                                np.array([h_min_high, min_s, min_v], dtype=np.uint8),
                                np.array([h_max_high, max_s, max_v], dtype=np.uint8)
                            ))
                    else:
                        # Standard red (no wrapping observed during calibration)
                        min_hsv[0] = max(0, min_hsv[0] - 3)
                        min_hsv[1] = max(0, min_hsv[1] - 30)
                        min_hsv[2] = max(0, min_hsv[2] - 30)
                        max_hsv[0] = min(179, max_hsv[0] + 3)
                        max_hsv[1] = min(255, max_hsv[1] + 30)
                        max_hsv[2] = min(255, max_hsv[2] + 30)
                        ranges_to_save.append((np.array(min_hsv, dtype=np.uint8), np.array(max_hsv, dtype=np.uint8)))

                else:
                    # Universal padding for O, Y, G, B
                    # Orange is very close to Red, so tighter lower hue bound
                    # Yellow is close to Green, so tighter upper bound for Y, lower bound for G
                    h_pad_low = 1 if color_code in ['O', 'G'] else 3
                    h_pad_high = 1 if color_code == 'Y' else 3
                    
                    min_hsv[0] = max(0, min_hsv[0] - h_pad_low)
                    min_hsv[1] = max(0, min_hsv[1] - 30)
                    min_hsv[2] = max(0, min_hsv[2] - 30)
                    
                    max_hsv[0] = min(179, max_hsv[0] + h_pad_high)
                    max_hsv[1] = min(255, max_hsv[1] + 30)
                    max_hsv[2] = min(255, max_hsv[2] + 30)
                    
                    ranges_to_save.append((np.array(min_hsv, dtype=np.uint8), np.array(max_hsv, dtype=np.uint8)))
                
                calibrated_ranges[color_code] = ranges_to_save
                
                for r in ranges_to_save:
                    log_msg(f"[{color_name}] Calibrated Range: Min {r[0]} Max {r[1]}")
                
                current_idx += 1
                roi_history.clear() # Reset for next color
                time.sleep(1.0) # Pause so user can switch face
                
        elif key in [ord('q'), ord('Q')]:
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
    
    # Stability tracking (Consensus Voting)
    from collections import Counter
    history = []
    STABILITY_FRAMES = 15 # Gather 15 frames for consensus
    
    print("Hold the SCRAMBLED cube to the camera. Face capturing is automatic.")
    print("Press 'q' to quit at any time.")
    
    solution_moves = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, _ = detector.process_frame(frame, calibration_mode=False)
        
        if face_colors:
            center_color = face_colors[4]
            # Only accumulate if we have a valid known center
            if center_color != 'U' and center_color in state.center_to_face:
                # If the center color changes, reset the history
                if history and history[0][4] != center_color:
                    history.clear()
                
                history.append(face_colors)
                
                # Provide visual feedback on capture progress
                progress = int((len(history) / STABILITY_FRAMES) * 100)
                cv2.putText(annotated_frame, f"Scanning {state.center_to_face[center_color]}... {progress}%", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                if len(history) >= STABILITY_FRAMES:
                    # Compute consensus for each of the 9 squares
                    consensus_colors = []
                    for i in range(9):
                        square_colors = [f[i] for f in history]
                        valid_colors = [c for c in square_colors if c != 'U']
                        
                        if not valid_colors:
                            consensus_colors.append('U')
                        else:
                            most_common = Counter(valid_colors).most_common(1)[0][0]
                            consensus_colors.append(most_common)
                            
                    # If consensus is complete and clean
                    if 'U' not in consensus_colors:
                        face_name = state.center_to_face[consensus_colors[4]]
                        if face_name not in state.faces:
                            print(f"Captured {face_name} face!")
                            state.add_face(consensus_colors)
                            history.clear() # Reset history after capture
                            
                            if state.is_complete() and not solution_moves:
                                print("All faces captured! Solving...")
                                state_str = state.to_54_string()
                                print(f"State String: {state_str}")
                                solution_moves = solve_cube(state_str)
                                print(f"Solution: {' '.join(solution_moves) if isinstance(solution_moves, list) else solution_moves}")
                    
                    # Keep the sliding window moving
                    if len(history) > 0:
                        history.pop(0)
            else:
                history.clear()
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
