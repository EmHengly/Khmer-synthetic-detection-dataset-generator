# Synthetic Khmer Official Document Dataset

This project generates synthetic Khmer ministry and legal documents for word
detection/spotting experiments. It creates PNG page images and YOLO-format
word bounding-box labels.

The generator supports:

- Modern ministry letters
- Legal decrees and official decisions
- Dense Khmer paragraphs and numbered legal sections
- Multi-page PDF-style documents
- Khmer OS Muol titles and headers
- Khmer OS Battambang or Siemreap body text
- Synthetic stamps, signatures, tables, headers, and footers

## 1. Requirements

Use Python 3.10 or newer. The generator requires:

- Pillow with `libraqm` support for correct Khmer shaping
- OpenCV
- NumPy
- Khmer OS font files

Check your Python environment:

```bash
python3 -c "import sys; from PIL import features; print(sys.executable); print(features.check('raqm'))"
```

The final line must print:

```text
True
```

If it prints `False`, the generator stops because Khmer text may render
incorrectly.

## 2. Platform setup

### Windows

Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/)
and enable **Add Python to PATH** during installation. In PowerShell, create a
virtual environment and install the dependencies:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install Pillow numpy opencv-python
```

Recent Pillow Windows wheels normally include RAQM support. Verify it with:

```powershell
python -c "from PIL import features; print(features.check('raqm'))"
```

If PowerShell prevents environment activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate `.venv` again and rerun the verification command.

### Linux (Ubuntu/Debian)

Install Python, the native libraries needed by Pillow, and the Python
dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
  libraqm-dev libharfbuzz-dev libjpeg-dev

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install Pillow numpy opencv-python
```

Verify that Pillow can use RAQM:

```bash
python -c "import sys; from PIL import features; print(sys.executable); print(features.check('raqm'))"
```

If the result is `False`, reinstall Pillow after the native libraries are
installed:

```bash
python -m pip install --force-reinstall --no-cache-dir Pillow
```

### macOS

Install Homebrew libraries:

```bash
brew install libraqm harfbuzz jpeg-turbo
```

Build Pillow with RAQM support:

```bash
export BREW_PREFIX="$(brew --prefix)"
export CFLAGS="-I$BREW_PREFIX/opt/jpeg-turbo/include"
export LDFLAGS="-L$BREW_PREFIX/opt/jpeg-turbo/lib"
export PKG_CONFIG_PATH="$BREW_PREFIX/opt/jpeg-turbo/lib/pkgconfig:$BREW_PREFIX/lib/pkgconfig"

python3 -m pip install --force-reinstall --no-cache-dir --no-binary=Pillow Pillow
```

Install the Python packages:

```bash
python3 -m pip install numpy opencv-python
```

If `python3` points to the Apple system Python, use your Conda interpreter:

```bash
export PATH="/Users/$USER/miniconda3/bin:$PATH"
hash -r
```

Then verify RAQM again.

## 3. Required fonts

The `fonts/` directory must contain:

```text
KhmerOSmuol.ttf
KhmerOSbattambang.ttf
KhmerOSsiemreap.ttf
```

The generator uses:

- `KhmerOSmuol.ttf` for titles, headers, section names, and table headers
- `KhmerOSbattambang.ttf` or `KhmerOSsiemreap.ttf` for body text

## 4. Generate a small test dataset

From the project directory:

```bash
python3 generate_synthetic_ministry_docs.py \
  --num-samples 5 \
  --pages-per-document 1 \
  --layout mixed \
  --font-dir ./fonts \
  --output-dir ./dataset/ministry_synth
```

Inspect the generated images under:

```text
dataset/ministry_synth/images/
```

## 5. Generate multi-page documents

Generate 500 two-page documents using both modern and legal layouts:

```bash
python3 generate_synthetic_ministry_docs.py \
  --num-samples 500 \
  --pages-per-document 2 \
  --layout mixed \
  --font-dir ./fonts \
  --output-dir ./dataset/ministry_synth
```

This creates 1,000 page images. Pages are split randomly into train, validation,
and test sets.

## 6. Layout options

### Mixed layouts

```bash
--layout mixed
```

Randomly combines modern ministry letters and legal documents.

### Modern ministry documents

```bash
--layout modern
```

Generates ministry letters with ministry headers, paragraphs, tables, dates,
stamps, signatures, and footers.

### Legal documents

```bash
--layout legal
```

