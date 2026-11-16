# Task: V3, lighting and shadows

## Why
Everything in the pictures is lit the same way and nothing casts a shadow, so the scenes look flat.

## What
New `arcade/art/lighting.py` (plain Pillow, no Streamlit), used by `arcade/art/scenes.py`:
- a vignette: the edges and corners of the room, the title screen and the table view are a little darker;
- soft, blurred shadows: under the furniture of the room, under each table, under every character;
- a warm light that follows the player in the room, and a lamp over the game table.

## Out of scope
- The neon glow (V2) and animations (V5).
- Light that changes over time.

## Done when
- Tests show the vignette darkens the corners more than the middle, and strength 0 changes nothing.
- Tests show a strength outside 0 to 1 is rejected.
- Tests show a drop shadow falls beside a shape and not on empty space.
- Tests show the light only brightens, more near its centre, and the original picture is untouched.
- A test shows the room, the title and the table view still draw at 960x540.
- Checked by hand in the browser.
