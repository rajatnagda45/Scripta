"""
Scripta — Gradio Web UI
Run:  python app.py  →  http://localhost:7860
"""

import os
import time
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import gradio as gr

import config
from scripta.debug_utils import debug_log, timed_stage
from scripta.input_handler import from_file, from_text
from scripta.page_compositor import PAGE_STYLES, PageCompositor


# ---------------------------------------------------------------------------
# Lazy-loaded singletons
# ---------------------------------------------------------------------------

_font_store = None
_neural_renderer = None


def _load_font_store():
    global _font_store
    if _font_store is None:
        from scripta.glyph_store import GlyphStore

        _font_store = GlyphStore()
        _font_store.load(verbose=False)
    return _font_store


def _load_neural_renderer():
    global _neural_renderer
    if _neural_renderer is None:
        from scripta.neural_renderer import NeuralRenderer

        _neural_renderer = NeuralRenderer()
        _neural_renderer.load(verbose=True)
    return _neural_renderer


# ---------------------------------------------------------------------------
# Style metadata
# ---------------------------------------------------------------------------

_FONT_STYLE_DESC = {
    "w01": "Casual · Loose",
    "w02": "Neat · Compact",
    "w03": "Flowing · Cursive",
    "w04": "Bold · Chunky",
    "w05": "Sharp · Angular",
    "w06": "Relaxed · Bouncy",
    "w07": "Tight · Careful",
    "w08": "Free · Expressive",
    "w09": "Straight · Formal",
    "w10": "Slanted · Dynamic",
}
_NEURAL_STYLE_DESC = {
    "a01": "Neat · Precise",
    "a02": "Casual · Flowing",
    "a03": "Cursive · Connected",
    "a05": "Tight · Compact",
    "a06": "Bold · Confident",
    "a07": "Delicate · Fine",
    "a08": "Round · Soft",
    "a09": "Sharp · Angular",
    "a10": "Free · Expressive",
    "a11": "Neat · Organised",
    "a12": "Slanted · Dynamic",
    "a13": "Formal · Careful",
    "a14": "Loose · Natural",
    "a15": "Flowing · Elegant",
    "a16": "Bouncy · Playful",
    "a17": "Straight · Direct",
    "a18": "Connected · Cursive",
    "a19": "Fine · Delicate",
    "a20": "Bold · Strong",
    "a21": "Casual · Relaxed",
    "a22": "Tight · Precise",
    "a23": "Round · Soft",
    "a24": "Angular · Sharp",
    "a25": "Flowing · Smooth",
}
_ALL_STYLE_DESC = {**_FONT_STYLE_DESC, **_NEURAL_STYLE_DESC}

_STYLE_SWATCHES = [
    "swatch-a",
    "swatch-b",
    "swatch-c",
    "swatch-d",
    "swatch-e",
    "swatch-f",
]


# ---------------------------------------------------------------------------
# Writer discovery
# ---------------------------------------------------------------------------

def _discover_font_writers() -> List[str]:
    try:
        return sorted(_load_font_store().writers)
    except Exception:
        return [f"w{i:02d}" for i in range(1, 11)]


def _discover_neural_writers() -> List[str]:
    try:
        from scripta.neural_renderer import STYLE_DIR

        if STYLE_DIR.exists():
            return sorted(d.name for d in STYLE_DIR.iterdir() if d.is_dir())
    except Exception:
        pass
    return []


FONT_WRITERS = _discover_font_writers()
NEURAL_WRITERS = _discover_neural_writers()
NEURAL_AVAILABLE = bool(NEURAL_WRITERS)


def _font_choices() -> List[Tuple[str, str]]:
    return [(f"{_FONT_STYLE_DESC.get(w, w)}  [{w}]", w) for w in FONT_WRITERS]


def _neural_choices() -> List[Tuple[str, str]]:
    return [(f"{_NEURAL_STYLE_DESC.get(w, w)}  [{w}]", w) for w in NEURAL_WRITERS]


def _style_ids_for_backend(backend: str) -> List[str]:
    return NEURAL_WRITERS if backend == "realistic" else FONT_WRITERS


def _style_choices_for_backend(backend: str) -> List[Tuple[str, str]]:
    return _neural_choices() if backend == "realistic" else _font_choices()


def _style_card_choices_for_backend(backend: str) -> List[Tuple[str, str]]:
    return [(_style_label(writer_id) + f" · {writer_id}", writer_id) for writer_id in _style_ids_for_backend(backend)]


def _preset_button_defs_for_backend(backend: str) -> List[Tuple[str, str, str]]:
    writer_ids = _style_ids_for_backend(backend)[:8]
    return [
        (writer_id, _style_label(writer_id), _STYLE_SWATCHES[idx % len(_STYLE_SWATCHES)])
        for idx, writer_id in enumerate(writer_ids)
    ]


def _preset_button_updates_for_backend(backend: str) -> List[dict]:
    defs = _preset_button_defs_for_backend(backend)
    updates = []
    for idx in range(8):
        if idx < len(defs):
            writer_id, label, _swatch = defs[idx]
            updates.append(gr.update(value=f"{label}\n{writer_id.upper()}", visible=True))
        else:
            updates.append(gr.update(value="", visible=False))
    return updates


