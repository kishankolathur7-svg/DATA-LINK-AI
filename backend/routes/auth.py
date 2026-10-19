from flask import Blueprint, request, jsonify, session
import sqlite3

from werkzeug.security import check_password_hash

from models.user import create_user


# --------------------------------------------------
# Blueprint
# --------------------------------------------------

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# ==================================================
# REGISTER
# ==================================================

@auth_bp.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400


    name = data.get(
        "name",
        ""
    ).strip()


    email = data.get(
        "email",
        ""
    ).strip().lower()


    password = data.get(
        "password",
        ""
    )


    # Validation
    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters"
        }), 400


    try:

        user_id = create_user(
            name,
            email,
            password
        )

        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id
        }), 201


    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409


    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Registration failed",
            "error": str(error)
        }), 500


# ==================================================
# LOGIN
# ==================================================

@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400


    email = data.get(
        "email",
        ""
    ).strip().lower()


    password = data.get(
        "password",
        ""
    )


    # Validation
    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400


    from database import get_db_connection


    connection = get_db_connection()


    user = connection.execute(
        """
        SELECT
            id,
            name,
            email,
            password_hash
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()


    connection.close()


    # User not found
    if user is None:

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401


    # Password verification
    if not check_password_hash(
        user["password_hash"],
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401


    # Establish a signed server-side session. Never trust a user ID supplied by the browser.
    session.clear()
    session["user_id"] = int(user["id"])
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    # Successful login
    return jsonify({

        "success": True,

        "message": "Login successful",

        "user": {

            "id": user["id"],

            "name": user["name"],

            "email": user["email"]
        }

    }), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    response = jsonify({"success": True, "message": "Logged out successfully"})
    response.delete_cookie("session")
    return response, 200


@auth_bp.route("/me", methods=["GET"])
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required"}), 401
    return jsonify({"success": True, "user": {
        "id": user_id,
        "name": session.get("user_name", ""),
        "email": session.get("user_email", "")
    }}), 200
