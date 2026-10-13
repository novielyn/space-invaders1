import pygame
import math


class MobileButtons:

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.button_width = 100
        self.button_height = 70

        self.margin = 25
        self.gap = 20

        self.bottom_margin = 25

        self.left_rect = pygame.Rect(
            self.margin,
            self.screen_height -
            self.button_height -
            self.bottom_margin,
            self.button_width,
            self.button_height
        )

        self.right_rect = pygame.Rect(
            self.margin +
            self.button_width +
            self.gap,
            self.screen_height -
            self.button_height -
            self.bottom_margin,
            self.button_width,
            self.button_height
        )

        self.fire_rect = pygame.Rect(
            self.screen_width -
            self.button_width -
            self.margin,
            self.screen_height -
            self.button_height -
            self.bottom_margin,
            self.button_width,
            self.button_height
        )

        self.left_button = self.left_rect
        self.right_button = self.right_rect

        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False

        self.font = pygame.font.SysFont(
            "Arial",
            38,
            bold=True
        )

        self.small_font = pygame.font.SysFont(
            "Arial",
            20,
            bold=True
        )

        self.button_sound = None

        try:
            self.button_sound = pygame.mixer.Sound(
                "assets/sounds/button_click.wav"
            )
        except pygame.error:
            self.button_sound = None

    def update(self, events):

        self.left_pressed = False
        self.right_pressed = False
        self.fire_pressed = False

        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()

        if mouse_pressed:

            if self.left_rect.collidepoint(mouse_pos):
                self.left_pressed = True

            elif self.right_rect.collidepoint(mouse_pos):
                self.right_pressed = True

            elif self.fire_rect.collidepoint(mouse_pos):
                self.fire_pressed = True

        for event in events:

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if self.left_rect.collidepoint(
                        event.pos
                    ):
                        self.left_pressed = True
                        self.play_sound()

                    elif self.right_rect.collidepoint(
                        event.pos
                    ):
                        self.right_pressed = True
                        self.play_sound()

                    elif self.fire_rect.collidepoint(
                        event.pos
                    ):
                        self.fire_pressed = True
                        self.play_sound()

            elif event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:

                    self.left_pressed = False
                    self.right_pressed = False
                    self.fire_pressed = False

    def is_left_pressed(self):
        return self.left_pressed

    def is_right_pressed(self):
        return self.right_pressed

    def is_fire_pressed(self):
        return self.fire_pressed

    def play_sound(self):

        if self.button_sound:
            self.button_sound.play()

    def draw_button(
        self,
        screen,
        rect,
        text,
        pressed
    ):

        glow_rect = rect.inflate(
            12,
            12
        )

        glow_surface = pygame.Surface(
            (
                glow_rect.width,
                glow_rect.height
            ),
            pygame.SRCALPHA
        )

        glow_alpha = 35

        if pressed:
            glow_alpha = 75

        pygame.draw.rect(
            glow_surface,
            (
                0,
                220,
                255,
                glow_alpha
            ),
            glow_surface.get_rect(),
            border_radius=18
        )

        screen.blit(
            glow_surface,
            glow_rect.topleft
        )

        if pressed:

            button_color = (
                0,
                180,
                220
            )

            border_color = (
                180,
                250,
                255
            )

        else:

            button_color = (
                15,
                30,
                65
            )

            border_color = (
                0,
                210,
                255
            )

        pygame.draw.rect(
            screen,
            button_color,
            rect,
            border_radius=16
        )

        pygame.draw.rect(
            screen,
            border_color,
            rect,
            3,
            border_radius=16
        )

        text_surface = self.font.render(
            text,
            True,
            (
                235,
                250,
                255
            )
        )

        text_x = (
            rect.centerx -
            text_surface.get_width() // 2
        )

        text_y = (
            rect.centery -
            text_surface.get_height() // 2
        )

        screen.blit(
            text_surface,
            (
                text_x,
                text_y
            )
        )

    def draw(self, screen):

        self.draw_button(
            screen,
            self.left_rect,
            "◀",
            self.left_pressed
        )

        self.draw_button(
            screen,
            self.right_rect,
            "▶",
            self.right_pressed
        )

        self.draw_button(
            screen,
            self.fire_rect,
            "FIRE",
            self.fire_pressed
        )

        label = self.small_font.render(
            "MOVE",
            True,
            (
                130,
                180,
                220
            )
        )

        screen.blit(
            label,
            (
                self.left_rect.x,
                self.left_rect.y -
                28
            )
        )