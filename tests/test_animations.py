"""Visual update, idea 5: small animations."""

from PIL import Image, ImageChops

from arcade import bots
from arcade.art import scenes, sprites

LOOK = bots.look(bots.BOTS[0])
SKIN = scenes.rgb(LOOK[0])


def _character(direction):
    img = Image.new("RGB", (60, 60), (40, 30, 80))
    sprites.draw_character(img, 30, 50, LOOK, direction)
    return img


def _changed(a, b):
    box = ImageChops.difference(a, b).getbbox()
    return box


def test_a_blink_paints_only_the_eyes_with_skin():
    img = _character("down")
    before = img.copy()
    scenes.blink(img, 30, 50, LOOK[0], "down")
    box = _changed(before, img)
    assert box is not None  # something closed
    left, top, right, bottom = box
    assert right - left <= 5 and bottom - top <= 2  # two small eyes, nothing else
    for x in range(left, right):
        for y in range(top, bottom):
            if img.getpixel((x, y)) != before.getpixel((x, y)):
                assert img.getpixel((x, y)) == SKIN


def test_a_character_seen_from_behind_does_not_blink():
    img = _character("up")
    before = img.copy()
    scenes.blink(img, 30, 50, LOOK[0], "up")
    assert _changed(before, img) is None


def test_a_blink_never_paints_over_something_that_is_not_an_eye():
    img = Image.new("RGB", (60, 60), (200, 10, 10))  # no eyes anywhere
    before = img.copy()
    for direction in ("down", "left", "right"):
        scenes.blink(img, 30, 50, LOOK[0], direction)
    assert _changed(before, img) is None


def test_side_views_blink_too():
    for direction in ("left", "right"):
        img = _character(direction)
        before = img.copy()
        scenes.blink(img, 30, 50, LOOK[0], direction)
        assert _changed(before, img) is not None, direction


def test_the_title_screen_moves_and_loops():
    first = scenes.title_scene(0)
    assert _changed(first, scenes.title_scene(1)) is not None
    assert _changed(first, scenes.title_scene(scenes.TITLE_FRAMES)) is None


def test_confetti_only_comes_with_a_win():
    table = Image.new("RGB", (scenes.SCREEN_W, scenes.SCREEN_H), (60, 20, 30))
    win = scenes.result_panel(table, "VICTORY!", "WELL PLAYED", 5)
    loss = scenes.result_panel(table, "GAME OVER", "WELL PLAYED", 0)
    corner = (0, 0, 140, scenes.SCREEN_H)  # left of the box
    assert len(set(win.crop(corner).get_flattened_data())) > len(set(loss.crop(corner).get_flattened_data()))


def test_confetti_stays_off_the_box():
    img = Image.new("RGB", (scenes.SCREEN_W, scenes.SCREEN_H), (0, 0, 0))
    box = (300, 200, 660, 340)
    scenes.confetti(img, box)
    assert img.crop(box).getbbox() is None  # the box area is still empty
    assert img.getbbox() is not None