def _paper_button_defs() -> List[Tuple[str, str]]:
    return [
        ("ruled", "Ruled"),
        ("college", "College"),
        ("grid", "Grid"),
        ("blank", "Blank"),
        ("parchment", "Parchment"),
    ]


def _ink_button_defs() -> List[Tuple[str, str]]:
    return [
        ("blue", "Blue Ink"),
        ("black", "Black Ink"),
        ("pencil", "Pencil"),
    ]


def _style_label(writer_id: Optional[str]) -> str:
    if not writer_id:
        return "Pick a style"
    return _ALL_STYLE_DESC.get(writer_id, writer_id)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _hero_html() -> str:
    realistic_badge = "Neural handwriting available" if NEURAL_AVAILABLE else "Font rendering ready"
    return f"""
    <section class="hero-shell">
      <div class="hero-copy">
        <span class="eyebrow">AI handwriting studio</span>
        <h1>Scripta</h1>
        <p>
          Turn text, PDFs, and DOCX files into believable handwritten pages with
          writer-aware variation, paper simulation, and premium export flow.
        </p>
        <div class="hero-badges">
          <span>WriterState variation</span>
          <span>Artifact simulation</span>
          <span>{realistic_badge}</span>
        </div>
      </div>
      <div class="hero-aside">
        <div class="hero-stat">
          <strong>2</strong>
          <span>Rendering backends</span>
        </div>
        <div class="hero-stat">
          <strong>5</strong>
          <span>Paper styles</span>
        </div>
        <div class="hero-stat">
          <strong>{len(FONT_WRITERS) + len(NEURAL_WRITERS)}</strong>
          <span>Total writer presets</span>
        </div>
      </div>
    </section>
    """


def _panel_title(eyebrow: str, title: str, subtitle: str) -> str:
    return f"""
    <div class="panel-head">
      <span>{eyebrow}</span>
      <h3>{title}</h3>
      <p>{subtitle}</p>
    </div>
    """


def _upload_cards_html() -> str:
    return """
    <div class="upload-grid">
      <div class="upload-card">
        <span class="upload-icon">TXT</span>
        <strong>Notes & prompts</strong>
        <p>Quick drafts, lists, and direct text prompts.</p>
      </div>
      <div class="upload-card">
        <span class="upload-icon">PDF</span>
        <strong>Essays & scans</strong>
        <p>Extract text from paginated documents for handwriting conversion.</p>
      </div>
      <div class="upload-card">
        <span class="upload-icon">DOCX</span>
        <strong>Formatted docs</strong>
        <p>Bring in classroom notes, reports, and polished writing.</p>
      </div>
    </div>
    """


def _preview_placeholder_html() -> str:
    return """
    <div class="empty-state">
      <div class="empty-illustration">✍</div>
      <h3>No render yet</h3>
      <p>Choose a writer, drop in text or a document, and generate a polished handwritten page.</p>
    </div>
    """


def _idle_status_markdown() -> str:
    return (
        "Configure your handwriting, then generate a page to preview exports, compare styles, "
        "and download PNG or PDF outputs."
    )


