import json
import os
import pygame


PREFERENCES_FILE = "preferences.json"


PREFERENCES = {
    "difficulty": "normal",
    "mobilecontrols": False,
    "master_volume": 1.0,
    "sfx_volume": 1.0,
    "music_volume": 1.0,
}


DIFFICULTIES = {
    "easy": {
        "enemy_speed": 0.8,
        "enemy_fire_rate": 0.8,
        "score_multiplier": 0.8,
        "lives": 5,
    },
    "normal": {
        "enemy_speed": 1.0,
        "enemy_fire_rate": 1.0,
        "score_multiplier": 1.0,
        "lives": 3,
    },
    "hard": {
        "enemy_speed": 1.25,
        "enemy_fire_rate": 1.25,
        "score_multiplier": 1.5,
        "lives": 3,
    },
}


# Used by settings_screen.py
DIFFICULTY_ORDER = ("easy", "normal", "hard")


WHITE = (255, 255, 255)
CYAN = (80, 220, 255)
RED = (255, 80, 100)
GOLD = (255, 205, 80)

BUTTON_IDLE = (35, 45, 65)
BUTTON_HOVER = (55, 75, 100)


def save_preferences(preferences=None):
    """
    Save the current game preferences to preferences.json.
    """

    global PREFERENCES

    if preferences is not None:
        PREFERENCES.update(preferences)

    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as file:
            json.dump(PREFERENCES, file, indent=4)

    except Exception as e:
        print(f"Could not save preferences: {e}")


def load_preferences():
    """
    Load saved preferences if preferences.json exists.
    """

    global PREFERENCES

    if not os.path.exists(PREFERENCES_FILE):
        return PREFERENCES

    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)

        if isinstance(saved, dict):
            for key in PREFERENCES:
                if key in saved:
                    PREFERENCES[key] = saved[key]

    except Exception as e:
        print(f"Could not load preferences: {e}")

    # Validate difficulty
    if PREFERENCES.get("difficulty") not in DIFFICULTIES:
        PREFERENCES["difficulty"] = "normal"

    # Validate mobile controls
    PREFERENCES["mobilecontrols"] = bool(
        PREFERENCES.get("mobilecontrols", False)
    )

    # Validate volume values
    for key in ("master_volume", "sfx_volume", "music_volume"):
        try:
            PREFERENCES[key] = max(
                0.0,
                min(1.0, float(PREFERENCES.get(key, 1.0)))
            )
        except (TypeError, ValueError):
            PREFERENCES[key] = 1.0

    return PREFERENCES


def apply_volume_settings():
    """
    Apply the saved music volume to pygame's music mixer.
    """

    try:
        if not pygame.mixer.get_init():
            return

        master = float(PREFERENCES.get("master_volume", 1.0))
        music = float(PREFERENCES.get("music_volume", 1.0))

        master = max(0.0, min(1.0, master))
        music = max(0.0, min(1.0, music))

        pygame.mixer.music.set_volume(master * music)

    except Exception as e:
        print(f"Could not apply volume settings: {e}")


# Load saved preferences when the settings module starts.
load_preferences()