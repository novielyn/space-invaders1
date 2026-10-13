import os
import pygame

from database import initialize_database

from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.menu_screen import MenuScreen
from screens.leaderboard_screen import LeaderboardScreen
from screens.profile_screen import ProfileScreen
from screens.settings_screen import SettingsScreen

try:
    from screens.tutorial import TutorialScreen
except ImportError:
    TutorialScreen = None
    print("tutorial_screen.py not found in screens/ - tutorial disabled")

from managers.game_manager import GameManager


initialize_database()

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    pass


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption(
    "Space Invaders by Pohanes Novielyn S."
)

clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MUSIC_FILE = os.path.join(
    BASE_DIR,
    "assets",
    "sounds",
    "background.mp3"
)

music_enabled = False

try:
    if os.path.exists(MUSIC_FILE):
        pygame.mixer.music.load(MUSIC_FILE)
        pygame.mixer.music.set_volume(0.45)
        pygame.mixer.music.play(-1)
        music_enabled = True
except pygame.error:
    music_enabled = False


# menu results that should open the tutorial
TUTORIAL_RESULTS = ("tutorial", "how_to_play", "howtoplay", "help")

current_screen = "login"

player = None

login_screen = None
register_screen = None
menu_screen = None
leaderboard_screen = None
profile_screen = None
settings_screen = None
tutorial_screen = None
game = None


def create_login():
    global login_screen

    login_screen = LoginScreen(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    )


def create_register():
    global register_screen

    register_screen = RegisterScreen(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    )


def create_menu():
    global menu_screen

    if not isinstance(player, dict):
        return

    menu_screen = MenuScreen(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        player
    )


def create_leaderboard():
    global leaderboard_screen

    leaderboard_screen = LeaderboardScreen(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    )


def create_profile():
    global profile_screen

    if not isinstance(player, dict):
        return

    profile_screen = ProfileScreen(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        player
    )


def create_settings():
    global settings_screen

    settings_screen = SettingsScreen(
        screen,
        clock
    )


def create_tutorial():
    global tutorial_screen

    if TutorialScreen is None:
        tutorial_screen = None
        return

    tutorial_screen = TutorialScreen(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    )


def create_game():
    global game

    if not isinstance(player, dict):
        return

    game = GameManager(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        username=player.get("username"),
        player_id=player.get(
            "player_id",
            player.get("id")
        ),
        player_data=player,
    )


def clear_screens():
    global login_screen
    global register_screen
    global menu_screen
    global leaderboard_screen
    global profile_screen
    global settings_screen
    global tutorial_screen
    global game

    login_screen = None
    register_screen = None
    menu_screen = None
    leaderboard_screen = None
    profile_screen = None
    settings_screen = None
    tutorial_screen = None
    game = None


def go_to_login():
    global current_screen
    global player

    player = None

    clear_screens()
    create_login()

    current_screen = "login"


def go_to_menu():
    global current_screen
    global menu_screen

    if not isinstance(player, dict):
        go_to_login()
        return

    menu_screen = None
    create_menu()

    current_screen = "menu"


def go_to_leaderboard():
    global current_screen
    global leaderboard_screen

    leaderboard_screen = None
    create_leaderboard()

    current_screen = "leaderboard"


def go_to_profile():
    global current_screen
    global profile_screen

    if not isinstance(player, dict):
        go_to_login()
        return

    profile_screen = None
    create_profile()

    current_screen = "profile"


def go_to_settings():
    global current_screen
    global settings_screen

    settings_screen = None
    create_settings()

    current_screen = "settings"


def go_to_tutorial():
    global current_screen
    global tutorial_screen

    if TutorialScreen is None:
        # no tutorial file available: stay on the menu instead of crashing
        return

    tutorial_screen = None
    create_tutorial()

    current_screen = "tutorial"


def go_to_game():
    global current_screen
    global game

    if not isinstance(player, dict):
        go_to_login()
        return

    game = None
    create_game()

    current_screen = "game"


create_login()

running = True