def _build_summary_html(
    mode_label: str,
    style_label: str,
    page_style: str,
    ink_color: str,
    total_words: int,
    page_count: int,
) -> str:
    return f"""
    <div class="summary-grid">
      <div class="summary-card">
        <span>Mode</span>
        <strong>{mode_label}</strong>
      </div>
      <div class="summary-card">
        <span>Style</span>
        <strong>{style_label}</strong>
      </div>
      <div class="summary-card">
        <span>Paper</span>
        <strong>{page_style.title()}</strong>
      </div>
      <div class="summary-card">
        <span>Ink</span>
        <strong>{ink_color.title()}</strong>
      </div>
      <div class="summary-card">
        <span>Words</span>
        <strong>{total_words}</strong>
      </div>
      <div class="summary-card">
        <span>Pages</span>
        <strong>{page_count}</strong>
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _save_pdf(pages: List, out_path: Path) -> None:
    debug_log("exports", f"saving PDF to {out_path}")
    if len(pages) == 1:
        pages[0].save(str(out_path), "PDF", resolution=config.PAGE_DPI)
    else:
        pages[0].save(
            str(out_path),
            "PDF",
            resolution=config.PAGE_DPI,
            save_all=True,
            append_images=pages[1:],
        )


def _save_exports(pages: List) -> Tuple[str, str]:
    with timed_stage("exports", "save exports"):
        config.ensure_runtime_dirs()
        out_dir = config.OUTPUT_DIR
        debug_log("exports", f"output directory ready at {out_dir}")
        pdf_path = out_dir / "scripta_output.pdf"
        _save_pdf(pages, pdf_path)

        if len(pages) == 1:
            png_path = out_dir / "scripta_output.png"
            debug_log("exports", f"saving single-page PNG to {png_path}")
            pages[0].save(str(png_path))
            debug_log("exports", f"wrote files exists? png={png_path.exists()} pdf={pdf_path.exists()}")
            return str(png_path), str(pdf_path)

        zip_path = out_dir / "scripta_output_pngs.zip"
        debug_log("exports", f"saving multi-page PNG zip to {zip_path}")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for index, page in enumerate(pages, start=1):
                png_path = out_dir / f"scripta_output_p{index}.png"
                page.save(str(png_path))
                zf.write(png_path, arcname=png_path.name)
        debug_log("exports", f"wrote files exists? zip={zip_path.exists()} pdf={pdf_path.exists()}")
        return str(zip_path), str(pdf_path)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def on_backend_change(backend: str):
    choices = _style_choices_for_backend(backend)
    value = choices[0][1] if choices else None
    info = (
        "Authentic pen-stroke styles with VATr++ synthesis"
        if backend == "realistic"
        else "Fast font rendering shaped by WriterState variation"
    )
    debug_log("ui", f"backend changed to {backend}; default writer={value}")
    return (
        gr.update(choices=choices, value=value, info=info),
        value,
        *_preset_button_updates_for_backend(backend),
    )


def on_style_dropdown_change(writer_style: Optional[str]):
    debug_log("ui", f"writer dropdown changed to {writer_style}")
    return gr.update(value=writer_style), writer_style


def on_preset_button_click(backend: str, preset_index: int):
    writer_ids = _style_ids_for_backend(backend)
    writer_id = writer_ids[preset_index] if preset_index < len(writer_ids) else None
    debug_log("ui", f"writer preset button clicked: backend={backend} slot={preset_index} writer={writer_id}")
    return gr.update(value=writer_id), writer_id


def on_paper_button_click(page_style: str):
    debug_log("ui", f"paper button clicked: {page_style}")
    return gr.update(value=page_style), page_style


def on_ink_button_click(ink_color: str):
    debug_log("ui", f"ink button clicked: {ink_color}")
    return gr.update(value=ink_color), ink_color


def on_page_style_change(page_style: str):
    debug_log("ui", f"page style changed to {page_style}")


def on_ink_color_change(ink_color: str):
    debug_log("ui", f"ink color changed to {ink_color}")


def generate(
    input_text,
    input_file,
    backend,
    writer_style,
    selected_writer,
    page_style,
    ink_color,
    apply_artifacts,
    seed_raw,
    progress=gr.Progress(),
):
    with timed_stage("gradio", "generate callback"):
        t0 = time.time()
        seed = int(seed_raw) if seed_raw not in (None, "", 0) else None
        available_writers = _style_ids_for_backend(backend)
        resolved_writer = writer_style if writer_style in available_writers else selected_writer
        if resolved_writer not in available_writers:
            resolved_writer = available_writers[0] if available_writers else None
        if writer_style != selected_writer:
            debug_log(
                "ui",
                f"writer state mismatch dropdown={writer_style} state={selected_writer}; "
                f"resolved={resolved_writer}",
            )
        debug_log(
            "gradio",
            f"request backend={backend} dropdown_writer={writer_style} state_writer={selected_writer} "
            f"resolved_writer={resolved_writer} page={page_style} "
            f"ink={ink_color} artifacts={apply_artifacts} seed={seed}",
        )

        progress(0.02, desc="Reading your content")
        if input_file is not None:
            try:
                path = Path(str(input_file))
                debug_log("input", f"parsing uploaded file {path}")
                paragraphs = from_file(path)
            except Exception as exc:
                return (
                    None,
                    [],
                    None,
                    None,
                    f"❌ Couldn't read the uploaded file: {exc}",
                    _preview_placeholder_html(),
                    "",
                )
        elif input_text and input_text.strip():
            debug_log("input", f"parsing text input chars={len(input_text.strip())}")
            paragraphs = from_text(input_text.strip())
        else:
            return (
                None,
                [],
                None,
                None,
                "⚠️ Add text or upload a TXT, PDF, or DOCX file to get started.",
                _preview_placeholder_html(),
                "",
            )

        if not any(paragraphs):
            return (
                None,
                [],
                None,
                None,
                "⚠️ The input appears to be empty after parsing.",
                _preview_placeholder_html(),
                "",
            )

        total_words = sum(len(p) for p in paragraphs)
        debug_log("input", f"parsed paragraphs={len(paragraphs)} total_words={total_words}")
        use_realistic = backend == "realistic"
        mode_label = "Realistic" if use_realistic else "Instant"

        progress(0.12, desc="Preparing the writer profile")
        try:
            if use_realistic:
                from scripta.neural_page_compositor import NeuralPageCompositor

                debug_log("writer", "loading neural renderer")
                nr = _load_neural_renderer()
                available = nr.available_styles()
                style_id = resolved_writer if resolved_writer in available else (available[0] if available else None)
                if not style_id:
                    return (
                        None,
                        [],
                        None,
                        None,
                        "❌ Realistic mode is unavailable. Add VATr++ assets or switch to Instant.",
                        _preview_placeholder_html(),
                        "",
                    )

                debug_log("writer", f"using neural style {style_id}")
                nr.set_style(style_id)
                compositor = NeuralPageCompositor(
                    neural_renderer=nr,
                    writer_id=style_id,
                    ink_color=ink_color,
                    page_style=page_style,
                    apply_artifacts=apply_artifacts,
                    seed=seed,
                )
            else:
                debug_log("writer", "loading font store")
                store = _load_font_store()
                writer_ids = sorted(store.writers)
                style_id = resolved_writer if resolved_writer in writer_ids else (writer_ids[0] if writer_ids else None)
                debug_log("writer", f"using font style {style_id}")
                compositor = PageCompositor(
                    glyph_store=store,
                    writer_id=style_id,
                    ink_color=ink_color,
                    page_style=page_style,
                    apply_artifacts=apply_artifacts,
                    seed=seed,
                )

            style_desc = _style_label(style_id)
            debug_log("render-debug", f"selected preset name={style_desc}")
            debug_log("render-debug", f"selected writer id={style_id}")
            debug_log("render-debug", f"render backend={backend}")
            debug_log(
                "render-debug",
                f"style parameters page_style={page_style} ink={ink_color} "
                f"apply_artifacts={apply_artifacts}",
            )
            debug_log("render-debug", f"variation seed/state={compositor.writer_state.debug_snapshot()}")
            if use_realistic:
                debug_log(
                    "render-debug",
                    f"renderer sync neural_style={nr.current_style} writer_state={compositor.writer_state.writer_id}",
                )
            else:
                debug_log(
                    "render-debug",
                    f"renderer sync renderer_writer={compositor.renderer.state.writer_id}",
                )

            progress(0.34, desc="Rendering handwritten pages")
            debug_log("gradio", "starting compositor.render")
            pages = compositor.render(paragraphs)
            debug_log("gradio", f"compositor.render returned {len(pages)} page(s)")

            if not pages:
                raise RuntimeError("Rendering completed without producing any page images.")

            debug_log("gradio", f"preview object type={type(pages[0]).__name__} size={getattr(pages[0], 'size', None)}")

            progress(0.82, desc="Packaging exports")
            png_export, pdf_export = _save_exports(pages)
            elapsed = time.time() - t0

            preview = pages[0]
            gallery = pages
            status = (
                f"✅ Generated {len(pages)} page{'s' if len(pages) != 1 else ''} in {elapsed:.1f}s. "
                f"{style_desc} · {mode_label} · {ink_color.title()} ink."
            )
            summary = _build_summary_html(
                mode_label=mode_label,
                style_label=style_desc,
                page_style=page_style,
                ink_color=ink_color,
                total_words=total_words,
                page_count=len(pages),
            )

            debug_log("gradio", f"returning callback payload png={png_export} pdf={pdf_export}")
            progress(1.0, desc="Ready to preview and download")
            return (
                preview,
                gallery,
                png_export,
                pdf_export,
                status,
                "",
                summary,
            )

        except Exception as exc:
            import traceback

            debug_log("gradio", f"callback failed: {exc}")
            return (
                None,
                [],
                None,
                None,
                f"❌ Error while rendering: {exc}\n```\n{traceback.format_exc()}\n```",
                _preview_placeholder_html(),
                "",
            )


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

_theme = gr.themes.Base(
    primary_hue="sky",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Space Grotesk"), "ui-sans-serif", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace", "monospace"],
).set(
    body_text_size="15px",
    block_radius="20px",
    block_border_width="1px",
    input_radius="14px",
    button_large_radius="16px",
    button_large_text_weight="700",
)


CSS = """
:root {
    color-scheme: light;
    --bg: #f4f7fb;
    --bg-elevated: rgba(255,255,255,0.82);
    --panel: rgba(255,255,255,0.86);
    --panel-strong: #ffffff;
    --line: rgba(148,163,184,0.20);
    --line-strong: rgba(71,85,105,0.18);
    --text: #0f172a;
    --muted: #526077;
    --soft: #6b7a91;
    --accent: #0f766e;
    --accent-2: #2563eb;
    --accent-glow: rgba(37,99,235,0.16);
    --shadow: 0 20px 50px rgba(15,23,42,0.08);
    --hero: linear-gradient(135deg, #071129 0%, #0f1b3d 45%, #123267 100%);
}

@media (prefers-color-scheme: dark) {
    :root {
        color-scheme: dark;
        --bg: #08111f;
        --bg-elevated: rgba(10,18,34,0.82);
        --panel: rgba(10,18,34,0.90);
        --panel-strong: #0d1729;
        --line: rgba(148,163,184,0.18);
        --line-strong: rgba(148,163,184,0.24);
        --text: #e5eefc;
        --muted: #b3c0d5;
        --soft: #8ea0bb;
        --accent: #5eead4;
        --accent-2: #60a5fa;
        --accent-glow: rgba(96,165,250,0.18);
        --shadow: 0 24px 60px rgba(0,0,0,0.34);
        --hero: linear-gradient(135deg, #020617 0%, #0b1730 45%, #0f3460 100%);
    }
}

html, body, .gradio-container {
    background:
        radial-gradient(circle at top left, rgba(37,99,235,0.12), transparent 30%),
        radial-gradient(circle at top right, rgba(15,118,110,0.10), transparent 25%),
        var(--bg) !important;
    color: var(--text) !important;
}

body {
    font-feature-settings: "ss01" on, "cv02" on;
}

footer {
    display: none !important;
}

.gradio-container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    padding: 24px 24px 48px !important;
}

.block, .form, fieldset {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    box-shadow: var(--shadow) !important;
    backdrop-filter: blur(18px);
}

label span, .label-wrap span, p, .prose, h1, h2, h3, h4, h5, h6 {
    color: var(--text) !important;
}

.block-info, .panel-head p, .summary-card span, .style-copy span {
    color: var(--muted) !important;
}

textarea, input[type="text"], input[type="number"], select {
    background: var(--panel-strong) !important;
    color: var(--text) !important;
    border-color: var(--line-strong) !important;
}

textarea::placeholder, input::placeholder {
    color: var(--soft) !important;
}

#app-shell {
    gap: 20px !important;
}

