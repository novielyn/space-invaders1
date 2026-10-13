import pygame
import random
import math


class Bullet:

    def __init__(self, x, y):

        self.width = 32
        self.height = 32

        self.x = float(x)
        self.y = float(y)

        self.speed = 11.0

        self.is_active = True

        self.image = pygame.image.load(
            "assets/images/bullet.png"
        ).convert_alpha()

        self.image = pygame.transform.smoothscale(
            self.image,
            (
                self.width,
                self.height
            )
        )

        self.original_image = self.image.copy()

        self.timer = random.uniform(
            0,
            math.pi * 2
        )

        self.particles = []

        self.flame_particles = []

        self.trail_positions = []

        self.trail_length = 18

        self.particle_timer = 0

        self.flame_timer = 0

    def update(self):

        if not self.is_active:
            return

        self.timer += 0.25

        self.y -= self.speed

        center_x = (
            self.x +
            self.width / 2
        )

        center_y = (
            self.y +
            self.height
        )

        self.trail_positions.append(
            (
                center_x,
                center_y
            )
        )

        if len(
            self.trail_positions
        ) > self.trail_length:

            self.trail_positions.pop(0)

        self.particle_timer += 1

        if self.particle_timer >= 1:

            self.particle_timer = 0

            particle = {
                "x": center_x + random.uniform(
                    -6,
                    6
                ),

                "y": center_y + random.uniform(
                    -2,
                    8
                ),

                "vx": random.uniform(
                    -1.2,
                    1.2
                ),

                "vy": random.uniform(
                    1.0,
                    3.5
                ),

                "life": random.randint(
                    10,
                    24
                ),

                "max_life": 24,

                "size": random.randint(
                    2,
                    6
                )
            }

            self.flame_particles.append(
                particle
            )

        self.flame_timer += 1

        if self.flame_timer >= 3:

            self.flame_timer = 0

            particle = {
                "x": center_x + random.uniform(
                    -4,
                    4
                ),

                "y": center_y + random.uniform(
                    2,
                    10
                ),

                "vx": random.uniform(
                    -0.7,
                    0.7
                ),

                "vy": random.uniform(
                    1.5,
                    3.0
                ),

                "life": random.randint(
                    8,
                    16
                ),

                "max_life": 16,

                "size": random.randint(
                    2,
                    4
                )
            }

            self.particles.append(
                particle
            )

        for particle in self.flame_particles[:]:

            particle["x"] += particle["vx"]

            particle["y"] += particle["vy"]

            particle["vx"] *= 0.98

            particle["vy"] *= 0.98

            particle["life"] -= 1

            if particle["life"] <= 0:

                self.flame_particles.remove(
                    particle
                )

        for particle in self.particles[:]:

            particle["x"] += particle["vx"]

            particle["y"] += particle["vy"]

            particle["life"] -= 1

            if particle["life"] <= 0:

                self.particles.remove(
                    particle
                )

        if self.y < -self.height * 2:

            self.is_active = False

    def get_rect(self):

        hitbox_width = 12
        hitbox_height = 25

        return pygame.Rect(
            int(
                self.x +
                self.width / 2 -
                hitbox_width / 2
            ),
            int(
                self.y +
                self.height / 2 -
                hitbox_height / 2
            ),
            hitbox_width,
            hitbox_height
        )

    def draw_outer_glow(self, screen):

        center_x = int(
            self.x +
            self.width / 2
        )

        center_y = int(
            self.y +
            self.height / 2
        )

        glow_size = 120

        glow = pygame.Surface(
            (
                glow_size,
                glow_size
            ),
            pygame.SRCALPHA
        )

        center = (
            glow_size // 2,
            glow_size // 2
        )

        pulse = (
            math.sin(
                self.timer * 2
            ) + 1
        ) * 3

        pygame.draw.circle(
            glow,
            (
                255,
                50,
                5,
                12
            ),
            center,
            int(
                40 +
                pulse
            )
        )

        pygame.draw.circle(
            glow,
            (
                255,
                100,
                5,
                18
            ),
            center,
            int(
                29 +
                pulse
            )
        )

        pygame.draw.circle(
            glow,
            (
                255,
                180,
                20,
                28
            ),
            center,
            int(
                19 +
                pulse
            )
        )

        screen.blit(
            glow,
            (
                center_x -
                glow_size // 2,
                center_y -
                glow_size // 2
            )
        )

    def draw_flame_trail(self, screen):

        if len(
            self.trail_positions
        ) < 2:

            return

        total = len(
            self.trail_positions
        )

        for i, position in enumerate(
            self.trail_positions
        ):

            progress = (
                i /
                max(
                    1,
                    total - 1
                )
            )

            alpha = int(
                20 +
                130 *
                progress
            )

            radius = int(
                2 +
                7 *
                progress
            )

            x = int(
                position[0]
            )

            y = int(
                position[1]
            )

            surface = pygame.Surface(
                (
                    radius * 6,
                    radius * 6
                ),
                pygame.SRCALPHA
            )

            center = (
                surface.get_width() // 2,
                surface.get_height() // 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    50,
                    5,
                    alpha
                ),
                center,
                radius
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    140,
                    10,
                    alpha
                ),
                center,
                max(
                    1,
                    radius // 2
                )
            )

            screen.blit(
                surface,
                (
                    x -
                    surface.get_width() // 2,
                    y -
                    surface.get_height() // 2
                )
            )

    def draw_flame_particles(self, screen):

        for particle in self.flame_particles:

            ratio = (
                particle["life"] /
                particle["max_life"]
            )

            alpha = int(
                220 *
                ratio
            )

            size = max(
                1,
                int(
                    particle["size"] *
                    ratio
                )
            )

            surface = pygame.Surface(
                (
                    size * 6,
                    size * 6
                ),
                pygame.SRCALPHA
            )

            center = (
                surface.get_width() // 2,
                surface.get_height() // 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    45,
                    5,
                    alpha
                ),
                center,
                size * 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    150,
                    10,
                    alpha
                ),
                center,
                size
            )

            screen.blit(
                surface,
                (
                    int(
                        particle["x"] -
                        surface.get_width() / 2
                    ),
                    int(
                        particle["y"] -
                        surface.get_height() / 2
                    )
                )
            )

    def draw_particles(self, screen):

        for particle in self.particles:

            ratio = (
                particle["life"] /
                particle["max_life"]
            )

            alpha = int(
                160 *
                ratio
            )

            size = max(
                1,
                int(
                    particle["size"] *
                    ratio
                )
            )

            surface = pygame.Surface(
                (
                    size * 5,
                    size * 5
                ),
                pygame.SRCALPHA
            )

            center = (
                surface.get_width() // 2,
                surface.get_height() // 2
            )

            pygame.draw.circle(
                surface,
                (
                    255,
                    210,
                    60,
                    alpha
                ),
                center,
                size
            )

            screen.blit(
                surface,
                (
                    int(
                        particle["x"] -
                        surface.get_width() / 2
                    ),
                    int(
                        particle["y"] -
                        surface.get_height() / 2
                    )
                )
            )

    def draw_core(self, screen):

        center_x = int(
            self.x +
            self.width / 2
        )

        center_y = int(
            self.y +
            self.height / 2
        )

        pulse = (
            math.sin(
                self.timer * 3
            ) + 1
        ) * 2

        pygame.draw.ellipse(
            screen,
            (
                255,
                50,
                5
            ),
            (
                center_x - 9,
                center_y - 18,
                18,
                38
            )
        )

        pygame.draw.ellipse(
            screen,
            (
                255,
                150,
                10
            ),
            (
                center_x - 7,
                center_y - 16,
                14,
                34
            )
        )

        pygame.draw.ellipse(
            screen,
            (
                255,
                230,
                80
            ),
            (
                center_x - 5,
                center_y - 14,
                10,
                29
            )
        )

        pygame.draw.ellipse(
            screen,
            (
                255,
                255,
                230
            ),
            (
                center_x - 3,
                center_y - 12,
                6,
                25
            )
        )

        pygame.draw.circle(
            screen,
            (
                255,
                255,
                255
            ),
            (
                center_x,
                center_y - 8
            ),
            int(
                3 +
                pulse / 2
            )
        )

    def draw(self, screen):

        if not self.is_active:
            return

        self.draw_outer_glow(
            screen
        )

        self.draw_flame_trail(
            screen
        )

        self.draw_flame_particles(
            screen
        )

        self.draw_particles(
            screen
        )

        self.draw_core(
            screen
        )