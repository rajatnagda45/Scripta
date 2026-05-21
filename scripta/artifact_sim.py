"""
Physical artifact simulation — applied to the fully composited page image.

Layers applied in order:
  1. Ink bleed       — slight edge blur, simulates ink absorbing into paper
  2. Scan noise      — luminance noise, simulates scanner grain
  3. Paper texture   — multiply-blend a paper texture if one is available
  4. Vignette        — subtle darkening at corners (scanner lamp falloff)
  5. Slight warp     — micro-distortion, eliminates any pixel-perfect regularity
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageDraw

import config
from scripta.debug_utils import debug_log, timed_stage

try:
    from opensimplex import noise2 as pnoise2
    _HAS_NOISE = True
except ImportError:
    _HAS_NOISE = False


_PAPER_TEXTURE_CACHE: dict[Tuple[int, int], Image.Image] = {}


def apply_ink_bleed(img: Image.Image, radius: float = 0.6) -> Image.Image:
    """Soften glyph edges — ink spreads slightly on paper grain."""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_scan_noise(img: Image.Image, intensity: float = 6.0) -> Image.Image:
    """Add subtle luminance noise — simulates scanner sensor noise."""
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, intensity, arr.shape[:2])

    if arr.ndim == 3:
        for c in range(min(3, arr.shape[2])):
            arr[:, :, c] = np.clip(arr[:, :, c] + noise, 0, 255)
    else:
        arr = np.clip(arr + noise, 0, 255)

    return Image.fromarray(arr.astype(np.uint8), mode=img.mode)


def apply_paper_texture(
    page: Image.Image,
    texture_path: Optional[Path] = None,
    blend_alpha: float = 0.18,
) -> Image.Image:
    """
    Multiply-blend a paper texture over the page.
    If no texture file exists, synthesize a simple linen grain.
    """
    with timed_stage("artifacts", "paper texture"):
        if texture_path and texture_path.exists():
            debug_log("artifacts", f"using external paper texture {texture_path}")
            texture = Image.open(texture_path).convert("RGB").resize(page.size, Image.LANCZOS)
        else:
            texture = _synthesize_paper_grain(page.size)

        page_rgb = page.convert("RGB")
        blended = ImageChops.multiply(page_rgb, texture)
        out = Image.blend(page_rgb, blended, blend_alpha)

        if page.mode == "RGBA":
            r, g, b = out.split()
            _, _, _, a = page.split()
            out = Image.merge("RGBA", [r, g, b, a])

        return out


def _synthesize_paper_grain(size: Tuple[int, int]) -> Image.Image:
    """Generate a subtle cream paper grain texture using Perlin or fallback."""
    cached = _PAPER_TEXTURE_CACHE.get(size)
    if cached is not None:
        debug_log("artifacts", f"reusing cached synthesized paper texture for size={size}")
        return cached.copy()

    w, h = size
    debug_log("artifacts", f"synthesizing paper grain for size={size} noise_backend={'opensimplex' if _HAS_NOISE else 'gaussian'}")

    if _HAS_NOISE:
        # Avoid millions of Python-level opensimplex calls at full page resolution.
        low_w = max(64, w // 8)
        low_h = max(64, h // 8)
        arr = np.zeros((low_h, low_w), dtype=np.float32)
        scale = 0.008 * 8
        for y in range(low_h):
            if y % 40 == 0:
                debug_log("artifacts", f"paper grain row {y + 1}/{low_h}")
            for x in range(low_w):
                arr[y, x] = pnoise2(x * scale, y * scale)
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6)
        paper_small = (arr * 35 + 220).astype(np.uint8)
        texture = Image.fromarray(paper_small, mode="L").resize((w, h), Image.BICUBIC).convert("RGB")
    else:
        # Simple fallback: gaussian-smoothed noise
        from scipy.ndimage import gaussian_filter

        arr = np.random.rand(h, w).astype(np.float32)
        arr = gaussian_filter(arr, sigma=3)
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6)
        paper = (arr * 35 + 220).astype(np.uint8)
        texture = Image.fromarray(paper, mode="L").convert("RGB")

    _PAPER_TEXTURE_CACHE[size] = texture.copy()
    return texture


def apply_vignette(img: Image.Image, strength: float = 0.06) -> Image.Image:
    """Darken corners slightly — scanner lamp falloff effect."""
    w, h = img.size
    vignette = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(vignette)

    # Radial gradient approximated by concentric ellipses
    cx, cy = w // 2, h // 2
    steps = 30
    for i in range(steps):
        t = i / steps
        darkness = int(255 * (1.0 - strength * t * t))
        rx = int(cx * (1 - t))
        ry = int(cy * (1 - t))
        draw.ellipse(
            [cx - rx, cy - ry, cx + rx, cy + ry],
            fill=darkness,
        )

    # Actually we want corners dark, center bright — invert logic
    vignette_arr = np.array(vignette, dtype=np.float32) / 255.0
    # Flip: bright at center → dark at corners
    corner_mask = 1.0 - vignette_arr
    darkening = 1.0 - corner_mask * strength * 3.0
    darkening = np.clip(darkening, 0, 1)

    img_arr = np.array(img.convert("RGB")).astype(np.float32)
    img_arr[:, :, 0] *= darkening
    img_arr[:, :, 1] *= darkening
    img_arr[:, :, 2] *= darkening
    img_arr = np.clip(img_arr, 0, 255).astype(np.uint8)

    out = Image.fromarray(img_arr, "RGB")
    if img.mode == "RGBA":
        _, _, _, a = img.split()
        r, g, b = out.split()
        out = Image.merge("RGBA", [r, g, b, a])
    return out


def apply_micro_warp(img: Image.Image, amplitude: float = 1.2) -> Image.Image:
    """
    Subtle pixel-level warp using a scipy-based displacement map.
    Eliminates pixel-perfect regularity — the last tell of digital rendering.
    Uses gaussian-filtered noise (fast, no pixel-level Python loops).
    """
    from scipy.ndimage import gaussian_filter
    import cv2

    w, h = img.size
    arr = np.array(img)

    # Smooth random displacement fields — gaussian filter gives organic curves
    rng = np.random.default_rng()
    dx = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=18) * amplitude * 2
    dy = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=18) * amplitude * 2

    grid_y, grid_x = np.mgrid[0:h, 0:w]
    map_x = np.clip(grid_x + dx, 0, w - 1).astype(np.float32)
    map_y = np.clip(grid_y + dy, 0, h - 1).astype(np.float32)

    warped = cv2.remap(arr, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(warped, mode=img.mode)


def apply_all(
    page: Image.Image,
    fatigue_level: float = 0.3,
    texture_path: Optional[Path] = None,
) -> Image.Image:
    """
    Apply the full artifact stack to a completed page.
    fatigue_level (0–1) scales noise and warp intensity.
    """
    with timed_stage("artifacts", "full artifact pipeline"):
        debug_log("artifacts", f"page size={page.size} fatigue={fatigue_level:.3f}")
        with timed_stage("artifacts", "ink bleed"):
            page = apply_ink_bleed(page, radius=0.5 + fatigue_level * 0.4)
        with timed_stage("artifacts", "micro warp"):
            page = apply_micro_warp(page, amplitude=0.8 + fatigue_level * 0.6)
        with timed_stage("artifacts", "scan noise"):
            page = apply_scan_noise(page, intensity=4.0 + fatigue_level * 3.0)
        page = apply_paper_texture(page, texture_path=texture_path, blend_alpha=0.15)
        with timed_stage("artifacts", "vignette"):
            page = apply_vignette(page, strength=0.05)
        return page
