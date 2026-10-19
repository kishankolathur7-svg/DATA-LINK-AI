from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename

import os
import uuid
import math
import json
import pandas as pd

from database import get_db_connection

from services.data_quality import (
    analyze_data_quality
)

from services.data_cleaning import (
    clean_missing_values,
    clean_duplicate_rows,
    find_empty_columns,
    clean_empty_columns,
    save_cleaned_dataset
)


# ============================================================
# BLUEPRINT
# ============================================================

files_bp = Blueprint(
    "files",
    __name__,
    url_prefix="/api/files"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        BASE_DIR,
        ".."
    )
)

STORAGE_ROOT = os.environ.get("DATA_STORAGE_DIR", PROJECT_ROOT)
UPLOAD_FOLDER = os.path.join(STORAGE_ROOT, "uploads")
CLEANED_FOLDER = os.path.join(STORAGE_ROOT, "cleaned")

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    CLEANED_FOLDER,
    exist_ok=True
)


# ============================================================
# FILE SETTINGS
# ============================================================

ALLOWED_EXTENSIONS = {
    "csv",
    "xlsx",
    "xls"
}

MAX_FILE_SIZE = 50 * 1024 * 1024


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def make_json_safe(value):
    """
    Convert Pandas/NumPy values into standard
    JSON-safe values.

    NaN and Infinity become None.
    """

    if value is None:
        return None

    if isinstance(value, dict):

        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set)
    ):

        return [
            make_json_safe(item)
            for item in value
        ]

    if hasattr(
        value,
        "item"
    ):

        try:
            value = value.item()

        except Exception:
            pass

    if isinstance(
        value,
        float
    ):

        if not math.isfinite(value):
            return None

        return value

    if isinstance(
        value,
        pd.Timestamp
    ):

        if pd.isna(value):
            return None

        return value.isoformat()

    try:

        missing = pd.isna(
            value
        )

        if isinstance(
            missing,
            bool
        ):

            if missing:
                return None

    except Exception:
        pass

    return value


# ============================================================
# FILE HELPERS
# ============================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def get_file_path(
    file_id,
    user_id
):

    connection = get_db_connection()

    try:

        file = connection.execute(
            """
            SELECT
                id,
                original_name,
                stored_name,
                file_type,
                file_size
            FROM uploaded_files
            WHERE id = ?
            AND user_id = ?
            """,
            (
                file_id,
                user_id
            )
        ).fetchone()

    finally:

        connection.close()

    if file is None:

        return None, None

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file["stored_name"]
    )

    return file, file_path


def read_dataset(
    file_path,
    file_type
):

    file_type = str(
        file_type
    ).lower()

    if file_type == "csv":

        return pd.read_csv(
            file_path
        )

    if file_type in {
        "xlsx",
        "xls"
    }:

        return pd.read_excel(
            file_path
        )

    raise ValueError(
        "Unsupported file type"
    )


def get_user_id():
    """Return the authenticated user ID from the signed session only."""
    user_id = session.get("user_id")
    try:
        return int(user_id) if user_id is not None else None
    except (TypeError, ValueError):
        return None


# ============================================================
# UPLOAD
# ============================================================

