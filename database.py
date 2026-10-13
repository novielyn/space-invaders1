import mysql.connector
from mysql.connector import Error


MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": ""
}


DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "space_invaders_pohanes_db"
}


DATABASE_NAME = "space_invaders_pohanes_db"


def create_database():

    connection = None
    cursor = None

    try:

        connection = mysql.connector.connect(
            **MYSQL_CONFIG
        )

        cursor = connection.cursor()

        cursor.execute(
            f"""
            CREATE DATABASE IF NOT EXISTS
            {DATABASE_NAME}
            """
        )

        return True

    except Error as e:

        print(
            "Database creation error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_connection():

    try:

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        if connection.is_connected():
            return connection

    except Error as e:

        print(
            "MySQL connection error:",
            e
        )

    return None


def create_tables():

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return False

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS players (

                player_id INT AUTO_INCREMENT PRIMARY KEY,

                username VARCHAR(50)
                NOT NULL UNIQUE,

                email VARCHAR(100)
                UNIQUE,

                password VARCHAR(255)
                NOT NULL,

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (

                score_id INT AUTO_INCREMENT PRIMARY KEY,

                player_id INT NOT NULL,

                score INT NOT NULL
                DEFAULT 0,

                level INT NOT NULL
                DEFAULT 1,

                played_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
            """
        )

        connection.commit()

        return True

    except Error as e:

        print(
            "Table creation error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def initialize_database():

    if not create_database():
        return False

    if not create_tables():
        return False

    return True


def get_player(player_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return None

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                password,
                created_at
            FROM players
            WHERE player_id = %s
            """,
            (player_id,)
        )

        player = cursor.fetchone()

        return player

    except Error as e:

        print(
            "Get player error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_player_by_username(username):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return None

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                player_id,
                username,
                email,
                password,
                created_at
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        player = cursor.fetchone()

        return player

    except Error as e:

        print(
            "Get player by username error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def save_score(player_id, score, level=1):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return False

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO scores (
                player_id,
                score,
                level
            )
            VALUES (
                %s,
                %s,
                %s
            )
            """,
            (
                player_id,
                int(score),
                int(level)
            )
        )

        connection.commit()

        return True

    except Error as e:

        print(
            "Save score error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_player_scores(player_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return []

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                score_id,
                player_id,
                score,
                level,
                played_at
            FROM scores
            WHERE player_id = %s
            ORDER BY score DESC, played_at DESC
            """,
            (player_id,)
        )

        scores = cursor.fetchall()

        return scores

    except Error as e:

        print(
            "Get player scores error:",
            e
        )

        return []

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_high_score(player_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return 0

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(MAX(score), 0)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result:
            return int(result[0] or 0)

        return 0

    except Error as e:

        print(
            "Get high score error:",
            e
        )

        return 0

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_latest_score(player_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return None

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                score_id,
                player_id,
                score,
                level,
                played_at
            FROM scores
            WHERE player_id = %s
            ORDER BY played_at DESC, score_id DESC
            LIMIT 1
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        return result

    except Error as e:

        print(
            "Get latest score error:",
            e
        )

        return None

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def get_leaderboard(limit=100):

    connection = None
    cursor = None

    try:

        connection = get_connection()

        if connection is None:
            return []

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                p.player_id,
                p.username,
                MAX(s.score) AS score,
                MAX(s.level) AS level
            FROM players p
            INNER JOIN scores s
                ON p.player_id = s.player_id
            GROUP BY
                p.player_id,
                p.username
            ORDER BY
                score DESC
            LIMIT %s
            """,
            (int(limit),)
        )

        leaderboard = cursor.fetchall()

        return leaderboard

    except Error as e:

        print(
            "Leaderboard error:",
            e
        )

        return []

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def test_connection():

    connection = get_connection()

    if connection:

        connection.close()

        return True

    return False


if __name__ == "__main__":

    if initialize_database():

        print(
            "Database initialized successfully."
        )

        if test_connection():

            print(
                "Database connection successful."
            )

        else:

            print(
                "Database connection failed."
            )

    else:

        print(
            "Database initialization failed."
        )