.hero-shell {
    display: grid;
    grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.8fr);
    gap: 22px;
    padding: 28px;
    border-radius: 28px;
    background: var(--hero);
    color: #f8fbff;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 30px 80px rgba(2,6,23,0.30);
}

.hero-shell::before,
.hero-shell::after {
    content: "";
    position: absolute;
    border-radius: 999px;
    pointer-events: none;
}

.hero-shell::before {
    width: 260px;
    height: 260px;
    top: -110px;
    right: -40px;
    background: radial-gradient(circle, rgba(125,211,252,0.25), transparent 70%);
}

.hero-shell::after {
    width: 200px;
    height: 200px;
    bottom: -80px;
    left: 35%;
    background: radial-gradient(circle, rgba(94,234,212,0.18), transparent 70%);
}

.hero-copy, .hero-aside {
    position: relative;
    z-index: 1;
}

.eyebrow {
    display: inline-block;
    margin-bottom: 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(191,219,254,0.88);
}

.hero-copy h1 {
    margin: 0;
    font-size: clamp(2.5rem, 5vw, 4.4rem);
    line-height: 0.96;
    letter-spacing: -0.05em;
    color: #ffffff !important;
}

.hero-copy p {
    max-width: 720px;
    margin: 16px 0 0;
    font-size: 1rem;
    line-height: 1.7;
    color: rgba(226,232,240,0.88) !important;
}