while running:

    dt = clock.tick(60) / 1000.0
    dt = min(dt, 0.05)

    events = pygame.event.get()

    for event in events:

        if event.type == pygame.QUIT:

            running = False

        elif event.type == pygame.VIDEORESIZE:

            SCREEN_WIDTH = max(
                800,
                event.w
            )

            SCREEN_HEIGHT = max(
                600,
                event.h
            )

            screen = pygame.display.set_mode(
                (
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT
                ),
                pygame.RESIZABLE
            )

            if current_screen == "login":

                create_login()

            elif current_screen == "register":

                create_register()

            elif current_screen == "menu":

                create_menu()

            elif current_screen == "leaderboard":

                create_leaderboard()

            elif current_screen == "profile":

                create_profile()

            elif current_screen == "settings":

                create_settings()

            elif current_screen == "tutorial":

                create_tutorial()

            elif current_screen == "game":

                if game is not None:
                    game.resize(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

    if not running:
        break


    if current_screen == "login":

        if login_screen is None:
            create_login()

        result = login_screen.update(
            events
        )

        login_screen.draw()

        if isinstance(result, dict):

            player = result
            go_to_menu()

        elif result == "register":

            register_screen = None
            create_register()

            current_screen = "register"

        elif result == "quit":

            running = False


    elif current_screen == "register":

        if register_screen is None:
            create_register()

        result = register_screen.update(
            events
        )

        register_screen.draw()

        if result == "login":

            login_screen = None
            create_login()

            current_screen = "login"

        elif result == "quit":

            running = False


    elif current_screen == "menu":

        if not isinstance(player, dict):

            go_to_login()
            continue

        if menu_screen is None:
            create_menu()

        result = menu_screen.update(
            events,
            dt
        )

        menu_screen.draw()

        if result == "play":

            go_to_game()

        elif result == "leaderboard":

            go_to_leaderboard()

        elif result == "profile":

            go_to_profile()

        elif result == "settings":

            go_to_settings()

        elif result in TUTORIAL_RESULTS:

            go_to_tutorial()

        elif result == "logout":

            go_to_login()

        elif result == "quit":

            running = False


    elif current_screen == "leaderboard":

        if leaderboard_screen is None:
            create_leaderboard()

        result = leaderboard_screen.update(
            events,
            dt
        )

        leaderboard_screen.draw()

        if result in (
            "menu",
            "back"
        ):

            go_to_menu()

        elif result == "quit":

            running = False


    elif current_screen == "profile":

        if not isinstance(player, dict):

            go_to_login()
            continue

        if profile_screen is None:
            create_profile()

        result = profile_screen.update(
            events,
            dt
        )

        profile_screen.draw()

        if result in (
            "menu",
            "back"
        ):

            go_to_menu()

        elif result == "delete_account":

            player = None
            go_to_login()

        elif result == "quit":

            running = False


    elif current_screen == "settings":

        if settings_screen is None:
            create_settings()

        result = settings_screen.update(
            events,
            dt
        )

        current_display = pygame.display.get_surface()

        if current_display is not None:

            screen = current_display

            SCREEN_WIDTH = screen.get_width()
            SCREEN_HEIGHT = screen.get_height()

        settings_screen.screen = screen
        settings_screen.width = SCREEN_WIDTH
        settings_screen.height = SCREEN_HEIGHT

        settings_screen.draw()

        if result in (
            "back",
            "menu"
        ):

            go_to_menu()

        elif result == "quit":

            running = False


    elif current_screen == "tutorial":

        if tutorial_screen is None:
            create_tutorial()

        if tutorial_screen is None:
            # tutorial screen unavailable: return to the menu
            go_to_menu()
            continue

        result = tutorial_screen.update(
            events,
            dt
        )

        tutorial_screen.draw()

        if result in (
            "back",
            "menu"
        ):

            go_to_menu()

        elif result == "quit":

            running = False


    elif current_screen == "game":

        if game is None:
            create_game()

        game.update(
            events,
            dt
        )

        game.draw()

        game_state = getattr(
            game,
            "game_state",
            None
        )

        if game_state == "menu":

            game = None
            go_to_menu()


    pygame.display.flip()


if music_enabled:

    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass


pygame.quit()