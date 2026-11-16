"""Visual update, idea 3: light and shadow."""

import pytest
from PIL import Image

from arcade.art import lighting


def _grey(size=(160, 90), value=180):
    return Image.new("RGB", size, (value, value, value))


def test_a_vignette_darkens_the_corners_more_than_the_middle():
    out = lighting.vignette(_grey(), 0.5)
    middle, corner = out.getpixel((80, 45))[0], out.getpixel((0, 0))[0]
    assert middle == 180  # the middle is untouched
    assert corner < middle


def test_a_vignette_of_zero_changes_nothing():
    img = _grey()
    assert lighting.vignette(img, 0).tobytes() == img.tobytes()


@pytest.mark.parametrize("strength", [-0.5, 2])
def test_a_strength_outside_zero_to_one_is_rejected(strength):
    with pytest.raises(ValueError):
        lighting.vignette(_grey(), strength)
    with pytest.raises(ValueError):
        lighting.light_pool(_grey(), (80, 45), 20, strength=strength)


def test_a_drop_shadow_falls_beside_the_shape_not_on_empty_space():
    layer = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    layer.paste((255, 0, 0, 255), (10, 10, 20, 20))
    shadow = lighting.drop_shadow(layer, (3, 3), 0.5, blur=0.5)
    assert shadow.getpixel((21, 21))[3] > 0  # just below-right of the shape
    assert shadow.getpixel((35, 2))[3] == 0  # far from it: nothing


def test_a_light_pool_brightens_near_the_centre_and_never_darkens():
    img = _grey(value=60)
    out = lighting.light_pool(img, (80, 45), 30)
    assert out.getpixel((80, 45))[0] > 60
    assert out.getpixel((0, 0))[0] == 60
    assert all(a >= b for a, b in zip(out.tobytes(), img.tobytes()))


def test_the_original_picture_is_not_changed():
    img = _grey()
    before = img.tobytes()
    lighting.vignette(img, 0.6)
    lighting.light_pool(img, (10, 10), 10)
    assert img.tobytes() == before


def test_the_room_title_and_table_still_draw_with_the_lighting():
    from arcade import bots, catalog
    from arcade.art import scenes
    from arcade.config import SCREEN_H, SCREEN_W
    actors = [{"name": b["name"], "look": bots.look(b), "pos": b["home"], "dir": b["dir"],
               "tag": catalog.spec_for("name", b["tag"])} for b in bots.BOTS]
    actors.append(dict(actors[0], name="ME", pos=(160, 150), player=True))
    room, _ = scenes.hub_scene(actors, 0)
    table = scenes.table_scene("uno", actors[:3])
    for picture in (room, table, scenes.title_scene(0)):
        assert picture.size == (SCREEN_W, SCREEN_H)
