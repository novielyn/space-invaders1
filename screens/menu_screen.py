import os
import random

import pygame

try:
    from database import get_player
except Exception:
    get_player = None

try:
    from screens.login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, TAN,
    )
except ImportError:
    from login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, TAN,
    )

# ---------------------------------------------------------------
# Main menu in the same cozy desktop style as login / register.
# Same interface as before:
#   MenuScreen(screen, w, h, player)
#   update(events, dt) -> "play" | "tutorial" | "leaderboard" |
#                         "profile" | "settings" | "logout" | None
#   draw(), resize(w, h)
# ---------------------------------------------------------------

LOGOUT_FILL = (143, 78, 68)
LOGOUT_HOVER = (176, 98, 86)

ITEMS = [
    ("play game", "play"),
    ("tutorial", "tutorial"),
    ("leaderboard", "leaderboard"),
    ("profile", "profile"),
    ("settings", "settings"),
    ("logout", "logout"),
]


class MenuScreen(LoginScreen):
    ADDRESS = "www.space-invaders.com/menu:"

    # profile card is part of the static layer
    def draw_card_static(self, s, rnd):
        self.f_tiny = load_font(13)

        sketch_rect(s, rnd, (228, 222, 390, 300), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (218, 212, 390, 300), ROSE, INK, 14, 3)

        pygame.draw.circle(s, DARK, (264, 254), 30)
        pygame.draw.circle(s, CREAM, (264, 254), 30, 2)

        for i, name in enumerate(("high score", "xp", "achievements")):
            x = 236 + i * 123
            sketch_rect(s, rnd, (x, 296, 112, 58), CREAM, INK, 10, 2)
            self.text(s, self.f_tiny, name, INK, midtop=(x + 56, 302))

        self.text(s, self.f_tiny, "rank progress", INK, topleft=(236, 372))
        sketch_rect(s, rnd, (236, 390, 358, 16), CREAM, INK, 8, 2)

        self.text(s, self.f_small, "objective: destroy 25 invaders", INK,
                  topleft=(236, 424))
        sketch_rect(s, rnd, (236, 452, 300, 16), CREAM, INK, 8, 2)
        pygame.draw.rect(s, TAN, (240, 456, int(292 * 0.64), 8), border_radius=4)
        self.text(s, self.f_small, "16 / 25", INK, midright=(594, 460))

    def __init__(self, screen, screen_width, screen_height, player):
        super().__init__(screen, screen_width, screen_height)

        self.player = player if isinstance(player, dict) else {}

        self.selected_index = 0
        self.hover_index = -1
        self.confirm_logout = False
        self.confirm_hover = -1

        self.item_rects = [
            pygame.Rect(650, 220 + i * 47, 285, 38) for i in range(len(ITEMS))
        ]
        self.cancel_rect = pygame.Rect(420, 392, 150, 38)
        self.logout_rect = pygame.Rect(630, 392, 150, 38)

        self.hover_sound = None
        for path in ("assets/sounds/update_hover.mp3", "assets/sounds/update_hover.wav",
                     "assets/sounds/hover.mp3", "assets/sounds/hover.wav"):
            if os.path.exists(path):
                try:
                    self.hover_sound = pygame.mixer.Sound(path)
                    break
                except Exception:
                    pass

        self.refresh_player()

    # ------------------------------------------------------------
    # player data
    # ------------------------------------------------------------
    def refresh_player(self):
        player_id = self.player.get("player_id", self.player.get("id"))
        if player_id is None or not get_player:
            return
        try:
            data = get_player(player_id)
            if isinstance(data, dict):
                self.player.update(data)
        except Exception:
            pass

    def _int(self, *keys):
        for key in keys:
            if key in self.player:
                try:
                    return int(self.player[key])
                except (TypeError, ValueError):
                    return 0
        return 0

    def get_score(self):
        return self._int("high_score", "score")

    def get_xp(self):
        return self._int("xp", "experience")

    def get_achievements(self):
        value = self.player.get("achievements", 0)
        if isinstance(value, (list, tuple, set, dict)):
            return len(value)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def get_rank(self):
        rank = self.player.get("rank")
        if rank:
            return str(rank)
        xp = self.get_xp()
        for limit, name in ((30000, "Mythic Immortal"), (15000, "Mythic"),
                            (7000, "Legend"), (3500, "Grandmaster"),
                            (1500, "Master"), (500, "Elite")):
            if xp >= limit:
                return name
        return "Rookie"

    def get_rank_progress(self):
        xp = self.get_xp()
        steps = [(0, 500), (500, 1500), (1500, 3500), (3500, 7000),
                 (7000, 15000), (15000, 30000), (30000, 50000)]
        current, target = 0, 500
        for low, high in steps:
            if low <= xp < high:
                current, target = low, high
                break
        if xp >= 30000:
            current, target = 30000, max(50000, xp + 1)
        progress = (xp - current) / max(1, target - current)
        return max(0.0, min(1.0, progress)), current, target

    @staticmethod
    def fmt(value):
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return "0"

    # ------------------------------------------------------------
    # sounds
    # ------------------------------------------------------------
    def play_hover(self):
        if self.hover_sound:
            try:
                self.hover_sound.play()
            except Exception:
                pass

    # ------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------
    def fit(self, font, msg, max_w):
        img = font.render(msg, True, CREAM)
        while img.get_width() > max_w and len(msg) > 1:
            msg = msg[:-1]
            img = font.render(msg, True, CREAM)
        return msg

    def draw_profile(self, s):
        name = str(self.player.get("username", "Player"))
        initial = name[:1].upper() or "?"
        self.text(s, self.f_label, initial, CREAM, center=(264, 252))

        shown = self.fit(self.f_icon, name, 290)
        self.text(s, self.f_icon, shown, DARK, midleft=(308, 242))

        rank = self.get_rank().lower()
        label = self.f_small.render(rank, True, CREAM)
        badge = pygame.Rect(308, 262, label.get_width() + 28, 24)
        pygame.draw.rect(s, DARK, badge, border_radius=12)
        s.blit(label, label.get_rect(center=badge.center))
        draw_heart(s, badge.right + 18, badge.centery - 1, 7)

        values = (self.get_score(), self.get_xp(), self.get_achievements())
        for i, value in enumerate(values):
            x = 236 + i * 123
            msg = self.fmt(value)
            font = self.f_icon if self.f_icon.size(msg)[0] <= 100 else self.f_btn
            self.text(s, font, msg, DARK, center=(x + 56, 335))

        progress, current, target = self.get_rank_progress()
        self.text(s, self.f_tiny, f"{self.fmt(current)} / {self.fmt(target)}", INK,
                  topright=(594, 373))
        fill = int(350 * progress)
        if fill >= 8:
            pygame.draw.rect(s, DARK, (240, 394, fill, 8), border_radius=4)
        elif fill > 0:
            pygame.draw.rect(s, DARK, (240, 394, fill, 8))

    def draw_items(self, s):
        for i, (label, action) in enumerate(ITEMS):
            rect = self.item_rects[i]
            active = i == self.selected_index or i == self.hover_index
            is_logout = action == "logout"

            if is_logout:
                fill = LOGOUT_HOVER if active else LOGOUT_FILL
            else:
                fill = DARK_HOVER if active else DARK

            pygame.draw.rect(s, fill, rect, border_radius=19)
            if active:
                pygame.draw.rect(s, CREAM, rect, 2, border_radius=19)
                draw_heart(s, rect.x + 24, rect.centery - 1, 7)
            else:
                pygame.draw.circle(s, (190, 150, 130), (rect.x + 24, rect.centery), 4)

            self.text(s, self.f_icon, label, CREAM,
                      midleft=(rect.x + 46, rect.centery - 1))

    def draw_confirm(self, s):
        overlay = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        overlay.fill((90, 55, 45, 120))
        s.blit(overlay, (0, 0))

        rnd = random.Random(7)
        sketch_rect(s, rnd, (370, 235, 480, 225), ROSE_DEEP, ROSE_DEEP, 16, 1, 0)
        sketch_rect(s, rnd, (360, 225, 480, 225), CREAM, INK, 16, 3)

        draw_heart(s, 600, 262, 14)
        self.text(s, self.f_label, "log out?", DARK, center=(600, 306))
        self.text(s, self.f_small, "your session will be closed.", INK,
                  center=(600, 346))

        for rect, label, idx, base, hov in (
            (self.cancel_rect, "cancel", 0, DARK, DARK_HOVER),
            (self.logout_rect, "log out", 1, LOGOUT_FILL, LOGOUT_HOVER),
        ):
            active = self.confirm_hover == idx
            pygame.draw.rect(s, hov if active else base, rect, border_radius=19)
            self.text(s, self.f_btn, label, CREAM, center=rect.center)

    def present(self):
        """Copy the design surface to the real screen (scaled + centered).
        Defined here too so this screen works even with an older login_screen.py."""
        if self.scale == 1.0 and self.offset == (0, 0):
            self.screen.blit(self.base, (0, 0))
        else:
            self.screen.fill(PEACH)
            size = (int(self.base.get_width() * self.scale),
                    int(self.base.get_height() * self.scale))
            self.screen.blit(pygame.transform.smoothscale(self.base, size), self.offset)

    def draw(self):
        self.time += 1
        s = self.base
        s.blit(self.static, (0, 0))

        self.draw_profile(s)
        self.draw_items(s)
        if self.confirm_logout:
            self.draw_confirm(s)

        self.present()

    # ------------------------------------------------------------
    # input
    # ------------------------------------------------------------
    def close_confirm(self):
        self.confirm_logout = False
        self.confirm_hover = -1

    def open_confirm(self):
        self.confirm_logout = True
        self.confirm_hover = 0

    def activate(self, index):
        """Run the item at index. Returns an action string or None."""
        self.selected_index = index
        self.play_click()
        action = ITEMS[index][1]
        if action == "logout":
            self.open_confirm()
            return None
        return action

    def update(self, events=None, dt=0.0):
        action = None

        for event in events or []:
            if event.type == pygame.VIDEORESIZE:
                self.resize(max(800, event.w), max(600, event.h))

            elif event.type == pygame.KEYDOWN:
                if self.confirm_logout:
                    if event.key == pygame.K_LEFT:
                        self.confirm_hover = 0
                    elif event.key == pygame.K_RIGHT:
                        self.confirm_hover = 1
                    elif event.key in (pygame.K_ESCAPE, pygame.K_n):
                        self.close_confirm()
                    elif event.key == pygame.K_y:
                        self.play_click()
                        self.close_confirm()
                        action = "logout"
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        if self.confirm_hover == 1:
                            self.play_click()
                            self.close_confirm()
                            action = "logout"
                        elif self.confirm_hover == 0:
                            self.play_click()
                            self.close_confirm()
                    continue

                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(ITEMS)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(ITEMS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    action = self.activate(self.selected_index) or action
                elif event.key == pygame.K_ESCAPE:
                    self.open_confirm()

            elif event.type == pygame.MOUSEMOTION:
                pos = self.to_base(event.pos)

                if self.confirm_logout:
                    new_hover = -1
                    if self.cancel_rect.collidepoint(pos):
                        new_hover = 0
                    elif self.logout_rect.collidepoint(pos):
                        new_hover = 1
                    if new_hover != self.confirm_hover and new_hover != -1:
                        self.play_hover()
                    self.confirm_hover = new_hover
                    continue

                new_hover = -1
                for i, rect in enumerate(self.item_rects):
                    if rect.collidepoint(pos):
                        new_hover = i
                        break

                if new_hover != self.hover_index and new_hover != -1:
                    self.play_hover()
                self.hover_index = new_hover
                if new_hover != -1:
                    self.selected_index = new_hover

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.to_base(event.pos)

                if self.confirm_logout:
                    if self.cancel_rect.collidepoint(pos):
                        self.play_click()
                        self.close_confirm()
                    elif self.logout_rect.collidepoint(pos):
                        self.play_click()
                        self.close_confirm()
                        action = "logout"
                    continue

                for i, rect in enumerate(self.item_rects):
                    if rect.collidepoint(pos):
                        action = self.activate(i) or action
                        break

        return action