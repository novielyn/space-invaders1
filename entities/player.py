import pygame
import math
import random


class Player:

    def __init__(self, screen_width, screen_height):

        self.width = 86
        self.height = 86

        self.max_speed = 5
        self.acceleration = 0.45
        self.friction = 0.82

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - 165

        self.velocity_x = 0

        try:
            self.image = pygame.image.load(
                "assets/images/ship.png"
            ).convert_alpha()

            self.image = pygame.transform.smoothscale(
                self.image,
                (self.width, self.height)
            )

            self.base_image = self.image.copy()

        except pygame.error:

            self.image = None
            self.base_image = None

        self.is_blinking = False
        self.blink_timer = 0
        self.visible = True

        self.animation_timer = 0
        self.engine_timer = 0

        self.tilt_angle = 0

        self.shield_active = False
        self.shield_timer = 0
        self.shield_duration = 300

        self.hit_flash = 0

        self.trail = []
        self.lava_particles = []

    def move_left(self):

        if self.is_blinking:
            return

        self.velocity_x -= self.acceleration

        self.velocity_x = max(
            -self.max_speed,
            self.velocity_x
        )

    def move_right(self):

        if self.is_blinking:
            return

        self.velocity_x += self.acceleration

        self.velocity_x = min(
            self.max_speed,
            self.velocity_x
        )

    def update(self):

        if not self.is_blinking:

            self.x += self.velocity_x

            if abs(self.velocity_x) < 0.05:
                self.velocity_x = 0
            else:
                self.velocity_x *= self.friction

        self.keep_inside_screen()

        self.tilt_angle = 0

        self.animation_timer += 1
        self.engine_timer += 1

        if self.shield_active:

            self.shield_timer += 1

            if self.shield_timer >= self.shield_duration:
                self.deactivate_shield()

        if self.hit_flash > 0:
            self.hit_flash -= 1

        self.update_blink()
        self.update_trail()
        self.update_lava_particles()

    def update_blink(self):

        if self.is_blinking:

            self.blink_timer += 1

            if self.blink_timer % 7 == 0:
                self.visible = not self.visible

            if self.blink_timer >= 120:

                self.is_blinking = False
                self.blink_timer = 0
                self.visible = True

        else:

            self.visible = True

    def update_trail(self):

        center_x = int(
            self.x +
            self.width // 2
        )

        bottom_y = int(
            self.y +
            self.height -
            3
        )

        if abs(self.velocity_x) > 0.5:

            self.trail.append(
                [
                    center_x,
                    bottom_y,
                    12,
                    255
                ]
            )

        for particle in self.trail:

            particle[1] += 2
            particle[2] -= 0.35
            particle[3] -= 12

        self.trail = [
            particle
            for particle in self.trail
            if particle[2] > 0
            and particle[3] > 0
        ]

        if len(self.trail) > 25:
            self.trail.pop(0)

    def update_lava_particles(self):

        center_x = int(
            self.x +
            self.width // 2
        )

        engine_y = int(
            self.y +
            self.height -
            3
        )

        if self.visible:

            for _ in range(2):

                size = random.uniform(3, 8)

                self.lava_particles.append(
                    {
                        "x": center_x + random.uniform(-8, 8),
                        "y": engine_y + random.uniform(-2, 6),
                        "vx": random.uniform(-1.2, 1.2),
                        "vy": random.uniform(1.5, 4.5),
                        "size": size,
                        "life": random.randint(18, 32),
                        "max_life": 32
                    }
                )

        for particle in self.lava_particles:

            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]

            particle["vy"] *= 0.97
            particle["size"] *= 0.94
            particle["life"] -= 1

        self.lava_particles = [
            particle
            for particle in self.lava_particles
            if particle["life"] > 0
            and particle["size"] > 0.8
        ]

        if len(self.lava_particles) > 70:
            self.lava_particles = self.lava_particles[-70:]

    def keep_inside_screen(self):

        self.x = max(
            0,
            min(
                self.x,
                self.screen_width -
                self.width
            )
        )

        if self.x <= 0:

            self.velocity_x = max(
                0,
                self.velocity_x
            )

        elif self.x >= self.screen_width - self.width:

            self.velocity_x = min(
                0,
                self.velocity_x
            )

    def get_rect(self):

        return pygame.Rect(
            int(self.x + 10),
            int(self.y + 10),
            self.width - 20,
            self.height - 20
        )

    def activate_shield(self, duration=300):

        self.shield_active = True
        self.shield_timer = 0
        self.shield_duration = duration

    def deactivate_shield(self):

        self.shield_active = False
        self.shield_timer = 0

    def hit(self):

        self.hit_flash = 15
        self.is_blinking = True
        self.blink_timer = 0
        self.visible = True

    def draw_lava_particles(self, screen):

        for particle in self.lava_particles:

            x = int(particle["x"])
            y = int(particle["y"])
            size = max(1, int(particle["size"]))

            life_ratio = (
                particle["life"] /
                particle["max_life"]
            )

            alpha = int(
                max(
                    0,
                    min(
                        255,
                        life_ratio * 255
                    )
                )
            )

            surface_size = size * 5

            surface = pygame.Surface(
                (
                    surface_size,
                    surface_size
                ),
                pygame.SRCALPHA
            )

            center = (
                surface_size // 2,
                surface_size // 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    40,
                    0,
                    int(alpha * 0.25)
                ),
                center,
                size * 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    90,
                    0,
                    alpha
                ),
                center,
                size
            )

            if size >= 3:

                pygame.draw.circle(
                    surface,
                    (
                        255,
                        220,
                        40,
                        alpha
                    ),
                    center,
                    max(1, size // 2)
                )

            screen.blit(
                surface,
                (
                    x - surface_size // 2,
                    y - surface_size // 2
                )
            )

    def draw_trail(self, screen):

        for particle in self.trail:

            x = int(particle[0])
            y = int(particle[1])
            size = int(particle[2])
            alpha = int(particle[3])

            if size <= 0:
                continue

            surface = pygame.Surface(
                (
                    size * 2,
                    size * 2
                ),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    45,
                    0,
                    alpha
                ),
                (
                    size,
                    size
                ),
                size
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    130,
                    0,
                    min(
                        255,
                        alpha + 20
                    )
                ),
                (
                    size,
                    size
                ),
                max(
                    1,
                    size // 2
                )
            )

            screen.blit(
                surface,
                (
                    x - size,
                    y - size
                )
            )

    def draw_engine(self, screen):

        center_x = int(
            self.x +
            self.width // 2
        )

        engine_y = int(
            self.y +
            self.height -
            4
        )

        pulse = (
            math.sin(
                self.engine_timer * 0.30
            ) + 1
        ) / 2

        flame_height = int(
            24 +
            pulse * 20
        )

        glow_size = 100

        glow = pygame.Surface(
            (
                glow_size,
                glow_size
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (
                255,
                35,
                0,
                35
            ),
            (
                glow_size // 2,
                glow_size // 2
            ),
            38
        )

        pygame.draw.circle(
            glow,
            (
                255,
                90,
                0,
                50
            ),
            (
                glow_size // 2,
                glow_size // 2
            ),
            27
        )

        pygame.draw.circle(
            glow,
            (
                255,
                180,
                0,
                55
            ),
            (
                glow_size // 2,
                glow_size // 2
            ),
            17
        )

        screen.blit(
            glow,
            (
                center_x -
                glow_size // 2,
                engine_y -
                glow_size // 2
            )
        )

        outer_points = [
            (
                center_x - 18,
                engine_y
            ),
            (
                center_x - 8,
                engine_y +
                flame_height // 2
            ),
            (
                center_x,
                engine_y +
                flame_height
            ),
            (
                center_x + 8,
                engine_y +
                flame_height // 2
            ),
            (
                center_x + 18,
                engine_y
            )
        ]

        middle_points = [
            (
                center_x - 12,
                engine_y
            ),
            (
                center_x,
                engine_y +
                flame_height -
                5
            ),
            (
                center_x + 12,
                engine_y
            )
        ]

        inner_points = [
            (
                center_x - 7,
                engine_y
            ),
            (
                center_x,
                engine_y +
                flame_height -
                12
            ),
            (
                center_x + 7,
                engine_y
            )
        ]

        pygame.draw.polygon(
            screen,
            (
                255,
                35,
                0
            ),
            outer_points
        )

        pygame.draw.polygon(
            screen,
            (
                255,
                100,
                0
            ),
            middle_points
        )

        pygame.draw.polygon(
            screen,
            (
                255,
                200,
                30
            ),
            inner_points
        )

        pygame.draw.circle(
            screen,
            (
                255,
                245,
                180
            ),
            (
                center_x,
                engine_y + 4
            ),
            5
        )

    def draw_glow(self, screen):

        center_x = int(
            self.x +
            self.width // 2
        )

        center_y = int(
            self.y +
            self.height // 2
        )

        glow = pygame.Surface(
            (
                self.width * 2,
                self.height * 2
            ),
            pygame.SRCALPHA
        )

        for radius, alpha in [
            (50, 8),
            (44, 12),
            (38, 18),
            (32, 24)
        ]:

            pygame.draw.circle(
                glow,
                (
                    255,
                    60,
                    0,
                    alpha
                ),
                (
                    self.width,
                    self.height
                ),
                radius
            )

        screen.blit(
            glow,
            (
                center_x -
                self.width,
                center_y -
                self.height
            )
        )

    def draw_ship_details(self, screen):

        center_x = int(
            self.x +
            self.width // 2
        )

        top_y = int(
            self.y + 10
        )

        bottom_y = int(
            self.y +
            self.height -
            10
        )

        left_x = int(
            self.x + 8
        )

        right_x = int(
            self.x +
            self.width -
            8
        )

        wing_left = [
            (
                center_x - 10,
                top_y + 25
            ),
            (
                left_x,
                bottom_y - 5
            ),
            (
                center_x - 18,
                bottom_y - 15
            )
        ]

        wing_right = [
            (
                center_x + 10,
                top_y + 25
            ),
            (
                right_x,
                bottom_y - 5
            ),
            (
                center_x + 18,
                bottom_y - 15
            )
        ]

        pygame.draw.polygon(
            screen,
            (
                55,
                15,
                10
            ),
            wing_left
        )

        pygame.draw.polygon(
            screen,
            (
                55,
                15,
                10
            ),
            wing_right
        )

        pygame.draw.line(
            screen,
            (
                255,
                80,
                0
            ),
            wing_left[0],
            wing_left[1],
            2
        )

        pygame.draw.line(
            screen,
            (
                255,
                80,
                0
            ),
            wing_right[0],
            wing_right[1],
            2
        )

        cockpit = pygame.Rect(
            center_x - 13,
            top_y + 10,
            26,
            30
        )

        pygame.draw.ellipse(
            screen,
            (
                35,
                10,
                8
            ),
            cockpit
        )

        pygame.draw.ellipse(
            screen,
            (
                255,
                90,
                0
            ),
            cockpit,
            2
        )

        pygame.draw.line(
            screen,
            (
                255,
                220,
                80
            ),
            (
                center_x,
                cockpit.top + 5
            ),
            (
                center_x,
                cockpit.bottom - 5
            ),
            2
        )

    def draw_shield(self, screen):

        if not self.shield_active:
            return

        center = (
            int(
                self.x +
                self.width // 2
            ),
            int(
                self.y +
                self.height // 2
            )
        )

        pulse = (
            math.sin(
                self.shield_timer * 0.12
            ) + 1
        ) / 2

        radius = int(
            50 +
            pulse * 5
        )

        shield = pygame.Surface(
            (
                radius * 2 + 20,
                radius * 2 + 20
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            shield,
            (
                255,
                70,
                0,
                20
            ),
            (
                radius + 10,
                radius + 10
            ),
            radius
        )

        pygame.draw.circle(
            shield,
            (
                255,
                120,
                0,
                170
            ),
            (
                radius + 10,
                radius + 10
            ),
            radius,
            2
        )

        screen.blit(
            shield,
            (
                center[0] -
                radius -
                10,
                center[1] -
                radius -
                10
            )
        )

    def draw(self, screen):

        self.draw_lava_particles(screen)
        self.draw_trail(screen)
        self.draw_engine(screen)

        if not self.visible:
            return

        self.draw_glow(screen)

        if self.base_image is not None:

            image_rect = self.base_image.get_rect(
                center=(
                    int(
                        self.x +
                        self.width // 2
                    ),
                    int(
                        self.y +
                        self.height // 2
                    )
                )
            )

            screen.blit(
                self.base_image,
                image_rect
            )

        else:

            self.draw_ship_fallback(
                screen
            )

        self.draw_ship_details(
            screen
        )

        if self.hit_flash > 0:

            flash = pygame.Surface(
                (
                    self.width,
                    self.height
                ),
                pygame.SRCALPHA
            )

            flash.fill(
                (
                    255,
                    80,
                    0,
                    80
                )
            )

            screen.blit(
                flash,
                (
                    int(self.x),
                    int(self.y)
                )
            )

        self.draw_shield(screen)

    def draw_ship_fallback(self, screen):

        cx = int(
            self.x +
            self.width // 2
        )

        top = int(
            self.y + 5
        )

        bottom = int(
            self.y +
            self.height -
            8
        )

        body = [
            (
                cx,
                top
            ),
            (
                cx + 28,
                bottom - 12
            ),
            (
                cx + 18,
                bottom
            ),
            (
                cx,
                bottom - 8
            ),
            (
                cx - 18,
                bottom
            ),
            (
                cx - 28,
                bottom - 12
            )
        ]

        pygame.draw.polygon(
            screen,
            (
                90,
                20,
                5
            ),
            body
        )

        pygame.draw.polygon(
            screen,
            (
                255,
                70,
                0
            ),
            body,
            2
        )