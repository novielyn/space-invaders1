import json
import math
import os

import pygame

try:
    from screens.login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, HEART, GREEN,
    )
except ImportError:
    from login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, HEART, GREEN,
    )

# ---------------------------------------------------------------
# Settings in the same cozy desktop style as the other screens.
# Same interface as before:
#   SettingsScreen(screen, clock)
#   update(events, dt=0.0) -> "back" | None
#   draw()
#   settings_screen(screen, clock, on_back=None)
# Settings are still saved to profile_settings.json and mirrored
# into the module-level PREFERENCES dict.
# ---------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, "profile_settings.json")

PREFERENCES = {}

DEFAULTS = {
    "master_volume": 0.70,
    "music_volume": 0.70,
    "sfx_volume": 0.80,
    "difficulty": "Normal",
    "fullscreen": False,
    "screen_effects": True,
    "mobile_controls": True,
}

DIFFICULTIES = ["Easy", "Normal", "Hard"]

# row layout (1200x675 design space, inside the rose card)
ROW_X, ROW_W, ROW_H, ROW_STEP, ROW_TOP = 502, 421, 28, 33, 222
SLIDER_X, SLIDER_W = 716, 146

# row index -> what lives there
SLIDERS = {0: ("master", "master_volume", "master volume"),
           1: ("music", "music_volume", "music volume"),
           2: ("sfx", "sfx_volume", "sfx volume")}
TOGGLES = {4: ("fullscreen", "fullscreen"),
           5: ("screen_effects", "screen effects"),
           6: ("mobile_controls", "mobile controls")}


def clamp01(value, default):
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


