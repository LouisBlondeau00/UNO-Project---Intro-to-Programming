"""Numbers and settings shared by the whole game.

Change values here instead of hunting for them inside the screens.
"""

GAME_TITLE = "ARCADE MASTERS"

# Every picture is painted on a small canvas and blown up 3x, which is what
# gives the game its chunky pixel-art look.
BASE_W, BASE_H, SCALE = 320, 180, 3
SCREEN_W, SCREEN_H = BASE_W * SCALE, BASE_H * SCALE

# Rewards
COINS_PER_WIN = 5
CHAMPIONSHIP_PRIZE = 50
POINTS_WIN = 2
POINTS_TIE = 1

# Store prices by rarity
PRICES = {"common": 20, "rare": 100, "legendary": 500}
RARITIES = ["legendary", "rare", "common"]
SLOTS = ["hair", "shirt", "name"]
SLOT_LABELS = {"hair": "Hair", "shirt": "Shirt", "name": "Name"}

# Games
GAMES = ["uno", "checkers", "connect4"]
GAME_LABELS = {"uno": "UNO", "checkers": "CHECKERS", "connect4": "CONNECT FOUR"}
BOTS_PER_GAME = {"uno": 3, "checkers": 1, "connect4": 1}
CHAMPIONSHIP_BOTS = 3

# How strong the bots are. Lower depth and higher blunder = easier to beat.
CHECKERS_DEPTH = 2
CHECKERS_BLUNDER = 0.3
CONNECT4_DEPTH = 2
CONNECT4_BLUNDER = 0.2
SIMULATED_TIE_CHANCE = 0.1  # bot-versus-bot Connect Four in the championship

# Player name rules
NAME_MIN, NAME_MAX = 1, 10

# Animation (set ANIMATIONS to False to make every screen change instant)
ANIMATIONS = True
FRAME_DELAY = 0.045
BOT_DELAY = 0.7

# Fade to black between screens (task A1): frames down to black (and the same back up), and the time per frame
FADE_STEPS = 5
FADE_DELAY = 0.035

# Bots shuffle and turn while idle (task A4): seconds between two idle moments in the room
IDLE_EVERY = 1.2

# Soft neon glow around bright colours on every picture (visual update, idea 2). Costs about 20 ms a picture.
GLOW = True

# Font for all text painted on the pictures (visual update, idea 4): a file in arcade/art/fonts/,
# or None for the old built-in 5x7 font
TEXT_FONT = "Jersey10-Regular.ttf"

# Title screen animation (visual update, idea 5): seconds between two frames
TITLE_EVERY = 0.4
