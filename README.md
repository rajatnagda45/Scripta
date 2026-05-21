<div align="center">

# ✍️ Scripta

### AI-Powered Handwriting Generation System

Transform plain text, PDFs, and DOCX files into realistic handwritten pages with modular rendering pipelines, writer-style simulation, and optional neural handwriting synthesis.

<br>

<img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
<img src="https://img.shields.io/badge/Gradio-UI-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/PyTorch-Neural-red?style=for-the-badge&logo=pytorch" />
<img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" />
<img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-black?style=for-the-badge" />

<br><br>

<img width="100%" alt="Scripta Preview" src="https://placehold.co/1200x600/0f172a/ffffff?text=Scripta+Preview" />

</div>

---

# ✨ Features

## 🖋 Realistic Handwriting Rendering

Generate believable handwritten pages using:

- Writer-style variation engine (`WriterState`)
- Baseline drift & spacing variation
- Ink simulation
- Natural imperfections
- Realistic paper rendering
- PNG & PDF export

---

## 📄 Multi-Format Input Support

Scripta supports:

- Plain text
- PDF documents
- DOCX files

Perfect for:
- assignments
- notes
- essays
- study material
- journals
- handwritten mockups

---

## 🎨 Handwriting Presets

Choose from multiple writer personalities:

| Preset | Description |
|---|---|
| Casual · Loose | Relaxed notebook writing |
| Neat · Compact | Clean organized writing |
| Flowing · Cursive | Connected cursive flow |
| Bold · Chunky | Thick expressive strokes |
| Sharp · Angular | Technical sharp edges |
| Relaxed · Bouncy | Rounded energetic motion |
| Tight · Careful | Precise compact writing |
| Free · Expressive | Loose dynamic handwriting |

---

## 🧠 Neural Backend (Optional)

Experimental VATr++ integration enables:

- Neural handwriting synthesis
- Writer-conditioned generation
- Human-like stroke realism
- IAM handwriting dataset support
- Learned handwriting behavior

---

# 🏗 Architecture

```text
Input Parsing
      ↓
WriterState Variation Engine
      ↓
Glyph / Neural Rendering
      ↓
Page Composition
      ↓
Artifact Simulation
      ↓
PNG / PDF Export
```

---

# 📂 Project Structure

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

# 🚀 Quick Start

## 1. Clone Repository

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

## 4. Download Fonts

```bash
mkdir -p fonts

curl -L https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Regular.ttf \
-o fonts/Caveat-Regular.ttf

curl -L https://raw.githubusercontent.com/googlefonts/caveat/main/fonts/ttf/Caveat-Bold.ttf \
-o fonts/Caveat-Bold.ttf
```

---

# ▶️ Run Scripta

## Launch Web App

```bash
python app.py
```

Open:

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

# ⚙️ Environment Variables

Optional configuration:

```bash
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT=7860
```

---

# 🧠 Neural Backend Setup

> Optional advanced setup for VATr++ neural handwriting synthesis.

## Clone VATr++

```bash
git clone https://github.com/EDM-Research/VATr-pp.git VATr-pp
```

---

## Install VATr++ Dependencies

```bash
cd VATr-pp

pip install -r requirements.txt
pip install msgpack wandb
```

---

## Required Model Files

```text
VATr-pp/files/vatrpp.pth
VATr-pp/files/resnet_18_pretrained.pth
```

---

## IAM Dataset Structure

```text
data/iam/data_subset/data_subset/*.png
```

---

## Prepare Style Samples

```bash
python scripts/prep_style_samples.py
```

---

## Run Neural Rendering

```bash
python main.py \
  --backend neural \
  --input "Hello world" \
  --output output/neural.png
```

---

# 🛠 Tech Stack

| Category | Technology |
|---|---|
| Language | Python |
| UI | Gradio |
| Rendering | Pillow, OpenCV |
| AI | PyTorch |
| Neural Synthesis | VATr++ |
| Dataset | IAM Handwriting |
| Processing | NumPy |

---

# 📦 Runtime Directories

Automatically created when needed:

```text
output/
fonts/
pages/
data/iam/
```

---

# ⚠️ Notes

- Font backend works independently.
- Neural backend is optional.
- Missing assets produce friendly setup errors.
- Apple Silicon supported through PyTorch MPS.
- Designed for modular experimentation and extensibility.

---

# 📌 Current Status

## Stable

- Font rendering pipeline
- UI rendering flow
- WriterState engine
- Paper + ink simulation
- PNG/PDF export

## Experimental

- VATr++ neural synthesis
- Neural writer cloning
- IAM style conditioning

---

# 💡 Vision

Scripta aims to become a modular AI handwriting synthesis platform for:

- digital note generation
- educational tooling
- document realism pipelines
- synthetic handwriting research
- AI-assisted writing workflows

---

<div align="center">

### Built with ❤️ using Python, Gradio, and AI rendering pipelines.

</div>
