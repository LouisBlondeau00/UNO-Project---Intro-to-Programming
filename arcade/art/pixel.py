"""Tiny pixel-art toolkit built on Pillow.

Scenes are painted on a small "base" canvas (320x180) and scaled up 3x with
hard edges. Text and menus are then drawn on the big picture.

Text uses Jersey 10 (arcade/art/fonts/, SIL Open Font License) drawn without
smoothing so it stays crisp. Set TEXT_FONT = None in config.py to go back to the
built-in 5x7 font (arcade/art/font.py).
"""

from __future__ import annotations

import textwrap
from functools import lru_cache

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from arcade.art import font
from arcade.config import BASE_H, BASE_W, SCALE, TEXT_FONT

FONT_DIR = Path(__file__).parent / "fonts"

CHAR_W, CHAR_H = 6, font.GLYPH_H  # average letter advance and letter height, in font pixels


def rgb(color) -> tuple[int, int, int]:
    """Turn '#rrggbb' into (r, g, b). Tuples pass straight through."""
    if isinstance(color, tuple):
        return color[:3]
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t: float) -> tuple[int, int, int]:
    """Blend colour a towards colour b (t=0 gives a, t=1 gives b)."""
    a, b = rgb(a), rgb(b)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(color, factor: float) -> tuple[int, int, int]:
    """factor < 1 darkens, factor > 1 lightens."""
    if factor <= 1:
        return mix((0, 0, 0), color, factor)
    return mix(color, (255, 255, 255), min(1.0, factor - 1))


def readable_on(color) -> str:
    """Pick dark or light text so it can be read on the given background."""
    r, g, b = rgb(color)
    return "#16122b" if (r * 299 + g * 587 + b * 114) / 1000 > 140 else "#ffffff"


def rect(draw: ImageDraw.ImageDraw, x, y, w, h, color) -> None:
    if w > 0 and h > 0:
        draw.rectangle([x, y, x + w - 1, y + h - 1], fill=color)


def new_base(color="#000000") -> Image.Image:
    return Image.new("RGB", (BASE_W, BASE_H), rgb(color))


def upscale(img: Image.Image, factor: int = SCALE) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def darken(img: Image.Image, amount: float = 0.55) -> Image.Image:
    """Return a dimmed copy, used behind pop-up panels."""
    black = Image.new("RGB", img.size, (8, 6, 20))
    return Image.blend(img.convert("RGB"), black, amount)


OUTLINE = (16, 12, 34)


def new_layer(size=(BASE_W, BASE_H)) -> Image.Image:
    """A see-through sheet to draw on. Use outlined() and then paste it onto a picture."""
    return Image.new("RGBA", size, (0, 0, 0, 0))


def outlined(layer: Image.Image, colour=OUTLINE) -> Image.Image:
    """Give everything drawn on a see-through layer a dark 1-pixel edge.

    This is what makes characters and furniture look chunky and readable,
    like classic top-down pixel-art games.
    """
    solid = layer.getchannel("A").point(lambda a: 255 if a else 0)
    grown = solid.filter(ImageFilter.MaxFilter(3))
    out = new_layer(layer.size)
    out.paste(Image.new("RGBA", layer.size, tuple(colour) + (255,)), (0, 0), grown)
    out.alpha_composite(layer)
    return out


def stamp(img: Image.Image, layer: Image.Image, xy=(0, 0)) -> None:
    """Paste a see-through layer onto a picture."""
    img.paste(layer, (int(xy[0]), int(xy[1])), layer)


# ---------------------------------------------------------------- text

def _font_size(scale: int) -> int:
    """Font size whose capital letters are as tall as the old 5x7 letters (7 pixels at scale 1)."""
    return 13 * scale


@lru_cache(maxsize=16)
def _ttf(scale: int) -> ImageFont.FreeTypeFont | None:
    """The TrueType font at this scale, or None to use the built-in 5x7 font (which reads better at scale 1)."""
    if not TEXT_FONT or scale < 2:
        return None
    return ImageFont.truetype(str(FONT_DIR / TEXT_FONT), _font_size(scale))


@lru_cache(maxsize=4096)
def _ttf_mask(text: str, scale: int) -> Image.Image:
    """The text drawn with the TrueType font, crisp (no smoothing). Capitals fill the top GLYPH_H*scale rows."""
    face = _ttf(scale)
    cap_top = face.getbbox("H")[1]
    left, _, right, _ = face.getbbox(text)
    height = font.GLYPH_H * scale
    mask = Image.new("L", (max(1, right - left), height + 3 * scale), 0)  # room below for , Q and J
    draw = ImageDraw.Draw(mask)
    draw.fontmode = "1"
    draw.text((-left, -cap_top), text, font=face, fill=255)
    return mask


@lru_cache(maxsize=4096)
def _text_mask(text: str, scale: int) -> Image.Image:
    if _ttf(scale) is not None:
        return _ttf_mask(text.upper(), scale)
    mask = Image.new("L", (max(1, font.width(text)), font.GLYPH_H), 0)
    x = 0
    for char in text:
        rows = font.glyph(char)
        for y, row in enumerate(rows):
            for dx, cell in enumerate(row):
                if cell == "#":
                    mask.putpixel((x + dx, y), 255)
        x += len(rows[0]) + 1
    if scale != 1:
        mask = mask.resize((mask.width * scale, mask.height * scale), Image.NEAREST)
    return mask