class SettingsScreen(LoginScreen):
    ADDRESS = "www.space-invaders.com/settings:"

    def draw_card_static(self, s, rnd):
        self.text(s, self.f_label, "settings", DARK, center=(384, 240))

        sketch_rect(s, rnd, (500, 216, 445, 318), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (490, 208, 445, 318), ROSE, INK, 14, 3)

    def __init__(self, screen, clock):
        super().__init__(screen, screen.get_width(), screen.get_height())
        self.clock = clock
        self.f_tiny = load_font(13)

        self.settings = dict(DEFAULTS)
        self.hovered_row = None
        self.button_hover = None
        self.dragging_slider = None

        self.back_btn = pygame.Rect(559, 478, 80, 26)
        self.save_btn = pygame.Rect(647, 478, 80, 26)
        self.reset_btn = pygame.Rect(735, 478, 130, 26)

        self.load_settings()
        self.apply_audio_settings()

    # ------------------------------------------------------------
    # data
    # ------------------------------------------------------------
    def clamp_volumes(self):
        for key in ("master_volume", "music_volume", "sfx_volume"):
            self.settings[key] = clamp01(self.settings.get(key), DEFAULTS[key])

    def load_settings(self):
        global PREFERENCES

        if not os.path.exists(SETTINGS_FILE):
            PREFERENCES = dict(self.settings)
            return

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                PREFERENCES = dict(data)

                for key in self.settings:
                    if key in data:
                        self.settings[key] = data[key]

                # older files only had one "sound_volume"
                if "sound_volume" in data and "sfx_volume" not in data:
                    self.settings["sfx_volume"] = data["sound_volume"]

                self.clamp_volumes()
        except Exception:
            pass

    def save_settings(self):
        global PREFERENCES

        self.clamp_volumes()

        to_save = dict(self.settings)
        to_save["sound_volume"] = to_save["sfx_volume"]
        PREFERENCES = dict(to_save)

        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(to_save, file, indent=4)
        except Exception:
            pass

        self.apply_audio_settings()

    def apply_audio_settings(self):
        global PREFERENCES

        self.clamp_volumes()
        master = self.settings["master_volume"]
        music = self.settings["music_volume"]
        sfx = self.settings["sfx_volume"]

        PREFERENCES["master_volume"] = master
        PREFERENCES["music_volume"] = music
        PREFERENCES["sfx_volume"] = sfx
        PREFERENCES["sound_volume"] = sfx

        final_music = max(0.0, min(1.0, master * music))
        final_sfx = max(0.0, min(1.0, master * sfx))

        if self.button_click:
            try:
                self.button_click.set_volume(0.45 * final_sfx)
            except pygame.error:
                pass

        try:
            if not pygame.mixer.get_init():
                return
            pygame.mixer.music.set_volume(final_music)
            for index in range(pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(index).set_volume(final_sfx)
        except pygame.error:
            pass

    def reset_defaults(self):
        self.settings = dict(DEFAULTS)
        self.apply_audio_settings()
        self.save_settings()

    def update_size(self):
        surface = pygame.display.get_surface()
        if surface is None:
            return
        self.screen = surface
        if surface.get_width() != self.width or surface.get_height() != self.height:
            self.resize(surface.get_width(), surface.get_height())

    # ------------------------------------------------------------
    # geometry
    # ------------------------------------------------------------
    def row_rect(self, index):
        return pygame.Rect(ROW_X, ROW_TOP + index * ROW_STEP, ROW_W, ROW_H)

    def slider_rect(self, index):
        row = self.row_rect(index)
        return pygame.Rect(SLIDER_X, row.centery - 3, SLIDER_W, 6)

    def toggle_rect(self, index):
        row = self.row_rect(index)
        return pygame.Rect(row.right - 14 - 44, row.centery - 10, 44, 20)

    def difficulty_rect(self):
        row = self.row_rect(3)
        return pygame.Rect(row.right - 14 - 96, row.centery - 11, 96, 22)

    # ------------------------------------------------------------
    # actions
    # ------------------------------------------------------------
    def set_slider(self, name, pos_x):
        value = clamp01((pos_x - SLIDER_X) / SLIDER_W, 0.0)
        for index, (slider_name, key, _label) in SLIDERS.items():
            if slider_name == name:
                self.settings[key] = value
        self.apply_audio_settings()

    def cycle_difficulty(self):
        current = self.settings.get("difficulty", "Normal")
        try:
            index = DIFFICULTIES.index(current)
        except ValueError:
            index = 1
        self.settings["difficulty"] = DIFFICULTIES[(index + 1) % len(DIFFICULTIES)]

    def toggle_fullscreen(self):
        new_state = not self.settings.get("fullscreen", False)

        try:
            if new_state:
                new_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                new_screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
            self.settings["fullscreen"] = new_state
        except pygame.error:
            self.settings["fullscreen"] = False
            try:
                new_screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
            except pygame.error:
                return

        self.screen = new_screen
        self.resize(new_screen.get_width(), new_screen.get_height())

    def toggle_setting(self, key):
        if key == "fullscreen":
            self.toggle_fullscreen()
        else:
            self.settings[key] = not self.settings.get(key, True)

    def do_save(self):
        self.save_settings()
        self.message = "settings saved!"
        self.message_color = GREEN

    def do_reset(self):
        self.reset_defaults()
        self.message = "defaults restored"
        self.message_color = GREEN

    # ------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------
    def draw_row_label(self, rect, text):
        self.text(self.base, self.f_small, text, DARK,
                  midleft=(rect.x + 16, rect.centery))

    def draw_slider_row(self, index, mouse):
        _name, key, label = SLIDERS[index]
        s = self.base
        row = self.row_rect(index)
        value = clamp01(self.settings.get(key), DEFAULTS[key])

        self.draw_row_label(row, label)

        track = self.slider_rect(index)
        pygame.draw.rect(s, ROSE, track, border_radius=3)
        filled = int(track.width * value)
        if filled > 0:
            pygame.draw.rect(s, DARK, (track.x, track.y, filled, track.height),
                             border_radius=3)

        knob = (int(track.x + track.width * value), track.centery)
        active = self.dragging_slider == SLIDERS[index][0]
        pygame.draw.circle(s, HEART, knob, 9 if active else 8)
        pygame.draw.circle(s, INK, knob, 9 if active else 8, 2)

        self.text(s, self.f_tiny, f"{int(value * 100)}%", INK,
                  midright=(row.right - 14, row.centery))

    def draw_difficulty_row(self, mouse):
        s = self.base
        row = self.row_rect(3)
        self.draw_row_label(row, "difficulty")

        rect = self.difficulty_rect()
        hover = rect.collidepoint(mouse)
        pygame.draw.rect(s, DARK_HOVER if hover else DARK, rect, border_radius=11)
        self.text(s, self.f_tiny, str(self.settings.get("difficulty", "Normal")).lower(),
                  CREAM, center=(rect.centerx - 6, rect.centery))
        self.text(s, self.f_tiny, "\u203a", CREAM,
                  center=(rect.right - 12, rect.centery - 1))

    def draw_toggle_row(self, index, mouse):
        key, label = TOGGLES[index]
        s = self.base
        row = self.row_rect(index)
        on = bool(self.settings.get(key, False))

        self.draw_row_label(row, label)

        rect = self.toggle_rect(index)
        pygame.draw.rect(s, DARK if on else ROSE_DEEP, rect, border_radius=10)
        pygame.draw.rect(s, INK, rect, 2, border_radius=10)
        knob_x = rect.right - 10 if on else rect.left + 10
        pygame.draw.circle(s, CREAM, (knob_x, rect.centery), 7)

        self.text(s, self.f_tiny, "on" if on else "off", INK,
                  midright=(rect.left - 10, rect.centery))

    def draw_rows(self, mouse):
        s = self.base
        self.hovered_row = None

        for index in range(7):
            rect = self.row_rect(index)
            hovered = rect.collidepoint(mouse)
            if hovered:
                self.hovered_row = index

            if hovered:
                fill = HEART
            elif index % 2 == 0:
                fill = CREAM
            else:
                fill = (252, 236, 222)

            pygame.draw.rect(s, fill, rect, border_radius=12)
            pygame.draw.rect(s, INK, rect, 2, border_radius=12)

            if index in SLIDERS:
                self.draw_slider_row(index, mouse)
            elif index == 3:
                self.draw_difficulty_row(mouse)
            else:
                self.draw_toggle_row(index, mouse)

    def draw(self):
        self.update_size()
        self.time += 1

        s = self.base
        s.blit(self.static, (0, 0))
        mouse = self.to_base(pygame.mouse.get_pos())

        bob = math.sin(self.time * 0.05) * 3
        draw_heart(s, 349, 281 + bob * 0.6, 18)
        draw_heart(s, 418, 285 - bob * 0.6, 20)
        self.draw_cup(int(bob))

        self.draw_rows(mouse)

        self.draw_button(self.back_btn, "back", mouse)
        self.draw_button(self.save_btn, "save", mouse)
        self.draw_button(self.reset_btn, "reset defaults", mouse)

        if self.message:
            self.text(s, self.f_small, self.message, self.message_color,
                      center=(578, 572))

        self.present()

    def present(self):
        if self.scale == 1.0 and self.offset == (0, 0):
            self.screen.blit(self.base, (0, 0))
        else:
            self.screen.fill(PEACH)
            size = (int(self.base.get_width() * self.scale),
                    int(self.base.get_height() * self.scale))
            self.screen.blit(pygame.transform.smoothscale(self.base, size), self.offset)

    # ------------------------------------------------------------
    # input
    # ------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            pos = self.to_base(event.pos)
            self.button_hover = None
            for name, rect in (("back", self.back_btn),
                               ("save", self.save_btn),
                               ("reset", self.reset_btn)):
                if rect.collidepoint(pos):
                    self.button_hover = name

            if self.dragging_slider:
                self.set_slider(self.dragging_slider, pos[0])

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_base(event.pos)

            if self.back_btn.collidepoint(pos):
                self.play_click()
                return "back"
            if self.save_btn.collidepoint(pos):
                self.play_click()
                self.do_save()
                return None
            if self.reset_btn.collidepoint(pos):
                self.play_click()
                self.do_reset()
                return None

            for index, (name, _key, _label) in SLIDERS.items():
                if self.slider_rect(index).inflate(16, 20).collidepoint(pos):
                    self.dragging_slider = name
                    self.set_slider(name, pos[0])
                    return None

            if self.row_rect(3).collidepoint(pos):
                self.play_click()
                self.cycle_difficulty()
                self.message = ""
                return None

            for index, (key, _label) in TOGGLES.items():
                if self.row_rect(index).collidepoint(pos):
                    self.play_click()
                    self.toggle_setting(key)
                    self.message = ""
                    return None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_slider = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_click()
                return "back"
            if event.key == pygame.K_s:
                self.play_click()
                self.do_save()
            elif event.key == pygame.K_r:
                self.play_click()
                self.do_reset()

        elif event.type == pygame.VIDEORESIZE:
            self.resize(event.w, event.h)

        return None

    def update(self, events=None, dt=0.0):
        self.update_size()

        for event in events or []:
            if event.type == pygame.QUIT:
                return "quit"

            result = self.handle_event(event)
            if result is not None:
                return result

        # keep dragging smooth even if the mouse leaves the window
        if self.dragging_slider:
            pos = self.to_base(pygame.mouse.get_pos())
            self.set_slider(self.dragging_slider, pos[0])

        return None


def settings_screen(screen, clock, on_back=None):
    settings = SettingsScreen(screen, clock)

    while True:
        clock.tick(60)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        result = settings.update(events, 1 / 60)
        settings.draw()
        pygame.display.flip()

        if result == "back":
            if on_back:
                on_back()
            return

        if result == "quit":
            pygame.quit()
            return