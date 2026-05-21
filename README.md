````md
# Scripta

> Transform plain text, PDFs, and DOCX files into realistic handwritten pages with AI-powered rendering pipelines.

Scripta is a modular handwriting generation system designed to simulate authentic human writing on digital paper.  
It combines procedural rendering, writer-style variation, artifact simulation, and optional neural synthesis into a single developer-friendly workflow.

---

## ✨ Features

### 🖋 Font Rendering Backend
Fast handwriting generation using:
- Caveat-based glyph rendering
- `WriterState` behavioral variation engine
- Baseline drift, spacing variation, and natural imperfections
- Realistic paper + ink simulation

### 🧠 Neural Rendering Backend (Optional)
Experimental VATr++ integration for:
- Neural handwriting synthesis
- Writer-conditioned generation
- Human-like stroke flow and realism
- IAM handwriting dataset support

### 📄 Multi-Format Input
Supports:
- Plain text
- PDF documents
- DOCX files

### 🎨 Realistic Output
Generate:
- Ruled notebook pages
- Multiple handwriting personalities
- Blue/black ink styles
- Scanned-paper aesthetics
- Exportable PNG and PDF outputs

### 🧩 Modular Architecture
Built with isolated rendering layers:
- Input parsing
- Glyph rendering
- Writer variation engine
- Page composition
- Artifact simulation
- Gradio UI

---

# 📸 Preview

Scripta generates realistic handwritten documents like:

- Lecture notes
- Assignments
- Journal pages
- Essays
- Draft manuscripts
- Study material

---

# 🚀 Quick Start (macOS)

## Recommended Environment

- Python `3.10` → `3.12`
- macOS (Apple Silicon supported)
- Virtual environment recommended

---

## 1. Clone the Repository

```bash
git clone <YOUR_REPO_URL>
cd Scripta
```

---

## 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Download Required Fonts

```bash
mkdir -p fonts

curl -L https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Regular.ttf \
-o fonts/Caveat-Regular.ttf

curl -L https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Bold.ttf \
-o fonts/Caveat-Bold.ttf
```

---

# ▶️ Running Scripta

## Launch the Web App

```bash
source .venv/bin/activate
python app.py
```

Open in browser:

```text
http://127.0.0.1:7860
```

---

## CLI Example

```bash
python main.py \
  --input "Hello from Scripta" \
  --output output/hello.png
```

---

# ⚙️ Configuration

Optional environment variables:

```bash
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT=7860
```

---

# 🖌 Handwriting Presets

Scripta includes multiple handwriting personalities:

| Preset | Style |
|---|---|
| Casual · Loose | Relaxed notebook writing |
| Neat · Compact | Organized clean handwriting |
| Flowing · Cursive | Connected flowing strokes |
| Bold · Chunky | Thick expressive letters |
| Sharp · Angular | Technical sharp edges |
| Relaxed · Bouncy | Rounded playful motion |
| Tight · Careful | Precise compact writing |
| Free · Expressive | Loose energetic writing |

---

# 🧠 Neural Backend Setup (Optional)

The neural rendering pipeline is intentionally separated from the lightweight font backend.

## 1. Clone VATr++

```bash
git clone https://github.com/EDM-Research/VATr-pp.git VATr-pp
```

---

## 2. Install VATr++ Dependencies

```bash
cd VATr-pp

pip install -r requirements.txt
pip install msgpack wandb
```

---

## 3. Add Model Weights

Required files:

```text
VATr-pp/files/vatrpp.pth
VATr-pp/files/resnet_18_pretrained.pth
```

---

## 4. Add IAM Dataset

Expected structure:

```text
data/iam/data_subset/data_subset/*.png
```

---

## 5. Prepare Style Samples

Run from the Scripta root:

```bash
source .venv/bin/activate
python scripts/prep_style_samples.py
```

This generates:
- segmented writer samples
- word-level handwriting crops
- neural conditioning assets

---

## 6. Run Neural Rendering

```bash
python main.py \
  --backend neural \
  --input "Hello world" \
  --output output/neural.png
```

---

# 🏗 Project Architecture

```text
Input → WriterState → Renderer → Page Composer
      → Artifact Simulation → Export
```

Core modules:

```text
scripta/
├── input_handler.py
├── glyph_store.py
├── variation_engine.py
├── renderer.py
├── page_compositor.py
├── neural_renderer.py
├── neural_page_compositor.py
└── artifact_sim.py
```

---

# 📂 Runtime Directories

These folders are automatically created when needed:

```text
output/
fonts/
pages/
data/iam/
```

---

# 🛠 Tech Stack

- Python
- Pillow
- OpenCV
- NumPy
- PyTorch
- Gradio
- VATr++
- IAM Handwriting Dataset

---

# ⚠️ Notes

- Font backend works independently without neural dependencies.
- Neural backend requires external assets and model weights.
- Missing dependencies produce clear setup guidance instead of deep tracebacks.
- Apple Silicon users can optionally enable PyTorch MPS acceleration.

---

# 📌 Current Status

### Stable
- Font rendering pipeline
- UI generation flow
- WriterState variation engine
- Paper + ink simulation
- PNG/PDF export

### Experimental
- VATr++ neural synthesis
- IAM style conditioning
- Neural writer cloning

---

# 📜 License

MIT License

---

# 💡 Vision

Scripta aims to become a fully modular AI handwriting synthesis platform for:
- digital note generation
- educational tooling
- synthetic handwriting research
- document realism pipelines
- AI-assisted writing workflows
````
