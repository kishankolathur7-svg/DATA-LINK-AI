from flask import Flask, jsonify, send_from_directory
import os

from database import initialize_database, get_db_connection
from routes.auth import auth_bp
from routes.files import files_bp
from routes.ai import ai_bp


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "development-only-change-this-key"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
)

FRONTEND_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)
initialize_database()


app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)
app.register_blueprint(ai_bp)


@app.route("/")
def home():
    return send_from_directory(
        FRONTEND_FOLDER,
        "index.html"
    )


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


@app.route("/api/health")
def health():

    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "Data Link AI"
    })


@app.route("/api/db-test")
def database_test():

    try:

        connection = get_db_connection()

        connection.execute("SELECT 1")

        connection.close()

        return jsonify({
            "success": True,
            "database": "connected"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "database": "connection failed",
            "error": str(error)
        }), 500



if __name__ == "__main__":
    # Local development only. Production should use Gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)