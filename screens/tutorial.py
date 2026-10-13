import math
import random

import pygame

try:
    from screens.login_screen import (
        LoginScreen, sketch_rect, draw_heart,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, TAN, HEART,
    )
except ImportError:
    from login_screen import (
        LoginScreen, sketch_rect, draw_heart,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, CREAM, TAN, HEART,
    )

# ---------------------------------------------------------------
# How-to-play screen, same cozy desktop window as the other screens.
#   TutorialScreen(screen, w, h)
#   update(events, dt=None) -> "menu" | None
#   draw(), resize(w, h)
# Edit PAGES below so the text matches your real controls/rules.
# ---------------------------------------------------------------

PAGES = [
    ("move & shoot", [
        "Use the left and right arrow keys (or A and D) to move your ship.",
        "Press SPACE to fire.",
        "Press ESC to pause the game.",
    ]),
    ("your mission", [
        "Destroy every invader before they reach the ground.",
        "Each wave moves faster than the last.",
        "You only have a few lives, so dodge their shots.",
    ]),
    ("score & rank", [
        "Every invader you destroy adds to your score.",
        "Score and XP raise your rank.",
        "Your best score is saved as your high score.",
    ]),
    ("tips", [
        "Keep moving. A still ship is an easy target.",
        "Shoot in short bursts instead of holding fire.",
        "Take out the edge invaders first to slow the wave.",
    ]),
]

SPRITE_A = [
    "..#.....#..",
    "...#...#...",
    "..#######..",
    ".##.###.##.",
    "###########",
    "#.#######.#",
    "#.#.....#.#",
    "...##.##...",
]

SPRITE_B = [
    "..#.....#..",
    "#..#...#..#",
    "#.#######.#",
    "###.###.###",
    "###########",
    ".#########.",
    "..#.....#..",
    ".#.......#.",
]

FIELD = pygame.Rect(225, 222, 365, 270)
FIELD_BG = (88, 62, 52)
ROW_COLORS = [HEART, CREAM, TAN, HEART]


class TutorialScreen(LoginScreen):
    ADDRESS = "www.space-invaders.com/tutorial:"

    def draw_card_static(self, s, rnd):
        sketch_rect(s, rnd, (616, 216, 285, 312), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (606, 208, 285, 312), ROSE, INK, 14, 3)

        sketch_rect(s, rnd, (FIELD.x + 8, FIELD.y + 8, FIELD.w, FIELD.h),
                    ROSE_DEEP, ROSE_DEEP, 12, 1, 0)
        sketch_rect(s, rnd, FIELD, FIELD_BG, INK, 12, 3)

    def __init__(self, screen, width, height):
        super().__init__(screen, width, height)

        self.page = 0

        rnd = random.Random(11)
        self.field_stars = [
            (rnd.randint(FIELD.x + 12, FIELD.right - 12),
             rnd.randint(FIELD.y + 12, FIELD.bottom - 12),
             rnd.choice((1, 1, 2)))
            for _ in range(28)
        ]

        self.prev_btn = pygame.Rect(640, 487, 104, 26)
        self.next_btn = pygame.Rect(752, 487, 118, 26)
        self.menu_link = pygame.Rect(292, 512, 226, 24)

    # ------------------------------------------------------------
    def wrap(self, font, text, max_w):
        lines, line = [], ""
        for word in text.split():
            trial = (line + " " + word).strip()
            if font.size(trial)[0] <= max_w:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    def draw_sprite(self, s, sprite, x, y, px, color):
        for ry, row in enumerate(sprite):
            for rx, ch in enumerate(row):
                if ch == "#":
                    pygame.draw.rect(s, color, (x + rx * px, y + ry * px, px, px))

    def draw_demo(self, s):
        for x, y, size in self.field_stars:
            pygame.draw.circle(s, (170, 135, 120), (x, y), size)

        t = self.time
        sprite = SPRITE_A if (t // 30) % 2 == 0 else SPRITE_B
        sway = math.sin(t * 0.025) * 22

        px = 3
        for row in range(4):
            for col in range(6):
                x = FIELD.x + 38 + col * 52 + sway
                y = FIELD.y + 26 + row * 38
                self.draw_sprite(s, sprite, int(x), int(y), px, ROW_COLORS[row])

        def ship_x(tick):
            return FIELD.centerx + math.sin(tick * 0.03) * 120

        ship_y = FIELD.bottom - 34
        sx = ship_x(t)
        pygame.draw.polygon(s, CREAM, [(sx, ship_y - 16), (sx - 16, ship_y + 6), (sx + 16, ship_y + 6)])
        pygame.draw.rect(s, CREAM, (sx - 20, ship_y + 6, 40, 8), border_radius=3)

        # one bullet every 50 frames, fired from where the ship was
        fire_tick = (t // 50) * 50
        age = t - fire_tick
        by = ship_y - 18 - age * 5
        if by > FIELD.y + 120:
            bx = ship_x(fire_tick)
            pygame.draw.rect(s, HEART, (bx - 2, by, 4, 12), border_radius=2)

    def draw_card(self, s, mouse):
        title, items = PAGES[self.page]
        self.text(s, self.f_label, title, DARK, topleft=(630, 226))

        y = 276
        max_w = 235
        for item in items:
            lines = self.wrap(self.f_small, item, max_w)
            draw_heart(s, 635, y + 9, 5)
            for line in lines:
                self.text(s, self.f_small, line, INK, topleft=(652, y))
                y += 21
            y += 9

        # page dots
        n = len(PAGES)
        start = 748 - (n - 1) * 9
        for i in range(n):
            c = (start + i * 18, 470)
            if i == self.page:
                pygame.draw.circle(s, DARK, c, 5)
            else:
                pygame.draw.circle(s, DARK, c, 5, 2)

        first = self.page == 0
        last = self.page == n - 1
        self.draw_button(self.prev_btn, "menu" if first else "back", mouse)
        self.draw_button(self.next_btn, "done" if last else "next", mouse)

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
        mouse = self.to_base(pygame.mouse.get_pos())

        self.draw_demo(s)
        self.draw_card(s, mouse)

        link = self.text(s, self.f_small, "skip tutorial", INK, center=self.menu_link.center)
        if self.menu_link.collidepoint(mouse):
            pygame.draw.line(s, INK, (link.left, link.bottom), (link.right, link.bottom), 2)

        self.present()

    # ------------------------------------------------------------
    def go_next(self):
        if self.page >= len(PAGES) - 1:
            self.page = 0
            return "menu"
        self.page += 1
        return None

    def go_prev(self):
        if self.page == 0:
            return "menu"
        self.page -= 1
        return None

    def update(self, events, dt=None):
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.play_click()
                    self.page = 0
                    return "menu"
                elif event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.play_click()
                    result = self.go_next()
                    if result:
                        return result
                elif event.key == pygame.K_LEFT:
                    self.play_click()
                    result = self.go_prev()
                    if result:
                        return result

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.to_base(event.pos)

                if self.next_btn.collidepoint(pos):
                    self.play_click()
                    result = self.go_next()
                    if result:
                        return result

                elif self.prev_btn.collidepoint(pos):
                    self.play_click()
                    result = self.go_prev()
                    if result:
                        return result

                elif self.menu_link.collidepoint(pos):
                    self.play_click()
                    self.page = 0
                    return "menu"

        return None