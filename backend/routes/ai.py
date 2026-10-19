"""Add-on AI analysis and dataset assistant endpoints for Data Link AI.

The feature works without an AI API key using deterministic data-quality insights.
If OPENAI_API_KEY is configured, OpenAI is used to turn dataset summaries into
natural-language insights. Raw dataset rows are never sent to the AI provider.
"""
from __future__ import annotations

import os
from flask import Blueprint, jsonify, request, session
import pandas as pd

from database import get_db_connection
from routes.files import get_file_path, read_dataset

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


def _authenticated_user_id():
    value = session.get("user_id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _dataset_summary(file_id: int, user_id: int):
    file_record, path = get_file_path(file_id, user_id)
    if file_record is None:
        return None, (jsonify({"success": False, "message": "Dataset not found or access denied."}), 404)
    if not os.path.isfile(path):
        return None, (jsonify({"success": False, "message": "Dataset file is no longer available. Please upload it again."}), 404)

    frame = read_dataset(path, file_record["file_type"])
    row_count, column_count = frame.shape
    missing_by_column = {str(c): int(n) for c, n in frame.isna().sum().items()}
    missing_total = int(frame.isna().sum().sum())
    duplicate_count = int(frame.duplicated().sum())
    empty_columns = [str(c) for c in frame.columns if frame[c].isna().all() or frame[c].astype(str).str.strip().eq("").all()]
    numeric_columns = [str(c) for c in frame.select_dtypes(include="number").columns]
    categorical_columns = [str(c) for c in frame.select_dtypes(exclude="number").columns]
    column_details = []
    for col in frame.columns:
        series = frame[col]
        detail = {
            "name": str(col),
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            detail["mean"] = None if series.dropna().empty else round(float(series.mean()), 4)
            detail["min"] = None if series.dropna().empty else float(series.min())
            detail["max"] = None if series.dropna().empty else float(series.max())
        column_details.append(detail)

    summary = {
        "file_id": int(file_id),
        "filename": str(file_record["original_name"]),
        "rows": int(row_count),
        "columns": int(column_count),
        "missing_total": missing_total,
        "missing_by_column": missing_by_column,
        "duplicate_rows": duplicate_count,
        "empty_columns": empty_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "column_details": column_details,
    }
    return summary, None


def _rule_based_insights(summary):
    rows = summary["rows"]
    cells = rows * summary["columns"]
    missing_pct = round(100 * summary["missing_total"] / cells, 2) if cells else 0
    duplicate_pct = round(100 * summary["duplicate_rows"] / rows, 2) if rows else 0
    insights = []
    if summary["missing_total"]:
        impacted = [name for name, count in summary["missing_by_column"].items() if count]
        insights.append(f"{summary['missing_total']} missing values ({missing_pct}% of all cells) occur in {len(impacted)} column(s): {', '.join(impacted[:8])}. Choose an imputation method appropriate to each column; numeric columns often use median, while categorical columns often use mode.")
    else:
        insights.append("No missing values were detected in the dataset.")
    if summary["duplicate_rows"]:
        insights.append(f"{summary['duplicate_rows']} duplicate row(s) were detected ({duplicate_pct}% of rows). Review them before removing duplicates.")
    else:
        insights.append("No exact duplicate rows were detected.")
    if summary["empty_columns"]:
        insights.append("Completely empty columns: " + ", ".join(summary["empty_columns"][:10]) + ". Consider removing them if they are not intentionally reserved fields.")
    if rows == 0 or summary["columns"] == 0:
        insights.append("The dataset has no usable rows or columns. Verify that the uploaded file contains a header and data.")
    if summary["numeric_columns"]:
        insights.append("Numeric columns available for statistical analysis: " + ", ".join(summary["numeric_columns"][:10]) + ". Check ranges and outliers before modeling.")
    if not summary["numeric_columns"]:
        insights.append("No numeric columns were detected. If numerical analysis is expected, check whether numeric values were imported as text.")
    return insights


def _openai_text(instructions: str, payload: dict) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=instructions,
            input=str(payload),
        )
        return (response.output_text or "").strip() or None
    except Exception:
        # Do not expose provider details or secrets to the browser.
        return None


@ai_bp.route("/analysis/<int:file_id>", methods=["GET"])
def ai_analysis(file_id):
    user_id = _authenticated_user_id()
    if user_id is None:
        return jsonify({"success": False, "message": "Please log in to use AI analysis."}), 401
    try:
        summary, error = _dataset_summary(file_id, user_id)
        if error:
            return error
        insights = _rule_based_insights(summary)
        ai_text = _openai_text(
            "You are a careful data-quality analyst. Summarize the provided dataset statistics, explain likely risks, and give practical next steps. Do not claim causation or invent facts. The input contains aggregate metadata only, not raw records.",
            summary,
        )
        return jsonify({
            "success": True,
            "mode": "openai" if ai_text else "built-in",
            "summary": summary,
            "insights": insights,
            "ai_analysis": ai_text or "\n\n".join(insights),
            "message": "AI-generated narrative is enabled." if ai_text else "Built-in analysis is active. Add OPENAI_API_KEY in Render Environment settings to enable AI-generated narratives.",
        })
    except Exception:
        return jsonify({"success": False, "message": "Could not analyze this dataset. Check that the file is a valid CSV or Excel dataset."}), 400


@ai_bp.route("/agent", methods=["POST"])
def ai_agent():
    user_id = _authenticated_user_id()
    if user_id is None:
        return jsonify({"success": False, "message": "Please log in to use the AI agent."}), 401
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    file_id = body.get("file_id")
    if not message:
        return jsonify({"success": False, "message": "Enter a question for the AI agent."}), 400
    if len(message) > 2000:
        return jsonify({"success": False, "message": "Please keep your question under 2,000 characters."}), 400

    summary = None
    if file_id not in (None, ""):
        try:
            summary, error = _dataset_summary(int(file_id), user_id)
            if error:
                return error
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Invalid dataset selection."}), 400
        except Exception:
            return jsonify({"success": False, "message": "Could not read the selected dataset."}), 400

    context = summary or {"note": "No dataset selected. Give general data-cleaning guidance and ask the user to select a dataset for dataset-specific advice."}
    ai_text = _openai_text(
        "You are Data Link AI's dataset assistant. Answer clearly and practically. Use only the supplied aggregate dataset metadata; raw records are not available. Do not claim to have changed or cleaned a file. For destructive cleaning, explain the recommended steps and ask the user to run the relevant cleaning action themselves. If the question is unrelated, politely redirect to dataset preparation and analysis.",
        {"user_question": message, "dataset_summary": context},
    )
    if ai_text:
        answer = ai_text
        mode = "openai"
    else:
        lower = message.lower()
        if summary:
            findings = _rule_based_insights(summary)
            if any(word in lower for word in ("missing", "null", "empty value")):
                answer = next((x for x in findings if "missing" in x.lower()), findings[0])
            elif any(word in lower for word in ("duplicate", "repeated")):
                answer = next((x for x in findings if "duplicate" in x.lower()), findings[0])
            elif any(word in lower for word in ("column", "field", "schema")):
                answer = f"Your dataset has {summary['columns']} columns. Numeric columns: {', '.join(summary['numeric_columns']) or 'none detected'}. Categorical/text columns: {', '.join(summary['categorical_columns'][:12]) or 'none detected'}.\n\n" + "\n".join(findings[:2])
            elif any(word in lower for word in ("clean", "recommend", "improve", "quality", "analy")):
                answer = "Here is my dataset-specific review:\n\n" + "\n".join(f"• {item}" for item in findings)
            else:
                answer = f"I am using the built-in Data Link AI assistant (no OPENAI_API_KEY is configured). Your selected dataset, {summary['filename']}, has {summary['rows']} rows and {summary['columns']} columns.\n\n" + "\n".join(f"• {item}" for item in findings[:3]) + "\n\nAsk me about missing values, duplicates, empty columns, or data-quality improvements."
        else:
            answer = "I can help with dataset preparation, missing values, duplicate rows, empty columns, and analysis recommendations. Select a dataset to get advice based on its actual statistics. To enable conversational AI responses, configure OPENAI_API_KEY in Render's Environment settings."
        mode = "built-in"

    return jsonify({"success": True, "mode": mode, "answer": answer})
