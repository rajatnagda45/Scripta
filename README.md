# Scripta

Scripta converts plain text, PDF, and DOCX inputs into realistic handwritten pages while preserving a modular rendering pipeline:

- Font backend: fast local rendering using Caveat fonts plus `WriterState`
- Neural backend: VATr++ line synthesis with the same layout and artifact pipeline
- Shared layers: input parsing, page compositing, artifact simulation, and Gradio UI

## Current status

- Font backend can run locally on macOS once Python dependencies and fonts are installed.
- Neural backend remains optional and requires an additional `VATr-pp` checkout, style assets, model weights, and a compatible PyTorch install.

## macOS quick start

Recommended:

- Python `3.10` to `3.12` for the broadest package and PyTorch compatibility
- A virtual environment inside the repo

Create the environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Download the required handwriting fonts for the font backend:

```bash
mkdir -p fonts
curl -L https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Regular.ttf -o fonts/Caveat-Regular.ttf
curl -L https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Bold.ttf -o fonts/Caveat-Bold.ttf
```

## Run locally

CLI example:

```bash
source .venv/bin/activate
python main.py --input "Hello from Scripta" --output output/hello.png
```

Gradio app:

```bash
source .venv/bin/activate
python app.py
```

The app listens on `127.0.0.1:7860` by default.

Optional environment variables:

```bash
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT=7860
```

## Neural backend setup

The neural path is intentionally separate from the font backend.

1. Clone `VATr-pp` into the repository root as `VATr-pp/`.
2. Add `VATr-pp/files/vatrpp.pth`.
3. Add `VATr-pp/files/resnet_18_pretrained.pth`.
4. Place the IAM dataset under `data/iam/data_subset/data_subset/`.
5. Prepare style samples:

```bash
source .venv/bin/activate
python scripts/prep_style_samples.py
```

After that, try:

```bash
python main.py --backend neural --input "Hello world" --output output/neural.png
```

## Notes

- Runtime folders such as `output/`, `fonts/`, `pages/`, and `data/iam/` are created automatically.
- If fonts are missing, the font backend will fail with a targeted error message rather than a traceback.
- If VATr++ assets are missing, the neural backend will explain exactly which dependency is absent.
