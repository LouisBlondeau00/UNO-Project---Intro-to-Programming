# Task: V4, sharper text with an openly licensed pixel font

## Why
All text on the pictures uses the game's own 5x7 font. It is readable but looks like an early home computer.

## What
- Text painted on the pictures (titles, labels, menus, panels) uses **Jersey 10**, a pixel font under the SIL
  Open Font License. The font file and its licence are in `arcade/art/fonts/`.
- It is drawn without smoothing, at sizes where its capitals are exactly as tall as the old letters, so no
  layout moves. It is a little narrower, so long lines fit better.
- The smallest text (scale 1, for example the walking hint) keeps the old 5x7 font, which reads better that small.
- `TEXT_FONT = None` in `arcade/config.py` brings back the old font everywhere.

## Out of scope
- Changing any wording, or the font of the buttons under the picture (V1).

## Done when
- A test shows the font file and its licence are in the repository.
- A test shows capitals keep the old height at every scale, and the width given matches what is drawn.
- A test shows C and O do not look the same (a font we tried first failed this).
- A test shows scale 1 keeps the built-in font.
- Checked by hand: title, room, How to play, pause menu, store and a table.
