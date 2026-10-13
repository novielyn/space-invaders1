import math
import os
import random

import pygame

from player_crud import login_player

# ---------------------------------------------------------------
# Cozy "desktop window" login screen.
# Everything is drawn with pygame primitives (no image assets needed)
# and every outline is slightly wobbled so it looks hand-inked.
# Same interface as your old LoginScreen:
#   update(events) -> player dict | "register" | "exit" | None
#   draw(), resize(w, h)
# Optional: drop a handwriting font at assets/fonts/handwriting.ttf
# ---------------------------------------------------------------

BASE_W, BASE_H = 1200, 675

PEACH = (247, 214, 197)
CREAM = (255, 245, 229)
INK = (107, 69, 52)
DARK = (110, 72, 55)
DARK_HOVER = (143, 98, 75)
ACTIVE_PILL = (128, 86, 66)
ROSE = (230, 184, 174)
ROSE_DEEP = (214, 163, 152)
ROSE_SHADOW = (232, 192, 172)
TAN = (176, 134, 100)
HEART = (248, 198, 205)
HEART_EDGE = (214, 140, 120)
RED = (200, 70, 80)
GREEN = (95, 140, 100)


def load_font(size):
    custom = "assets/fonts/handwriting.ttf"
    if os.path.exists(custom):
        try:
            return pygame.font.Font(custom, size)
        except pygame.error:
            pass
    for name in (
        "segoeprint", "bradleyhandita", "chalkboardse", "chalkboard",
        "comicsansms", "kristenitc", "arialroundedmtbold", "trebuchetms",
    ):
        path = pygame.font.match_font(name, bold=False)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("Arial", size, bold=True)


# ---------- sketchy drawing helpers ----------

def rounded_points(rect, r, step=9):
    x, y, w, h = rect
    r = min(r, w // 2, h // 2)
    pts = []

    def edge(x1, y1, x2, y2):
        dist = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(dist // step))
        for i in range(n):
            t = i / n
            pts.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))

    def arc(cx, cy, a0):
        for i in range(7):
            a = math.radians(a0 + i * 15)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))

    edge(x + r, y, x + w - r, y)
    arc(x + w - r, y + r, 270)
    edge(x + w, y + r, x + w, y + h - r)
    arc(x + w - r, y + h - r, 0)
    edge(x + w - r, y + h, x + r, y + h)
    arc(x + r, y + h - r, 90)
    edge(x, y + h - r, x, y + r)
    arc(x + r, y + r, 180)
    return pts


def jitter(pts, rnd, amt):
    return [(px + rnd.uniform(-amt, amt), py + rnd.uniform(-amt, amt))
            for px, py in pts]


