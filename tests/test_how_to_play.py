"""A3: the "How to play" panel lists the keys for the room and each table."""

import pytest
from PIL import Image

from arcade import controls
from arcade.art import scenes
from arcade.config import GAMES, SCREEN_H, SCREEN_W


def _background():
    return Image.new("RGB", (SCREEN_W, SCREEN_H), (40, 30, 80))


def test_there_is_a_tab_for_the_room_and_each_game():
    assert controls.TAB_KEYS == ["room"] + GAMES


def test_the_room_tab_lists_walking_playing_and_pausing():
    keys = [key for key, _ in controls.TABS[0]["rows"]]
    assert {"W A S D", "E", "ESC"} <= set(keys)


@pytest.mark.parametrize("tab", controls.TAB_KEYS)
def test_every_tab_can_be_drawn(tab):
    img, regions = scenes.howto_panel(_background(), controls.TABS, tab)
    assert img.size == (SCREEN_W, SCREEN_H)
    assert [action for _, action in regions] == [("tab", key) for key in controls.TAB_KEYS]


def test_a_click_on_a_tab_lands_on_that_tab_only():
    _, regions = scenes.howto_panel(_background(), controls.TABS, "room")
    for (left, top, right, bottom), action in regions:
        x, y = (left + right) / 2, (top + bottom) / 2
        under = [other for (l, t, r, b), other in regions if l <= x <= r and t <= y <= b]
        assert under == [action]


def test_a_click_outside_the_tabs_selects_nothing():
    _, regions = scenes.howto_panel(_background(), controls.TABS, "room")
    x, y = 5, 5  # the top-left corner of the screen, outside the panel
    assert not [action for (l, t, r, b), action in regions if l <= x <= r and t <= y <= b]


def test_an_unknown_tab_is_rejected():
    with pytest.raises(ValueError):
        scenes.howto_panel(_background(), controls.TABS, "poker")


def test_a_line_too_long_for_the_panel_is_rejected():
    too_long = [dict(controls.TABS[0], rows=[("E", "A DESCRIPTION FAR TOO LONG TO FIT INSIDE THE PANEL, EVEN WITH A NARROW FONT")])]
    with pytest.raises(ValueError):
        scenes.howto_panel(_background(), too_long, "room")


def test_a_key_label_too_long_for_its_column_is_rejected():
    too_long = [dict(controls.TABS[0], rows=[("CLICK ANYWHERE YOU LIKE", "WALK")])]
    with pytest.raises(ValueError):
        scenes.howto_panel(_background(), too_long, "room")


def test_the_panel_does_not_change_the_background_picture():
    background = _background()
    scenes.howto_panel(background, controls.TABS, "uno")
    assert background.getpixel((0, 0)) == (40, 30, 80)