.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 20px;
}

.hero-badges span,
.hero-stat {
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
}

.hero-badges span {
    padding: 10px 14px;
    border-radius: 999px;
    font-size: 12px;
    color: rgba(239,246,255,0.96);
}

.hero-aside {
    display: grid;
    gap: 12px;
    align-content: end;
}

.hero-stat {
    padding: 16px 18px;
    border-radius: 18px;
}

.hero-stat strong {
    display: block;
    font-size: 1.5rem;
    color: #ffffff;
}

.hero-stat span {
    font-size: 12px;
    color: rgba(226,232,240,0.82);
}

#main-row {
    gap: 20px !important;
    align-items: flex-start !important;
}

#ctrl-panel, #preview-panel {
    gap: 18px !important;
}

.panel-head {
    display: grid;
    gap: 6px;
    margin-bottom: 14px;
}

.panel-head span {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--soft) !important;
}

.panel-head h3 {
    margin: 0;
    font-size: 1.15rem;
    letter-spacing: -0.03em;
}

.panel-head p {
    margin: 0;
    font-size: 0.92rem;
    line-height: 1.55;
}

.section-stack {
    gap: 12px !important;
}

.upload-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 14px;
}

.upload-card {
    padding: 14px;
    border-radius: 16px;
    border: 1px solid var(--line);
    background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04));
}

.upload-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 42px;
    padding: 8px 10px;
    border-radius: 12px;
    background: var(--accent-glow);
    color: var(--accent-2);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}

.upload-card strong {
    display: block;
    font-size: 0.95rem;
    color: var(--text);
}

.upload-card p {
    margin: 6px 0 0;
    font-size: 0.82rem;
    line-height: 1.5;
    color: var(--muted) !important;
}

#text-input textarea {
    min-height: 220px !important;
    line-height: 1.7 !important;
    font-size: 0.96rem !important;
    resize: vertical !important;
}

#quality-radio .wrap {
    gap: 10px !important;
}

#quality-radio label {
    flex: 1 !important;
    border: 1px solid var(--line) !important;
    background: var(--panel-strong) !important;
    border-radius: 16px !important;
    padding: 14px 16px !important;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
}

#quality-radio label:hover {
    transform: translateY(-1px);
    border-color: var(--accent-2) !important;
    box-shadow: 0 12px 30px rgba(37,99,235,0.10);
}

#quality-radio input[type="radio"]:checked + span,
#quality-radio .selected {
    color: var(--accent-2) !important;
    font-weight: 700 !important;
}

.style-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.preset-button-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.option-button-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.preset-button {
    min-height: 118px !important;
}

.preset-button button {
    width: 100% !important;
    min-height: 118px !important;
    padding: 20px 22px !important;
    border-radius: 22px !important;
    border: 1px solid var(--line) !important;
    background: var(--panel-strong) !important;
    color: var(--text) !important;
    box-shadow: none !important;
    overflow: hidden !important;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
    white-space: pre-line !important;
    line-height: 1.5 !important;
    text-align: left !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}

.preset-button button:hover {
    transform: translateY(-1px);
    border-color: rgba(37,99,235,0.45) !important;
    box-shadow: 0 16px 32px rgba(37,99,235,0.12) !important;
}

