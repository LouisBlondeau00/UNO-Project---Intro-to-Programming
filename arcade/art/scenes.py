"""Paints the big pictures: title screen, arcade room, table views and pop-ups.

Nothing in this file knows about Streamlit. Every function takes plain data and
returns a Pillow image (960x540), so it can be tested by saving a PNG.
"""

from __future__ import annotations

import random
from functools import lru_cache

from PIL import Image, ImageDraw

from arcade import bots, hubmap
from arcade.art import lighting, sprites
from arcade.art.pixel import (
    CHAR_H, coin, darken, draw_lines, draw_text, key_icon, lock, mix, new_base, new_layer, outlined, panel, rect,
    rgb, shade, stamp, text_size, upscale, wrap,
)
from arcade.config import BASE_H, BASE_W, GAME_TITLE, SCALE, SCREEN_H, SCREEN_W

INK = "#16122b"
LIGHT_BLUE = "#bfe6ff"
NEON = ["#ff4fa3", "#3ad6ff", "#ffe94a", "#7cff3a", "#a06bff", "#ff9f1a"]
TABLE_COLOURS = {"uno": "#d83a3a", "checkers": "#b97a3f", "connect4": "#2f6fe0"}
FELT = {"uno": "#7d1f2b", "checkers": "#6a4526", "connect4": "#1f3f8a"}


# ---------------------------------------------------------------- props