def text_size(text: str, scale: int = 2) -> tuple[int, int]:
    """Width and height (of the capital letters) of the text, in pixels of the picture."""
    text = str(text)
    if _ttf(scale) is not None:
        return (_ttf_mask(text.upper(), scale).width if text else 0), font.GLYPH_H * scale
    return font.width(text) * scale, font.GLYPH_H * scale


def draw_text(img, xy, text, scale=2, fill="#ffffff", anchor="lt", shadow=None):
    """Draw pixel text. anchor is two letters: l/m/r then t/m/b."""
    text = str(text)
    if not text:
        return (xy[0], xy[1], xy[0], xy[1])
    mask = _text_mask(text, scale)
    width, height = text_size(text, scale)  # anchors use the capital letters, not the room left for , Q and J
    x, y = xy
    if anchor[0] == "m":
        x -= width // 2
    elif anchor[0] == "r":
        x -= width
    if anchor[1] == "m":
        y -= height // 2
    elif anchor[1] == "b":
        y -= height
    x, y = int(x), int(y)
    if shadow is not None:
        img.paste(rgb(shadow), (x + scale, y + scale), mask)
    img.paste(rgb(fill), (x, y), mask)
    return (x, y, x + width, y + height)


def wrap(text: str, max_chars: int) -> list[str]:
    return textwrap.wrap(text, max_chars) or [""]


def draw_lines(img, xy, lines, scale=2, fill="#ffffff", anchor="mt", gap=3, shadow=None):
    """Draw several lines under each other. Returns the y after the last line."""
    x, y = xy
    for line in lines:
        draw_text(img, (x, y), line, scale, fill, anchor, shadow)
        y += CHAR_H * scale + gap * scale
    return y


# ---------------------------------------------------------------- shapes

def panel(img, box, fill, border="#16122b", bw=3, shadow=True):
    """A rectangle with chunky cut corners, used for bubbles and menus."""
    x0, y0, x1, y1 = (int(v) for v in box)
    d = ImageDraw.Draw(img)
    if shadow:
        d.rectangle([x0 + bw * 2, y0 + bw * 2, x1 + bw * 2, y1 + bw * 2], fill=(8, 6, 20))
    d.rectangle([x0 + bw, y0, x1 - bw, y1], fill=rgb(border))
    d.rectangle([x0, y0 + bw, x1, y1 - bw], fill=rgb(border))
    d.rectangle([x0 + bw * 2, y0 + bw, x1 - bw * 2, y1 - bw], fill=rgb(fill))
    d.rectangle([x0 + bw, y0 + bw * 2, x1 - bw, y1 - bw * 2], fill=rgb(fill))
    return (x0, y0, x1, y1)


def key_icon(img, x, y, label, scale=2, fill="#ffffff", ink="#16122b"):
    """A keyboard key: a square with the letter inside. Returns its width."""
    tw, th = text_size(label, scale)
    w = max(tw + 6 * scale, th + 4 * scale)
    h = th + 4 * scale
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w - 1, y + h + scale - 1], fill=rgb(ink))
    d.rectangle([x + scale, y + scale, x + w - scale - 1, y + h - scale - 1], fill=rgb(fill))
    draw_text(img, (x + w // 2, y + h // 2), label, scale, ink, "mm")
    return w


def coin(img, x, y, unit=3):
    """A pixel coin whose top-left corner is (x, y). It is 8 units wide."""
    d = ImageDraw.Draw(img)
    u = unit
    gold, light, dark = (255, 205, 60), (255, 236, 150), (176, 120, 20)
    rows = [(2, 4), (1, 6), (0, 8), (0, 8), (0, 8), (0, 8), (1, 6), (2, 4)]
    for r, (start, length) in enumerate(rows):
        d.rectangle([x + start * u, y + r * u, x + (start + length) * u - 1, y + (r + 1) * u - 1], fill=dark)
    for r, (start, length) in enumerate(rows[1:-1], start=1):
        d.rectangle(
            [x + (start + 1) * u, y + r * u, x + (start + length - 1) * u - 1, y + (r + 1) * u - 1], fill=gold
        )
    d.rectangle([x + 2 * u, y + 2 * u, x + 3 * u - 1, y + 5 * u - 1], fill=light)
    d.rectangle([x + 4 * u, y + 2 * u, x + 5 * u - 1, y + 6 * u - 1], fill=dark)
    return 8 * u


def lock(img, x, y, unit=3, color="#c9ccd6"):
    """A small padlock, 7 units wide and 9 tall."""
    d = ImageDraw.Draw(img)
    u = unit
    c, dk = rgb(color), shade(color, 0.55)
    d.rectangle([x + 1 * u, y, x + 6 * u - 1, y + 1 * u - 1], fill=c)
    d.rectangle([x + 1 * u, y, x + 2 * u - 1, y + 4 * u - 1], fill=c)
    d.rectangle([x + 5 * u, y, x + 6 * u - 1, y + 4 * u - 1], fill=c)
    d.rectangle([x, y + 4 * u, x + 7 * u - 1, y + 9 * u - 1], fill=(240, 190, 60))
    d.rectangle([x + 3 * u, y + 5 * u, x + 4 * u - 1, y + 7 * u - 1], fill=dk)
    return 7 * u