@files_bp.route(
    "/upload",
    methods=["POST"]
)
def upload_file():

    try:

        user_id = get_user_id()
        if user_id is None:
            return jsonify({"success": False, "message": "Authentication required"}), 401

        if "file" not in request.files:

            return jsonify({
                "success": False,
                "message": "No file was uploaded"
            }), 400

        uploaded_file = request.files[
            "file"
        ]

        if not uploaded_file.filename:

            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400

        if not allowed_file(
            uploaded_file.filename
        ):

            return jsonify({
                "success": False,
                "message": (
                    "Unsupported file type. "
                    "Only CSV, XLSX and XLS files are allowed."
                )
            }), 400

        if request.content_length:

            if (
                request.content_length
                > MAX_FILE_SIZE
            ):

                return jsonify({
                    "success": False,
                    "message": "File size exceeds 50 MB limit"
                }), 400

        original_name = secure_filename(
            uploaded_file.filename
        )

        extension = original_name.rsplit(
            ".",
            1
        )[1].lower()

        stored_name = (
            f"{uuid.uuid4().hex}."
            f"{extension}"
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            stored_name
        )

        uploaded_file.save(
            file_path
        )

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Failed to save uploaded file"
            }), 500

        file_size = os.path.getsize(
            file_path
        )

        connection = get_db_connection()

        try:

            cursor = connection.execute(
                """
                INSERT INTO uploaded_files
                (
                    user_id,
                    original_name,
                    stored_name,
                    file_type,
                    file_size
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    original_name,
                    stored_name,
                    extension,
                    file_size
                )
            )

            connection.commit()

            file_id = cursor.lastrowid

        finally:

            connection.close()

        return jsonify(
            make_json_safe({
                "success": True,
                "message": "File uploaded successfully",
                "file": {
                    "id": file_id,
                    "name": original_name,
                    "type": extension,
                    "size": file_size
                }
            })
        ), 201

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not upload file",
            "error": str(error)
        }), 500


# ============================================================
# LIST FILES
# ============================================================

@files_bp.route(
    "/list",
    methods=["GET"]
)
def list_files():

    user_id = get_user_id()

    if user_id is None:

        return jsonify({
            "success": False,
            "message": "Valid user ID is required"
        }), 400

    try:

        connection = get_db_connection()

        try:

            rows = connection.execute(
                """
                SELECT
                    id,
                    original_name,
                    file_type,
                    file_size,
                    uploaded_at
                FROM uploaded_files
                WHERE user_id = ?
                ORDER BY uploaded_at DESC
                """,
                (
                    user_id,
                )
            ).fetchall()

        finally:

            connection.close()

        files = []

        for row in rows:

            files.append({
                "id": row["id"],
                "name": row["original_name"],
                "type": row["file_type"],
                "size": row["file_size"],
                "uploaded_at": row["uploaded_at"]
            })

        return jsonify(
            make_json_safe({
                "success": True,
                "files": files
            })
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load files",
            "error": str(error)
        }), 500


# ============================================================
# ANALYZE DATASET
# ============================================================

@files_bp.route(
    "/<int:file_id>/analyze",
    methods=["GET"]
)
def analyze_file(
    file_id
):

    user_id = get_user_id()

    if user_id is None:

        return jsonify({
            "success": False,
            "message": "Valid user ID is required"
        }), 400

    try:

        file, file_path = get_file_path(
            file_id,
            user_id
        )

        if file is None:

            return jsonify({
                "success": False,
                "message": "File not found"
            }), 404

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Uploaded file no longer exists"
            }), 404

        dataframe = read_dataset(
            file_path,
            file["file_type"]
        )

        row_count = len(
            dataframe
        )

        column_count = len(
            dataframe.columns
        )

        missing_values = {}

        total_missing = 0

        for column in dataframe.columns:

            missing_count = int(
                dataframe[column]
                .isna()
                .sum()
            )

            missing_values[
                str(column)
            ] = missing_count

            total_missing += missing_count

        duplicate_rows = int(
            dataframe
            .duplicated()
            .sum()
        )

        numeric_columns = []
        text_columns = []
        date_columns = []
        other_columns = []

        for column in dataframe.columns:

            dtype = dataframe[
                column
            ].dtype

            column_name = str(
                column
            )

            if pd.api.types.is_numeric_dtype(
                dtype
            ):

                numeric_columns.append(
                    column_name
                )

            elif pd.api.types.is_datetime64_any_dtype(
                dtype
            ):

                date_columns.append(
                    column_name
                )

            elif (
                pd.api.types.is_object_dtype(
                    dtype
                )
                or
                pd.api.types.is_string_dtype(
                    dtype
                )
            ):

                text_columns.append(
                    column_name
                )

            else:

                other_columns.append(
                    column_name
                )

        preview_json = (
            dataframe
            .head(10)
            .to_json(
                orient="records",
                date_format="iso"
            )
        )

        preview = json.loads(
            preview_json
        )

        columns = []

        for column in dataframe.columns:

            columns.append({
                "name": str(column),
                "type": str(
                    dataframe[column].dtype
                ),
                "missing": int(
                    dataframe[column]
                    .isna()
                    .sum()
                ),
                "unique": int(
                    dataframe[column]
                    .nunique(
                        dropna=True
                    )
                )
            })

        response = {
            "success": True,

            "file": {
                "id": file["id"],
                "name": file["original_name"],
                "type": file["file_type"]
            },

            "summary": {
                "rows": row_count,
                "columns": column_count,
                "missing_values": total_missing,
                "duplicate_rows": duplicate_rows,
                "numeric_columns": len(
                    numeric_columns
                ),
                "text_columns": len(
                    text_columns
                ),
                "date_columns": len(
                    date_columns
                ),
                "other_columns": len(
                    other_columns
                )
            },

            "missing_values": missing_values,

            "column_types": {
                "numeric": numeric_columns,
                "text": text_columns,
                "date": date_columns,
                "other": other_columns
            },

            "columns": columns,

            "preview": preview
        }

        return jsonify(
            make_json_safe(
                response
            )
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not analyze dataset",
            "error": str(error)
        }), 500


# ============================================================
# DATA QUALITY
# ============================================================

@files_bp.route(
    "/<int:file_id>/quality",
    methods=["GET"]
)
def quality_report(
    file_id
):

    user_id = get_user_id()

    if user_id is None:

        return jsonify({
            "success": False,
            "message": "Valid user ID is required"
        }), 400

    try:

        file, file_path = get_file_path(
            file_id,
            user_id
        )

        if file is None:

            return jsonify({
                "success": False,
                "message": "File not found"
            }), 404

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Uploaded file no longer exists"
            }), 404

        dataframe = read_dataset(
            file_path,
            file["file_type"]
        )

        quality = analyze_data_quality(
            dataframe
        )

        response = {
            "success": True,

            "file": {
                "id": file["id"],
                "name": file["original_name"]
            },

            "quality": quality
        }

        return jsonify(
            make_json_safe(
                response
            )
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not analyze data quality",
            "error": str(error)
        }), 500


# ============================================================
# FIND EMPTY COLUMNS
# ============================================================

@files_bp.route(
    "/<int:file_id>/empty-columns",
    methods=["GET"]
)
def empty_columns(
    file_id
):

    user_id = get_user_id()

    if user_id is None:

        return jsonify({
            "success": False,
            "message": "Valid user ID is required"
        }), 400

    try:

        file, file_path = get_file_path(
            file_id,
            user_id
        )

        if file is None:

            return jsonify({
                "success": False,
                "message": "File not found"
            }), 404

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Uploaded file no longer exists"
            }), 404

        dataframe = read_dataset(
            file_path,
            file["file_type"]
        )

        empty_columns_found = (
            find_empty_columns(
                dataframe
            )
        )

        return jsonify(
            make_json_safe({
                "success": True,

                "file": {
                    "id": file["id"],
                    "name": file["original_name"]
                },

                "total_columns": len(
                    dataframe.columns
                ),

                "empty_columns_count": len(
                    empty_columns_found
                ),

                "empty_columns": (
                    empty_columns_found
                )
            })
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not find empty columns",
            "error": str(error)
        }), 500


# ============================================================
# CLEAN MISSING VALUES
# ============================================================

@files_bp.route(
    "/<int:file_id>/clean-missing",
    methods=["POST"]
)
def clean_missing(
    file_id
):

    user_id = get_user_id()
    if user_id is None:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json(
        silent=True
    ) or {}

    strategy = data.get(
        "strategy"
    )

    custom_value = data.get(
        "custom_value"
    )

    if not strategy:

        return jsonify({
            "success": False,
            "message": "Cleaning strategy is required"
        }), 400

    try:

        file, file_path = get_file_path(
            file_id,
            user_id
        )

        if file is None:

            return jsonify({
                "success": False,
                "message": "File not found"
            }), 404

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Uploaded file no longer exists"
            }), 404

        dataframe = read_dataset(
            file_path,
            file["file_type"]
        )

        result = clean_missing_values(
            dataframe,
            strategy,
            custom_value
        )

        saved_file = save_cleaned_dataset(
            result["dataframe"],
            file["original_name"],
            CLEANED_FOLDER,
            suffix="missing_cleaned"
        )

        return jsonify(
            make_json_safe({
                "success": True,
                "message": (
                    "Missing values cleaned successfully"
                ),
                "file": {
                    "id": file["id"],
                    "original_name": file[
                        "original_name"
                    ]
                },
                "cleaned_file": {
                    "filename": saved_file[
                        "filename"
                    ]
                },
                "summary": result[
                    "summary"
                ]
            })
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not clean missing values",
            "error": str(error)
        }), 500


# ============================================================
# CLEAN DUPLICATE ROWS
# ============================================================

@files_bp.route(
    "/<int:file_id>/clean-duplicates",
    methods=["POST"]
)
def clean_duplicates(
    file_id
):

    user_id = get_user_id()
    if user_id is None:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    try:

        file, file_path = get_file_path(
            file_id,
            user_id
        )

        if file is None:

            return jsonify({
                "success": False,
                "message": "File not found"
            }), 404

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Uploaded file no longer exists"
            }), 404

        dataframe = read_dataset(
            file_path,
            file["file_type"]
        )

        result = clean_duplicate_rows(
            dataframe
        )

        saved_file = save_cleaned_dataset(
            result["dataframe"],
            file["original_name"],
            CLEANED_FOLDER,
            suffix="duplicates_cleaned"
        )

        return jsonify(
            make_json_safe({
                "success": True,
                "message": (
                    "Duplicate rows removed successfully"
                ),
                "file": {
                    "id": file["id"],
                    "original_name": file[
                        "original_name"
                    ]
                },
                "cleaned_file": {
                    "filename": saved_file[
                        "filename"
                    ]
                },
                "summary": result[
                    "summary"
                ]
            })
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not remove duplicate rows",
            "error": str(error)
        }), 500


# ============================================================
# CLEAN EMPTY COLUMNS
# ============================================================

@files_bp.route(
    "/<int:file_id>/clean-empty-columns",
    methods=["POST"]
)
def clean_empty_columns_route(
    file_id
):

    user_id = get_user_id()
    if user_id is None:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    try:

        file, file_path = get_file_path(
            file_id,
            user_id
        )

        if file is None:

            return jsonify({
                "success": False,
                "message": "File not found"
            }), 404

        if not os.path.exists(
            file_path
        ):

            return jsonify({
                "success": False,
                "message": "Uploaded file no longer exists"
            }), 404

        dataframe = read_dataset(
            file_path,
            file["file_type"]
        )

        result = clean_empty_columns(
            dataframe
        )

        saved_file = save_cleaned_dataset(
            result["dataframe"],
            file["original_name"],
            CLEANED_FOLDER,
            suffix="empty_columns_cleaned"
        )

        return jsonify(
            make_json_safe({
                "success": True,
                "message": (
                    "Empty columns cleaned successfully"
                ),
                "file": {
                    "id": file["id"],
                    "original_name": file[
                        "original_name"
                    ]
                },
                "cleaned_file": {
                    "filename": saved_file[
                        "filename"
                    ]
                },
                "summary": result[
                    "summary"
                ]
            })
        )

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not clean empty columns",
            "error": str(error)
        }), 500