Generates dense legal-style documents with royal headers, numbered sections,
legal paragraphs, continuation-page headers, signatures, stamps, and footers.

## 7. Output structure

```text
dataset/ministry_synth/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

For multi-page documents, filenames use this format:

```text
document_00000_page_01.png
document_00000_page_01.txt
document_00000_page_02.png
document_00000_page_02.txt
```

Each label line uses the YOLO format:

```text
class_id x_center y_center width height
```

Coordinates are normalized between `0` and `1`. Class `0` is
`khmer_word`.

## 8. Useful commands

Show all options:

```bash
python3 generate_synthetic_ministry_docs.py --help
```

Generate only legal pages for a quick test:

```bash
python3 generate_synthetic_ministry_docs.py \
  --num-samples 10 \
  --pages-per-document 2 \
  --layout legal \
  --font-dir ./fonts \
  --output-dir ./dataset/legal_synth
```

Before regenerating an existing dataset, remove the old output so stale images
and labels are not mixed with the new dataset:

```bash
rm -rf ./dataset/ministry_synth
```

## 9. Troubleshooting

### `Pillow lacks libraqm`

Your active Python environment does not have Khmer shaping support. Install or
rebuild Pillow using the macOS instructions above, then verify:

```bash
python3 -c "from PIL import features; print(features.check('raqm'))"
```

The result must be `True`.

### `Missing required Khmer OS fonts`

Confirm the three required files exist:

```bash
ls -l fonts/KhmerOSmuol.ttf \
      fonts/KhmerOSbattambang.ttf \
      fonts/KhmerOSsiemreap.ttf
```

### `ModuleNotFoundError: cv2`

Install OpenCV in the same environment used to run the generator:

```bash
python3 -m pip install opencv-python
```

### Text still looks incorrect

Check that the command uses the same Python environment for both Pillow and the
generator:

```bash
python3 -c "import sys; from PIL import features; print(sys.executable); print(features.check('raqm'))"
```

Do not use a different Python executable from the one where Pillow was rebuilt.

## 10. YOLO pilot training on Apple Silicon

Ultralytics YOLO can use the Apple GPU through PyTorch MPS. Install the
training packages in the same environment used to generate the dataset:

```bash
python3 -m pip install ultralytics
```

Check MPS support:

```bash
python3 -c "import torch; print(torch.backends.mps.is_available())"
```

Run a short pilot:

```bash
python3 - <<'PY'
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
model.train(
    data="dataset/ministry_synth/data.yaml",
    epochs=10,
    imgsz=640,
    batch=2,
    device="mps",
    workers=0,
    project="runs/khmer_word_spotting",
    name="pilot_yolo11n",
    pretrained=True,
    patience=5,
    plots=True,
)
PY
```

The best checkpoint is saved under:

```text
runs/detect/runs/khmer_word_spotting/pilot_yolo11n/weights/best.pt
```

Evaluate the checkpoint on the test split:

```bash
python3 - <<'PY'
from ultralytics import YOLO

model = YOLO("runs/detect/runs/khmer_word_spotting/pilot_yolo11n/weights/best.pt")
model.val(
    data="dataset/ministry_synth/data.yaml",
    split="test",
    imgsz=640,
    batch=2,
    device="mps",
    workers=0,
    project="runs/khmer_word_spotting",
    name="pilot_test",
    plots=True,
)
PY
```

Run detection on test images and save visualized predictions:

```bash
python3 - <<'PY'
from ultralytics import YOLO

model = YOLO("runs/detect/runs/khmer_word_spotting/pilot_yolo11n/weights/best.pt")
model.predict(
    source="dataset/ministry_synth/images/test",
    imgsz=640,
    conf=0.25,
    device="mps",
    save=True,
    save_txt=True,
    show_labels=False,
    show_conf=False,
    project="runs/khmer_word_spotting",
    name="pilot_predictions",
)
PY
```

`show_labels=False` and `show_conf=False` save images with bounding boxes only.
The detector is word-level because the generator creates one annotation for
each rendered word. The prediction text files still contain the detected box
coordinates and confidence values.

For a real training run after the pilot, increase the dataset size and train
for approximately 50–100 epochs. Keep `workers=0` on macOS if DataLoader
worker processes cause issues. `yolo11n` is suitable for a quick pilot;
`yolo11s` or `yolo11m` may improve accuracy after enough training data is
available.
