import pygame
import math
import random


class Enemy:

    ENTERING = "entering"
    WAITING = "waiting"
    DIVING = "diving"
    RETURNING = "returning"
    OFFSCREEN = "offscreen"
    DEAD = "dead"

    def __init__(self, index, total_enemies, screen_width):

        self.screen_width = screen_width

        self.width = 80
        self.height = 80

        self.max_health = 1
        self.health = 1

        self.score_value = 10

        self.original_image = pygame.image.load(
            "assets/images/enemy.png"
        ).convert_alpha()

        self.original_image = pygame.transform.smoothscale(
            self.original_image,
            (self.width, self.height)
        )

        self.image = self.original_image

        spacing = screen_width / (total_enemies + 1)

        self.formation_x = (
            spacing * (index + 1)
            - self.width / 2
        )

        self.formation_y = (
            120 + (index % 2) * 50
        )

        self.x = self.formation_x
        self.y = -150

        self.speed = 220
        self.dive_speed = 300

        self.dx = 0
        self.dy = 0

        self.state = Enemy.ENTERING

        self.angle = 0

        self.bob_timer = random.uniform(0, 10)
        self.bob_amount = 6

        self.visual_y = self.y

        self.alive = True

        self.dive_target_x = 0
        self.dive_target_y = 0

    def start_dive(self, target_x, target_y):

        if self.state != Enemy.WAITING:
            return False

        self.state = Enemy.DIVING

        self.dive_target_x = target_x
        self.dive_target_y = target_y

        center_x = self.x + self.width / 2
        center_y = self.visual_y + self.height / 2

        dx = target_x - center_x
        dy = target_y - center_y

        distance = math.sqrt(
            dx * dx + dy * dy
        )

        if distance > 0:

            self.dx = dx / distance
            self.dy = dy / distance

        else:

            self.dx = 0
            self.dy = 1

        return True

    def take_damage(self, amount=1):

        self.health -= amount

        if self.health <= 0:

            self.health = 0
            self.state = Enemy.DEAD
            self.alive = False

            return True

        return False

    def can_shoot(self):

        if self.state != Enemy.WAITING:
            return False

        return random.random() < 0.002

    def update(self, dt):

        if not self.alive:
            return

        self.bob_timer += dt

        if self.state == Enemy.ENTERING:

            self.y += self.speed * dt
            self.visual_y = self.y

            if self.y >= self.formation_y:

                self.y = self.formation_y
                self.visual_y = self.y
                self.state = Enemy.WAITING

        elif self.state == Enemy.WAITING:

            bob = (
                math.sin(
                    self.bob_timer * 3
                ) * self.bob_amount
            )

            self.visual_y = (
                self.formation_y + bob
            )

        elif self.state == Enemy.DIVING:

            self.x += (
                self.dx
                * self.dive_speed
                * dt
            )

            self.y += (
                self.dy
                * self.dive_speed
                * dt
            )

            self.angle += 240 * dt

            if (
                self.y > 700
                or self.x < -150
                or self.x > self.screen_width + 150
            ):

                self.state = Enemy.OFFSCREEN
                self.alive = False

        elif self.state == Enemy.OFFSCREEN:

            self.alive = False

        elif self.state == Enemy.DEAD:

            self.alive = False

    def get_rect(self):

        if self.state == Enemy.WAITING:

            y = self.visual_y

        else:

            y = self.y

        return pygame.Rect(
            int(self.x),
            int(y),
            self.width,
            self.height
        )

    def draw(self, screen):

        if not self.alive:
            return

        if self.state == Enemy.WAITING:

            draw_y = self.visual_y

        else:

            draw_y = self.y

        if self.state == Enemy.DIVING:

            rotated = pygame.transform.rotate(
                self.original_image,
                self.angle
            )

            rect = rotated.get_rect(
                center=(
                    self.x + self.width / 2,
                    draw_y + self.height / 2
                )
            )

            screen.blit(
                rotated,
                rect
            )

        else:

            screen.blit(
                self.image,
                (
                    int(self.x),
                    int(draw_y)
                )
            )

    def is_alive(self):

        return self.alive