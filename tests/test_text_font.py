"""Visual update, idea 4: text drawn with an openly licensed pixel font."""

import pytest

from arcade.art import font, pixel


def test_the_font_file_and_its_licence_are_in_the_repository():
    from arcade.config import TEXT_FONT
    assert (pixel.FONT_DIR / TEXT_FONT).is_file()
    assert "SIL Open Font License" in (pixel.FONT_DIR / "OFL.txt").read_text()


@pytest.mark.parametrize("scale", [2, 3, 5])
def test_capital_letters_keep_the_old_height_so_layouts_do_not_move(scale):
    assert pixel.text_size("HELLO", scale)[1] == font.GLYPH_H * scale


def test_the_width_matches_what_is_drawn():
    from PIL import Image
    img = Image.new("RGB", (400, 60))
    box = pixel.draw_text(img, (10, 10), "CHECKERS", 3)
    assert box[2] - box[0] == pixel.text_size("CHECKERS", 3)[0]
    assert img.getbbox()[2] <= box[2] + 1  # nothing drawn to the right of the box


def test_c_and_o_look_different():
    assert pixel._text_mask("C", 2).tobytes() != pixel._text_mask("O", 2).tobytes()


def test_the_smallest_text_keeps_the_built_in_font():
    assert pixel.text_size("WALK", 1)[0] == font.width("WALK")


def test_an_empty_text_has_no_width():
    assert pixel.text_size("", 2)[0] == 0
