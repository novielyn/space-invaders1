import os
import json
import math
import random

import pygame

try:
    from screens.login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, HEART, RED, GREEN,
    )
except ImportError:
    from login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, HEART, RED, GREEN,
    )

# ---------------------------------------------------------------
# Profile in the same cozy desktop style as the other screens.
#
# Everything above the ProfileScreen class (settings, statistics,
# ship loading, database helpers) is unchanged in behaviour, so any
# other file that imports get_game_statistics, load_game_player_ship,
# get_game_loadout, etc. keeps working.
#
#   ProfileScreen(screen, w, h, player)
#   update(events, dt=0.0) -> "menu" | "delete_account" | None
#   draw()
#   profile_screen(screen, clock, player) -> "menu" | "delete_account" | "quit"
# ---------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROFILE_SETTINGS_FILE = os.path.join(BASE_DIR, "profile_settings.json")

BG_IMAGE = os.path.join(BASE_DIR, "assets", "images", "background.jpg")

PREFERENCES = {}


# ===============================================================
# helpers (same behaviour as before)
# ===============================================================

def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def get_value(data, *keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if data.get(key) is not None:
            return data[key]

    return default


def load_settings(player_id=None):
    if not os.path.exists(PROFILE_SETTINGS_FILE):
        return {}

    try:
        with open(PROFILE_SETTINGS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        if player_id is not None:
            key = str(player_id)
            if key in data and isinstance(data[key], dict):
                return dict(data[key])

        return dict(data)

    except Exception:
        return {}


def save_settings(player_id, settings):
    if player_id is None:
        return

    try:
        existing = {}

        if os.path.exists(PROFILE_SETTINGS_FILE):
            with open(PROFILE_SETTINGS_FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)
                if isinstance(loaded, dict):
                    existing = loaded

        existing[str(player_id)] = settings

        with open(PROFILE_SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(existing, file, indent=4)

    except Exception:
        pass


def get_game_statistics(player_id, player=None):
    """
    Reads gameplay statistics from both the database/player dictionary
    and player-specific profile_settings.json, merging the values so the
    Profile can still show statistics when the database lacks newer fields.
    """

    player = player if isinstance(player, dict) else {}

    cached = load_settings(player_id)
    if not isinstance(cached, dict):
        cached = {}

    nested_keys = ("statistics", "stats", "game_statistics", "game_stats")

    sources = [player]

    for key in nested_keys:
        nested = player.get(key)
        if isinstance(nested, dict):
            sources.append(nested)

    sources.append(cached)

    for key in nested_keys:
        nested = cached.get(key)
        if isinstance(nested, dict):
            sources.append(nested)

    def read(convert, *keys):
        values = []
        for source in sources:
            value = get_value(source, *keys, default=None)
            if value is not None:
                values.append(convert(value))
        return max(values) if values else convert(0)

    def read_int(*keys):
        return read(safe_int, *keys)

    def read_float(*keys):
        return read(safe_float, *keys)

    games_played = read_int("games_played", "total_games", "games")
    total_kills = read_int("total_kills", "kills", "ships_destroyed",
                           "enemies_killed", "enemy_kills")
    shots_fired = read_int("shots_fired", "total_shots", "shots")
    shots_hit = read_int("shots_hit", "total_hits", "hits")
    best_wave = read_int("best_wave", "highest_wave", "max_wave")
    last_wave = read_int("last_wave", "final_wave", "wave")
    total_score = read_int("total_score", "score")
    last_score = read_int("last_score", "final_score", "current_score")
    best_score = read_int("best_score", "high_score", "highest_score", "max_score")
    level = read_int("level", "player_level")

    if level <= 0:
        level = 1

    stored_accuracy = read_float("accuracy", "accuracy_percent", "hit_accuracy")

    if shots_fired > 0:
        accuracy = (shots_hit / shots_fired) * 100.0
    else:
        accuracy = stored_accuracy

    accuracy = max(0.0, min(100.0, accuracy))

    if best_score <= 0:
        best_score = total_score

    if total_score <= 0:
        total_score = best_score

    return {
        "games_played": max(0, games_played),
        "total_kills": max(0, total_kills),
        "shots_fired": max(0, shots_fired),
        "shots_hit": max(0, shots_hit),
        "accuracy": accuracy,
        "best_wave": max(0, best_wave),
        "last_wave": max(0, last_wave),
        "total_score": max(0, total_score),
        "last_score": max(0, last_score),
        "best_score": max(0, best_score),
        "level": max(1, level),
    }


def _call_database(names, attempts):
    """Try each database function name with each calling style."""
    try:
        import database

        for name in names:
            function = getattr(database, name, None)

            if callable(function):
                for args, kwargs in attempts:
                    try:
                        return function(*args, **kwargs)
                    except Exception:
                        pass

    except Exception:
        pass

    return None


def get_player_by_id(player_id):
    for name in ("get_player_by_id", "get_user_by_id", "fetch_player", "get_player"):
        result = _call_database((name,), [((player_id,), {})])
        if isinstance(result, dict):
            return result

    return None


def update_player_profile(player_id, updates):
    result = _call_database(
        ("update_player_profile", "update_player", "update_user", "save_player"),
        [
            ((player_id, updates), {}),
            ((), {"player_id": player_id, "updates": updates}),
            ((), {"user_id": player_id, "updates": updates}),
        ],
    )

    return result if result is not None else False


def delete_player(player_id):
    result = _call_database(
        ("delete_player", "delete_user", "remove_player", "remove_user"),
        [
            ((player_id,), {}),
            ((), {"player_id": player_id}),
            ((), {"user_id": player_id}),
        ],
    )

    return result if result is not None else False


def get_highest_score(player_id):
    result = _call_database(
        ("get_highest_score", "get_best_score", "get_high_score"),
        [((player_id,), {})],
    )

    return safe_int(result) if result is not None else 0


def load_ship(ship, size=72):
    if not ship:
        return None

    ship_names = {
        "starter": ["starter.png", "ship.png", "player.png"],
        "dragon": ["dragon.png", "ship_dragon.png"],
        "ninja": ["ninja.png", "ship_ninja.png"],
        "phoenix": ["phoenix.png", "ship_phoenix.png"],
        "falcon": ["falcon.png", "ship_falcon.png"],
    }

    names = ship_names.get(str(ship).lower(), [f"{ship}.png", f"ship_{ship}.png"])

    folders = [
        os.path.join(BASE_DIR, "assets", "images"),
        os.path.join(BASE_DIR, "assets", "images", "ships"),
    ]

    for folder in folders:
        for filename in names:
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            try:
                image = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(image, (size, size))
            except Exception:
                continue

    return None


def recolor_ship_body(surface, color_name="ICE"):
    if surface is None:
        return None

    colors = {
        "ICE": (190, 235, 255),
        "CYAN": (40, 220, 255),
        "RED": (255, 70, 90),
        "GOLD": (255, 205, 70),
        "YELLOW": (255, 235, 80),
        "PURPLE": (180, 100, 255),
        "GREEN": (70, 235, 130),
        "PINK": (255, 100, 180),
        "ORANGE": (255, 145, 50),
        "WHITE": (245, 248, 255),
    }

    tint = colors.get(str(color_name).upper(), colors["ICE"])

    result = surface.copy()

    overlay = pygame.Surface(result.get_size(), pygame.SRCALPHA)
    overlay.fill((tint[0], tint[1], tint[2], 65))

    result.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return result


def get_game_loadout(player=None):
    player = player if isinstance(player, dict) else {}

    player_id = get_value(player, "id", "player_id", "user_id", default=None)

    settings = load_settings(player_id)

    ship = get_value(player, "selected_ship", "current_ship",
                     "equipped_ship", "ship", default=None)

    if not ship:
        ship = (settings.get("selected_ship")
                or settings.get("preview_ship")
                or "starter")

    color = get_value(player, "ship_color", default=None)

    if not color:
        color = settings.get("ship_color", "ICE")

    return str(ship), str(color).upper()


def load_game_player_ship(player, size=72):
    ship, color = get_game_loadout(player)

    image = load_ship(ship, size)

    if image is None:
        return None

    return recolor_ship_body(image, color)


# ===============================================================
# screen
# ===============================================================

STAT_KEYS = [
    "GAMES PLAYED", "TOTAL KILLS", "ACCURACY", "LEVEL",
    "BEST WAVE", "TOTAL SCORE", "BEST SCORE", "LAST SCORE",
]

LINK_RED = (143, 78, 68)
LINK_RED_HOVER = (176, 98, 86)

DIALOG = pygame.Rect(350, 195, 500, 285)
DELETE_DIALOG = pygame.Rect(360, 225, 480, 225)
AVATAR_CENTER = (325, 268)
AVATAR_R = 48

STAT_X, STAT_W, STAT_H, STAT_GAP = 476, 104, 54, 9
STAT_ROWS_Y = (360, 422)

ACCOUNTS = ["Facebook", "Google", "Discord"]
PRIVACY_ITEMS = [
    ("profile_public", "profile visibility"),
    ("show_statistics", "show statistics"),
    ("show_online", "show online status"),
]


class ProfileScreen(LoginScreen):
    ADDRESS = "www.space-invaders.com/profile:"

    def draw_card_static(self, s, rnd):
        self.f_tiny = load_font(13)

        # left: avatar ring
        pygame.draw.circle(s, CREAM, AVATAR_CENTER, AVATAR_R + 6)
        pygame.draw.circle(s, INK, AVATAR_CENTER, AVATAR_R + 6, 3)

        # right: card
        sketch_rect(s, rnd, (470, 218, 475, 318), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (460, 208, 475, 318), ROSE, INK, 14, 3)

        self.text(s, self.f_icon, "player profile", DARK, topleft=(478, 214))
        self.text(s, self.f_small, "statistics", INK, topleft=(478, 332))

        for index, key in enumerate(STAT_KEYS):
            col, row = index % 4, index // 4
            x = STAT_X + col * (STAT_W + STAT_GAP)
            y = STAT_ROWS_Y[row]
            sketch_rect(s, rnd, (x, y, STAT_W, STAT_H), CREAM, INK, 10, 2)
            self.text(s, self.f_tiny, key.lower(), INK, midtop=(x + STAT_W // 2, y + 6))

    def __init__(self, screen, width, height, player):
        super().__init__(screen, width, height)

        self.player = player if isinstance(player, dict) else {}

        self.player_id = get_value(self.player, "id", "player_id", "user_id", default=None)

        self.refresh_player()

        self.username = str(
            get_value(self.player, "username", "display_name", "name", default="PLAYER")
            or "PLAYER"
        )
        self.original_username = self.username
        self.password = ""

        self.editing_username = False
        self.editing_password = False
        self.active_field = None

        self.avatar_path = get_value(
            self.player, "profile_picture", "avatar_path", "avatar", default=None
        )
        self.avatar_image = None
        self._avatar_cache = None

        self.privacy = {
            "profile_public": True,
            "show_statistics": True,
            "show_online": True,
        }
        self.linked_accounts = {"Facebook": False, "Google": False, "Discord": False}

        saved = load_settings(self.player_id)

        if isinstance(saved, dict):
            if isinstance(saved.get("privacy"), dict):
                self.privacy.update(saved["privacy"])

            if isinstance(saved.get("linked_accounts"), dict):
                self.linked_accounts.update(saved["linked_accounts"])

            if saved.get("username"):
                self.username = str(saved["username"])
                self.original_username = self.username

            if saved.get("avatar"):
                self.avatar_path = saved["avatar"]

        self.active_overlay = None

        self.message = ""
        self.message_timer = 0
        self.message_color = INK

        self.f_label_s = load_font(22)
        self.f_input_s = load_font(21)

        # hit boxes (1200x675 design space)
        self.username_box = pygame.Rect(476, 250, 443, 34)
        self.password_box = pygame.Rect(476, 292, 443, 34)
        self.change_btn = pygame.Rect(275, 332, 100, 26)
        self.privacy_link = pygame.Rect(250, 376, 150, 26)
        self.accounts_link = pygame.Rect(250, 408, 150, 26)
        self.delete_link = pygame.Rect(250, 440, 150, 26)
        self.back_btn = pygame.Rect(514, 488, 100, 26)
        self.save_btn = pygame.Rect(622, 488, 150, 26)
        self.reset_btn = pygame.Rect(780, 488, 100, 26)

        self.load_avatar()
        self.stats = self.build_statistics()

    # ------------------------------------------------------------
    # data
    # ------------------------------------------------------------
    def update_size(self):
        surface = pygame.display.get_surface()
        if surface is None:
            return
        self.screen = surface
        if surface.get_width() != self.width or surface.get_height() != self.height:
            self.resize(surface.get_width(), surface.get_height())

    def refresh_player(self):
        if self.player_id is None:
            return

        fresh = get_player_by_id(self.player_id)

        if isinstance(fresh, dict):
            self.player.clear()
            self.player.update(fresh)

    def build_statistics(self):
        stats = get_game_statistics(self.player_id, self.player)

        return {
            "GAMES PLAYED": stats["games_played"],
            "TOTAL KILLS": stats["total_kills"],
            "ACCURACY": f"{stats['accuracy']:.1f}%",
            "LEVEL": stats["level"],
            "BEST WAVE": stats["best_wave"],
            "TOTAL SCORE": stats["total_score"],
            "BEST SCORE": stats["best_score"],
            "LAST SCORE": stats["last_score"],
        }

    def get_statistics(self):
        self.refresh_player()
        self.stats = self.build_statistics()
        return self.stats

    # ------------------------------------------------------------
    # avatar
    # ------------------------------------------------------------
    def load_avatar(self):
        self.avatar_image = None
        self._avatar_cache = None

        if not self.avatar_path:
            return

        path = str(self.avatar_path)

        if not os.path.isabs(path):
            path = os.path.join(BASE_DIR, path)

        if not os.path.exists(path):
            return

        try:
            self.avatar_image = pygame.image.load(path).convert_alpha()
        except Exception:
            self.avatar_image = None

    def round_avatar(self):
        if self._avatar_cache is None and self.avatar_image is not None:
            size = AVATAR_R * 2
            image = pygame.transform.smoothscale(self.avatar_image, (size, size))

            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (AVATAR_R, AVATAR_R), AVATAR_R)

            image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._avatar_cache = image

        return self._avatar_cache

    def select_profile_image(self):
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()

            path = filedialog.askopenfilename(
                title="Choose Profile Picture",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp")],
            )

            root.destroy()

            if not path:
                return

            self.avatar_path = path
            self.load_avatar()

            self.player["profile_picture"] = path
            self.save_local_profile()

            self.flash("profile picture updated")

        except Exception:
            self.flash("unable to choose image", RED)

    # ------------------------------------------------------------
    # saving
    # ------------------------------------------------------------
    def flash(self, text, color=INK):
        self.message = text
        self.message_color = color
        self.message_timer = 180

    def save_local_profile(self):
        saved = load_settings(self.player_id)

        if not isinstance(saved, dict):
            saved = {}

        saved["username"] = self.username
        saved["avatar"] = self.avatar_path
        saved["privacy"] = dict(self.privacy)
        saved["linked_accounts"] = dict(self.linked_accounts)

        # the password is sent to the database only, never kept in the json file
        saved.pop("password", None)

        save_settings(self.player_id, saved)

    def save_profile(self):
        updates = {"username": self.username}

        if self.avatar_path:
            updates["profile_picture"] = self.avatar_path

        if self.password:
            updates["password"] = self.password

        result = update_player_profile(self.player_id, updates)

        if isinstance(result, dict):
            self.player.update(result)
        else:
            self.player.update({k: v for k, v in updates.items() if k != "password"})

        self.save_local_profile()

        self.original_username = self.username
        self.password = ""
        self.stats = self.build_statistics()
        self.cancel_editing()

        self.flash("profile saved!", GREEN)

    def reset_changes(self):
        self.username = self.original_username
        self.password = ""
        self.cancel_editing()
        self.flash("changes reset")

    def toggle_privacy(self, key):
        self.privacy[key] = not self.privacy.get(key, True)
        self.save_local_profile()

    def toggle_linked_account(self, name):
        self.linked_accounts[name] = not self.linked_accounts.get(name, False)
        self.save_local_profile()

    # ------------------------------------------------------------
    # editing state
    # ------------------------------------------------------------
    def start_username_edit(self):
        self.editing_username, self.editing_password = True, False
        self.active_field = "username"

    def start_password_edit(self):
        self.editing_username, self.editing_password = False, True
        self.active_field = "password"

    def cancel_editing(self):
        self.editing_username = False
        self.editing_password = False
        self.active_field = None

    # ------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------
    def present(self):
        if self.scale == 1.0 and self.offset == (0, 0):
            self.screen.blit(self.base, (0, 0))
        else:
            self.screen.fill(PEACH)
            size = (int(self.base.get_width() * self.scale),
                    int(self.base.get_height() * self.scale))
            self.screen.blit(pygame.transform.smoothscale(self.base, size), self.offset)

    def draw_avatar(self, s):
        image = self.round_avatar()

        if image is not None:
            s.blit(image, image.get_rect(center=AVATAR_CENTER))
        else:
            pygame.draw.circle(s, DARK, AVATAR_CENTER, AVATAR_R)
            initial = self.username[:1].upper() or "P"
            self.text(s, self.f_label, initial, CREAM, center=AVATAR_CENTER)

    def draw_field(self, s, rect, label, field, value, is_password):
        self.draw_pill(rect, label, field, value, is_password,
                       self.f_label_s, self.f_input_s)

        if not value and self.active_field != field:
            x = rect.x + 19 + self.f_label_s.size(label)[0] + 10
            self.text(s, self.f_small, "click to edit", (190, 150, 130),
                      midleft=(x, rect.centery))

    def draw_stats(self, s):
        for index, key in enumerate(STAT_KEYS):
            col, row = index % 4, index // 4
            x = STAT_X + col * (STAT_W + STAT_GAP)
            y = STAT_ROWS_Y[row]

            value = self.stats.get(key, 0)
            msg = value if isinstance(value, str) else f"{int(value):,}"

            font = self.f_icon
            if font.size(msg)[0] > STAT_W - 14:
                font = self.f_btn
            if font.size(msg)[0] > STAT_W - 14:
                font = self.f_small

            self.text(s, font, msg, DARK, center=(x + STAT_W // 2, y + 35))

    def draw_link(self, s, rect, label, mouse, red=False):
        hover = rect.collidepoint(mouse)

        fill = HEART if hover else CREAM
        pygame.draw.rect(s, fill, rect, border_radius=13)
        pygame.draw.rect(s, INK, rect, 2, border_radius=13)

        color = LINK_RED if red else DARK
        self.text(s, self.f_small, label, color, center=rect.center)

    def draw_dialog_frame(self, s, rect, title):
        overlay = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        overlay.fill((90, 55, 45, 120))
        s.blit(overlay, (0, 0))

        rnd = random.Random(7)
        shadow = rect.move(10, 10)
        sketch_rect(s, rnd, shadow, ROSE_DEEP, ROSE_DEEP, 16, 1, 0)
        sketch_rect(s, rnd, rect, CREAM, INK, 16, 3)

        self.text(s, self.f_label, title, DARK, center=(rect.centerx, rect.y + 38))

    def draw_privacy(self, s, mouse):
        self.draw_dialog_frame(s, DIALOG, "privacy")

        for i, (key, label) in enumerate(PRIVACY_ITEMS):
            y = 262 + i * 58
            self.text(s, self.f_icon, label, INK, midleft=(DIALOG.x + 34, y + 10))

            toggle = self.toggle_rect(i)
            on = self.privacy.get(key, True)

            pygame.draw.rect(s, DARK if on else (205, 180, 165), toggle, border_radius=14)
            knob_x = toggle.right - 15 if on else toggle.left + 15
            pygame.draw.circle(s, CREAM, (knob_x, toggle.centery), 10)

        self.draw_button(self.dialog_close_rect(), "close", mouse)

    def draw_accounts(self, s, mouse):
        self.draw_dialog_frame(s, DIALOG, "linked accounts")

        for i, name in enumerate(ACCOUNTS):
            item = self.account_row(i)
            pygame.draw.rect(s, ROSE, item, border_radius=14)
            pygame.draw.rect(s, INK, item, 2, border_radius=14)
            self.text(s, self.f_icon, name.lower(), DARK, midleft=(item.x + 16, item.centery))

            connected = self.linked_accounts.get(name, False)
            self.draw_button(self.account_button(i),
                             "connected" if connected else "connect", mouse)

        self.draw_button(self.dialog_close_rect(), "close", mouse)

    def draw_delete(self, s, mouse):
        self.draw_dialog_frame(s, DELETE_DIALOG, "delete account?")

        self.text(s, self.f_small, "this can't be undone.", INK,
                  center=(DELETE_DIALOG.centerx, DELETE_DIALOG.y + 92))
        draw_heart(s, DELETE_DIALOG.centerx, DELETE_DIALOG.y + 135, 12)

        cancel, delete = self.delete_buttons()

        pygame.draw.rect(s, DARK_HOVER if cancel.collidepoint(mouse) else DARK,
                         cancel, border_radius=19)
        self.text(s, self.f_btn, "cancel", CREAM, center=cancel.center)

        pygame.draw.rect(s, LINK_RED_HOVER if delete.collidepoint(mouse) else LINK_RED,
                         delete, border_radius=19)
        self.text(s, self.f_btn, "delete", CREAM, center=delete.center)

    def draw(self):
        self.update_size()
        self.time += 1

        s = self.base
        s.blit(self.static, (0, 0))
        mouse = self.to_base(pygame.mouse.get_pos())

        bob = math.sin(self.time * 0.05) * 3
        draw_heart(s, 268, 236 + bob * 0.6, 10)
        draw_heart(s, 384, 232 - bob * 0.6, 11)

        self.draw_avatar(s)
        self.draw_button(self.change_btn, "change", mouse)

        self.draw_link(s, self.privacy_link, "privacy", mouse)
        self.draw_link(s, self.accounts_link, "linked accounts", mouse)
        self.draw_link(s, self.delete_link, "delete account", mouse, red=True)

        self.draw_field(s, self.username_box, "user:", "username", self.username, False)
        self.draw_field(s, self.password_box, "pass:", "password", self.password, True)

        self.draw_stats(s)

        self.draw_button(self.back_btn, "back", mouse)
        self.draw_button(self.save_btn, "save profile", mouse)
        self.draw_button(self.reset_btn, "reset", mouse)

        if self.message_timer > 0:
            self.text(s, self.f_small, self.message, self.message_color, center=(578, 572))
            self.message_timer -= 1

        if self.active_overlay == "privacy":
            self.draw_privacy(s, mouse)
        elif self.active_overlay == "accounts":
            self.draw_accounts(s, mouse)
        elif self.active_overlay == "delete":
            self.draw_delete(s, mouse)

        self.present()

    # ------------------------------------------------------------
    # dialog geometry (shared by drawing and clicking)
    # ------------------------------------------------------------
    def toggle_rect(self, i):
        y = 262 + i * 58
        return pygame.Rect(DIALOG.right - 96, y - 4, 58, 28)

    def account_row(self, i):
        return pygame.Rect(DIALOG.x + 30, 255 + i * 50, DIALOG.w - 60, 40)

    def account_button(self, i):
        item = self.account_row(i)
        return pygame.Rect(item.right - 120, item.y + 7, 108, 26)

    def dialog_close_rect(self):
        return pygame.Rect(DIALOG.x + 30, DIALOG.bottom - 50, DIALOG.w - 60, 30)

    def delete_buttons(self):
        cancel = pygame.Rect(420, 392, 150, 38)
        delete = pygame.Rect(630, 392, 150, 38)
        return cancel, delete

    # ------------------------------------------------------------
    # input
    # ------------------------------------------------------------
    def handle_overlay_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.play_click()
            self.active_overlay = None
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        pos = self.to_base(event.pos)

        if self.active_overlay == "privacy":
            for i, (key, _) in enumerate(PRIVACY_ITEMS):
                if self.toggle_rect(i).collidepoint(pos):
                    self.play_click()
                    self.toggle_privacy(key)
                    return None

            if self.dialog_close_rect().collidepoint(pos):
                self.play_click()
                self.active_overlay = None

        elif self.active_overlay == "accounts":
            for i, name in enumerate(ACCOUNTS):
                if self.account_button(i).collidepoint(pos):
                    self.play_click()
                    self.toggle_linked_account(name)
                    return None

            if self.dialog_close_rect().collidepoint(pos):
                self.play_click()
                self.active_overlay = None

        elif self.active_overlay == "delete":
            cancel, delete = self.delete_buttons()

            if delete.collidepoint(pos):
                self.play_click()
                delete_player(self.player_id)
                return "delete_account"

            if cancel.collidepoint(pos):
                self.play_click()
                self.active_overlay = None

        return None

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.resize(event.w, event.h)
            return None

        if self.active_overlay:
            return self.handle_overlay_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_base(event.pos)

            if self.change_btn.collidepoint(pos):
                self.play_click()
                self.select_profile_image()

            elif self.username_box.collidepoint(pos):
                self.play_click()
                self.start_username_edit()

            elif self.password_box.collidepoint(pos):
                self.play_click()
                self.start_password_edit()

            elif self.privacy_link.collidepoint(pos):
                self.play_click()
                self.cancel_editing()
                self.active_overlay = "privacy"

            elif self.accounts_link.collidepoint(pos):
                self.play_click()
                self.cancel_editing()
                self.active_overlay = "accounts"

            elif self.delete_link.collidepoint(pos):
                self.play_click()
                self.cancel_editing()
                self.active_overlay = "delete"

            elif self.back_btn.collidepoint(pos):
                self.play_click()
                return "menu"

            elif self.save_btn.collidepoint(pos):
                self.play_click()
                self.save_profile()

            elif self.reset_btn.collidepoint(pos):
                self.play_click()
                self.reset_changes()

            else:
                self.cancel_editing()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.editing_username or self.editing_password:
                    self.cancel_editing()
                    return None
                self.play_click()
                return "menu"

            if event.key == pygame.K_TAB and (self.editing_username or self.editing_password):
                if self.editing_username:
                    self.start_password_edit()
                else:
                    self.start_username_edit()
                return None

            if self.editing_username:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.editing_username = False
                    self.active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if len(self.username) < 20:
                        self.username += event.unicode

            elif self.editing_password:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.editing_password = False
                    self.active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    self.password = self.password[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if len(self.password) < 32:
                        self.password += event.unicode

        return None

    def update(self, events=None, dt=0.0):
        self.update_size()

        for event in events or []:
            result = self.handle_event(event)

            if result is not None:
                return result

        return None


def profile_screen(screen, clock, player=None):
    profile = ProfileScreen(screen, screen.get_width(), screen.get_height(), player)

    while True:
        clock.tick(60)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

        result = profile.update(events, 0.0)

        profile.draw()
        pygame.display.flip()

        if result in ("menu", "delete_account", "quit"):
            return result