.option-button button {
    border-radius: 16px !important;
    border: 1px solid var(--line) !important;
    background: var(--panel-strong) !important;
    color: var(--text) !important;
    box-shadow: none !important;
    padding: 12px 16px !important;
    min-width: 120px !important;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
}

.option-button button:hover {
    transform: translateY(-1px);
    border-color: rgba(37,99,235,0.45) !important;
    box-shadow: 0 12px 24px rgba(37,99,235,0.10) !important;
}

#style-card-picker .wrap {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px !important;
    overflow: visible !important;
}

#style-card-picker label {
    min-height: 84px;
    align-items: flex-start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    white-space: normal !important;
    border: 1px solid var(--line) !important;
    background: var(--panel-strong) !important;
    border-radius: 18px !important;
    padding: 14px !important;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
    cursor: pointer !important;
    position: relative;
    z-index: 2;
    pointer-events: auto !important;
}

#style-card-picker label:hover {
    transform: translateY(-1px);
    border-color: rgba(37,99,235,0.45) !important;
    box-shadow: 0 16px 32px rgba(37,99,235,0.12);
}

#style-card-picker label span {
    line-height: 1.45 !important;
    font-size: 0.88rem !important;
    color: var(--text) !important;
    pointer-events: none !important;
}

#style-card-picker input[type="radio"]:checked + span,
#style-card-picker .selected {
    color: var(--accent-2) !important;
    font-weight: 700 !important;
}

#page-style-picker .wrap,
#ink-color-picker .wrap {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
}

#page-style-picker label,
#ink-color-picker label {
    border: 1px solid var(--line) !important;
    background: var(--panel-strong) !important;
    border-radius: 14px !important;
    padding: 12px 14px !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
}

#page-style-picker label:hover,
#ink-color-picker label:hover {
    transform: translateY(-1px);
    border-color: rgba(37,99,235,0.45) !important;
    box-shadow: 0 12px 24px rgba(37,99,235,0.10);
}

#page-style-picker input[type="radio"]:checked + span,
#ink-color-picker input[type="radio"]:checked + span,
#page-style-picker .selected,
#ink-color-picker .selected {
    color: var(--accent-2) !important;
    font-weight: 700 !important;
}

#ctrl-panel .block,
#ctrl-panel fieldset,
#ctrl-panel .form {
    overflow: visible !important;
}

.style-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    border-radius: 18px;
    border: 1px solid var(--line);
    background: var(--panel-strong);
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.style-card.selected {
    transform: translateY(-1px);
    border-color: rgba(37,99,235,0.45);
    box-shadow: 0 16px 32px rgba(37,99,235,0.12);
}

.style-mark {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    flex: 0 0 auto;
    border: 1px solid rgba(255,255,255,0.20);
}

