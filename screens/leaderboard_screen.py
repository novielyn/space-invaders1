import math

import pygame

from score_crud import get_leaderboard

try:
    from screens.login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, CREAM, HEART,
    )
except ImportError:
    from login_screen import (
        LoginScreen, sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, CREAM, HEART,
    )

# ---------------------------------------------------------------
# Leaderboard in the same cozy desktop style as the other screens.
# Same interface as before:
#   LeaderboardScreen(screen, w, h)
#   update(events, dt=None) -> "back" | "quit" | None
#   draw(), refresh()
#   leaderboard_screen(screen, clock, on_back=None)
# ---------------------------------------------------------------

GOLD = (222, 170, 70)
SILVER = (170, 160, 160)
BRONZE = (190, 120, 80)

ROW_X, ROW_W, ROW_H, ROW_STEP, ROW_TOP = 502, 421, 23, 26, 252
MAX_ROWS = 10


class LeaderboardScreen(LoginScreen):
    ADDRESS = "www.space-invaders.com/leaderboard:"

    def draw_card_static(self, s, rnd):
        self.f_tiny = load_font(13)

        # title above the cup
        self.text(s, self.f_label, "top 10", DARK, center=(384, 240))

        # table card
        sketch_rect(s, rnd, (500, 216, 445, 318), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (490, 208, 445, 318), ROSE, INK, 14, 3)

        # header pill
        pygame.draw.rect(s, DARK, (ROW_X, 220, ROW_W, 26), border_radius=13)
        self.text(s, self.f_tiny, "rank", CREAM, center=(ROW_X + 24, 233))
        self.text(s, self.f_tiny, "player", CREAM, midleft=(ROW_X + 52, 233))
        self.text(s, self.f_tiny, "high score", CREAM,
                  midright=(ROW_X + ROW_W - 16, 233))

    def __init__(self, screen, width, height):
        super().__init__(screen, width, height)

        self.leaderboard = []
        self.hovered_row = None
        self.button_hover = None

        self.back_btn = pygame.Rect(300, 506, 80, 26)
        self.refresh_btn = pygame.Rect(388, 506, 80, 26)

        self.load_data()

    # ------------------------------------------------------------
    # data
    # ------------------------------------------------------------
    def load_data(self):
        try:
            data = get_leaderboard(MAX_ROWS)
            self.leaderboard = list(data) if data else []
        except Exception as error:
            print("Leaderboard error:", error)
            self.leaderboard = []

    def refresh(self):
        self.load_data()

    def update_size(self):
        surface = pygame.display.get_surface()
        if surface is None:
            return
        self.screen = surface
        if surface.get_width() != self.width or surface.get_height() != self.height:
            self.resize(surface.get_width(), surface.get_height())

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

    def row_rect(self, index):
        return pygame.Rect(ROW_X, ROW_TOP + index * ROW_STEP, ROW_W, ROW_H)

    @staticmethod
    def rank_color(rank):
        if rank == 1:
            return GOLD
        if rank == 2:
            return SILVER
        if rank == 3:
            return BRONZE
        return DARK

    def fit(self, font, msg, max_w):
        shown = msg
        while font.size(shown)[0] > max_w and len(shown) > 1:
            shown = shown[:-1]
        if shown != msg:
            shown = shown[:-1] + "…" if len(shown) > 1 else shown
        return shown

    def draw_rows(self, s, mouse):
        self.hovered_row = None

        if not self.leaderboard:
            self.text(s, self.f_icon, "no scores yet", INK, center=(712, 380))
            self.text(s, self.f_small, "be the first invader slayer!", INK,
                      center=(712, 412))
            return

        for i, data in enumerate(self.leaderboard[:MAX_ROWS]):
            rank = i + 1
            rect = self.row_rect(i)
            hovered = rect.collidepoint(mouse)
            if hovered:
                self.hovered_row = rank

            if hovered:
                fill = HEART
            elif i % 2 == 0:
                fill = CREAM
            else:
                fill = (252, 236, 222)

            pygame.draw.rect(s, fill, rect, border_radius=12)
            pygame.draw.rect(s, INK, rect, 2, border_radius=12)

            # rank badge
            color = self.rank_color(rank)
            center = (rect.x + 24, rect.centery)
            pygame.draw.circle(s, color, center, 10)
            self.text(s, self.f_tiny, str(rank), CREAM, center=center)
            if rank == 1:
                draw_heart(s, rect.x + 44, rect.centery - 1, 4, HEART, (214, 140, 120))

            # name
            name = str(data.get("username", "Unknown"))
            name = self.fit(self.f_small, name, 230)
            self.text(s, self.f_small, name, DARK,
                      midleft=(rect.x + (58 if rank == 1 else 52), rect.centery))

            # score
            value = data.get("score", data.get("high_score", 0))
            try:
                value = int(value or 0)
            except (TypeError, ValueError):
                value = 0
            self.text(s, self.f_small, f"{value:,}", INK,
                      midright=(rect.right - 16, rect.centery))

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

        self.draw_rows(s, mouse)

        self.draw_button(self.back_btn, "back", mouse)
        self.draw_button(self.refresh_btn, "refresh", mouse)

        self.present()

    # ------------------------------------------------------------
    # input
    # ------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            pos = self.to_base(event.pos)
            self.button_hover = None
            if self.back_btn.collidepoint(pos):
                self.button_hover = "back"
            elif self.refresh_btn.collidepoint(pos):
                self.button_hover = "refresh"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.to_base(event.pos)
            if self.back_btn.collidepoint(pos):
                self.play_click()
                return "back"
            if self.refresh_btn.collidepoint(pos):
                self.play_click()
                self.refresh()

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.play_click()
                return "back"
            if event.key == pygame.K_r:
                self.play_click()
                self.refresh()

        elif event.type == pygame.VIDEORESIZE:
            self.resize(event.w, event.h)

        return None

    def update(self, events, dt=None):
        self.update_size()

        for event in events or []:
            if event.type == pygame.QUIT:
                return "quit"

            result = self.handle_event(event)
            if result is not None:
                return result

        return None


def leaderboard_screen(screen, clock, on_back=None):
    board = LeaderboardScreen(screen, screen.get_width(), screen.get_height())

    while True:
        clock.tick(60)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        result = board.update(events, 1 / 60)
        board.draw()
        pygame.display.flip()

        if result == "back":
            if on_back:
                on_back()
            return

        if result == "quit":
            pygame.quit()
            return