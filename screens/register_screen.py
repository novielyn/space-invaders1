import math

import pygame

from player_crud import register_player
try:
    # project layout: Pohanes/screens/login_screen.py
    from screens.login_screen import (
        LoginScreen,
        sketch_rect,
        draw_heart,
        load_font,
        PEACH,
        ROSE,
        ROSE_DEEP,
        INK,
        DARK,
        CREAM,
        RED,
        GREEN,
    )
except ImportError:
    # both files sitting in the same folder
    from login_screen import (
        LoginScreen,
        sketch_rect,
        draw_heart,
        load_font,
        PEACH,
        ROSE,
        ROSE_DEEP,
        INK,
        DARK,
        CREAM,
        RED,
        GREEN,
    )

# ---------------------------------------------------------------
# Register screen: same cozy desktop window as the login screen,
# with a taller card holding 4 fields. Same interface as before:
#   update(events, dt=None) -> "login" | None
#   draw(), resize(w, h)
# ---------------------------------------------------------------

FIELDS = ["username", "email", "password", "confirm_password"]


class RegisterScreen(LoginScreen):
    ADDRESS = "www.space-invaders.com/register:"

    def draw_card_static(self, s, rnd):
        sketch_rect(s, rnd, (616, 216, 285, 312), ROSE_DEEP, INK, 14, 2)
        sketch_rect(s, rnd, (606, 208, 285, 312), ROSE, INK, 14, 3)
        pygame.draw.circle(s, DARK, (748, 250), 34)

    def __init__(self, screen, width, height):
        super().__init__(screen, width, height)

        self.email = ""
        self.confirm_password = ""

        self.f_label_s = load_font(22)
        self.f_input_s = load_font(21)

        x, w, h = 636, 234, 40
        self.username_box = pygame.Rect(x, 296, w, h)
        self.email_box = pygame.Rect(x, 342, w, h)
        self.password_box = pygame.Rect(x, 388, w, h)
        self.confirm_box = pygame.Rect(x, 434, w, h)

        self.back_btn = pygame.Rect(640, 487, 104, 26)
        self.create_btn = pygame.Rect(752, 487, 118, 26)
        self.login_link = pygame.Rect(260, 512, 226, 24)

        self.boxes = {
            "username": self.username_box,
            "email": self.email_box,
            "password": self.password_box,
            "confirm_password": self.confirm_box,
        }

    # ------------------------------------------------------------
    def get_value(self, field):
        return getattr(self, field)

    def set_value(self, field, value):
        setattr(self, field, value)

    def draw(self):
        self.time += 1
        s = self.base
        s.blit(self.static, (0, 0))
        mouse = self.to_base(pygame.mouse.get_pos())

        bob = math.sin(self.time * 0.05) * 3
        draw_heart(s, 349, 281 + bob * 0.6, 18)
        draw_heart(s, 418, 285 - bob * 0.6, 20)
        self.draw_cup(int(bob))

        hover = self.login_link.collidepoint(mouse)
        link = self.text(s, self.f_small, "have an account?  log in", INK,
                         center=self.login_link.center)
        if hover:
            pygame.draw.line(s, INK, (link.left, link.bottom),
                             (link.right, link.bottom), 2)

        self.draw_pill(self.username_box, "user:", "username",
                       self.username, False, self.f_label_s, self.f_input_s)
        self.draw_pill(self.email_box, "email:", "email",
                       self.email, False, self.f_label_s, self.f_input_s)
        self.draw_pill(self.password_box, "pass:", "password",
                       self.password, True, self.f_label_s, self.f_input_s)
        self.draw_pill(self.confirm_box, "again:", "confirm_password",
                       self.confirm_password, True, self.f_label_s, self.f_input_s)

        self.draw_button(self.back_btn, "back", mouse)
        self.draw_button(self.create_btn, "create", mouse)

        if self.message:
            self.text(s, self.f_small, self.message, self.message_color,
                      center=(578, 572))

        if self.scale == 1.0 and self.offset == (0, 0):
            self.screen.blit(s, (0, 0))
        else:
            self.screen.fill(PEACH)
            size = (int(self.base.get_width() * self.scale),
                    int(self.base.get_height() * self.scale))
            self.screen.blit(pygame.transform.smoothscale(s, size), self.offset)

    # ------------------------------------------------------------
    def fail(self, text):
        self.message = text
        self.message_color = RED
        return None

    def do_register(self):
        username = self.username.strip()
        email = self.email.strip()
        password = self.password
        confirm = self.confirm_password

        if not username:
            return self.fail("please enter a username")
        if len(username) < 3:
            return self.fail("username is too short")
        if not email:
            return self.fail("please enter your email")
        if "@" not in email or "." not in email:
            return self.fail("that email doesn't look right")
        if not password:
            return self.fail("please enter a password")
        if len(password) < 4:
            return self.fail("password is too short")
        if not confirm:
            return self.fail("please confirm your password")
        if password != confirm:
            return self.fail("passwords do not match")

        try:
            result = register_player(username, email, password)
        except Exception as error:
            print("Register screen error:", error)
            result = False

        if result:
            self.message = "account created!"
            self.message_color = GREEN
            self.username = ""
            self.email = ""
            self.password = ""
            self.confirm_password = ""
            return "login"

        return self.fail("username or email already exists")

    def update(self, events, dt=None):
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.play_click()
                    return "login"

                elif event.key == pygame.K_TAB:
                    i = FIELDS.index(self.active_field)
                    self.active_field = FIELDS[(i + 1) % len(FIELDS)]
                    self.message = ""
                    self.play_click()

                elif event.key == pygame.K_BACKSPACE:
                    self.set_value(self.active_field,
                                   self.get_value(self.active_field)[:-1])

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.play_click()
                    result = self.do_register()
                    if result:
                        return result

                elif event.unicode and event.unicode.isprintable():
                    limit = 100 if self.active_field == "email" else 50
                    value = self.get_value(self.active_field)
                    if len(value) < limit:
                        self.set_value(self.active_field, value + event.unicode)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.to_base(event.pos)

                clicked_field = None
                for name, box in self.boxes.items():
                    if box.collidepoint(pos):
                        clicked_field = name
                        break

                if clicked_field:
                    self.active_field = clicked_field
                    self.message = ""
                    self.play_click()

                elif self.create_btn.collidepoint(pos):
                    self.play_click()
                    result = self.do_register()
                    if result:
                        return result

                elif self.back_btn.collidepoint(pos) or self.login_link.collidepoint(pos):
                    self.play_click()
                    return "login"

        return None