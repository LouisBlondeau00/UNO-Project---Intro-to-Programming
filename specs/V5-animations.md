# Task: V5, small animations

## Why
Apart from walking, nothing on screen moves, which makes the game feel static and old.

## What
- **Title screen:** stars twinkle, the neon floor grid slides towards you, and the five regulars bounce and
  blink. The picture redraws itself every 0.4 s (`TITLE_EVERY` in `arcade/config.py`) with
  `st.fragment(run_every=...)`, looping through 8 frames that are drawn once and cached.
- **Room:** characters blink now and then, and rainbow hair and sparkly shirts animate. They use a clock
  of two ticks a second. Together with A4 (idle bots), the room redraws itself, so the blinks show even when
  you stand still.
- **Winning:** the result box gets a burst of confetti around it, and the coin gets sparkles.
- Everything new is original pixel art drawn in `arcade/art/scenes.py`.

## Out of scope
- Animations inside the game tables (stream B), and an animated confetti fall (the box is drawn once).

## Done when
- A test shows a blink changes only the eyes, and only into skin colour.
- A test shows a character seen from behind does not blink, and nothing that is not an eye is ever painted over.
- A test shows the title screen changes from one frame to the next and loops after `TITLE_FRAMES`.
- A test shows confetti only comes with a win, and stays off the box.
- Checked by hand: the title moves while you type your name, and the room still works.
