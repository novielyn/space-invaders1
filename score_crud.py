import mysql.connector

from database import get_connection


def save_score(
    player_id,
    score,
    level
):

    connection = get_connection()

    if connection is None:
        return False

    cursor = None

    try:

        if player_id is None:
            print(
                "Save score error: player ID is missing."
            )
            return False

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO scores
            (
                player_id,
                score,
                level
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                int(player_id),
                int(score),
                int(level)
            )
        )

        connection.commit()

        print(
            "Score saved:",
            score,
            "| Player:",
            player_id,
            "| Level:",
            level
        )

        return True

    except mysql.connector.Error as e:

        connection.rollback()

        print(
            "Save score error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def get_leaderboard(limit=10):

    connection = get_connection()

    if connection is None:
        return []

    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )

        limit = int(limit)

        if limit < 1:
            limit = 10

        if limit > 100:
            limit = 100

        query = f"""
            SELECT
                p.player_id,
                p.username,
                MAX(s.score) AS score,
                MAX(s.level) AS level

            FROM scores s

            INNER JOIN players p
                ON s.player_id = p.player_id

            GROUP BY
                p.player_id,
                p.username

            ORDER BY
                score DESC,
                level DESC,
                p.username ASC

            LIMIT {limit}
        """

        cursor.execute(query)

        return cursor.fetchall()

    except mysql.connector.Error as e:

        print(
            "Leaderboard error:",
            e
        )

        return []

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def get_player_scores(player_id):

    connection = get_connection()

    if connection is None:
        return []

    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                score_id,
                score,
                level,
                played_at

            FROM scores

            WHERE player_id = %s

            ORDER BY
                score DESC,
                played_at DESC
            """,
            (player_id,)
        )

        return cursor.fetchall()

    except mysql.connector.Error as e:

        print(
            "Player scores error:",
            e
        )

        return []

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def get_highest_score(player_id):

    connection = get_connection()

    if connection is None:
        return 0

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(
                    MAX(score),
                    0
                )

            FROM scores

            WHERE player_id = %s
            """,
            (player_id,)
        )

        result = cursor.fetchone()

        if result:

            return int(
                result[0] or 0
            )

        return 0

    except mysql.connector.Error as e:

        print(
            "Highest score error:",
            e
        )

        return 0

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()


def delete_score(score_id):

    connection = get_connection()

    if connection is None:
        return False

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM scores

            WHERE score_id = %s
            """,
            (score_id,)
        )

        deleted = (
            cursor.rowcount > 0
        )

        connection.commit()

        return deleted

    except mysql.connector.Error as e:

        connection.rollback()

        print(
            "Delete score error:",
            e
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if connection.is_connected():
            connection.close()