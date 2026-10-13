import pygame
import random
import math
import os
import json

from entities.player import Player
from entities.button import MobileButtons
from entities.enemy import Enemy
from entities.bullet import Bullet
from database import save_score, get_player


try:
    from screens.login_screen import (
        sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, ACTIVE_PILL,
        CREAM, HEART, HEART_EDGE, TAN, RED, GREEN,
    )
except ImportError:
    from screens.login_screen import (
        sketch_rect, draw_heart, load_font,
        PEACH, ROSE, ROSE_DEEP, INK, DARK, DARK_HOVER, ACTIVE_PILL,
        CREAM, HEART, HEART_EDGE, TAN, RED, GREEN,
    )

# ---------------------------------------------------------------
# Game screen in the same cozy hand-inked style as the menus.
# Gameplay logic is unchanged. The ship, enemy and bullet sprites
# are still drawn by entities/*.py, so restyle those files for
# a fully matching look.
# ---------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_STATS_FILE = os.path.join(PROJECT_ROOT, "profile_settings.json")

# set True to draw assets/images/background.jpg instead of the plain peach background
USE_BACKGROUND_IMAGE = False


def _load_profile_stats_cache(player_id):
    if player_id is None:
        return {}
    try:
        if not os.path.isfile(PROFILE_STATS_FILE):
            return {}
        with open(PROFILE_STATS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            values = data.get(str(player_id), {})
            return values if isinstance(values, dict) else {}
    except Exception:
        pass
    return {}


def _save_profile_stats_cache(player_id, values):
    if player_id is None:
        return False
    try:
        data = {}
        if os.path.isfile(PROFILE_STATS_FILE):
            try:
                with open(PROFILE_STATS_FILE, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    data = loaded
            except Exception:
                data = {}
        existing = data.get(str(player_id), {})
        if not isinstance(existing, dict):
            existing = {}
        existing.update(values)
        data[str(player_id)] = existing
        temp = PROFILE_STATS_FILE + ".tmp"
        with open(temp, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        os.replace(temp, PROFILE_STATS_FILE)
        return True
    except Exception:
        return False


# effect colours (cozy palette)
SPARK = TAN                  # muzzle sparks
HIT = (222, 170, 70)         # enemy hit
KILL = (240, 140, 160)       # enemy destroyed
DEATH = RED                  # player destroyed
OVERLAY = (90, 55, 45, 120)  # dim layer behind dialogs

SOUND_DIR = os.path.join("assets", "sounds")
TARGET_FPS = 60


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


# ===============================================================
# background decoration
# ===============================================================

class FloatHeart:
    """Soft hearts and dots drifting upwards behind the action."""

    def __init__(self, w, h):
        self.w = w
        self.h = h

        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.base_x = self.x

        self.heart = random.random() < 0.55
        self.size = random.randint(6, 14) if self.heart else random.randint(3, 7)
        self.speed = random.uniform(0.15, 0.45)
        self.phase = random.uniform(0, math.pi * 2)
        self.color = random.choice((HEART, ROSE, (252, 226, 214)))

    def update(self):
        self.y -= self.speed
        self.x = self.base_x + math.sin(pygame.time.get_ticks() * 0.0006 + self.phase) * 14

        if self.y < -20:
            self.y = self.h + 20
            self.base_x = random.uniform(0, self.w)

    def draw(self, surface, t):
        if self.heart:
            draw_heart(surface, int(self.x), int(self.y), self.size, self.color, ROSE_DEEP)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


class Particle:

    def __init__(self, x, y, color):

        self.x = x
        self.y = y
        self.color = color

        angle = random.uniform(0, math.pi * 2)

        speed = random.uniform(0.6, 1.8)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = random.randint(24, 45)

        self.max_life = self.life

        self.size = random.uniform(2.0, 4.0)

    def update(self):

        self.x += self.vx
        self.y += self.vy

        self.vx *= 0.94
        self.vy *= 0.94

        self.life -= 1

    def draw(self, surface):

        if self.life <= 0:
            return

        fade = self.life / self.max_life

        cur_size = max(1, int(self.size * (0.5 + 0.5 * fade)))

        # fade towards the peach background instead of towards black
        color = lerp_color(PEACH, self.color, fade)

        pygame.draw.circle(
            surface,
            color,
            (int(self.x), int(self.y)),
            cur_size
        )

    @property
    def alive(self):

        return self.life > 0


class ImpactRing:

    def __init__(self, x, y, color, max_radius=78, life=24, width=3):
        self.x = float(x)
        self.y = float(y)
        self.color = tuple(color[:3])
        self.radius = 7.0
        self.max_radius = float(max_radius)
        self.life = int(life)
        self.max_life = int(life)
        self.width = int(width)
        self.angle = random.uniform(0.0, math.pi * 2.0)

    def update(self):
        self.radius += (self.max_radius - self.radius) * 0.22
        self.angle += 0.08
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(210 * (self.life / max(1, self.max_life)))
        r = max(2, int(self.radius))
        glow = pygame.Surface((r * 2 + 40, r * 2 + 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, alpha), glow.get_rect().center, r, self.width)
        surface.blit(glow, (int(self.x - r - 20), int(self.y - r - 20)))


# ===============================================================
# game manager
# ===============================================================

class GameManager:

    def __init__(
        self,
        screen,
        screen_width,
        screen_height,
        username=None,
        player_id=None,
        player_data=None
    ):

        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player_id = player_id
        self.player_data = player_data if isinstance(player_data, dict) else {}

        if self.player_id is None:
            self.player_id = (
                self.player_data.get("id")
                or self.player_data.get("player_id")
                or self.player_data.get("user_id")
            )

        self.username = username
        if not self.username and self.player_data:
            self.username = (
                self.player_data.get("username")
                or self.player_data.get("name")
            )

        # Fonts (handwriting style, same as the other screens)
        self.font = load_font(24)
        self.small_font = load_font(16)
        self.big_font = load_font(44)
        self.label_font = load_font(30)
        self.button_font = load_font(20)

        self.button_width = 280
        self.button_height = 40

        self.button_x = self.screen_width // 2 - self.button_width // 2

        self.resume_button_rect = pygame.Rect(self.button_x, 240, self.button_width, self.button_height)
        self.restart_button_rect = pygame.Rect(self.button_x, 292, self.button_width, self.button_height)
        self.pause_menu_button_rect = pygame.Rect(self.button_x, 344, self.button_width, self.button_height)
        self.game_over_restart_rect = pygame.Rect(self.button_x, 360, self.button_width, self.button_height)
        self.game_over_menu_rect = pygame.Rect(self.button_x, 412, self.button_width, self.button_height)

        self.decor = [
            FloatHeart(screen_width, screen_height)
            for _ in range(26)
        ]

        self.particles = []

        self.frame = 0
        self.shake_timer = 0

        self._hud_cache = None

        self.background_image = None
        self.background_scaled = None
        self.background_scaled_size = None
        if USE_BACKGROUND_IMAGE:
            self._load_game_background()

        self._init_audio()

        self.reset_game()

    def _load_game_background(self):
        candidates = (
            os.path.join("assets", "images", "background.jpg"),
            os.path.join("assets", "images", "background.jpeg"),
            os.path.join("assets", "images", "background.png"),
        )

        self.background_image = None

        for path in candidates:
            if not os.path.isfile(path):
                continue
            try:
                self.background_image = pygame.image.load(path).convert()
                break
            except Exception:
                self.background_image = None

        self.background_scaled = None
        self.background_scaled_size = None

    def _draw_game_background(self, surface):
        if self.background_image is None:
            surface.fill(PEACH)
            return

        size = surface.get_size()
        if self.background_scaled is None or self.background_scaled_size != size:
            try:
                self.background_scaled = pygame.transform.smoothscale(
                    self.background_image,
                    size
                )
                self.background_scaled_size = size
            except Exception:
                self.background_scaled = self.background_image
                self.background_scaled_size = self.background_image.get_size()

        surface.blit(self.background_scaled, (0, 0))

    # ------------------------------------------------------------
    # audio
    # ------------------------------------------------------------
    def _load_sound(self, filenames, volume):
        for filename in filenames:
            path = os.path.join(SOUND_DIR, filename)
            if not os.path.isfile(path):
                continue
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(max(0.0, min(1.0, volume)))
                return sound
            except Exception:
                continue
        return None

    def _load_audio_settings(self):
        self.master_volume = 1.0
        self.music_volume = 0.35
        self.sfx_volume = 0.70

        settings_path = "profile_settings.json"

        try:
            if os.path.isfile(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                self.master_volume = float(
                    settings.get("master_volume", 1.0)
                )
                self.music_volume = float(
                    settings.get("music_volume", 0.70)
                )
                self.sfx_volume = float(
                    settings.get("sfx_volume", settings.get("sound_volume", 0.80))
                )
        except Exception:
            pass

        self.master_volume = max(0.0, min(1.0, self.master_volume))
        self.music_volume = max(0.0, min(1.0, self.music_volume))
        self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

        self._load_audio_settings()

        self.sfx_click = None
        self.sfx_defeated = None
        self.sfx_bullet = None
        self.sfx_enemy = None

        music_candidates = (
            "background_music.mp3",
            "background.mp3",
            "game_music.mp3",
        )

        self.music_path = None
        for filename in music_candidates:
            candidate = os.path.join(SOUND_DIR, filename)
            if os.path.isfile(candidate):
                self.music_path = candidate
                break

        sfx_volume = self.master_volume * self.sfx_volume

        self.sfx_click = self._load_sound(
            ("button_click.wav", "click.wav", "update_hover.wav"),
            sfx_volume * 0.65
        )

        self.sfx_defeated = self._load_sound(
            ("defeat.mp3", "defeated.mp3", "game_over.mp3", "player_hit.mp3"),
            sfx_volume * 0.85
        )

        self.sfx_bullet = self._load_sound(
            ("bullet.mp3", "bullet.wav"),
            sfx_volume * 0.50
        )

        self.sfx_enemy = self._load_sound(
            ("hit.mp3", "bullet_hit.mp3", "enemy.mp3", "enemy_shot.mp3"),
            sfx_volume * 0.65
        )

    def _apply_audio_volumes(self):
        try:
            pygame.mixer.music.set_volume(
                self.master_volume * self.music_volume
            )
        except Exception:
            pass

    def play_click(self):

        if self.sfx_click:

            self.sfx_click.play()

    def play_defeated(self):

        if self.sfx_defeated:

            self.sfx_defeated.play()

    def play_bullet(self):

        if self.sfx_bullet:

            self.sfx_bullet.play()

    def play_enemy_hit(self):

        if self.sfx_enemy:

            self.sfx_enemy.play()

    def start_music(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            if not self.music_path or not os.path.isfile(self.music_path):
                return

            pygame.mixer.music.load(self.music_path)
            self._apply_audio_volumes()
            pygame.mixer.music.play(-1)

        except Exception:
            pass

    def pause_music(self):

        try:
            pygame.mixer.music.pause()
        except Exception:
            pass

    def resume_music(self):

        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass

    def stop_music(self):

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ------------------------------------------------------------
    # game state
    # ------------------------------------------------------------
    def reset_game(self):

        self.player = Player(
            self.screen_width,
            self.screen_height
        )

        try:
            self.player.speed = min(float(getattr(self.player, "speed", 5.0)), 5.2)
        except Exception:
            pass
        try:
            self.player.max_speed = 5.2
        except Exception:
            pass
        try:
            self.player.acceleration = 0.58
        except Exception:
            pass
        try:
            self.player.friction = 0.86
        except Exception:
            pass

        try:
            self.buttons = MobileButtons(
                self.screen_width,
                self.screen_height
            )
        except TypeError:
            try:
                self.buttons = MobileButtons()
            except Exception:
                self.buttons = None
        except Exception:
            self.buttons = None

        self._update_mobile_rects()
        self.mobile_left_active = False
        self.mobile_right_active = False
        self.mobile_fire_active = False
        self.active_touch_controls = {}

        self.bullets = []
        self.enemies = []

        self.score = 0
        self.wave = 1
        self.spawn_number = 5

        self.shots_fired = 0
        self.shots_hit = 0
        self.kills_this_game = 0
        self.game_started = True

        self.game_state = "playing"

        self.player_history = []

        self.timer = 0
        self.state_timer = 0

        self.score_saved = False

        self.particles.clear()
        self.impact_rings = []
        self.kill_flash_timer = 0

        self.shake_timer = 0
        self.fire_cooldown_timer = 0

        self.defeated_played = False

        self.spawn_enemies()

        self.start_music()

    def spawn_enemies(self):

        self.enemies = [
            Enemy(i, self.spawn_number, self.screen_width)
            for i in range(self.spawn_number)
        ]

        self.timer = 0

    def trigger_explosion(
        self,
        x,
        y,
        color=HIT,
        count=18
    ):

        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def trigger_kill_effect(self, x, y):
        palette = (
            (240, 140, 160),
            (222, 170, 70),
            (176, 134, 100),
        )
        for color in palette:
            self.impact_rings.append(ImpactRing(x, y, color, max_radius=random.randint(58, 92), life=random.randint(18, 27), width=random.choice((2, 3))))
        for _ in range(28):
            self.particles.append(Particle(x, y, random.choice(palette)))
        self.shake_timer = max(self.shake_timer, 6)
        self.kill_flash_timer = 5

    def update(self, events, dt=None):
        """Advance the game one frame. Drawing is done by draw() (main.py calls it)."""

        self.frame += 1

        for event in events:

            if event.type == pygame.QUIT:

                self.stop_music()

                return "quit"

        if self.game_state == "menu":

            self.stop_music()

            return "menu"

        result = self.handle_keyboard(events)

        if result == "menu":

            self.stop_music()

            return "menu"

        if result == "restart":

            self.reset_game()

        for item in self.decor:
            item.update()

        for p in self.particles:
            p.update()

        self.particles = [p for p in self.particles if p.alive]

        for ring in self.impact_rings:
            ring.update()

        self.impact_rings = [r for r in self.impact_rings if r.alive]

        if self.kill_flash_timer > 0:
            self.kill_flash_timer -= 1

        if self.game_state == "playing":

            self.update_playing(events, dt)

        elif self.game_state == "paused":

            result = self.update_paused(events)

            if result == "restart":

                self.play_click()

                self.reset_game()

            elif result == "menu":

                self.play_click()

                self.stop_music()

                self.game_state = "menu"

                return "menu"

        elif self.game_state == "blinking":

            self.update_blinking(dt)

        elif self.game_state == "game_over":

            result = self.update_game_over(events)

            if result == "restart":

                self.play_click()

                self.reset_game()

            elif result == "menu":

                self.play_click()

                self.stop_music()

                self.game_state = "menu"

                return "menu"

        if self.game_state == "menu":

            self.stop_music()

            return "menu"

        return None

    # ------------------------------------------------------------
    # controls
    # ------------------------------------------------------------
    def _mobile_controls_enabled(self):
        try:
            settings_path = os.path.join(PROJECT_ROOT, "profile_settings.json")
            if os.path.isfile(settings_path):
                with open(settings_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                if isinstance(data, dict):
                    value = data.get("mobile_controls", data.get("mobilecontrols", True))
                    if isinstance(value, str):
                        return value.strip().lower() in ("true", "1", "yes", "on")
                    return bool(value)
        except Exception:
            pass
        return True

    def _update_mobile_rects(self):
        margin = max(18, int(self.screen_width * 0.025))
        bottom = self.screen_height - max(18, int(self.screen_height * 0.035))
        h = min(64, max(48, int(self.screen_height * 0.08)))
        w = min(104, max(80, int(self.screen_width * 0.10)))
        gap = max(12, int(w * 0.12))
        self.mobile_left_rect = pygame.Rect(margin, bottom - h, w, h)
        self.mobile_right_rect = pygame.Rect(margin + w + gap, bottom - h, w, h)
        fire_w = min(130, max(104, int(self.screen_width * 0.125)))
        self.mobile_fire_rect = pygame.Rect(self.screen_width - margin - fire_w, bottom - h, fire_w, h)

    def _control_at_pos(self, pos):
        if not self._mobile_controls_enabled():
            return None
        if self.mobile_left_rect.collidepoint(pos):
            return "left"
        if self.mobile_right_rect.collidepoint(pos):
            return "right"
        if self.mobile_fire_rect.collidepoint(pos):
            return "fire"
        return None

    def _update_direct_controls(self, events):
        left = False
        right = False
        fire = False

        keys = pygame.key.get_pressed()
        left = bool(keys[pygame.K_LEFT] or keys[pygame.K_a])
        right = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])
        fire = bool(keys[pygame.K_SPACE] or keys[pygame.K_RETURN])

        mouse = pygame.mouse.get_pressed(3)
        if mouse[0]:
            control = self._control_at_pos(pygame.mouse.get_pos())
            if control == "left":
                left = True
            elif control == "right":
                right = True
            elif control == "fire":
                fire = True

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                control = self._control_at_pos(event.pos)
                if control:
                    self.active_touch_controls["mouse"] = control
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.active_touch_controls.pop("mouse", None)
            elif event.type == pygame.FINGERDOWN:
                pos = (int(event.x * self.screen_width), int(event.y * self.screen_height))
                control = self._control_at_pos(pos)
                if control:
                    self.active_touch_controls[event.finger_id] = control
            elif event.type == pygame.FINGERMOTION:
                if event.finger_id in self.active_touch_controls:
                    pos = (int(event.x * self.screen_width), int(event.y * self.screen_height))
                    control = self._control_at_pos(pos)
                    if control:
                        self.active_touch_controls[event.finger_id] = control
                    else:
                        self.active_touch_controls.pop(event.finger_id, None)
            elif event.type == pygame.FINGERUP:
                self.active_touch_controls.pop(event.finger_id, None)

        for control in self.active_touch_controls.values():
            if control == "left":
                left = True
            elif control == "right":
                right = True
            elif control == "fire":
                fire = True

        return left, right, fire

    def handle_keyboard(self, events):

        for event in events:

            if event.type != pygame.KEYDOWN:
                continue

            if event.key in (pygame.K_ESCAPE, pygame.K_p):

                if self.game_state == "playing":

                    self.game_state = "paused"

                    self.pause_music()

                    self.play_click()

                elif self.game_state == "paused":

                    self.game_state = "playing"

                    self.resume_music()

                    self.play_click()

            elif self.game_state == "paused":

                if event.key in (pygame.K_RETURN, pygame.K_SPACE):

                    self.game_state = "playing"

                    self.resume_music()

                    self.play_click()

            elif self.game_state == "game_over":

                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):

                    return "restart"

                if event.key in (pygame.K_m, pygame.K_BACKSPACE):

                    self.game_state = "menu"

                    return "menu"

        return None

    # ------------------------------------------------------------
    # per-state updates
    # ------------------------------------------------------------
    def update_playing(self, events, dt=None):
        self.player_history.append((self.player.x, self.player.y))
        if len(self.player_history) > 45:
            self.player_history.pop(0)

        dt_value = dt if dt is not None else (1.0 / 60.0)

        left_pressed, right_pressed, fire_requested = self._update_direct_controls(events)

        try:
            self.player.stop()
        except Exception:
            pass

        if left_pressed and not right_pressed:
            try:
                self.player.move_left()
            except Exception:
                self.player.x -= max(1.0, getattr(self.player, "speed", 6) * 1.15)
        elif right_pressed and not left_pressed:
            try:
                self.player.move_right()
            except Exception:
                self.player.x += max(1.0, getattr(self.player, "speed", 6) * 1.15)
        elif left_pressed and right_pressed:
            try:
                self.player.velocity_x = 0
            except Exception:
                pass

        moved = False
        try:
            self.player.update_movement()
            moved = True
        except Exception:
            pass
        if not moved:
            try:
                self.player.update(dt_value)
                moved = True
            except Exception:
                try:
                    self.player.update()
                    moved = True
                except Exception:
                    pass

        if not moved and (left_pressed or right_pressed):
            if left_pressed and not right_pressed:
                self.player.x -= max(1.0, getattr(self.player, "speed", 6) * 1.15)
            elif right_pressed and not left_pressed:
                self.player.x += max(1.0, getattr(self.player, "speed", 6) * 1.15)

        if fire_requested and self.fire_cooldown_timer <= 0:
            bullet_x = self.player.x + getattr(self.player, "width", 80) // 2 - 16
            bullet_y = self.player.y
            self.bullets.append(Bullet(bullet_x, bullet_y))
            self.shots_fired += 1
            self.play_bullet()
            self.trigger_explosion(bullet_x + 16, bullet_y, SPARK, count=5)
            self.fire_cooldown_timer = 12

        try:
            self.player.keep_inside_screen()
        except Exception:
            self.player.x = max(0, min(self.screen_width - getattr(self.player, "width", 80), self.player.x))

        if self.fire_cooldown_timer > 0:
            self.fire_cooldown_timer -= 1

        for bullet in self.bullets[:]:
            try:
                bullet.update()
            except TypeError:
                bullet.update(dt_value)
            if not bullet.is_active:
                self.bullets.remove(bullet)

        self.timer += 1
        attack_interval = max(150, 300 - (self.wave - 1) * 15)
        if self.timer >= attack_interval:
            waiting_enemies = [enemy for enemy in self.enemies if getattr(enemy, 'state', '') == 'waiting']
            if waiting_enemies:
                chosen_enemy = random.choice(waiting_enemies)
                if self.player_history:
                    target_x, target_y = self.player_history[0]
                    if hasattr(chosen_enemy, 'start_drop'):
                        chosen_enemy.start_drop(target_x, target_y)
                    elif hasattr(chosen_enemy, 'start_dive'):
                        chosen_enemy.start_dive(target_x, target_y)
            self.timer = 0

        all_despawned = True
        for enemy in self.enemies:
            enemy.update(dt_value)
            if enemy.state not in ('offscreen', 'dead'):
                all_despawned = False

        if all_despawned:
            self.wave += 1
            self.spawn_number = min(self.spawn_number + 1, 15)
            self.spawn_enemies()

        self.check_collisions()

    def update_paused(self, events):

        for event in events:

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:

                continue

            mouse_pos = event.pos

            if self.resume_button_rect.collidepoint(mouse_pos):

                self.play_click()

                self.game_state = "playing"

                self.resume_music()

                return None

            if self.restart_button_rect.collidepoint(mouse_pos):

                return "restart"

            if self.pause_menu_button_rect.collidepoint(mouse_pos):

                return "menu"

        return None

    def update_blinking(self, dt=None):

        self.player.update_blink()

        self.state_timer += 1

        for enemy in self.enemies:

            enemy.update(dt if dt is not None else (1.0 / 60.0))

        if self.state_timer >= 150:

            self.game_state = "game_over"

            self.save_final_score()

    def update_game_over(self, events):

        for event in events:

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:

                continue

            mouse_pos = event.pos

            if self.game_over_restart_rect.collidepoint(mouse_pos):

                return "restart"

            if self.game_over_menu_rect.collidepoint(mouse_pos):

                return "menu"

        return None

    # ------------------------------------------------------------
    # saving (unchanged)
    # ------------------------------------------------------------
    def save_final_score(self):
        if self.score_saved:
            return

        owner = self.player_id or self.username
        if not owner:
            return

        current = None
        try:
            current = get_player(self.player_id) if self.player_id is not None else get_player(owner)
        except Exception:
            current = None

        data = current if isinstance(current, dict) else self.player_data
        if not isinstance(data, dict):
            data = {}

        cached = _load_profile_stats_cache(self.player_id)

        def as_int(value, default=0):
            try:
                return int(float(value))
            except Exception:
                return default

        old_score = max(
            as_int(data.get("high_score")),
            as_int(data.get("highest_score")),
            as_int(data.get("best_score")),
            as_int(data.get("score")),
            as_int(cached.get("high_score")),
            as_int(cached.get("highest_score")),
            as_int(cached.get("best_score")),
            as_int(cached.get("score")),
        )
        final_high_score = max(old_score, int(self.score))

        old_wave = max(
            as_int(data.get("best_wave")),
            as_int(data.get("highest_wave")),
            as_int(data.get("wave")),
            as_int(data.get("final_wave")),
            as_int(cached.get("best_wave")),
            as_int(cached.get("highest_wave")),
            as_int(cached.get("wave")),
            as_int(cached.get("final_wave")),
        )
        final_best_wave = max(old_wave, int(self.wave))

        previous_games = max(as_int(data.get("games_played")), as_int(data.get("games")), as_int(cached.get("games_played")), as_int(cached.get("games")))
        previous_kills = max(as_int(data.get("ships_destroyed")), as_int(data.get("kills")), as_int(cached.get("ships_destroyed")), as_int(cached.get("kills")))
        previous_shots = max(as_int(data.get("shots_fired")), as_int(cached.get("shots_fired")))
        previous_hits = max(as_int(data.get("shots_hit")), as_int(data.get("hits")), as_int(cached.get("shots_hit")), as_int(cached.get("hits")))

        total_games = previous_games + 1
        total_kills = previous_kills + int(self.kills_this_game)
        total_shots = previous_shots + int(self.shots_fired)
        total_hits = previous_hits + int(self.shots_hit)
        accuracy = (total_hits / total_shots * 100.0) if total_shots > 0 else 0.0

        stats = {
            "games_played": total_games,
            "games": total_games,
            "ships_destroyed": total_kills,
            "kills": total_kills,
            "total_kills": total_kills,
            "shots_fired": total_shots,
            "shots_hit": total_hits,
            "hits": total_hits,
            "accuracy": round(accuracy, 2),
            "hit_accuracy": round(accuracy, 2),
            "score": final_high_score,
            "high_score": final_high_score,
            "highest_score": final_high_score,
            "best_score": final_high_score,
            "total_score": final_high_score,
            "last_score": int(self.score),
            "final_score": int(self.score),
            "last_wave": int(self.wave),
            "wave": int(self.wave),
            "final_wave": int(self.wave),
            "best_wave": final_best_wave,
            "last_kills": int(self.kills_this_game),
            "last_shots": int(self.shots_fired),
            "last_hits": int(self.shots_hit),
        }

        data.update(stats)
        self.player_data.update(data)

        if isinstance(current, dict):
            self.player_data.update(current)
            self.player_data.update(stats)

        _save_profile_stats_cache(self.player_id, stats)

        success = False
        try:
            try:
                result = save_score(owner, self.score, self.wave)
            except TypeError:
                result = save_score(owner, self.score)
            success = result is not False
        except Exception:
            success = False

        # If the database module provides a stats updater, use it without
        # requiring a specific function name in older database.py versions.
        try:
            import database
            updater = getattr(database, "update_game_stats", None)
            if callable(updater):
                try:
                    updater(self.player_id, stats)
                except TypeError:
                    updater(self.player_id, **stats)
                success = True
        except Exception:
            pass

        # Also update the in-memory player dictionary used by menu/profile.
        self.player_data.update(stats)
        self.score_saved = True

    def check_collisions(self):

        player_rect = self.player.get_rect()

        for enemy in self.enemies:

            if enemy.state in ("offscreen", "dead", "dying"):

                continue

            enemy_rect = enemy.get_rect()

            if player_rect.colliderect(enemy_rect):

                self.game_state = "blinking"

                self.player.is_blinking = True

                self.state_timer = 0

                self.shake_timer = 12

                self.pause_music()

                if not self.defeated_played:

                    self.play_defeated()

                    self.defeated_played = True

                self.trigger_explosion(
                    self.player.x + self.player.width // 2,
                    self.player.y + self.player.height // 2,
                    DEATH,
                    count=30
                )

                return

            for bullet in self.bullets[:]:

                if bullet.get_rect().colliderect(enemy_rect):

                    self.play_enemy_hit()

                    destroyed = enemy.take_damage()
                    self.shots_hit += 1

                    self.trigger_explosion(
                        enemy_rect.centerx,
                        enemy_rect.centery,
                        HIT,
                        count=12
                    )

                    if destroyed:

                        self.score += 1
                        self.kills_this_game += 1

                        self.trigger_explosion(
                            enemy_rect.centerx,
                            enemy_rect.centery,
                            KILL,
                            count=22
                        )

                    if bullet in self.bullets:

                        self.bullets.remove(bullet)

                    break

    # ------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------
    def text(self, surf, font, msg, color, **anchor):
        img = font.render(msg, True, color)
        rect = img.get_rect(**anchor)
        surf.blit(img, rect)
        return rect

    def draw_enemy_overlay(self, surface, enemy, t):
        """Soft ring + HP bar. Skipped once the enemy is dying / dead / has no HP left."""
        state = getattr(enemy, "state", "")
        hp = getattr(enemy, "health", None)
        max_hp = getattr(enemy, "max_health", None)

        if state in ("dying", "dead", "offscreen"):
            return
        if hp is not None and hp <= 0:
            return

        er = enemy.get_rect()

        # faint pulsing ring
        pulse = 0.5 + 0.5 * math.sin(t * 3.0 + er.x * 0.01)
        ring = pygame.Surface((er.w + 26, er.h + 26), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*ROSE_DEEP, int(60 + pulse * 60)), ring.get_rect(), 2)
        surface.blit(ring, (er.x - 13, er.y - 13))

        if hp is not None and max_hp:
            ratio = max(0.0, min(1.0, float(hp) / float(max_hp)))
            bar = pygame.Rect(er.x + 5, max(6, er.y - 14), max(10, er.w - 10), 8)
            pygame.draw.rect(surface, CREAM, bar, border_radius=4)
            fill_w = max(3, int(bar.width * ratio)) if ratio > 0 else 0
            if fill_w:
                if ratio > 0.66:
                    hp_color = GREEN
                elif ratio > 0.33:
                    hp_color = HIT
                else:
                    hp_color = RED
                fill = pygame.Rect(bar.x, bar.y, fill_w, bar.height)
                pygame.draw.rect(surface, hp_color, fill, border_radius=4)
            pygame.draw.rect(surface, INK, bar, 2, border_radius=4)

    def draw(self):

        t = self.frame / 60.0

        render_surf = pygame.Surface(
            (self.screen_width, self.screen_height)
        )

        self._draw_game_background(render_surf)

        for item in self.decor:
            item.draw(render_surf, t)

        for p in self.particles:
            p.draw(render_surf)

        if self.game_state not in ("game_over", "menu"):

            self.player.draw(render_surf)

            for enemy in self.enemies:
                try:
                    self.draw_enemy_overlay(render_surf, enemy, t)
                except Exception:
                    pass
                enemy.draw(render_surf)

            for bullet in self.bullets:
                bullet.draw(render_surf)

        for ring in self.impact_rings:
            ring.draw(render_surf)

        if self.game_state != "menu":

            self.draw_hud(render_surf)

        if self.game_state == "paused":

            self.draw_pause_screen(render_surf, t)

        elif self.game_state == "game_over":

            self.draw_game_over_screen(render_surf, t)

        shake_x = 0
        shake_y = 0

        if self.shake_timer > 0:

            shake_x = int(
                math.sin(self.shake_timer * 1.2) * (self.shake_timer * 0.22)
            )

            shake_y = int(
                math.cos(self.shake_timer * 1.2) * (self.shake_timer * 0.22)
            )

            self.shake_timer -= 1

        self.screen.fill(PEACH)
        self.screen.blit(render_surf, (shake_x, shake_y))

        if self.game_state == "playing":
            self.draw_mobile_controls(self.screen)

        pygame.display.flip()

    def resize(self, screen, screen_width=None, screen_height=None):
        self.screen = screen

        try:
            actual_width, actual_height = screen.get_size()
        except Exception:
            actual_width = screen_width or self.screen_width
            actual_height = screen_height or self.screen_height

        if actual_width <= 0 or actual_height <= 0:
            actual_width = screen_width or self.screen_width
            actual_height = screen_height or self.screen_height

        self.screen_width = int(actual_width)
        self.screen_height = int(actual_height)

        self.background_scaled = None
        self.background_scaled_size = None
        self._hud_cache = None

        try:
            self.buttons = MobileButtons(
                self.screen_width,
                self.screen_height
            )
        except TypeError:
            try:
                self.buttons = MobileButtons()
            except Exception:
                self.buttons = None
        except Exception:
            self.buttons = None

        self._update_mobile_rects()

        try:
            self.player.screen_width = self.screen_width
            self.player.screen_height = self.screen_height
            self.player.keep_inside_screen()
        except Exception:
            pass

        for item in self.decor:
            item.w = self.screen_width
            item.h = self.screen_height

    def draw_mobile_controls(self, surface):
        if not self._mobile_controls_enabled():
            return

        controls = [
            (self.mobile_left_rect, "<", "left"),
            (self.mobile_right_rect, ">", "right"),
            (self.mobile_fire_rect, "fire", "fire"),
        ]

        active_keys = set(self.active_touch_controls.values())
        if self.mobile_left_active:
            active_keys.add("left")
        if self.mobile_right_active:
            active_keys.add("right")
        if self.mobile_fire_active:
            active_keys.add("fire")

        for rect, label, key in controls:
            active = key in active_keys
            fill = ACTIVE_PILL if active else DARK
            edge = CREAM if active else INK
            radius = max(10, rect.height // 3)

            pygame.draw.rect(surface, fill, rect, border_radius=radius)
            pygame.draw.rect(surface, edge, rect, 2, border_radius=radius)

            inner = rect.inflate(-8, -8)
            pygame.draw.rect(
                surface,
                ROSE_DEEP if active else DARK_HOVER,
                inner,
                border_radius=max(8, inner.height // 4)
            )
            pygame.draw.line(
                surface,
                CREAM,
                (inner.left + 10, inner.top + 5),
                (inner.right - 10, inner.top + 5),
                1
            )

            font = self.label_font if key != "fire" else self.button_font
            self.text(surface, font, label, CREAM, center=(rect.centerx, rect.centery - 1))

    def _build_hud_frame(self, hud):
        """Hand-inked top bar, drawn once per window size."""
        frame = pygame.Surface((hud.w + 12, hud.h + 12), pygame.SRCALPHA)
        rnd = random.Random(11)
        sketch_rect(frame, rnd, (8, 8, hud.w - 2, hud.h - 2), ROSE_DEEP, INK, 14, 2)
        sketch_rect(frame, rnd, (2, 2, hud.w - 2, hud.h - 2), ROSE, INK, 14, 3)
        return frame

    def draw_hud(self, surface):
        margin = max(16, int(self.screen_width * 0.02))
        hud = pygame.Rect(margin, 12, self.screen_width - margin * 2, 58)

        key = (hud.w, hud.h)
        if self._hud_cache is None or self._hud_cache[0] != key:
            self._hud_cache = (key, self._build_hud_frame(hud))
        surface.blit(self._hud_cache[1], (hud.x - 2, hud.y - 2))

        pill_w = min(220, max(120, (hud.w - 120) // 3))
        pill_h = 32
        pill_y = hud.centery - pill_h // 2

        left = pygame.Rect(hud.x + 20, pill_y, pill_w, pill_h)
        right = pygame.Rect(hud.right - 20 - pill_w, pill_y, pill_w, pill_h)

        for pill, label, value in (
            (left, "score", f"{self.score:05d}"),
            (right, "wave", f"{self.wave:02d}"),
        ):
            pygame.draw.rect(surface, DARK, pill, border_radius=pill_h // 2)
            self.text(surface, self.small_font, label, CREAM,
                      midleft=(pill.x + 16, pill.centery - 1))
            self.text(surface, self.small_font, value, CREAM,
                      midright=(pill.right - 16, pill.centery - 1))

        # little hearts in the middle
        bob = math.sin(self.frame * 0.05) * 2
        cx, cy = hud.centerx, hud.centery
        draw_heart(surface, cx - 18, int(cy - 2 + bob), 9)
        draw_heart(surface, cx + 18, int(cy - 2 - bob), 10)

    def draw_dialog_frame(self, surface, rect, title):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        surface.blit(overlay, (0, 0))

        rnd = random.Random(7)
        sketch_rect(surface, rnd, rect.move(10, 10), ROSE_DEEP, ROSE_DEEP, 16, 1, 0)
        sketch_rect(surface, rnd, rect, CREAM, INK, 16, 3)

        self.text(surface, self.label_font, title, DARK, center=(rect.centerx, rect.y + 40))

    def draw_pause_screen(self, surface, t):
        panel_w = min(460, self.screen_width - 40)
        panel_h = min(320, self.screen_height - 60)
        panel = pygame.Rect(
            self.screen_width // 2 - panel_w // 2,
            self.screen_height // 2 - panel_h // 2,
            panel_w,
            panel_h
        )

        self.draw_dialog_frame(surface, panel, "paused")

        bob = math.sin(t * 3.0) * 2
        draw_heart(surface, panel.x + 52, int(panel.y + 38 + bob), 9)
        draw_heart(surface, panel.right - 52, int(panel.y + 38 - bob), 9)

        gap = 12
        btn_h = 40
        btn_w = min(300, panel.w - 70)
        x = panel.centerx - btn_w // 2
        y = panel.y + 84

        self.resume_button_rect = pygame.Rect(x, y, btn_w, btn_h)
        self.restart_button_rect = pygame.Rect(x, y + btn_h + gap, btn_w, btn_h)
        self.pause_menu_button_rect = pygame.Rect(x, y + (btn_h + gap) * 2, btn_w, btn_h)

        self.draw_button(surface, self.resume_button_rect, "resume")
        self.draw_button(surface, self.restart_button_rect, "restart")
        self.draw_button(surface, self.pause_menu_button_rect, "main menu")

        self.text(surface, self.small_font, "esc / p  -  resume", INK,
                  center=(panel.centerx, panel.bottom - 22))

    def draw_game_over_screen(self, surface, t):
        panel_w = min(480, self.screen_width - 40)
        panel_h = min(390, self.screen_height - 40)
        panel = pygame.Rect(
            self.screen_width // 2 - panel_w // 2,
            self.screen_height // 2 - panel_h // 2,
            panel_w,
            panel_h
        )

        self.draw_dialog_frame(surface, panel, "game over")

        bob = math.sin(t * 3.0) * 2
        draw_heart(surface, panel.x + 52, int(panel.y + 38 + bob), 9)
        draw_heart(surface, panel.right - 52, int(panel.y + 38 - bob), 9)

        # score card
        card = pygame.Rect(panel.x + 36, panel.y + 78, panel.w - 72, 92)
        rnd = random.Random(13)
        sketch_rect(surface, rnd, card, ROSE, INK, 14, 3)
        self.text(surface, self.small_font, "final score", INK,
                  center=(card.centerx, card.y + 24))
        self.text(surface, self.big_font, f"{self.score:,}", DARK,
                  center=(card.centerx, card.y + 60))

        self.text(surface, self.small_font, f"wave reached  {self.wave:02d}", INK,
                  center=(panel.centerx, card.bottom + 24))

        btn_w = min(300, panel.w - 70)
        btn_h = 40
        btn_x = panel.centerx - btn_w // 2
        self.game_over_restart_rect = pygame.Rect(btn_x, card.bottom + 50, btn_w, btn_h)
        self.game_over_menu_rect = pygame.Rect(btn_x, card.bottom + 50 + btn_h + 12, btn_w, btn_h)

        self.draw_button(surface, self.game_over_restart_rect, "play again")
        self.draw_button(surface, self.game_over_menu_rect, "main menu")

        self.text(surface, self.small_font, "r  -  again      m  -  menu", INK,
                  center=(panel.centerx, panel.bottom - 20))

    def draw_button(self, surface, rect, text, color=None):
        hovered = rect.collidepoint(pygame.mouse.get_pos())

        pygame.draw.rect(surface, DARK_HOVER if hovered else DARK, rect,
                         border_radius=rect.height // 2)
        self.text(surface, self.button_font, text, CREAM,
                  center=(rect.centerx, rect.centery - 1))