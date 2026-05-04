import cv2
import argparse
import time
from vision import CubeDetector
from cube_state import CubeState
from ui import FaceDisplay
from solver_utils import solve_cube

def run_camera():
    cap = cv2.VideoCapture(0)
    detector = CubeDetector()
    state = CubeState()
    ui = FaceDisplay()
    
    # Stability tracking
    history = []
    STABILITY_FRAMES = 5
    
    print("Hold the cube to the camera. Face capturing is automatic.")
    print("Press 'q' to quit at any time.")
    
    solution_moves = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        annotated_frame, face_colors = detector.process_frame(frame)
        
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
    
    annotated_frame, face_colors = detector.process_frame(frame)
    
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
    args = parser.parse_args()
    
    if args.image:
        run_image(args.image)
    else:
        run_camera()