.swatch-a { background: linear-gradient(135deg, #c4b5fd, #7c3aed); }
.swatch-b { background: linear-gradient(135deg, #7dd3fc, #2563eb); }
.swatch-c { background: linear-gradient(135deg, #86efac, #0f766e); }
.swatch-d { background: linear-gradient(135deg, #fdba74, #ea580c); }
.swatch-e { background: linear-gradient(135deg, #f9a8d4, #db2777); }
.swatch-f { background: linear-gradient(135deg, #fde68a, #ca8a04); }

.style-copy {
    display: grid;
    gap: 4px;
}

.style-copy strong {
    font-size: 0.92rem;
    color: var(--text);
}

.style-copy span {
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.style-empty,
.empty-state {
    padding: 24px;
    border-radius: 20px;
    border: 1px dashed var(--line-strong);
    background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
    text-align: center;
}

.style-empty strong,
.empty-state h3 {
    display: block;
    margin: 0;
    color: var(--text);
}

.style-empty p,
.empty-state p {
    margin: 8px 0 0;
    color: var(--muted) !important;
    line-height: 1.6;
}

.empty-illustration {
    width: 68px;
    height: 68px;
    margin: 0 auto 14px;
    border-radius: 20px;
    display: grid;
    place-items: center;
    font-size: 1.8rem;
    background: var(--accent-glow);
    color: var(--accent-2);
}

#preview-stage, #status-box, #summary-box, #downloads-box {
    background: var(--panel-strong) !important;
}

#preview-image {
    min-height: 420px !important;
    border-radius: 18px !important;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(148,163,184,0.10), rgba(148,163,184,0.04)) !important;
    border: 1px solid var(--line) !important;
}

#preview-image img {
    border-radius: 16px !important;
    box-shadow: 0 24px 60px rgba(15,23,42,0.16) !important;
}

#preview-gallery {
    min-height: 150px !important;
}

#preview-gallery .grid-wrap {
    gap: 10px !important;
}

#preview-gallery img {
    border-radius: 14px !important;
}

#status-box, #summary-box, #downloads-box {
    border-radius: 20px !important;
}

#status-box .prose p {
    margin: 0 !important;
    line-height: 1.65 !important;
    font-size: 0.92rem !important;
    color: var(--muted) !important;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
}

.summary-card {
    padding: 14px;
    border-radius: 16px;
    border: 1px solid var(--line);
    background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
}

.summary-card span {
    display: block;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.summary-card strong {
    display: block;
    margin-top: 8px;
    font-size: 1rem;
    color: var(--text);
}

#downloads-row {
    gap: 12px !important;
}

#gen-btn button {
    width: 100% !important;
    padding: 16px 22px !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%) !important;
    box-shadow: 0 16px 36px rgba(37,99,235,0.24) !important;
}

#gen-btn button:hover {
    transform: translateY(-1px);
}

.tabs > .tab-nav {
    border-bottom: 1px solid var(--line) !important;
    margin-bottom: 12px;
}

.tabs > .tab-nav button {
    border-radius: 14px 14px 0 0 !important;
    padding: 10px 14px !important;
    color: var(--soft) !important;
}

.tabs > .tab-nav button.selected {
    color: var(--accent-2) !important;
    border-bottom: 2px solid var(--accent-2) !important;
    background: transparent !important;
}

.accordion > .label-wrap span {
    font-size: 0.86rem !important;
    font-weight: 700 !important;
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-thumb {
    background: rgba(148,163,184,0.45);
    border-radius: 999px;
}

@media (max-width: 1100px) {
    .hero-shell {
        grid-template-columns: 1fr;
    }

    .upload-grid,
    .summary-grid,
    .style-grid,
    .preset-button-grid,
    #style-card-picker .wrap {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 760px) {
    .gradio-container {
        padding: 14px 14px 36px !important;
    }

    .hero-shell {
        padding: 22px;
        border-radius: 22px;
    }

    .hero-copy p {
        font-size: 0.94rem;
    }

    .upload-grid,
    .summary-grid,
    .style-grid,
    .preset-button-grid,
    #style-card-picker .wrap {
        grid-template-columns: 1fr;
    }

    #preview-image {
        min-height: 280px !important;
    }
}
"""


# ---------------------------------------------------------------------------
# Choices and defaults
# ---------------------------------------------------------------------------

_quality_choices = [("Instant · Fast font rendering", "font")]
if NEURAL_AVAILABLE:
    _quality_choices.append(("Realistic · Neural handwriting", "realistic"))

_page_choices = [
    ("Ruled", "ruled"),
    ("College", "college"),
    ("Grid", "grid"),
    ("Blank", "blank"),
    ("Parchment", "parchment"),
]
_ink_choices = [
    ("Blue Ink", "blue"),
    ("Black Ink", "black"),
    ("Pencil", "pencil"),
]

_init_backend = "font"
_init_choices = _style_choices_for_backend(_init_backend)
_init_writer = _init_choices[0][1] if _init_choices else None
_init_card_choices = _style_card_choices_for_backend(_init_backend)
_init_page_style = "ruled"
_init_ink_color = "blue"


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

config.ensure_runtime_dirs()


with gr.Blocks(title="Scripta — Text to Handwriting") as demo:
    with gr.Column(elem_id="app-shell"):
        gr.HTML(_hero_html())
        selected_writer = gr.State(_init_writer)
        selected_page_style = gr.State(_init_page_style)
        selected_ink_color = gr.State(_init_ink_color)

        with gr.Row(elem_id="main-row", equal_height=False):
            with gr.Column(scale=5, min_width=360, elem_id="ctrl-panel"):
                with gr.Group():
                    gr.HTML(_panel_title("Input", "Bring in your content", "Type directly or upload a source document. Scripta keeps the rendering pipeline the same underneath."))
                    gr.HTML(_upload_cards_html())
                    with gr.Tabs():
                        with gr.Tab("Type or Paste"):
                            input_text = gr.Textbox(
                                lines=10,
                                placeholder=(
                                    "Paste text here...\n\n"
                                    "Use blank lines for paragraph breaks.\n"
                                    "Long content will flow across multiple pages automatically."
                                ),
                                show_label=False,
                                elem_id="text-input",
                            )
                        with gr.Tab("Upload File"):
                            input_file = gr.File(
                                label="Drop a TXT, PDF, or DOCX file",
                                file_types=[".txt", ".pdf", ".docx"],
                                file_count="single",
                            )

                with gr.Group():
                    gr.HTML(_panel_title("Mode", "Choose render quality", "Switch between fast font rendering and the optional neural handwriting backend."))
                    backend = gr.Radio(
                        choices=_quality_choices,
                        value=_init_backend,
                        show_label=False,
                        container=False,
                        elem_id="quality-radio",
                    )
                    if not NEURAL_AVAILABLE:
                        gr.Markdown("Realistic mode appears automatically when VATr++ styles are installed.")

                with gr.Group():
                    gr.HTML(_panel_title("Style", "Handwriting presets", "Each preset has a different rhythm, weight, and personality."))
                    writer_style = gr.Dropdown(
                        choices=_init_choices,
                        value=_init_writer,
                        label="Writer preset",
                        info="Choose the personality that should drive the page.",
                        interactive=True,
                    )
                    with gr.Column(elem_classes=["preset-button-grid"]):
                        preset_buttons = []
                        for preset_index, (writer_id, label, swatch) in enumerate(_preset_button_defs_for_backend(_init_backend)):
                            btn = gr.Button(
                                value=f"{label}\n{writer_id.upper()}",
                                elem_classes=["preset-button"],
                            )
                            preset_buttons.append((preset_index, btn))

                with gr.Group():
                    gr.HTML(_panel_title("Paper", "Page look and ink", "Tune the output document surface before rendering."))
                    page_style = gr.Dropdown(
                        choices=_page_choices,
                        value=_init_page_style,
                        label="Paper",
                        interactive=True,
                    )
                    with gr.Row(elem_classes=["option-button-grid"]):
                        paper_buttons = []
                        for page_value, page_label in _paper_button_defs():
                            btn = gr.Button(page_label, elem_classes=["option-button"])
                            paper_buttons.append((page_value, btn))

                    ink_color = gr.Dropdown(
                        choices=_ink_choices,
                        value=_init_ink_color,
                        label="Ink",
                        interactive=True,
                    )
                    with gr.Row(elem_classes=["option-button-grid"]):
                        ink_buttons = []
                        for ink_value, ink_label in _ink_button_defs():
                            btn = gr.Button(ink_label, elem_classes=["option-button"])
                            ink_buttons.append((ink_value, btn))

                with gr.Accordion("Advanced controls", open=False):
                    apply_artifacts = gr.Checkbox(
                        label="Enable paper texture and aging effects",
                        value=True,
                        info="Applies ink bleed, micro-warp, paper grain, and scanner-style finish.",
                    )
                    seed_val = gr.Number(
                        label="Seed",
                        value=None,
                        precision=0,
                        minimum=0,
                        maximum=2_147_483_647,
                        info="Leave blank to get a fresh variation each time.",
                    )

                gen_btn = gr.Button("Generate Handwriting", variant="primary", elem_id="gen-btn", size="lg")

            with gr.Column(scale=7, min_width=420, elem_id="preview-panel"):
                with gr.Group(elem_id="preview-stage"):
                    gr.HTML(_panel_title("Preview", "Rendered output", "See the first page immediately, inspect additional pages below, and export polished files."))
                    preview_empty = gr.HTML(_preview_placeholder_html())
                    preview = gr.Image(
                        label="Primary preview",
                        type="pil",
                        interactive=False,
                        elem_id="preview-image",
                        height=500,
                    )
                    preview_gallery = gr.Gallery(
                        label="All rendered pages",
                        show_label=True,
                        elem_id="preview-gallery",
                        columns=3,
                        object_fit="contain",
                        height="auto",
                    )

                with gr.Group(elem_id="summary-box"):
                    gr.HTML(_panel_title("Snapshot", "Render summary", "A compact overview of the currently generated document."))
                    summary_html = gr.HTML("")

                with gr.Group(elem_id="status-box"):
                    gr.HTML(_panel_title("Status", "Live feedback", "Progress, parsing issues, and render results show up here."))
                    status_md = gr.Markdown(_idle_status_markdown())

                with gr.Group(elem_id="downloads-box"):
                    gr.HTML(_panel_title("Exports", "Download your files", "PNG export is a single image for one page or a ZIP of page PNGs for multi-page output."))
                    with gr.Row(elem_id="downloads-row"):
                        png_download = gr.File(label="PNG Export", interactive=False)
                        pdf_download = gr.File(label="PDF Export", interactive=False)

    backend.change(
        fn=on_backend_change,
        inputs=[backend],
        outputs=[writer_style, selected_writer, *[button for _, button in preset_buttons]],
    )
    writer_style.change(
        fn=on_style_dropdown_change,
        inputs=[writer_style],
        outputs=[writer_style, selected_writer],
    )
    for preset_index, preset_button in preset_buttons:
        preset_button.click(
            fn=lambda current_backend, slot=preset_index: on_preset_button_click(current_backend, slot),
            inputs=[backend],
            outputs=[writer_style, selected_writer],
        )
    page_style.change(
        fn=on_page_style_change,
        inputs=[page_style],
        outputs=[],
    )
    ink_color.change(
        fn=on_ink_color_change,
        inputs=[ink_color],
        outputs=[],
    )
    page_style.change(
        fn=lambda value: value,
        inputs=[page_style],
        outputs=[selected_page_style],
    )
    ink_color.change(
        fn=lambda value: value,
        inputs=[ink_color],
        outputs=[selected_ink_color],
    )
    for page_value, paper_button in paper_buttons:
        paper_button.click(
            fn=lambda value=page_value: on_paper_button_click(value),
            outputs=[page_style, selected_page_style],
        )
    for ink_value, ink_button in ink_buttons:
        ink_button.click(
            fn=lambda value=ink_value: on_ink_button_click(value),
            outputs=[ink_color, selected_ink_color],
        )
    gen_btn.click(
        fn=generate,
        inputs=[
            input_text,
            input_file,
            backend,
            writer_style,
            selected_writer,
            selected_page_style,
            selected_ink_color,
            apply_artifacts,
            seed_val,
        ],
        outputs=[
            preview,
            preview_gallery,
            png_download,
            pdf_download,
            status_md,
            preview_empty,
            summary_html,
        ],
    )


if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=False,
        show_error=True,
        theme=_theme,
        css=CSS,
    )
