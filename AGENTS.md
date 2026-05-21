# AGENTS.md

## Project intent

Scripta is a modular handwriting rendering system. Keep the existing pipeline intact:

- `main.py`: CLI entrypoint
- `app.py`: Gradio UI
- `scripta/input_handler.py`: TXT/PDF/DOCX ingestion
- `scripta/glyph_store.py`: font-backed glyph source
- `scripta/variation_engine.py`: `WriterState`
- `scripta/renderer.py`: glyph compositing/transforms
- `scripta/page_compositor.py`: font backend page layout
- `scripta/neural_renderer.py`: VATr++ wrapper
- `scripta/neural_page_compositor.py`: neural backend page layout
- `scripta/artifact_sim.py`: paper/scan artifacts
- `scripts/prep_style_samples.py`: IAM to VATr++ style-sample preparation

## Guardrails

- Preserve the modular architecture.
- Do not remove `WriterState`.
- Do not remove artifact simulation.
- Do not merge the font and neural backends into one simplified path.
- Prefer minimal, safe fixes over broad rewrites.
- Preserve existing CLI flags and behaviors unless a bug requires a compatibility-safe adjustment.

## Local assumptions

- The repository may be missing `fonts/`, `output/`, `data/iam/`, and `VATr-pp/` on a fresh clone.
- The font backend should remain usable without the neural backend present.
- The neural backend depends on external assets and should fail clearly when those assets are absent.

## Preferred workflow

1. Read `PLAN.md` before making architectural changes.
2. Verify whether an issue is setup-related before changing rendering logic.
3. Keep path handling rooted at the repository, not the caller's working directory.
4. Favor friendly startup errors over deep tracebacks for missing assets.
5. Verify both `python main.py ...` and `python app.py` after changes when dependencies are available.

## macOS notes

- Use a repo-local `.venv`.
- Default Gradio binding should stay local (`127.0.0.1`) unless the user asks otherwise.
- Be cautious with PyTorch advice: the neural backend may require a narrower Python version range than the font backend.
