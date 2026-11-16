"""The arcade room: walk with W A S D (or click where you want to go), then press E at a table, the store or the championship."""

from __future__ import annotations

import time

import streamlit as st

from arcade import bots, hubmap, idle, match, state, ui
from arcade.art import scenes
from arcade.config import ANIMATIONS, FRAME_DELAY, GAMES, IDLE_EVERY, SCALE
from arcade.logic import championship
from arcade.state import S
from arcade import sound  # A7 (own line, so it merges cleanly with A4)

_LABELS = {"uno": "Play UNO", "checkers": "Play checkers", "connect4": "Play Connect Four",
           "store": "Enter the store", "champ": "Start championship"}
_STEP = 8  # how far one step moves you (the walking keys send about ten steps a second)


def _prompts(near: str | None) -> list[dict]:
    """The bubbles shown next to the player."""
    if near in GAMES:
        return [{"text": "PLAY", "key": "E", "action": "interact"}]
    if near == "store":
        return [{"text": "SHOP", "key": "E", "action": "interact"}]
    if near == "champ":
        if not championship.is_unlocked(S.player):
            return [{"text": "LOCKED", "lock": True, "small": "MUST MASTER ALL GAMES TO UNLOCK"}]
        bubbles = [{"text": "START CHAMPIONSHIP", "key": "E", "action": "interact"}]
        if S.player["champ_intro_seen"]:
            bubbles.append({"text": "RULES", "key": "I", "action": "rules"})
        return bubbles
    return []


def picture(prompts=(), glow=None, overrides=None, hint=True):
    locked = not championship.is_unlocked(S.player)
    t = int(time.time() * 2) % 36  # V5: a clock for small animations (blinks, rainbow hair), two ticks a second
    return scenes.hub_scene(state.hub_actors(overrides), S.player["coins"], prompts, locked, glow, t=t, hint=hint)


