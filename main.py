import cv2
import argparse
import json
import time
import numpy as np
from datetime import datetime, timezone
from vision import CubeDetector, parse_calibration_data
from cube_state import CubeState
from calibration import CalibrationTracker
from data_collection import DataCollectionSession
from stability import FaceStabilityTracker
from ui import FaceDisplay
from solver_utils import solve_cube


CAPTURE_KEY_TO_FACE = {
    ord('u'): 'U',
    ord('r'): 'R',
    ord('f'): 'F',
    ord('d'): 'D',
    ord('l'): 'L',
    ord('b'): 'B',
}
CAPTURE_LEGEND = (
    "Recapturar: U branco/topo | R vermelho/direita | F verde/frente",
    "D amarelo/baixo | L laranja/esquerda | B azul/tras | Esc cancela",
)

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
    
    calibrated_profiles = {}
    current_idx = 0
    
    print("\n--- Color Calibration Mode ---")
    print("Please show a SOLVED face of the cube to the camera.")
    
    calibration_tracker = CalibrationTracker(
        min_frames=30,
        min_duration_seconds=1.0,
    )
    
    while current_idx < len(colors_to_calibrate):
        color_code, color_name = colors_to_calibrate[current_idx]
        
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, bgr_rois = detector.process_frame(frame, calibration_mode=True)
        
        if bgr_rois and len(bgr_rois) == 9 and all(r is not None for r in bgr_rois):
            lab_samples = np.array(
                [
                    np.median(
                        cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).reshape(-1, 3),
                        axis=0,
                    )
                    for roi in bgr_rois
                ]
            )
            calibrated_center = calibration_tracker.observe(lab_samples)
        else:
            calibration_tracker.reset()
            calibrated_center = None
            
        progress = int(calibration_tracker.progress() * 100)
        instructions = f"Show SOLVED {color_name} face. Auto-capturing: {progress}%"
        cv2.putText(annotated_frame, instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(annotated_frame, "Press 'q' to skip calibration.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        cv2.imshow('Rubik Cube Detection', annotated_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if calibrated_center is not None:
            calibrated_profiles[color_code] = calibration_tracker.profile()
            print(f"[{color_name}] Calibrated LAB Center: {calibrated_center}")
            current_idx += 1
            calibration_tracker.reset()
            time.sleep(1.0) # Pause so user can switch face
                
        elif key in [ord('q'), ord('Q')]:
            print("Calibration skipped.")
            return False
            
    with open("calibration.json", "w") as f:
        json.dump(
            {
                "schema_version": 2,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "camera": {"index": 0},
                "colors": calibrated_profiles,
            },
            f,
            indent=4,
        )
        
    # Apply calibrated centers
    for color, profile in calibrated_profiles.items():
        detector.color_detector.color_centers_lab[color] = np.array(profile["center_lab"])
        
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
            
        centers, legacy = parse_calibration_data(calibrated_centers)
        detector.color_detector.color_centers_lab.update(centers)
        if legacy:
            print("Loaded legacy calibration without variability metrics. Recalibration is recommended.")
        else:
            print("Successfully loaded calibration profile!")
        return True
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Could not parse calibration data: {e}. Using defaults.")
        return False


def draw_capture_legend(frame, pending_face):
    color = (0, 255, 255) if pending_face else (210, 210, 210)
    for index, line in enumerate(CAPTURE_LEGEND):
        cv2.putText(
            frame,
            line,
            (10, 150 + index * 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
        )
    if pending_face:
        cv2.putText(
            frame,
            f"Recaptura pendente: {pending_face}",
            (10, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
        )

def run_camera(skip_calibration=False, debug=False, collect_data=False):
    cap = cv2.VideoCapture(0)
    detector = CubeDetector(debug=debug)
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
    
    stability_tracker = FaceStabilityTracker(
        min_frames=15,
        min_duration_seconds=0.5,
        min_agreement=0.8,
    )
    
    print("Hold the SCRAMBLED cube to the camera. Face capturing is automatic.")
    print("Press 'q' to quit at any time.")
    
    solution_moves = None
    validation_error = None
    correction_report = None
    pending_recapture_face = None
    collection_session = DataCollectionSession() if collect_data else None
    collection_status = None
    if collection_session:
        print(f"Collecting solved-face samples in {collection_session.directory}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors, _ = detector.process_frame(frame, calibration_mode=False)
        if debug:
            debug_state = detector.get_debug_state()
            cv2.putText(annotated_frame, f"Candidates: {debug_state.get('candidate_count', 0)} | Grid: {debug_state.get('grid_score', 0):.2f}", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            rejection_reason = debug_state.get('rejection_reason')
            if rejection_reason:
                cv2.putText(annotated_frame, rejection_reason, (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            for title, image in detector.debug_views.items():
                cv2.imshow(f'Debug: {title}', image)
        
        if face_colors:
            center_color = face_colors[4]
            if center_color != 'U' and center_color in state.center_to_face:
                consensus_colors = stability_tracker.observe(
                    face_colors,
                    color_costs=detector.last_color_costs,
                )
                progress = int(stability_tracker.progress() * 100)
                cv2.putText(
                    annotated_frame,
                    f"Scanning {state.center_to_face[center_color]}... {progress}%",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2,
                )

                if consensus_colors:
                    face_name = state.center_to_face[consensus_colors[4]]
                    if collection_session:
                        saved, collection_status = collection_session.observe(
                            face_name,
                            consensus_colors,
                            frame,
                            detector.debug_views.get('Face retificada'),
                            metadata={'grid_score': detector.debug_state.get('grid_score')},
                        )
                        print(collection_status)
                    can_capture = (
                        face_name not in state.faces
                        or face_name == pending_recapture_face
                    )
                    if can_capture:
                        print(f"Captured {face_name} face!")
                        state.add_face(
                            consensus_colors,
                            stability_tracker.consensus_color_costs(),
                        )
                        stability_tracker.reset()

                        if face_name == pending_recapture_face:
                            pending_recapture_face = None
                            solution_moves = None
                            validation_error = None
                            correction_report = None
                            globals().pop('solution_kociemba', None)

                        if state.is_complete() and not solution_moves:
                            corrected, correction_report, correction_errors = (
                                state.apply_global_color_correction()
                            )
                            if not corrected:
                                validation_error = " ".join(correction_errors)
                                solution_moves = f"Invalid cube state: {validation_error}"
                                print("Global color correction was blocked:")
                                for error in correction_errors:
                                    print(f" - {error}")
                            else:
                                changes = correction_report['changes']
                                if changes:
                                    locations = ", ".join(
                                        f"{face}{position + 1}" for face, position, _, _ in changes
                                    )
                                    print(f"Global color correction adjusted {len(changes)} sticker(s): {locations}")
                                orientations_resolved, orientation_errors, rotations = state.resolve_orientations()
                                if not orientations_resolved:
                                    validation_error = " ".join(orientation_errors)
                                    solution_moves = f"Invalid cube state: {validation_error}"
                                    print("Cube orientation is unresolved. Solving was blocked:")
                                    for error in orientation_errors:
                                        print(f" - {error}")
                                else:
                                    print(f"Resolved face rotations: {rotations}")
                                    print("All faces captured and validated! Solving...")
                                    state_str = state.to_54_string()
                                    print(f"State String: {state_str}")
                                    solution_moves = solve_cube(state_str)
                                    print(f"Solution: {' '.join(solution_moves) if isinstance(solution_moves, list) else solution_moves}")

                                    try:
                                        koc_str = state.to_kociemba_string()
                                        print(f"State String (Kociemba): {koc_str}")
                                        from solver_utils import solve_cube_kociemba
                                        global solution_kociemba
                                        solution_kociemba = solve_cube_kociemba(koc_str)
                                        print(f"Solution (Kociemba): {solution_kociemba}")
                                    except Exception as e:
                                        solution_kociemba = f"Kociemba Error: {e}"
                    else:
                        stability_tracker.reset()
            else:
                stability_tracker.reset()
        else:
            stability_tracker.reset()

        # Display UI
        ui_img = ui.draw(state)
        draw_capture_legend(annotated_frame, pending_recapture_face)
        if collection_session:
            progress = collection_session.progress()
            progress_text = ' '.join(
                f'{color}:{progress.get(color, 0)}/{collection_session.max_samples_per_color}'
                for color in ('W', 'Y', 'G', 'B', 'R', 'O')
            )
            cv2.putText(
                annotated_frame,
                f'Coleta: {progress_text}',
                (10, 290),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 0),
                1,
            )
            if collection_status:
                cv2.putText(
                    annotated_frame,
                    collection_status[:90],
                    (10, 310),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (255, 255, 0),
                    1,
                )
        if correction_report and correction_report['changes']:
            cv2.putText(
                annotated_frame,
                f"Correcao global: {len(correction_report['changes'])} adesivo(s) ajustado(s)",
                (10, 250),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )
            if debug:
                locations = ", ".join(
                    f"{face}{position + 1} {before}>{after}"
                    for face, position, before, after in correction_report['changes']
                )
                cv2.putText(
                    annotated_frame,
                    locations[:90],
                    (10, 270),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (0, 255, 0),
                    1,
                )
        
        # Display instructions or status on camera feed
        if state.is_complete():
            if isinstance(solution_moves, list):
                sol_str = "Std: " + " ".join(solution_moves)
                # Split long solutions
                if len(sol_str) > 50:
                    cv2.putText(annotated_frame, sol_str[:50], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(annotated_frame, sol_str[50:], (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(annotated_frame, sol_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                status = validation_error or "Std Solving Failed"
                cv2.putText(annotated_frame, status[:70], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
                if len(status) > 70:
                    cv2.putText(annotated_frame, status[70:140], (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
                
            if 'solution_kociemba' in globals() and globals()['solution_kociemba']:
                koc_str = "Koc: " + str(globals()['solution_kociemba'])
                if len(koc_str) > 50:
                    cv2.putText(annotated_frame, koc_str[:50], (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    cv2.putText(annotated_frame, koc_str[50:], (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                else:
                    cv2.putText(annotated_frame, koc_str, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            missing = ", ".join(state.get_missing_faces())
            cv2.putText(annotated_frame, f"Missing: {missing}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow('Rubik Cube Detection', annotated_frame)
        cv2.imshow('Cube Faces', ui_img)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == 27 and pending_recapture_face:
            pending_recapture_face = None
            stability_tracker.reset()
            print("Recapture cancelled.")
        elif key in CAPTURE_KEY_TO_FACE:
            pending_recapture_face = CAPTURE_KEY_TO_FACE[key]
            stability_tracker.reset()
            print(f"Recapturing {pending_recapture_face}; previous face is preserved until replacement.")

    cap.release()
    cv2.destroyAllWindows()

def run_image(image_path, debug=False):
    print(f"Processing image: {image_path}")
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not read image.")
        return
        
    detector = CubeDetector(debug=debug)
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
    if debug:
        for title, image in detector.debug_views.items():
            cv2.imshow(f'Debug: {title}', image)
    print("Press any key to exit.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rubik's Cube Solver with OpenCV")
    parser.add_argument("--image", type=str, help="Path to an image to process (optional)")
    parser.add_argument("--skip-calibration", action="store_true", help="Skip color calibration and use default ranges")
    parser.add_argument("--debug", action="store_true", help="Show geometry and rectification diagnostics")
    parser.add_argument(
        "--collect-data",
        action="store_true",
        help="Save deduplicated stable observations of solved faces for evaluation",
    )
    args = parser.parse_args()
    
    if args.image:
        run_image(args.image, debug=args.debug)
    else:
        run_camera(
            skip_calibration=args.skip_calibration,
            debug=args.debug,
            collect_data=args.collect_data,
        )
