# Anotação Manual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar uma ferramenta retomável para anotar imagens positivas e negativas e usar essas anotações nas métricas geométricas.

**Architecture:** `annotations.py` será o módulo puro de persistência e comparação de grade; `annotation.py` conterá apenas a interface OpenCV. `evaluation.py` carregará registros manuais separadamente das sessões automáticas e agregará presença e grade sem misturar a origem dos exemplos.

**Tech Stack:** Python 3, OpenCV, NumPy, `unittest`, JSON e CSV.

## Global Constraints

- A fila de entrada é `data/to_annotate/`; os registros ficam em `data/annotations.json`.
- Use caminhos relativos à fila nos registros JSON.
- Registros positivos contêm exatamente nove centros em ordem de leitura e nove cores `W/Y/G/B/R/O`.
- A grade é correta quando cada centro previsto correspondente está a até 40% do espaçamento mediano anotado.
- `n`, `y`, `r` e `q` mantêm os comportamentos definidos na especificação.
- Não alterar o pré-processamento padrão nem incluir imagens de dados no Git.

---

### Task 1: Modelo persistente e comparação geométrica

**Files:**
- Create: `annotations.py`
- Create: `tests/test_annotations.py`

**Interfaces:**
- Produces: `AnnotationStore(path)`, `pending_images(input_dir)`, `save(relative_path, has_face, centers=None, expected_colors=None)`.
- Produces: `grid_matches(annotated_centers, predicted_centers, tolerance_ratio=0.4) -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
def test_store_skips_an_image_already_annotated():
    store = AnnotationStore(path)
    store.save('hard.png', has_face=False)
    assert store.pending_images(input_dir) == ['new.png']

def test_grid_match_uses_relative_spacing_tolerance():
    centers = [(0, 0), (10, 0), (20, 0)] * 3
    assert grid_matches(centers, [(3, 0), (13, 0), (23, 0)] * 3)
    assert not grid_matches(centers, [(5, 0), (15, 0), (25, 0)] * 3)
```

- [ ] **Step 2: Run the tests to verify RED**

Run: `& '.\.venv\Scripts\python.exe' -m unittest tests.test_annotations -v`

Expected: import failure because `annotations.py` does not exist.

- [ ] **Step 3: Implement the minimal pure model**

```python
class AnnotationStore:
    def save(self, relative_path, has_face, centers=None, expected_colors=None):
        if has_face and (len(centers) != 9 or len(expected_colors) != 9):
            raise ValueError('Anotações positivas exigem nove centros e nove cores.')

def grid_matches(annotated_centers, predicted_centers, tolerance_ratio=0.4):
    spacing = median_neighbor_spacing(annotated_centers)
    return len(predicted_centers) == 9 and all(
        distance(expected, actual) <= spacing * tolerance_ratio
        for expected, actual in zip(annotated_centers, predicted_centers)
    )
```

- [ ] **Step 4: Run the focused tests to verify GREEN**

Run: `& '.\.venv\Scripts\python.exe' -m unittest tests.test_annotations -v`

Expected: PASS.

### Task 2: Interface de anotação OpenCV

**Files:**
- Create: `annotation.py`
- Modify: `.gitignore`
- Modify: `GUIA_DE_USO.md`
- Test: `tests/test_annotations.py`

**Interfaces:**
- Consumes: `AnnotationStore.pending_images`, `AnnotationStore.save`.
- Produces: `AnnotationController` with `mark_negative`, `start_positive`, `add_center`, `add_color`, `reset_current`.

- [ ] **Step 1: Write failing controller tests**

```python
def test_positive_annotation_requires_nine_clicks_then_nine_colors():
    controller = AnnotationController('hard.png', store)
    controller.start_positive()
    for point in nine_points:
        controller.add_center(point)
    for color in 'WYGBROWYG':
        controller.add_color(color)
    assert store.records['hard.png']['expected_colors'] == list('WYGBROWYG')

def test_negative_annotation_persists_without_centers():
    controller.mark_negative()
    assert store.records['hard.png'] == {'has_face': False}
```

- [ ] **Step 2: Run tests to verify RED**

