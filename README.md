# Data Link AI

A Flask web application for uploading and cleaning CSV/Excel datasets.

## Local run

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Set a non-default SECRET_KEY before public use
python app.py
```

Open http://127.0.0.1:5000.

## Render deployment

Create a Render **Web Service** connected to this repository and configure:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment variable: `SECRET_KEY` set to a long random value
- For durable data, attach a persistent disk and set `DATA_STORAGE_DIR` to its mount path and `DATABASE_PATH` to a SQLite file on that disk. If not configured, SQLite and uploads use the service's local filesystem and can be lost on redeploy/restart.

Do not commit real user databases, private uploads, or API keys. This package excludes the development SQLite databases and uploaded sample files.

## Notes

- Flask serves the frontend and API from the same origin.
- The API uses a signed Flask session for dataset ownership; browser-supplied user IDs are not trusted.
- This is a project deployment baseline, not a substitute for a full production security review.

## AI Analysis and AI Agent (add-on)

The dashboard includes AI Dataset Analysis and a Data Link AI Agent. Both require an authenticated user and only operate on that user's datasets. Aggregate dataset statistics are used as context; raw data rows are not sent to an AI provider.

- Without `OPENAI_API_KEY`, built-in data-quality insights and assistant guidance are available.
- To enable generated natural-language insights, add `OPENAI_API_KEY` in Render's Environment settings. Optionally set `OPENAI_MODEL` (default: `gpt-4.1-mini`).
- Keep API keys in Render Environment settings, never in frontend JavaScript or committed files.