def _animate_walk(slot) -> None:
    """Play the pending walk, put everyone on their new spot, then do what comes next."""
    hub = S.hub
    walk = hub["walk"]
    movers = walk["movers"]
    longest = max(hubmap.distance(start, end) for start, end, _ in movers.values())
    frames = max(1, min(24, round(longest / 6)))
    if ANIMATIONS and longest > 1:
        for i in range(1, frames + 1):
            t = i / frames
            overrides = {}
            for name, (start, end, face) in movers.items():
                moving = hubmap.distance(start, end) > 1
                pos = (round(start[0] + (end[0] - start[0]) * t), round(start[1] + (end[1] - start[1]) * t))
                overrides[name] = (pos, hubmap.facing(start, end) if moving else face, 1 + (i // 2) % 2 if moving else 0)
            ui.show(slot, picture(overrides=overrides, hint=False)[0])
            time.sleep(FRAME_DELAY)

    me = S.player["name"]
    for name, (_, end, face) in movers.items():
        if name == me:
            hub["pos"], hub["dir"] = end, face
        else:
            hub["bots"][name] = {"pos": end, "dir": face}
    hub["walk"] = None

    if walk.get("zoom"):
        if ANIMATIONS:
            still = picture(glow=walk["zoom"], hint=False)[0]
            cx, cy = hubmap.SPOTS[walk["zoom"]]["center"]
            ui.play_frames(slot, (scenes.zoom(still, (cx * SCALE, cy * SCALE), f) for f in (1.0, 1.2, 1.5, 1.9, 2.4, 3.0)),
                           0.06)
            time.sleep(0.12)
    if walk.get("then") == "start_game":
        ui.fade_next()  # from the zoomed table to the game, through black
        match.start_game()
    st.rerun()


def _bot_spots() -> list:
    """Where the bots stand: the player cannot walk through them (A5)."""
    return [bot["pos"] for bot in S.hub["bots"].values()]


def _step(slot, dx: int, dy: int) -> None:
    """One press of W, A, S or D: turn that way and take a step (with a quick half-way frame)."""
    hub = S.hub
    start = hub["pos"]
    direction = hubmap.facing(start, (start[0] + dx, start[1] + dy))
    target = hubmap.step_from(start, dx, dy, _STEP, _bot_spots())
    hub["stride"] = 2 if hub.get("stride") == 1 else 1  # alternate legs
    if ANIMATIONS and slot is not None and target != start:
        halfway = ((start[0] + target[0]) // 2, (start[1] + target[1]) // 2)
        overrides = {S.player["name"]: (halfway, direction, hub["stride"])}
        ui.show(slot, picture(overrides=overrides, hint=False)[0])
        time.sleep(0.03)
    hub["pos"], hub["dir"] = target, direction


def _walk_to(target, face=None) -> None:
    hub = S.hub
    target = hubmap.walk_line(hub["pos"], hubmap.clamp(*target), _bot_spots())  # stops before a bot or table
    if hubmap.distance(hub["pos"], target) < 2:
        return
    final = face or hubmap.facing(hub["pos"], target)
    hub["walk"] = {"movers": {S.player["name"]: (hub["pos"], target, final)}}


def _interact(near: str | None) -> None:
    if near in GAMES:
        sound.play("table")
        match.begin_free_play(near)
    elif near == "store":
        sound.play("coin")
        state.go("store")
    elif near == "champ" and championship.is_unlocked(S.player):
        if S.player["champ_intro_seen"]:
            match.begin_championship()
        else:
            S.intro_page = 0
            state.go("champ_intro")


@st.fragment(run_every=IDLE_EVERY if ANIMATIONS else None)
def _room_view() -> None:
    """The room picture. It also redraws itself every IDLE_EVERY seconds so the bots can shuffle (A4).

    A run of the whole page (a click or a key) walks the player first. A timed
    run of only this part does nothing but move the idle bots and redraw.
    """
    if S.screen != "hub":
        return
    hub = S.hub
    whole_page = S.pop("_hub_page_run", False)
    slot = ui.screen()
    if whole_page:
        if hub.get("walk"):
            _animate_walk(slot)
        step = ui.move()
        if step:  # a walking key is held down: take the step first, then draw the room as usual
            _step(slot, *step)
    elif not hub.get("walk"):
        homes = {bot["name"]: bot["home"] for bot in bots.BOTS}
        hub["bots"] = idle.idle_tick(hub["bots"], homes, hub["pos"], state.rng())

    near = hubmap.near_spot(hub["pos"])
    img, regions = picture(_prompts(near), near if near in GAMES else None)
    ui.show(slot, img)
    S["_hub_regions"] = regions


def render() -> None:
    hub = S.hub
    S._hub_page_run = True
    _room_view()
    near = hubmap.near_spot(hub["pos"])
    locked = not championship.is_unlocked(S.player)
    point = ui.click()
    action = ui.hit(S.get("_hub_regions", []), point)

    can_use = near is not None and not (near == "champ" and locked)
    can_read_rules = near == "champ" and not locked and S.player["champ_intro_seen"]
    bar = st.columns([2.4, 1.1, 0.55, 0.55, 0.55, 0.55, 1.1])
    with bar[0]:
        use = ui.button(_LABELS.get(near, "Walk up to a table"), "hub_use", "E", type="primary", disabled=not can_use)
    with bar[1]:
        rules = ui.button("Rules", "hub_rules", "I", disabled=not can_read_rules)
    arrows = {}
    for column, (label, name, delta) in zip(bar[2:6], (("↑", "up", (0, -1)), ("←", "left", (-1, 0)),
                                                        ("↓", "down", (0, 1)), ("→", "right", (1, 0)))):
        with column:  # for mouse and touch screens; on a keyboard use W A S D or the arrow keys
            arrows[delta] = ui.button(label, f"hub_step_{name}")
    with bar[6]:
        pause = ui.button("Pause", "hub_pause", "Esc")

    if pause:
        sound.play("pause")
        S.paused_from = "hub"
        state.go("pause")
        st.rerun()
    if (use and can_use) or action == ("prompt", "interact"):
        _interact(near)
        st.rerun()
    if (rules and can_read_rules) or action == ("prompt", "rules"):
        state.go("champ_rules")
        st.rerun()
    for (dx, dy), pressed in arrows.items():
        if pressed:
            _step(None, dx, dy)  # no half-way frame here: the next run draws the room
            st.rerun()
    if point is not None and action is None:
        base = hubmap.to_base(*point)
        spot = hubmap.spot_at(*base) or hubmap.table_at(hubmap.clamp(*base))
        if spot:
            _walk_to(hubmap.SPOTS[spot]["stand"], "up")
        else:
            _walk_to(base)
        st.rerun()