def _machine(d, cx, base_y, body, screen, w=22, h=40, glow=False, game=None):
    """An upright arcade cabinet seen from the front. game: 0, 1 or 2 puts a tiny game on its screen."""
    x = cx - w // 2
    top = base_y - h
    rect(d, x, top, w, h, body)
    rect(d, x, top, w, 6, shade(body, 1.35))  # marquee
    rect(d, x + 2, top + 1, w - 4, 3, screen if glow else shade(screen, 0.6))
    rect(d, x + 2, top + 8, w - 4, 13, (10, 8, 22))  # screen frame
    rect(d, x + 3, top + 9, w - 6, 11, screen)
    rect(d, x + 4, top + 10, 3, 2, shade(screen, 1.5))  # reflection
    sx, sy, sw = x + 3, top + 9, w - 6
    if game == 0:  # a little spaceship shooting at blocks
        for i in range(3):
            rect(d, sx + 2 + i * 5, sy + 2, 3, 2, (255, 233, 74))
        rect(d, sx + sw // 2 - 1, sy + 8, 3, 2, (255, 255, 255))
        rect(d, sx + sw // 2, sy + 5, 1, 2, (255, 120, 120))
    elif game == 1:  # falling blocks
        for bx, by, colour in ((1, 8, "#ff4fa3"), (4, 8, "#3ad6ff"), (4, 5, "#ffe94a"), (10, 8, "#7cff3a"), (8, 2, "#ff9f1a")):
            rect(d, sx + bx, sy + by, 3, 3, rgb(colour))
    elif game == 2:  # a racing road
        rect(d, sx, sy + 6, sw, 5, (40, 40, 52))
        for i in range(3):
            rect(d, sx + 2 + i * 5, sy + 8, 3, 1, (255, 255, 255))
        rect(d, sx + sw // 2 - 2, sy + 4, 4, 3, (230, 60, 60))
    rect(d, x - 1, top + 22, w + 2, 4, shade(body, 0.7))  # control panel
    rect(d, x + 4, top + 21, 1, 2, (230, 60, 60))  # joystick
    rect(d, x + w - 8, top + 23, 2, 1, (250, 220, 80))
    rect(d, x + w - 5, top + 23, 2, 1, (90, 220, 250))
    rect(d, cx - 1, top + 30, 2, 4, (10, 8, 22))  # coin slot
    rect(d, x, base_y - 2, w, 2, shade(body, 0.5))


def _side_machine(d, x, top, body, screen, facing_right=True):
    rect(d, x, top, 12, 32, body)
    rect(d, x, top, 12, 3, shade(body, 1.3))
    glow_x = x + 9 if facing_right else x
    rect(d, glow_x, top + 6, 3, 14, screen)
    rect(d, glow_x, top + 8, 3, 2, shade(screen, 1.5))
    rect(d, x, top + 30, 12, 2, shade(body, 0.5))


def _claw_machine(d, cx, base_y):
    """A prize grabber: glass box full of toys on a red stand."""
    x, top = cx - 12, base_y - 46
    rect(d, x, top, 24, 5, (232, 68, 120))
    for i in range(5):
        rect(d, x + 2 + i * 4, top + 1, 2, 2, (255, 233, 74) if i % 2 == 0 else (90, 220, 250))
    rect(d, x, top + 5, 24, 22, (150, 205, 235))  # glass frame
    rect(d, x + 1, top + 6, 22, 20, (30, 46, 100))
    for px, py, colour in ((2, 15, "#ff4fa3"), (6, 17, "#ffe94a"), (10, 15, "#7cff3a"), (14, 17, "#3ad6ff"),
                           (18, 15, "#ff9f1a"), (4, 12, "#a06bff"), (15, 12, "#ff4f6d")):
        rect(d, x + 1 + px, top + 6 + py - 2, 4, 4, rgb(colour))
        rect(d, x + 2 + px, top + 6 + py - 1, 1, 1, (255, 255, 255))
    rect(d, cx - 1, top + 6, 2, 5, (210, 214, 226))  # the claw
    rect(d, cx - 3, top + 11, 6, 1, (210, 214, 226))
    rect(d, cx - 3, top + 12, 1, 2, (210, 214, 226))
    rect(d, cx + 2, top + 12, 1, 2, (210, 214, 226))
    rect(d, x + 2, top + 7, 1, 8, (110, 150, 215))  # reflection on the glass
    rect(d, x, top + 27, 24, 19, (198, 52, 96))
    rect(d, x, top + 27, 24, 2, (240, 110, 150))
    rect(d, x + 3, top + 32, 8, 7, (20, 14, 40))  # prize door
    rect(d, x + 15, top + 32, 3, 3, (255, 233, 74))
    rect(d, x + 19, top + 32, 3, 3, (90, 220, 250))
    rect(d, x, base_y - 2, 24, 2, (120, 30, 60))


def _gumball(d, cx, base_y):
    rect(d, cx - 4, base_y - 11, 8, 11, (214, 60, 60))
    rect(d, cx - 5, base_y - 13, 10, 3, (150, 30, 40))
    d.ellipse([cx - 6, base_y - 25, cx + 5, base_y - 13], fill=(190, 228, 250))
    for i, colour in enumerate(("#ff4fa3", "#ffe94a", "#7cff3a", "#3ad6ff", "#ff9f1a", "#a06bff")):
        rect(d, cx - 4 + (i % 3) * 3, base_y - 19 + (i // 3) * 3, 2, 2, rgb(colour))
    rect(d, cx - 4, base_y - 23, 2, 2, (255, 255, 255))
    rect(d, cx - 1, base_y - 8, 2, 3, (20, 14, 40))
    rect(d, cx - 5, base_y - 2, 10, 2, (120, 30, 40))


def _poster(d, x, y, w, h, colour, motif):
    """A framed poster for the wall. motif: "star", "bolt", "heart" or "ship"."""
    rect(d, x, y, w, h, (243, 234, 210))
    rect(d, x + 1, y + 1, w - 2, h - 2, rgb(colour))
    cx, cy = x + w // 2, y + h // 2
    ink = (255, 255, 255)
    if motif == "star":
        rect(d, cx - 1, cy - 4, 2, 8, (255, 233, 74))
        rect(d, cx - 4, cy - 1, 8, 2, (255, 233, 74))
        rect(d, cx - 2, cy - 2, 4, 4, (255, 246, 170))
    elif motif == "bolt":
        for i, (bx, bw) in enumerate(((1, 3), (0, 3), (-1, 4), (0, 2), (-1, 2), (-2, 2))):
            rect(d, cx + bx - 1, cy - 4 + i * 2 - i // 2, bw, 2, (255, 233, 74))
    elif motif == "heart":
        rect(d, cx - 3, cy - 3, 2, 3, ink)
        rect(d, cx + 1, cy - 3, 2, 3, ink)
        rect(d, cx - 3, cy - 1, 6, 2, ink)
        rect(d, cx - 2, cy + 1, 4, 1, ink)
        rect(d, cx - 1, cy + 2, 2, 1, ink)
    else:  # ship
        rect(d, cx - 1, cy - 4, 2, 6, ink)
        rect(d, cx - 3, cy, 6, 2, ink)
        rect(d, cx - 1, cy + 3, 2, 2, (255, 159, 26))
    rect(d, x + 2, y + h - 3, w - 4, 1, (255, 255, 255))


def _bunting(d, y=2):
    """A string of little flags across the top of the wall."""
    rect(d, 0, y, BASE_W, 1, (230, 225, 255))
    for i, x in enumerate(range(1, BASE_W, 9)):
        d.polygon([(x, y + 1), (x + 6, y + 1), (x + 3, y + 6)], fill=rgb(NEON[i % len(NEON)]))


def _neon_sign(img, cx, y, text, colour) -> None:
    """Glowing neon letters on a dark board, hung on the wall (A6)."""
    tw, th = text_size(text, 1)
    d = ImageDraw.Draw(img)
    rect(d, cx - tw // 2 - 4, y - 3, tw + 8, th + 6, (22, 14, 50))
    rect(d, cx - tw // 2 - 3, y - 2, tw + 6, 1, (60, 44, 110))
    halo = mix(colour, (22, 14, 50), 0.55)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw_text(img, (cx + dx, y + dy), text, 1, halo, "mt")
    draw_text(img, (cx, y), text, 1, mix(colour, "#ffffff", 0.35), "mt")


def _light_beams(img, beams) -> None:
    """Soft cones of light from the ceiling. beams: (x at the top, x left and right at the bottom, bottom y)."""
    light = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(light)
    for top_x, left, right, bottom in beams:
        d.polygon([(top_x - 2, 0), (top_x + 2, 0), (right, bottom), (left, bottom)], fill=(255, 236, 200, 16))
        d.polygon([(top_x - 1, 0), (top_x + 1, 0), (right - 8, bottom), (left + 8, bottom)], fill=(255, 236, 200, 10))
    img.paste(Image.alpha_composite(img.convert("RGBA"), light).convert("RGB"))


def _light_pools(d) -> None:
    """Lighter patches on the floor where the ceiling lamps shine (drawn before the rugs)."""
    for cx, cy, rx, ry in ((120, 84, 40, 9), (224, 84, 40, 9)):
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=mix(FLOOR_A, "#9d8cff", 0.07))
        d.ellipse([cx - rx + 10, cy - ry + 3, cx + rx - 10, cy + ry - 3], fill=mix(FLOOR_A, "#9d8cff", 0.12))


DANCE_PAD = (104, 149)  # top-left corner of the dance pad on the floor (base canvas)
DANCE_PAD_SIZE = 3 * 8 + 4


def _dance_pad(d, x, y) -> None:
    """A dance-game floor pad: a 3x3 grid with arrow tiles. Flat, so you can walk over it (A6)."""
    size = 8
    rect(d, x - 2, y - 2, size * 3 + 4, size * 3 + 4, (20, 14, 44))
    arrows = {(1, 0): ("#ff4fa3", "up"), (0, 1): ("#3ad6ff", "left"), (2, 1): ("#7cff3a", "right"),
              (1, 2): ("#ffe94a", "down")}
    for gx in range(3):
        for gy in range(3):
            tx, ty = x + gx * size, y + gy * size
            colour, direction = arrows.get((gx, gy), ("#3a2f6b", None))
            rect(d, tx, ty, size - 1, size - 1, mix(colour, (20, 14, 44), 0.55) if direction else rgb(colour))
            if direction:
                cx, cy = tx + 3, ty + 3
                ink = rgb(colour)
                if direction in ("up", "down"):
                    rect(d, cx, cy - 2, 1, 5, ink)
                    tip = cy - 2 if direction == "up" else cy + 2
                    side = 1 if direction == "up" else -1
                    rect(d, cx - 1, tip + side, 3, 1, ink)
                else:
                    rect(d, cx - 2, cy, 5, 1, ink)
                    tip = cx - 2 if direction == "left" else cx + 2
                    side = 1 if direction == "left" else -1
                    rect(d, tip + side, cy - 1, 1, 3, ink)


def _floor_lane(d) -> None:
    """Little glowing dashes leading from the door into the room."""
    for y in range(150, 172, 6):
        rect(d, 159, y, 2, 3, mix("#ffe94a", FLOOR_B, 0.55))


def _trophy(d, cx, bottom):
    gold, dark, light = (255, 205, 60), (176, 120, 20), (255, 240, 170)
    rect(d, cx - 4, bottom - 2, 8, 2, dark)
    rect(d, cx - 1, bottom - 5, 2, 3, gold)
    rect(d, cx - 4, bottom - 11, 8, 6, gold)
    rect(d, cx - 3, bottom - 12, 6, 1, gold)
    rect(d, cx - 6, bottom - 10, 2, 3, gold)
    rect(d, cx + 4, bottom - 10, 2, 3, gold)
    rect(d, cx - 3, bottom - 10, 1, 4, light)
    rect(d, cx - 2, bottom - 5, 4, 1, dark)


def _plant(d, cx, bottom):
    rect(d, cx - 3, bottom - 5, 6, 5, (150, 84, 52))
    rect(d, cx - 4, bottom - 6, 8, 1, (176, 104, 66))
    for dx, dy, w, h in ((-5, -12, 4, 6), (1, -14, 4, 8), (-2, -16, 4, 10), (-7, -9, 3, 3), (4, -9, 3, 3)):
        rect(d, cx + dx, bottom + dy, w, h, (46, 150, 88))
    rect(d, cx - 1, bottom - 14, 1, 6, (90, 200, 120))


def draw_table(d, kind, cx, cy, glow=False):
    """One of the three game tables as it looks inside the arcade room."""
    top = rgb(TABLE_COLOURS[kind])
    rect(d, cx - 3, cy + 5, 6, 10, (40, 32, 62))
    d.ellipse([cx - 10, cy + 12, cx + 10, cy + 17], fill=(28, 22, 48))
    d.ellipse([cx - 23, cy - 8, cx + 23, cy + 10], fill=shade(top, 0.55))
    rim = (255, 240, 150) if glow else shade(top, 1.5)
    d.ellipse([cx - 23, cy - 10, cx + 23, cy + 8], fill=top, outline=rim)
    if kind == "uno":
        for i, colour in enumerate(("#f2c230", "#3fae5a", "#3a78e8")):
            rect(d, cx - 11 + i * 8, cy - 5 + (i % 2), 5, 7, (255, 255, 255))
            rect(d, cx - 10 + i * 8, cy - 4 + (i % 2), 3, 5, rgb(colour))
    elif kind == "checkers":
        for row in range(4):
            for col in range(6):
                colour = (40, 30, 30) if (row + col) % 2 else (240, 225, 190)
                rect(d, cx - 9 + col * 3, cy - 6 + row * 3, 3, 3, colour)
    else:
        rect(d, cx - 9, cy - 8, 18, 12, (20, 50, 150))
        for row in range(3):
            for col in range(5):
                colour = [(250, 210, 60), (230, 60, 60), (12, 20, 60)][(row * 2 + col) % 3]
                rect(d, cx - 8 + col * 3 + col // 2, cy - 7 + row * 4, 2, 2, colour)
        rect(d, cx - 10, cy + 4, 20, 2, (16, 36, 110))


TABLE_ORIGIN = (27, 13)  # where the table's centre sits inside its little picture


@lru_cache(maxsize=8)
def table_sprite(kind: str, glow: bool = False) -> Image.Image:
    """A table as a small outlined picture, ready to be stamped into the room."""
    layer = new_layer((54, 34))
    draw_table(ImageDraw.Draw(layer), kind, *TABLE_ORIGIN, glow=glow)
    return outlined(layer)


# ---------------------------------------------------------------- arcade room

FLOOR_A, FLOOR_B, GROUT = (46, 35, 106), (39, 29, 92), (30, 22, 74)
WALL, MORTAR = (44, 30, 96), (34, 23, 78)


def _room_shell(img) -> None:
    """Wall, floor tiles and the coloured rugs under the game tables (nothing with an outline)."""
    d = ImageDraw.Draw(img)
    top = hubmap.FLOOR_TOP

    # brick wall
    rect(d, 0, 0, BASE_W, top, WALL)
    for i, y in enumerate(range(0, top, 6)):
        rect(d, 0, y, BASE_W, 1, MORTAR)
        for x in range(-6 if i % 2 else 0, BASE_W, 12):
            rect(d, x, y, 1, 6, MORTAR)
    rect(d, 0, top - 9, BASE_W, 2, rgb("#ff4fa3"))  # neon strip along the wall
    rect(d, 0, top - 6, BASE_W, 1, rgb("#3ad6ff"))
    rect(d, 0, top - 3, BASE_W, 3, (14, 10, 32))  # skirting board

    # floor tiles with a few confetti specks (arcade carpet)
    for ty in range(top, BASE_H, 15):
        for tx in range(-5, BASE_W, 15):
            rect(d, tx, ty, 15, 15, FLOOR_A if ((tx + 5) // 15 + (ty - top) // 15) % 2 == 0 else FLOOR_B)
            rect(d, tx, ty, 15, 1, GROUT)
            rect(d, tx, ty, 1, 15, GROUT)
    _light_pools(d)
    rng = random.Random(7)
    for _ in range(120):
        x, y = rng.randrange(8, BASE_W - 8), rng.randrange(top + 4, BASE_H - 2)
        colour = mix(rng.choice(NEON), FLOOR_B, 0.4)
        rect(d, x, y, 2 if rng.random() < 0.5 else 1, 1 if rng.random() < 0.5 else 2, colour)

    _floor_lane(d)
    _dance_pad(d, *DANCE_PAD)

    # a round rug under each game table, tinted with the table's colour
    for key in ("uno", "checkers", "connect4"):
        cx, cy = hubmap.SPOTS[key]["center"]
        colour = TABLE_COLOURS[key]
        d.ellipse([cx - 40, cy - 14, cx + 40, cy + 28], fill=mix(colour, FLOOR_B, 0.55))
        d.ellipse([cx - 37, cy - 12, cx + 37, cy + 26], fill=mix(colour, FLOOR_B, 0.74))
        d.ellipse([cx - 30, cy - 8, cx + 30, cy + 22], outline=mix(colour, FLOOR_B, 0.5))

    # the side walls
    rect(d, 0, top, 6, BASE_H - top, (24, 17, 58))
    rect(d, BASE_W - 6, top, 6, BASE_H - top, (24, 17, 58))


def _lay(img: Image.Image, layer: Image.Image, xy=(0, 0)) -> None:
    """Put a see-through (RGBA) layer on top of an RGB picture, in place."""
    img.paste(layer, xy, layer)


@lru_cache(maxsize=2)
def _hub_background() -> Image.Image:
    img = new_base("#1c1642")
    top = hubmap.FLOOR_TOP
    _room_shell(img)

    # wall decoration (its own layer so the furniture can stand in front of it)
    wall = new_layer()
    d = ImageDraw.Draw(wall)
    _bunting(d)
    _poster(d, 61, 14, 13, 17, "#d93a9c", "star")
    _poster(d, 164, 12, 11, 15, "#2f6fe0", "ship")
    _poster(d, 6, 16, 13, 17, "#3aa655", "heart")
    stamp(img, outlined(wall))

    # furniture, all with a dark edge
    props = new_layer()
    d = ImageDraw.Draw(props)
    for game, (cx, body, screen) in enumerate(((88, "#5a3fa8", "#58c4d8"), (120, "#8a3f86", "#f0a060"),
                                               (152, "#3f5fae", "#8fd860"))):
        _machine(d, cx, top + 2, rgb(body), rgb(screen), game=game)
    _gumball(d, 68, top + 3)
    _claw_machine(d, 292, top + 3)
    _side_machine(d, 2, 82, rgb("#5a3fa8"), rgb("#ff7ac8"), True)
    _side_machine(d, 2, 124, rgb("#8a3f86"), rgb("#8fd860"), True)
    _side_machine(d, 306, 86, rgb("#3f5fae"), rgb("#58c4d8"), False)
    _side_machine(d, 306, 128, rgb("#5a3fa8"), rgb("#ffe94a"), False)
    _plant(d, 300, 177)
    _plant(d, 18, 177)

    # championship cabinet (gold, with a trophy on top)
    _machine(d, 43, top + 4, rgb("#d9a520"), rgb("#2a1a4a"), w=28, h=46, glow=True)
    _trophy(d, 43, top - 42)

    # store
    x0, x1 = 180, 268
    rect(d, x0, 16, x1 - x0, top - 14, (16, 12, 38))
    shelf_rng = random.Random(3)
    for shelf_y in (26, 36):
        rect(d, x0 + 3, shelf_y + 6, x1 - x0 - 6, 1, (110, 84, 56))
        for sx in range(x0 + 5, x1 - 6, 7):
            if abs(sx - 222) < 12:
                continue  # leave room for the shopkeeper
            rect(d, sx, shelf_y + 1, 4, 5, rgb(shelf_rng.choice(NEON)))
    sprites.draw_character(props, 224, 55, bots.look(bots.SHOPKEEPER), "down")
    rect(d, x0 - 4, 44, x1 - x0 + 8, 3, (214, 150, 86))
    rect(d, x0 - 2, 47, x1 - x0 + 4, top - 43, (138, 90, 51))
    for px in range(x0 + 6, x1, 14):
        rect(d, px, 49, 1, top - 47, (110, 70, 40))
    for i, ax in enumerate(range(x0 - 4, x1 + 4, 8)):
        rect(d, ax, 14, 8, 7, (232, 68, 58) if i % 2 == 0 else (243, 234, 210))
        rect(d, ax + 1, 21, 6, 1, (170, 44, 40) if i % 2 == 0 else (200, 190, 168))
    rect(d, x0 - 4, 14, 2, top - 10, (122, 90, 58))
    rect(d, x1 + 2, 14, 2, top - 10, (122, 90, 58))

    # door mat
    rect(d, 140, 173, 40, 7, (92, 61, 34))
    rect(d, 142, 175, 36, 3, (122, 84, 50))
    _lay(img, lighting.drop_shadow(props, (2, 3), 0.55))  # soft shadow of the furniture on wall and floor
    stamp(img, outlined(props))

    # A6: neon signs and light from the ceiling
    _neon_sign(img, 120, 9, "ARCADE", "#ff4fa3")
    _light_beams(img, ((120, 72, 168, top + 30), (224, 176, 272, top + 30), (43, 20, 66, top + 30)))
    return img


def hub_scene(actors, coins, prompts=(), champ_locked=True, glow=None, t=0, hud=True, hint=True):
    """Paint the arcade room.

    actors   list of dicts: name, look, pos (x, y), dir, step, tag (name tag spec), player (bool)
    prompts  list of dicts: text, key (keyboard letter or None), action, lock (bool)
    Returns (image, regions). A region is ((left, top, right, bottom), action) in screen pixels.
    """
    img = _hub_background().copy()
    d = ImageDraw.Draw(img)

    drawables = []
    for key in ("uno", "checkers", "connect4"):
        cx, cy = hubmap.SPOTS[key]["center"]
        drawables.append((cy + 4, 0, key, None))
    for actor in actors:
        drawables.append((actor["pos"][1], 1, None, actor))
    for _, _, table, actor in sorted(drawables, key=lambda item: (item[0], item[1])):
        if table:
            cx, cy = hubmap.SPOTS[table]["center"]
            _lay(img, lighting.soft_oval(50, 12, 0.55), (cx - 28, cy + 2))  # soft shadow under the table
            stamp(img, table_sprite(table, glow == table), (cx - TABLE_ORIGIN[0], cy - TABLE_ORIGIN[1]))
        else:
            x, y = actor["pos"]
            _lay(img, lighting.soft_oval(13, 5, 0.7), (x - 9, y - 5))  # soft shadow at the feet
            sprites.draw_character(img, x, y, actor["look"], actor.get("dir", "down"), actor.get("step", 0), t)

    for actor in actors:  # a warm light follows the player
        if actor.get("player"):
            img = lighting.light_pool(img, (actor["pos"][0], actor["pos"][1] - 6), 30)
    img = lighting.vignette(img, 0.45)
    big = upscale(img)
    regions = []

    # signs painted on the big picture
    panel(big, (224 * SCALE - 52, 4, 224 * SCALE + 52, 34), "#16122b", "#ffe94a", shadow=False)
    draw_text(big, (224 * SCALE, 19), "STORE", 2, "#ffe94a", "mm")
    draw_text(big, (43 * SCALE, 33 * SCALE), "#1", 2, "#ffe94a", "mm")
    if champ_locked:
        lock(big, 43 * SCALE - 10, 46 * SCALE, 3)
    for key in ("uno", "checkers", "connect4"):
        cx, cy = hubmap.SPOTS[key]["center"]
        colour = "#ffe94a" if glow == key else "#d9d4ff"
        draw_text(big, (cx * SCALE, (cy - 15) * SCALE), hubmap.SPOTS[key]["label"], 2, colour, "mb", shadow=INK)

    # name tags
    player = None
    for actor in sorted(actors, key=lambda a: a["pos"][1]):
        x, y = actor["pos"]
        sprites.draw_name_tag(big, x * SCALE, (y - 23) * SCALE - 4, actor["name"], actor.get("tag"), t)
        if actor.get("player"):
            player = actor

    # prompt bubbles next to the player
    if prompts and player:
        px, py = player["pos"]
        on_left = px > 200
        y = (py - 20) * SCALE
        for prompt in prompts:
            small = prompt.get("small")
            scale = 2
            tw, th = text_size(prompt["text"], scale)
            key_w = (text_size(prompt["key"], 2)[0] + 12 + 8) if prompt.get("key") else 0
            lock_w = 30 if prompt.get("lock") else 0
            w = tw + key_w + lock_w + 24
            h = 34 + (CHAR_H * 1 + 6 if small else 0)
            if small:
                w = max(w, text_size(small, 1)[0] + 24)
            x0 = (px - 12) * SCALE - w if on_left else (px + 12) * SCALE
            x0 = max(6, min(SCREEN_W - w - 12, x0))
            box = panel(big, (x0, y, x0 + w, y + h), "#ffffff" if not prompt.get("lock") else "#d9d4e6", INK)
            cursor = x0 + 12
            if prompt.get("lock"):
                lock(big, cursor, y + 5, 2, "#6b6880")
                cursor += lock_w - 8
            draw_text(big, (cursor, y + 17), prompt["text"], scale, INK, "lm")
            if prompt.get("key"):
                key_icon(big, cursor + tw + 8, y + 5, prompt["key"], 2, "#ffe94a")
            if small:
                draw_text(big, (x0 + 12, y + 31), small, 1, "#4a4660", "lt")
            if prompt.get("action"):
                regions.append((box, ("prompt", prompt["action"])))
            y += h + 10

    if hud:
        draw_coin_counter(big, coins)
    if hint:
        draw_text(big, (14, SCREEN_H - 10), "WALK: W A S D OR CLICK", 1, "#b9b3ee", "lb", shadow=INK)
    return big, regions


def draw_coin_counter(img, coins: int):
    label = f"X {coins}"
    w = text_size(label, 3)[0] + 58
    x0 = SCREEN_W - w - 12
    panel(img, (x0, 8, SCREEN_W - 12, 46), "#16122b", "#ffe94a", shadow=False)
    coin(img, x0 + 10, 15, 3)
    draw_text(img, (x0 + 44, 28), label, 3, "#ffe94a", "lm")


def zoom(img: Image.Image, centre, factor: float) -> Image.Image:
    """Zoom the picture in on a point (used when a game starts)."""
    w, h = img.width / factor, img.height / factor
    left = max(0, min(img.width - w, centre[0] - w / 2))
    top = max(0, min(img.height - h, centre[1] - h / 2))
    crop = img.crop((int(left), int(top), int(left + w), int(top + h)))
    return crop.resize(img.size, Image.NEAREST)


def fade(img: Image.Image, amount: float) -> Image.Image:
    """A dimmed copy of the picture: 0 leaves it as it is, 1 is completely black."""
    if not 0 <= amount <= 1:
        raise ValueError("a fade goes from 0 (the picture) to 1 (black)")
    img = img.convert("RGB")
    return Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), amount)


def fade_through_black(old: Image.Image, new: Image.Image, steps: int) -> list[Image.Image]:
    """The frames between two screens: the old picture fades to black, then the new one fades in.

    The old picture is already on screen and the new one is shown right after,
    so neither is in the list. The middle frame is plain black.
    """
    if steps < 1:
        raise ValueError("a fade needs at least one step")
    old = old.convert("RGB")
    if old.size != new.size:
        old = old.resize(new.size, Image.NEAREST)
    going = [fade(old, i / steps) for i in range(1, steps + 1)]
    coming = [fade(new, 1 - i / steps) for i in range(1, steps)]
    return going + coming


# ---------------------------------------------------------------- title screen

@lru_cache(maxsize=4)
def title_scene(t: int = 0) -> Image.Image:
    img = new_base("#120d2e")
    d = ImageDraw.Draw(img)
    for y in range(0, 110):
        rect(d, 0, y, BASE_W, 1, mix("#120d2e", "#3a1a5e", y / 110))
    rng = random.Random(11)
    for _ in range(60):
        rect(d, rng.randrange(BASE_W), rng.randrange(90), 1, 1, rgb(rng.choice(["#ffffff", "#ffe94a", "#3ad6ff"])))
    # neon floor grid
    rect(d, 0, 110, BASE_W, 70, (14, 10, 36))
    for i in range(9):
        y = 110 + int((i / 8) ** 1.8 * 70)
        rect(d, 0, y, BASE_W, 1, mix("#ff4fa3", "#120d2e", 0.35))
    for i in range(-10, 11):
        d.line([(160 + i * 12, 110), (160 + i * 60, 180)], fill=mix("#ff4fa3", "#120d2e", 0.45))
    # cabinets left and right
    for cx, body, screen in ((26, "#3a2f6b", "#3ad6ff"), (58, "#4a2f5f", "#ff4fa3"),
                             (262, "#2f3f6b", "#7cff3a"), (294, "#3a2f6b", "#ffe94a")):
        _machine(d, cx, 150, rgb(body), rgb(screen), w=26, h=62, glow=True)
    # the regulars
    for i, bot in enumerate(bots.BOTS):
        _lay(img, lighting.soft_oval(13, 5, 0.7), (100 + i * 30 - 9, 163))
        sprites.draw_character(img, 100 + i * 30, 168, bots.look(bot), "down", 0, t)
    img = lighting.vignette(img, 0.4)
    big = upscale(img)
    for line, y in (("ARCADE", 40), ("MASTERS", 150)):
        draw_text(big, (SCREEN_W // 2 + 6, y + 6), line, 12, "#3ad6ff", "mt")
        draw_text(big, (SCREEN_W // 2, y), line, 12, "#ff4fa3", "mt")
        draw_text(big, (SCREEN_W // 2 - 3, y - 3), line, 12, "#ffe94a", "mt")
    draw_text(big, (SCREEN_W // 2, 262), "UNO  -  CHECKERS  -  CONNECT FOUR", 2, "#d9d4ff", "mt", shadow=INK)
    return big


# ---------------------------------------------------------------- table view

def seat_positions(count: int) -> list[int]:
    """Base x positions of the opponents sitting across the table."""
    return {1: [160], 2: [106, 214], 3: [66, 160, 254]}.get(count, [160])


@lru_cache(maxsize=1)
def _table_backdrop() -> Image.Image:
    """The wall of the arcade as seen from a seat at a table (a little darker than in the room)."""
    img = new_base(WALL)
    d = ImageDraw.Draw(img)
    for i, y in enumerate(range(0, 72, 6)):
        rect(d, 0, y, BASE_W, 1, MORTAR)
        for x in range(-6 if i % 2 else 0, BASE_W, 12):
            rect(d, x, y, 1, 6, MORTAR)
    rect(d, 0, 0, BASE_W, 13, (16, 12, 34))  # dark strip behind the game's name
    rect(d, 0, 13, BASE_W, 1, rgb("#ff4fa3"))
    rect(d, 0, 15, BASE_W, 1, rgb("#3ad6ff"))
    props = new_layer()
    pd = ImageDraw.Draw(props)
    for game, (cx, body, screen) in enumerate(((14, "#5a3fa8", "#58c4d8"), (112, "#8a3f86", "#f0a060"),
                                               (208, "#3f5fae", "#8fd860"), (306, "#5a3fa8", "#ff7ac8"))):
        _machine(pd, cx, 72, rgb(body), rgb(screen), w=24, h=52, game=game % 3)
    stamp(img, outlined(props))
    return Image.blend(img, new_base("#0d0a1f"), 0.35)


def table_scene(kind, opponents, active=None, t=0):
    """First-person view of a game table with the opponents sitting across it.

    opponents: list of dicts with name, look and tag. active: name of whoever's turn it is.
    """
    img = _table_backdrop().copy()
    d = ImageDraw.Draw(img)
    xs = seat_positions(len(opponents))
    for x, opponent in zip(xs, opponents):
        sprites.draw_character(img, x, 72, opponent["look"], "down", 0, t, scale=2)
    felt = rgb(FELT[kind])
    d.polygon([(22, 66), (298, 66), (BASE_W, 92), (BASE_W, BASE_H), (0, BASE_H), (0, 92)], fill=felt)
    d.polygon([(22, 66), (298, 66), (304, 71), (16, 71)], fill=shade(felt, 1.5))
    d.line([(0, 92), (16, 71)], fill=shade(felt, 1.5))
    d.line([(BASE_W - 1, 92), (304, 71)], fill=shade(felt, 1.5))
    img = lighting.light_pool(img, (BASE_W // 2, 130), 120, strength=0.12)  # the lamp over the table
    img = lighting.vignette(img, 0.45)
    big = upscale(img)
    d = ImageDraw.Draw(big)
    for x, opponent in zip(xs, opponents):
        box = sprites.draw_name_tag(big, x * SCALE, 60, opponent["name"], opponent.get("tag"), t)
        if active == opponent["name"]:  # yellow frame = this player's turn
            d.rectangle([box[0] - 7, box[1] - 7, box[2] + 7, box[3] + 7], outline=(255, 233, 74), width=3)
    return big


# ---------------------------------------------------------------- pop-ups

def result_panel(img, title, line, coins=None, footer="ENTER"):
    """The box that appears when a free-play game ends."""
    out = darken(img, 0.6)
    lines = wrap(line, 34)
    h = 150 + len(lines) * 30 + (50 if coins else 0)
    x0, x1 = 150, SCREEN_W - 150
    y0 = (SCREEN_H - h) // 2
    panel(out, (x0, y0, x1, y0 + h), "#fff6da", INK, bw=6)
    draw_text(out, (SCREEN_W // 2, y0 + 30), title, 5, INK, "mt")
    y = draw_lines(out, (SCREEN_W // 2, y0 + 90), lines, 3, "#3b3560", "mt")
    if coins:
        label = f"+{coins} COINS"
        tw = text_size(label, 4)[0]
        cx = SCREEN_W // 2 - (tw + 40) // 2
        coin(out, cx, y + 6, 4)
        draw_text(out, (cx + 42, y + 8), label, 4, "#c98a12", "lt")
        y += 50
    _footer_hint(out, SCREEN_W // 2, y0 + h - 34, footer)
    return out


def _footer_hint(img, cx, y, key="ENTER", text="CONTINUE"):
    tw = text_size(text, 2)[0]
    kw = text_size(key, 2)[0] + 12
    x = cx - (tw + kw + 10) // 2
    key_icon(img, x, y, key, 2, "#ffe94a")
    draw_text(img, (x + kw + 10, y + 12), text, 2, INK, "lm")


def coin_pyramid(img, cx, bottom, rows=4, unit=3):
    size = 8 * unit
    for row in range(rows):
        count = rows - row
        y = bottom - (row + 1) * (size - unit * 2)
        x = cx - count * (size + unit) // 2
        for i in range(count):
            coin(img, x + i * (size + unit), y, unit)


def dialog_bubble(img, text, page=None, pages=None, with_coins=False, footer=True, title=None):
    """The big light-blue speech bubble used by the championship host."""
    out = darken(img, 0.5)
    x0, x1, y0, y1 = 110, SCREEN_W - 110, 130, 410
    panel(out, (x0, y0, x1, y1), LIGHT_BLUE, "#1b3a6b", bw=6)
    y = y0 + 34
    if title:
        draw_text(out, (SCREEN_W // 2, y), title, 3, "#1b3a6b", "mt")
        y += 44
    lines = wrap(text, 30)
    block_h = len(lines) * 30 + (90 if with_coins else 0)
    y = max(y, (y0 + y1) // 2 - block_h // 2 - (10 if footer else 0))
    y = draw_lines(out, (SCREEN_W // 2, y), lines, 3, INK, "mt")
    if with_coins:
        coin_pyramid(out, SCREEN_W // 2, y + 84)
    if page is not None and pages:
        draw_text(out, (x0 + 24, y1 - 22), f"{page}/{pages}", 2, "#4a6fa5", "lb")
    if footer:
        _footer_hint(out, x1 - 110, y1 - 44, "ENTER", "NEXT")
    return out


def rules_panel(img, lines):
    out = darken(img, 0.5)
    x0, x1, y0, y1 = 110, SCREEN_W - 110, 90, 450
    panel(out, (x0, y0, x1, y1), LIGHT_BLUE, "#1b3a6b", bw=6)
    draw_text(out, (SCREEN_W // 2, y0 + 28), "CHAMPIONSHIP RULES", 4, "#1b3a6b", "mt")
    y = y0 + 90
    for line in lines:
        for i, part in enumerate(wrap(line, 44)):
            draw_text(out, (x0 + 40, y), ("- " if i == 0 else "  ") + part, 2, INK, "lt")
            y += 26
        y += 8
    _footer_hint(out, SCREEN_W // 2, y1 - 44, "ENTER", "BACK")
    return out


def scoreboard(title, rows, max_points=6, progress=1.0, subtitle=None, headline=None, prize=None):
    """Championship standings with horizontal bars.

    rows: list of dicts with name, look, old (points before), new (points now), me (bool).
    progress 0..1 animates the bars growing from old to new.
    headline: big sentence (used on the final screen instead of the title). prize: coins won.
    """
    img = upscale(new_base("#191335"))
    d = ImageDraw.Draw(img)
    for x in range(0, SCREEN_W, 60):
        d.rectangle([x, 0, x + 29, SCREEN_H], fill=(30, 23, 66))
    x0, x1, y0, y1 = 90, SCREEN_W - 90, 24, SCREEN_H - 24
    panel(img, (x0, y0, x1, y1), "#eaf6ff", "#1b3a6b", bw=6)
    if headline:
        lines = wrap(headline, 30)[:3]
        top = draw_lines(img, (SCREEN_W // 2, y0 + 26), lines, 3, "#b3261e" if not prize else "#1b3a6b", "mt") + 4
        if prize:
            label = f"+{prize} COINS"
            tw = text_size(label, 3)[0]
            cx = SCREEN_W // 2 - (tw + 34) // 2
            coin(img, cx, top, 3)
            draw_text(img, (cx + 34, top + 2), label, 3, "#c98a12", "lt")
            top += 34
        top += 6
        row_h = min(62, (y1 - 60 - top) // max(1, len(rows)))
    else:
        draw_text(img, (SCREEN_W // 2, y0 + 26), title, 4, "#1b3a6b", "mt")
        if subtitle:
            draw_text(img, (SCREEN_W // 2, y0 + 70), subtitle, 2, "#4a6fa5", "mt")
        top = y0 + 108
        row_h = 70
    bar_x0, bar_x1 = x0 + 260, x1 - 90
    unit = (bar_x1 - bar_x0) / max_points
    half = 12 if row_h >= 60 else 9
    for i, row in enumerate(rows):
        ry = top + i * row_h
        mid = ry + (row_h - 8) // 2
        if row.get("me"):
            d.rectangle([x0 + 18, ry, x1 - 18, ry + row_h - 9], fill=(255, 246, 196))
        icon = sprites.head_icon(row["look"], 3 if row_h >= 60 else 2)
        img.paste(icon, (x0 + 32, mid - icon.height // 2), icon)
        draw_text(img, (x0 + 100, mid), row["name"], 3 if row_h >= 60 else 2, INK, "lm")
        d.rectangle([bar_x0, mid - half, bar_x1, mid + half], fill=(200, 220, 240))
        for tick in range(1, max_points):
            tx = int(bar_x0 + tick * unit)
            d.rectangle([tx, mid - half, tx + 1, mid + half], fill=(170, 195, 222))
        value = row["old"] + (row["new"] - row["old"]) * progress
        if value > 0:
            colour = rgb("#ffb81a") if row.get("me") else rgb("#3a78e8")
            d.rectangle([bar_x0, mid - half, int(bar_x0 + value * unit), mid + half], fill=colour)
            d.rectangle([bar_x0, mid - half, int(bar_x0 + value * unit), mid - half + 4], fill=shade(colour, 1.4))
        shown = row["new"] if progress >= 1 else int(value)
        draw_text(img, (bar_x1 + 28, mid), str(shown), 4, INK, "lm")
    _footer_hint(img, SCREEN_W // 2, y1 - 42, "ENTER", "CONTINUE")
    return img


def draw_button(img, box, label, scale=3, fill="#ffffff", ink=INK, key=None):
    """A chunky pixel button painted on a picture. Returns its box for click regions."""
    panel(img, box, fill, ink, bw=3, shadow=True)
    cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    if key:
        tw = text_size(label, scale)[0]
        kw = text_size(key, 2)[0] + 12
        x = cx - (tw + kw + 12) // 2
        draw_text(img, (x, cy + 1), label, scale, ink, "lm")
        key_icon(img, x + tw + 12, cy - 13, key, 2, "#ffe94a")
    else:
        draw_text(img, (cx, cy + 1), label, scale, ink, "mm")
    return tuple(int(v) for v in box)


def menu_panel(img, title, options):
    """A light-blue menu with one big button per option. Returns (image, regions)."""
    out = darken(img, 0.6)
    h = 110 + len(options) * 74
    x0, x1 = 250, SCREEN_W - 250
    y0 = (SCREEN_H - h) // 2
    panel(out, (x0, y0, x1, y0 + h), LIGHT_BLUE, "#1b3a6b", bw=6)
    draw_text(out, (SCREEN_W // 2, y0 + 28), title, 5, "#1b3a6b", "mt")
    regions = []
    y = y0 + 96
    for index, option in enumerate(options):
        box = draw_button(out, (x0 + 40, y, x1 - 40, y + 54), option["label"], 3 if len(option["label"]) < 16 else 2,
                          key=option.get("key"))
        regions.append((box, ("menu", option["action"])))
        y += 74
    return out, regions


def choice_buttons(img, options, y=330):
    """A row of buttons (for example YES / NO) on top of a picture. Returns regions."""
    regions = []
    width, gap = 200, 40
    total = len(options) * width + (len(options) - 1) * gap
    x = (SCREEN_W - total) // 2
    for option in options:
        box = draw_button(img, (x, y, x + width, y + 54), option["label"], 3, option.get("fill", "#ffffff"),
                          key=option.get("key"))
        regions.append((box, ("choice", option["action"])))
        x += width + gap
    return regions


def banner(title, coins=None, subtitle=None):
    """A wide strip used as the header of the store and the wardrobe."""
    img = Image.new("RGB", (SCREEN_W, 84), rgb("#1c1642"))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, SCREEN_W, 5], fill=rgb("#ff4fa3"))
    d.rectangle([0, 78, SCREEN_W, 83], fill=rgb("#3ad6ff"))
    draw_text(img, (24, 42), title, 5, "#ffe94a", "lm", shadow=INK)
    if subtitle:
        draw_text(img, (24 + text_size(title, 5)[0] + 24, 46), subtitle, 2, "#d9d4ff", "lm")
    if coins is not None:
        label = f"X {coins}"
        w = text_size(label, 3)[0] + 58
        x0 = SCREEN_W - w - 20
        panel(img, (x0, 22, SCREEN_W - 20, 60), "#16122b", "#ffe94a", shadow=False)
        coin(img, x0 + 10, 29, 3)
        draw_text(img, (x0 + 44, 42), label, 3, "#ffe94a", "lm")
    return img


# ---------------------------------------------------------------- how to play (task A3)

HOWTO_BOX = (90, 30, SCREEN_W - 90, SCREEN_H - 30)  # left, top, right, bottom of the panel
_HOWTO_KEY_W = 200  # width of the column with the keys
_HOWTO_MAX_ROWS = 7


def howto_panel(img, tabs, current):
    """The "How to play" panel on top of a dimmed picture. Returns (image, regions).

    tabs: the list in arcade/controls.py. current: the key of the tab to show.
    Text that would not fit inside the panel is refused (ValueError) instead of
    being drawn over its edge.
    """
    chosen = next((tab for tab in tabs if tab["key"] == current), None)
    if chosen is None:
        raise ValueError(f"no such tab: {current}")
    x0, y0, x1, y1 = HOWTO_BOX
    text_x = x0 + 40 + _HOWTO_KEY_W + 20
    if len(chosen["rows"]) > _HOWTO_MAX_ROWS:
        raise ValueError("too many rows for the panel")
    for key, what in chosen["rows"]:
        if text_size(key, 2)[0] + 16 > _HOWTO_KEY_W:
            raise ValueError(f"key label too long: {key}")
        if text_x + text_size(what, 2)[0] > x1 - 30:
            raise ValueError(f"line too long: {what}")
    goal = wrap(chosen["goal"], 54)
    if len(goal) > 2:
        raise ValueError("the goal must fit on two lines")

    out = darken(img, 0.6)
    panel(out, HOWTO_BOX, LIGHT_BLUE, "#1b3a6b", bw=6)
    draw_text(out, (SCREEN_W // 2, y0 + 22), "HOW TO PLAY", 4, "#1b3a6b", "mt")

    regions = []
    gap = 12
    tab_w = (x1 - x0 - 60 - gap * (len(tabs) - 1)) // len(tabs)
    for i, tab in enumerate(tabs):
        left = x0 + 30 + i * (tab_w + gap)
        box = (left, y0 + 66, left + tab_w, y0 + 106)
        selected = tab["key"] == current
        draw_button(out, box, tab["label"], 2, "#ffe94a" if selected else "#ffffff")
        regions.append((box, ("tab", tab["key"])))

    y = draw_lines(out, (SCREEN_W // 2, y0 + 128), goal, 2, "#1b3a6b", "mt", gap=4)
    y += 14
    for key, what in chosen["rows"]:
        tw = text_size(key, 2)[0]
        kx = x0 + 40 + _HOWTO_KEY_W - tw - 16  # keys are right-aligned against the descriptions
        key_icon(out, kx, y, key, 2, "#ffffff")
        draw_text(out, (text_x, y + 9), what, 2, INK, "lm")
        y += 40
    _footer_hint(out, SCREEN_W // 2, y1 - 44, "ESC", "BACK")
    return out, regions
