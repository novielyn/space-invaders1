import hashlib
import mysql.connector

from database import get_connection


def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def register_player(
    username,
    email,
    password
):

    connection = get_connection()

    if connection is None:
        return False

    cursor = None

    try:

        username = username.strip()
        email = email.strip().lower()

        if not username:
            print("Username is empty.")
            return False

        if not email:
            print("Email is empty.")
            return False

        if not password:
            print("Password is empty.")
            return False

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT player_id
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        if cursor.fetchone():

            print(
                "Username already exists."
            )

            return False

        cursor.execute(
            """
            SELECT player_id
            FROM players
            WHERE email = %s
            """,
            (email,)
        )

        if cursor.fetchone():

            print(
                "Email already exists."
            )

            return False

        hashed_password = hash_password(
            password
        )

        cursor.execute(
            """
            INSERT INTO players
            (
                username,
                email,
                password
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                username,
                email,
                hashed_password
            )
        )

        connection.commit()

        print(
            "Player registered:",
            username
        )

        return True

    except mysql.connector.Error as e:

        connection.rollback()

        print(
            "Register error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def login_player(
    username,
    password
):

    connection = get_connection()

    if connection is None:
        return None

    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )

        username = username.strip()

        hashed_password = hash_password(
            password
        )

        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                created_at

            FROM players

            WHERE username = %s
            AND password = %s
            """,
            (
                username,
                hashed_password
            )
        )

        player = cursor.fetchone()

        if player:

            print(
                "Login successful:",
                player["username"]
            )

        else:

            print(
                "Invalid username or password."
            )

        return player

    except mysql.connector.Error as e:

        print(
            "Login error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def get_player_by_id(player_id):

    connection = get_connection()

    if connection is None:
        return None

    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                created_at

            FROM players

            WHERE player_id = %s
            """,
            (player_id,)
        )

        return cursor.fetchone()

    except mysql.connector.Error as e:

        print(
            "Get player error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def get_player_by_username(username):

    connection = get_connection()

    if connection is None:
        return None

    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                created_at

            FROM players

            WHERE username = %s
            """,
            (username.strip(),)
        )

        return cursor.fetchone()

    except mysql.connector.Error as e:

        print(
            "Get player error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def get_player_by_email(email):

    connection = get_connection()

    if connection is None:
        return None

    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                created_at

            FROM players

            WHERE email = %s
            """,
            (email.strip().lower(),)
        )

        return cursor.fetchone()

    except mysql.connector.Error as e:

        print(
            "Get player by email error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def update_player_profile(
    player_id,
    username
):

    connection = get_connection()

    if connection is None:
        return False

    cursor = None

    try:

        username = username.strip()

        if not username:
            return False

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT player_id

            FROM players

            WHERE username = %s

            AND player_id != %s
            """,
            (
                username,
                player_id
            )
        )

        if cursor.fetchone():

            print(
                "Username already exists."
            )

            return False

        cursor.execute(
            """
            UPDATE players

            SET username = %s

            WHERE player_id = %s
            """,
            (
                username,
                player_id
            )
        )

        if cursor.rowcount == 0:

            connection.rollback()

            return False

        connection.commit()

        return True

    except mysql.connector.Error as e:

        connection.rollback()

        print(
            "Update profile error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def delete_player(player_id):

    connection = get_connection()

    if connection is None:
        return False

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM scores

            WHERE player_id = %s
            """,
            (player_id,)
        )

        cursor.execute(
            """
            DELETE FROM players

            WHERE player_id = %s
            """,
            (player_id,)
        )

        deleted = (
            cursor.rowcount > 0
        )

        connection.commit()

        if deleted:

            print(
                "Player account deleted:",
                player_id
            )

        return deleted

    except mysql.connector.Error as e:

        connection.rollback()

        print(
            "Delete player error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()