def stroke(surf, pts, color, width, closed=False):
    if len(pts) < 2:
        return
    pygame.draw.lines(surf, color, closed, pts, width)
    if width > 2:
        for p in pts:
            pygame.draw.circle(surf, color, (int(p[0]), int(p[1])), width // 2)


def sketch_rect(surf, rnd, rect, fill, outline=INK, r=10, width=3, amt=1.3):
    if fill is not None:
        pygame.draw.rect(surf, fill, rect, border_radius=r)
    pts = jitter(rounded_points(rect, r), rnd, amt)
    stroke(surf, pts, outline, width, closed=True)


def sketch_line(surf, rnd, p1, p2, color=INK, width=3, amt=1.2):
    dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    n = max(2, int(dist // 10))
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((p1[0] + (p2[0] - p1[0]) * t + rnd.uniform(-amt, amt),
                    p1[1] + (p2[1] - p1[1]) * t + rnd.uniform(-amt, amt)))
    stroke(surf, pts, color, width)


def draw_heart(surf, cx, cy, s, fill=HEART, edge=HEART_EDGE):
    def shape(size, col):
        r = size // 2 + 1
        pygame.draw.circle(surf, col, (int(cx - size / 2), int(cy - size / 4)), r)
        pygame.draw.circle(surf, col, (int(cx + size / 2), int(cy - size / 4)), r)
        pygame.draw.polygon(surf, col, [
            (cx - size - 1, cy - size / 6),
            (cx + size + 1, cy - size / 6),
            (cx, cy + size + 1),
        ])

    shape(s + 4, edge)
    shape(s, fill)
    pygame.draw.circle(surf, (255, 255, 255), (int(cx - s * 0.6), int(cy - s * 0.45)), max(2, s // 6))


def draw_folder(surf, rnd, x, y, w, h):
    tab = [(x, y + 8), (x + 4, y), (x + w * 0.4, y), (x + w * 0.48, y + 8)]
    pygame.draw.polygon(surf, DARK, tab)
    pygame.draw.rect(surf, DARK, (x, y + 8, w, h - 8), border_radius=5)
    pygame.draw.rect(surf, (200, 150, 135), (x + 4, y + 14, w - 8, 9), border_radius=3)


def draw_gear(surf, cx, cy, r, color):
    for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(surf, color,
                         (cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6),
                         (cx + math.cos(a) * r * 1.1, cy + math.sin(a) * r * 1.1), 9)
    pygame.draw.circle(surf, color, (cx, cy), int(r * 0.85))
    pygame.draw.circle(surf, PEACH, (cx, cy), int(r * 0.36))


def draw_wifi(surf, cx, cy, color):
    for i, rad in enumerate((34, 23, 12)):
        rect = pygame.Rect(0, 0, rad * 2, rad * 2)
        rect.center = (cx, cy)
        pygame.draw.arc(surf, color, rect, math.radians(48), math.radians(132), 6)
    pygame.draw.circle(surf, color, (cx, cy - 1), 4)


class LoginScreen:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height

        self.f_label = load_font(31)
        self.f_input = load_font(26)
        self.f_btn = load_font(18)
        self.f_addr = load_font(17)
        self.f_icon = load_font(24)
        self.f_small = load_font(16)

        self.username = ""
        self.password = ""
        self.active_field = "username"
        self.password_visible = False
        self.message = ""
        self.message_color = RED
        self.time = 0

        # hit boxes (in 1200x675 design space)
        self.user_box = pygame.Rect(648, 329, 212, 62)
        self.pass_box = pygame.Rect(648, 398, 212, 62)
        self.cancel_btn = pygame.Rect(667, 468, 92, 25)
        self.accept_btn = pygame.Rect(762, 468, 80, 25)
        self.register_rect = pygame.Rect(260, 512, 226, 24)

        self.base = pygame.Surface((BASE_W, BASE_H))
        self.static = self.build_static()
        self.scale = 1.0
        self.offset = (0, 0)
        self.update_layout()

        try:
            self.button_click = pygame.mixer.Sound("assets/sounds/button_click.wav")
            self.button_click.set_volume(0.45)
        except (pygame.error, FileNotFoundError):
            self.button_click = None

        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load("assets/sounds/background_music.mp3")
                pygame.mixer.music.set_volume(0.22)
                pygame.mixer.music.play(-1)
        except (pygame.error, FileNotFoundError):
            pass

    # ------------------------------------------------------------
    # layout / helpers
    # ------------------------------------------------------------
    def update_layout(self):
        self.scale = min(self.width / BASE_W, self.height / BASE_H)
        sw, sh = int(BASE_W * self.scale), int(BASE_H * self.scale)
        self.offset = ((self.width - sw) // 2, (self.height - sh) // 2)

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.update_layout()

    def to_base(self, pos):
        return ((pos[0] - self.offset[0]) / self.scale,
                (pos[1] - self.offset[1]) / self.scale)

    def play_click(self):
        if self.button_click:
            try:
                self.button_click.play()
            except pygame.error:
                pass

    def text(self, surf, font, msg, color, **anchor):
        img = font.render(msg, True, color)
        rect = img.get_rect(**anchor)
        surf.blit(img, rect)
        return rect

    # ------------------------------------------------------------
    # static layer (built once, wobble stays still)
    # ------------------------------------------------------------
    ADDRESS = "www.space-invaders.com:"

    def draw_card_static(self, s, rnd):
        sketch_rect(s, rnd, (616, 226, 285, 292), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (606, 218, 285, 292), ROSE, INK, 14, 3)
        pygame.draw.circle(s, DARK, (753, 276), 47)

    def build_static(self):
        s = pygame.Surface((BASE_W, BASE_H))
        rnd = random.Random(31)
        s.fill(PEACH)

        # swirly lines top-left
        for k in range(3):
            pts = [(x, 18 + k * 15 + 30 * math.sin(x / 36 + k * 0.25) + x * 0.12)
                   for x in range(0, 165, 6)]
            stroke(s, jitter(pts, rnd, 0.6), INK, 2)

        # desktop icons
        draw_folder(s, rnd, 26, 158, 78, 62)
        self.text(s, self.f_icon, "intro", DARK, midtop=(66, 222))
        draw_folder(s, rnd, 34, 308, 78, 62)
        self.text(s, self.f_icon, "outro", DARK, midtop=(70, 372))

        # colour dots on the right
        for i, c in enumerate([(110, 72, 55), (150, 108, 88), (170, 135, 120),
                               (200, 165, 150), (225, 190, 175)]):
            pygame.draw.circle(s, c, (1167, 250 + i * 73), 20)

        # little windows top-right
        for (x, y, w, h) in [(1038, 8, 135, 176), (1012, 98, 108, 112)]:
            sketch_rect(s, rnd, (x, y, w, h), (232, 192, 182), INK, 3, 2)
            pygame.draw.rect(s, (214, 160, 150), (x + 2, y + 2, w - 4, 12), border_radius=2)
            for i in range(3):
                pygame.draw.rect(s, (255, 245, 229), (x + w - 14 - i * 11, y + 4, 7, 7), 1)
            for _ in range(7):
                lx = x + rnd.randint(14, w - 30)
                ly = y + rnd.randint(26, h - 24)
                pygame.draw.ellipse(s, (170, 135, 100),
                                    (lx, ly, rnd.randint(18, 30), rnd.randint(12, 20)))

        # music player behind the main window
        sketch_rect(s, rnd, (835, 420, 288, 176), ROSE, INK, 2, 2)
        pygame.draw.rect(s, TAN, (837, 422, 284, 20))
        pygame.draw.polygon(s, DARK, [(1020, 484), (1020, 522), (1046, 503)])
        pygame.draw.polygon(s, DARK, [(1046, 484), (1046, 522), (1072, 503)])
        draw_heart(s, 1096, 507, 11, CREAM, CREAM)
        pygame.draw.rect(s, CREAM, (883, 545, 205, 12))
        pygame.draw.rect(s, DARK, (1045, 545, 43, 12))
        pygame.draw.rect(s, INK, (883, 545, 205, 12), 1)

        # main window: shadow, tab, body
        sketch_rect(s, rnd, (205, 158, 765, 392), ROSE_SHADOW, ROSE_SHADOW, 12, 1, 0)
        tab = [(222, 150), (230, 122), (392, 118), (406, 136), (418, 112),
               (560, 112), (588, 142), (930, 150)]
        pygame.draw.polygon(s, CREAM, tab)
        stroke(s, jitter(tab, rnd, 1.2), INK, 3)
        sketch_rect(s, rnd, (195, 148, 765, 392), CREAM, INK, 12, 3)
        sketch_line(s, rnd, (196, 200), (959, 200), INK, 3)

        # address bar
        sketch_rect(s, rnd, (268, 160, 588, 28), CREAM, INK, 14, 3)
        self.text(s, self.f_addr, self.ADDRESS, INK, midleft=(290, 175))
        stroke(s, [(220, 168), (211, 177), (220, 187)], INK, 3)
        stroke(s, [(243, 168), (252, 177), (243, 187)], INK, 3)
        stroke(s, [(872, 182), (881, 171), (890, 182)], INK, 3)
        pygame.draw.rect(s, INK, (906, 164, 15, 15), 3, border_radius=3)
        sketch_line(s, rnd, (934, 167), (946, 167), INK, 3)
        sketch_line(s, rnd, (934, 175), (946, 175), INK, 3)

        # card (overridden by the register screen)
        self.draw_card_static(s, rnd)

        # taskbar
        for i in range(4):
            pygame.draw.rect(s, DARK, (8 + (i % 2) * 26, 619 + (i // 2) * 26, 23, 23))
        draw_folder(s, rnd, 103, 623, 46, 40)
        sketch_rect(s, rnd, (197, 632, 330, 34), (242, 196, 186), INK, 6, 2)
        pygame.draw.circle(s, INK, (213, 647), 6, 2)
        pygame.draw.line(s, INK, (217, 651), (223, 657), 3)
        self.text(s, self.f_small, "x", INK, center=(514, 649))
        sketch_rect(s, rnd, (952, 630, 62, 38), PEACH, INK, 4, 3)
        pygame.draw.rect(s, INK, (1014, 640, 6, 18))
        stroke(s, [(989, 635), (976, 651), (987, 651), (977, 664)], INK, 3)
        draw_wifi(s, 1071, 662, DARK)
        draw_gear(s, 1147, 645, 22, DARK)
        return s

    # ------------------------------------------------------------
    # dynamic bits
    # ------------------------------------------------------------
    def draw_cup(self, bob):
        s = self.base
        ox, oy = 0, bob
        pygame.draw.rect(s, (252, 238, 228), (300 + ox, 332 + oy, 168, 166), border_radius=44)
        pygame.draw.rect(s, (190, 120, 90), (300 + ox, 332 + oy, 168, 166), 3, border_radius=44)
        pygame.draw.rect(s, (160, 124, 108), (318 + ox, 350 + oy, 132, 130), border_radius=36)
        for cx, cy in ((350, 342), (418, 342)):
            pygame.draw.circle(s, (160, 124, 108), (cx + ox, cy + 30 + oy), 14)
        for cx, cy, w, h in ((356, 358, 22, 14), (404, 358, 22, 14),
                             (383, 380, 22, 14), (424, 383, 22, 14)):
            pygame.draw.ellipse(s, (96, 62, 50), (cx - w // 2 + ox, cy - h // 2 + oy, w, h))
        pygame.draw.ellipse(s, (96, 62, 50), (370 + ox, 421 + oy, 12, 8))
        pygame.draw.circle(s, (226, 160, 150), (360 + ox, 440 + oy), 5)
        pygame.draw.circle(s, (226, 160, 150), (388 + ox, 440 + oy), 5)
        pygame.draw.circle(s, (255, 255, 255), (340 + ox, 372 + oy), 4)

    def draw_pill(self, rect, label, field, value, is_password=False,
                  label_font=None, input_font=None):
        label_font = label_font or self.f_label
        input_font = input_font or self.f_input
        s = self.base
        active = self.active_field == field
        pygame.draw.rect(s, ACTIVE_PILL if active else DARK, rect, border_radius=rect.height // 2)
        if active:
            pygame.draw.rect(s, CREAM, rect, 2, border_radius=rect.height // 2)

        label_rect = self.text(s, label_font, label, CREAM,
                               midleft=(rect.x + 19, rect.centery - 2))
        start_x = label_rect.right + 10

        shown = value
        if is_password:
            shown = "\u2022" * len(value)

        max_w = rect.right - start_x - 20
        img = input_font.render(shown, True, CREAM)
        while img.get_width() > max_w and shown:
            shown = shown[1:]
            img = input_font.render(shown, True, CREAM)

        r = img.get_rect(midleft=(start_x, rect.centery - 1))
        s.blit(img, r)

        if active and (self.time // 30) % 2 == 0:
            cx = r.right + 3 if shown else start_x
            pygame.draw.line(s, CREAM, (cx, rect.centery - 13), (cx, rect.centery + 13), 2)

    def draw_button(self, rect, label, mouse):
        hover = rect.collidepoint(mouse)
        pygame.draw.rect(self.base, DARK_HOVER if hover else DARK, rect, border_radius=13)
        self.text(self.base, self.f_btn, label, CREAM, center=(rect.centerx, rect.centery - 1))

    def present(self):
        """Copy the 1200x675 design surface to the real screen (scaled + centered)."""
        if self.scale == 1.0 and self.offset == (0, 0):
            self.screen.blit(self.base, (0, 0))
        else:
            self.screen.fill(PEACH)
            size = (int(BASE_W * self.scale), int(BASE_H * self.scale))
            self.screen.blit(pygame.transform.smoothscale(self.base, size), self.offset)

    # ------------------------------------------------------------
    # draw
    # ------------------------------------------------------------
    def draw(self):
        self.time += 1
        s = self.base
        s.blit(self.static, (0, 0))
        mouse = self.to_base(pygame.mouse.get_pos())

        # hearts + cup float gently
        bob = math.sin(self.time * 0.05) * 3
        draw_heart(s, 349, 281 + bob * 0.6, 18)
        draw_heart(s, 418, 285 - bob * 0.6, 20)
        self.draw_cup(int(bob))

        # register link
        hover = self.register_rect.collidepoint(mouse)
        link = self.text(s, self.f_small, "new player?  create account", INK,
                         center=self.register_rect.center)
        if hover:
            pygame.draw.line(s, INK, (link.left, link.bottom), (link.right, link.bottom), 2)

        self.draw_pill(self.user_box, "user:", "username", self.username)
        self.draw_pill(self.pass_box, "pass:", "password", self.password, True)
        self.draw_button(self.cancel_btn, "cancel", mouse)
        self.draw_button(self.accept_btn, "accept", mouse)

        if self.message:
            self.text(s, self.f_small, self.message, self.message_color, center=(578, 572))

        self.present()

    # ------------------------------------------------------------
    # logic
    # ------------------------------------------------------------
    def do_login(self):
        name = self.username.strip()

        if not name:
            self.message = "please enter your username"
            self.message_color = RED
            return None

        if not self.password:
            self.message = "please enter your password"
            self.message_color = RED
            return None

        try:
            player = login_player(name, self.password)
        except Exception as e:
            print("Login screen error:", e)
            player = None

        if player:
            self.message = ""
            return player

        self.message = "wrong username or password"
        self.message_color = RED
        return None

    def clear_fields(self):
        self.username = ""
        self.password = ""
        self.message = ""
        self.active_field = "username"

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.play_click()
                    return "exit"

                elif event.key == pygame.K_TAB:
                    self.play_click()
                    self.active_field = (
                        "password" if self.active_field == "username" else "username"
                    )

                elif event.key == pygame.K_BACKSPACE:
                    if self.active_field == "username":
                        self.username = self.username[:-1]
                    else:
                        self.password = self.password[:-1]

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.play_click()
                    player = self.do_login()
                    if player:
                        return player

                elif event.unicode and event.unicode.isprintable():
                    if self.active_field == "username":
                        if len(self.username) < 100:
                            self.username += event.unicode
                    else:
                        if len(self.password) < 100:
                            self.password += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.to_base(event.pos)

                if self.user_box.collidepoint(pos):
                    self.play_click()
                    self.active_field = "username"
                    self.message = ""

                elif self.pass_box.collidepoint(pos):
                    self.play_click()
                    self.active_field = "password"
                    self.message = ""

                elif self.accept_btn.collidepoint(pos):
                    self.play_click()
                    player = self.do_login()
                    if player:
                        return player

                elif self.cancel_btn.collidepoint(pos):
                    self.play_click()
                    self.clear_fields()

                elif self.register_rect.collidepoint(pos):
                    self.play_click()
                    return "register"

        return None