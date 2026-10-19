from werkzeug.security import generate_password_hash


def create_user(name, email, password):

    from database import get_db_connection

    password_hash = generate_password_hash(
        password
    )

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO users
        (
            name,
            email,
            password_hash
        )
        VALUES (?, ?, ?)
        """,
        (
            name,
            email,
            password_hash
        )
    )

    connection.commit()

    user_id = cursor.lastrowid

    connection.close()

    return user_id