Run: `& '.\.venv\Scripts\python.exe' -m unittest tests.test_annotations -v`

Expected: import failure because `AnnotationController` does not exist.

- [ ] **Step 3: Implement the controller and CLI**

```python
COLOR_KEYS = {ord('w'): 'W', ord('y'): 'Y', ord('g'): 'G', ord('b'): 'B', ord('r'): 'R', ord('o'): 'O'}

def run_annotation(input_dir='data/to_annotate', output='data/annotations.json'):
    for image_path in AnnotationStore(output).pending_images(input_dir):
        controller = AnnotationController(relative_path(image_path, input_dir), store)
        cv2.setMouseCallback('Annotate', lambda event, x, y, *_: controller.add_center((x, y)) if event == cv2.EVENT_LBUTTONDOWN else None)
        # Key n saves False; y changes controller to center entry; r resets state;
        # q returns; COLOR_KEYS append labels after the ninth center.
```

Add `data/to_annotate/` and `data/annotations.json` to `.gitignore`. Add a
section to `GUIA_DE_USO.md` explaining how to copy images, run
`python annotation.py`, and use the keys.

- [ ] **Step 4: Run focused tests to verify GREEN**

Run: `& '.\.venv\Scripts\python.exe' -m unittest tests.test_annotations -v`

Expected: PASS.

### Task 3: Métricas para anotações manuais

**Files:**
- Modify: `evaluation.py`
- Modify: `tests/test_evaluation.py`
- Modify: `GUIA_DE_USO.md`

**Interfaces:**
- Consumes: `AnnotationStore.records`, `grid_matches`.
- Produces: `evaluate_annotations(records, detector_factory=CubeDetector)` with rates `face_precision`, `face_recall`, `grid_accuracy` e `color_accuracy`.

- [ ] **Step 1: Write failing evaluation tests**

```python
def test_negative_annotation_counts_a_predicted_grid_as_false_positive():
    metrics = evaluate_annotations([negative_record], detector_factory=AlwaysDetectDetector)
    assert metrics['face_precision'] == 0.0

def test_positive_annotation_scores_grid_by_relative_tolerance():
    metrics = evaluate_annotations([positive_record], detector_factory=MatchingGridDetector)
    assert metrics['face_recall'] == 1.0
    assert metrics['grid_accuracy'] == 1.0
```

- [ ] **Step 2: Run tests to verify RED**

Run: `& '.\.venv\Scripts\python.exe' -m unittest tests.test_evaluation -v`

Expected: import failure because `evaluate_annotations` does not exist.

- [ ] **Step 3: Implement metric aggregation and reporting**

```python
def evaluate_annotations(records, detector_factory=CubeDetector):
    counts = {'true_positive': 0, 'false_positive': 0, 'false_negative': 0, 'grid_correct': 0, 'positive': 0}
    # A detected nine-cell grid is a positive prediction. Compare only positive
    # references with grid_matches; compare colors only for a correct grid.
    return rates_from_counts(counts)

def write_report(results, output_dir='data/reports', manual_records=()):
    report = {'results': results, 'manual_annotations': evaluate_annotations(manual_records)}
```

Extend CSV with a `source` column (`automatic` or `manual`) and add manual
metrics to JSON. Keep the existing pre-processing recommendation based only on
the automatic solved-face color base.

- [ ] **Step 4: Run focused tests to verify GREEN**

Run: `& '.\.venv\Scripts\python.exe' -m unittest tests.test_evaluation -v`

Expected: PASS.

### Task 4: Regressão, documentação e commit

**Files:**
- Modify: `README.md`
- Modify: `GUIA_DE_USO.md`
- Modify: `CONTEXT.md` only if implementation reveals a missing term

- [ ] **Step 1: Run the complete suite**

Run: `& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 2: Check generated files and diff formatting**

Run: `git diff --check; git status --short`

Expected: no whitespace errors and no generated data staged.

- [ ] **Step 3: Commit the implementation**

```powershell
git add annotations.py annotation.py evaluation.py tests/test_annotations.py tests/test_evaluation.py .gitignore README.md GUIA_DE_USO.md
git commit -m "feat(data): add manual annotations"
```
