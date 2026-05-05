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
    
    calibrated_centers_lab = {}
    current_idx = 0
    
    print("\n--- Color Calibration Mode ---")
    print("Please show a SOLVED face of the cube to the camera.")
    
    roi_history = []
    CALIBRATION_FRAMES = 15
    
    while current_idx < len(colors_to_calibrate):
        color_code, color_name = colors_to_calibrate[current_idx]
        
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, bgr_rois = detector.process_frame(frame, calibration_mode=True)
        
        if bgr_rois and len(bgr_rois) == 9 and all(r is not None for r in bgr_rois):
            roi_history.append(bgr_rois)
        else:
            roi_history.clear()
            
        progress = int((len(roi_history) / CALIBRATION_FRAMES) * 100)
        instructions = f"Show SOLVED {color_name} face. Auto-capturing: {progress}%"
        cv2.putText(annotated_frame, instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(annotated_frame, "Press 'q' to skip calibration.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        cv2.imshow('Rubik Cube Detection', annotated_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if len(roi_history) >= CALIBRATION_FRAMES:
            all_lab_pixels = []
            for history_rois in roi_history:
                for roi in history_rois:
                    if roi is not None and roi.size > 0:
                        lab_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
                        pixels = lab_roi.reshape(-1, 3)
                        all_lab_pixels.append(pixels)
            
            if all_lab_pixels:
                all_lab_pixels = np.vstack(all_lab_pixels)
                median_lab = np.median(all_lab_pixels, axis=0)
                calibrated_centers_lab[color_code] = [float(x) for x in median_lab]
                print(f"[{color_name}] Calibrated LAB Center: {median_lab}")
                
            current_idx += 1
            roi_history.clear() # Reset for next color
            time.sleep(1.0) # Pause so user can switch face
                
        elif key in [ord('q'), ord('Q')]:
            print("Calibration skipped.")
            return False
            
    import json
    with open("calibration.json", "w") as f:
        json.dump(calibrated_centers_lab, f, indent=4)
        
    # Apply calibrated centers
    for k, v in calibrated_centers_lab.items():
        detector.color_detector.color_centers_lab[k] = np.array(v)
        
    print("\nCalibration Complete and saved to calibration.json!")
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

import os
import json

def load_calibration_from_log(detector):
    """
    Parses calibration.json to find the most recent calibration bounds.
    """
    log_file = "calibration.json"
    if not os.path.exists(log_file):
        print(f"No {log_file} found. Using default colors.")
        return False
        
    try:
        with open(log_file, "r") as f:
            calibrated_centers = json.load(f)
            
        for code, center in calibrated_centers.items():
            detector.color_detector.color_centers_lab[code] = np.array(center)
            
        print("Successfully loaded calibration from log!")
        return True
    except Exception as e:
        print(f"Could not parse calibration data: {e}. Using defaults.")
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
    STABILITY_FRAMES = 1 # Gather 15 frames for consensus
    
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
