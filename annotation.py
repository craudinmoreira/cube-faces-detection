"""OpenCV interface for manually labeling difficult Rubik face images."""

import argparse
from pathlib import Path

import cv2

from annotations import AnnotationStore
from vision import CubeDetector


COLOR_KEYS = {
    ord('w'): 'W',
    ord('y'): 'Y',
    ord('g'): 'G',
    ord('b'): 'B',
    ord('r'): 'R',
    ord('o'): 'O',
}


class AnnotationController:
    """Keep one image annotation state independent from the OpenCV window."""

    def __init__(self, relative_path, store):
        self.relative_path = relative_path
        self.store = store
        self.reset_current()

    def start_positive(self):
        self.positive_started = True

    def mark_negative(self):
        self.store.save(self.relative_path, has_face=False)

    def add_center(self, point):
        if self.positive_started and len(self.centers) < 9:
            self.centers.append((int(point[0]), int(point[1])))

    def add_color(self, color):
        if self.positive_started and len(self.centers) == 9 and len(self.colors) < 9:
            self.colors.append(color)
        if len(self.colors) == 9:
            self.store.save(
                self.relative_path,
                has_face=True,
                centers=self.centers,
                expected_colors=self.colors,
            )
            return True
        return False

    def reset_current(self):
        self.positive_started = False
        self.centers = []
        self.colors = []

    @property
    def stage(self):
        if not self.positive_started:
            return 'Pressione y para face ou n para negativo.'
        if len(self.centers) < 9:
            return f'Clique centros: {len(self.centers)}/9.'
        return f'Informe cores W/Y/G/B/R/O: {len(self.colors)}/9.'


def _draw_annotation(frame, controller, predicted_centers, index, total):
    view = frame.copy()
    for x, y in predicted_centers:
        cv2.circle(view, (int(x), int(y)), 6, (0, 255, 255), 2)
    for center_number, (x, y) in enumerate(controller.centers, start=1):
        cv2.circle(view, (x, y), 6, (0, 255, 0), -1)
        cv2.putText(view, str(center_number), (x + 8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(view, f'Imagem {index}/{total}: {controller.relative_path}', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(view, controller.stage, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    cv2.putText(view, 'r reinicia | q sai | amarelo = previsao', (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
    return view


def run_annotation(input_dir='data/to_annotate', output='data/annotations.json'):
    root = Path(input_dir)
    store = AnnotationStore(output)
    pending = store.pending_images(root)
    if not pending:
        print('Nenhuma imagem pendente para anotação.')
        return

    detector = CubeDetector(debug=True)
    window = 'Anotacao manual'
    cv2.namedWindow(window)
    for index, relative_path in enumerate(pending, start=1):
        image = cv2.imread(str(root / relative_path))
        if image is None:
            print(f'Não foi possível abrir {relative_path}; ignorada.')
            continue
        detector.process_frame(image)
        predicted_centers = getattr(detector, 'last_grid_centers', ())
        controller = AnnotationController(relative_path, store)

        def on_click(event, x, y, *_):
            if event == cv2.EVENT_LBUTTONDOWN:
                controller.add_center((x, y))

        cv2.setMouseCallback(window, on_click)
        while True:
            cv2.imshow(window, _draw_annotation(image, controller, predicted_centers, index, len(pending)))
            key = cv2.waitKey(20) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                return
            if key == ord('r'):
                controller.reset_current()
            elif key == ord('n') and not controller.positive_started:
                controller.mark_negative()
                break
            elif key == ord('y') and not controller.positive_started:
                controller.start_positive()
            elif key in COLOR_KEYS and len(controller.centers) == 9:
                if controller.add_color(COLOR_KEYS[key]):
                    break
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Anote casos difíceis da visão do cubo')
    parser.add_argument('--input', default='data/to_annotate', help='Pasta com imagens a anotar')
    parser.add_argument('--output', default='data/annotations.json', help='Arquivo JSON de anotações')
    args = parser.parse_args()
    run_annotation(args.input, args.output)


if __name__ == '__main__':
    main()
