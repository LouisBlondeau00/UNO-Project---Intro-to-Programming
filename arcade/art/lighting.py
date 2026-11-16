"""Light and shadow for the pictures (visual update, idea 3).

All functions take plain Pillow images and return new ones; nothing here knows
about Streamlit or game rules.
"""

from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter


def _check(strength: float) -> None:
    if not 0 <= strength <= 1:
        raise ValueError("strength goes from 0 to 1")


@lru_cache(maxsize=8)
def _vignette_mask(size: tuple[int, int], strength: float) -> Image.Image:
    """Grey mask: white (keep) in the middle, darker towards the edges and corners."""
    w, h = size
    small = Image.new("L", (64, 36), 0)
    pixels = small.load()
    for y in range(36):
        for x in range(64):
            dx, dy = (x + 0.5) / 32 - 1, (y + 0.5) / 18 - 1
            edge = min(1.0, max(0.0, (dx * dx + dy * dy) ** 0.5 - 0.55) / 0.85)  # 0 in the middle, 1 at the corners
            pixels[x, y] = int(255 * (1 - strength * edge * edge))
    return small.resize((w, h), Image.BILINEAR)


def vignette(img: Image.Image, strength: float = 0.5) -> Image.Image:
    """Darken the edges and corners so the eye goes to the middle. strength 0 changes nothing."""
    _check(strength)
    img = img.convert("RGB")
    if strength == 0:
        return img.copy()
    mask = _vignette_mask(img.size, strength).convert("RGB")
    return ImageChops.multiply(img, mask)


def drop_shadow(layer: Image.Image, offset=(2, 3), opacity: float = 0.5, blur: float = 1.2) -> Image.Image:
    """A soft dark copy of a transparent layer's shapes, moved by offset (RGBA, to lay under the layer)."""
    _check(opacity)
    alpha = layer.getchannel("A").point(lambda v: int(v * opacity))
    moved = Image.new("L", layer.size, 0)
    moved.paste(alpha, offset)
    shadow = Image.new("RGBA", layer.size, (6, 4, 16, 0))
    shadow.putalpha(moved.filter(ImageFilter.GaussianBlur(blur)))
    return shadow


@lru_cache(maxsize=16)
def soft_oval(width: int, height: int, opacity: float = 0.6) -> Image.Image:
    """A blurred dark oval (RGBA) to put under a character or a table."""
    _check(opacity)
    pad = 3
    alpha = Image.new("L", (width + pad * 2, height + pad * 2), 0)
    ImageDraw.Draw(alpha).ellipse([pad, pad, pad + width - 1, pad + height - 1], fill=int(255 * opacity))
    oval = Image.new("RGBA", alpha.size, (6, 4, 16, 0))
    oval.putalpha(alpha.filter(ImageFilter.GaussianBlur(1)))
    return oval


def light_pool(img: Image.Image, centre, radius: int, colour=(255, 214, 160), strength: float = 0.18) -> Image.Image:
    """A soft warm light around a point. It only ever brightens."""
    _check(strength)
    img = img.convert("RGB")
    if strength == 0:
        return img.copy()
    glow = Image.new("RGB", img.size, (0, 0, 0))
    x, y = centre
    ImageDraw.Draw(glow).ellipse([x - radius, y - radius * 0.6, x + radius, y + radius * 0.6],
                                 fill=tuple(int(c * strength) for c in colour))
    glow = glow.filter(ImageFilter.GaussianBlur(radius / 2))
    return ImageChops.add(img, glow)
