# Backend (Flask + Firestore)

## Setup
1. Create a Firebase project and enable **Firestore in Native mode**.
2. Download a Service Account JSON and place it here as `serviceAccountKey.json` (or set `FIREBASE_CREDS_JSON` env var).
3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
4. Run locally:
   ```bash
   python app.py
   ```

## Deploy (Render/Railway/Heroku)
- Use `gunicorn app:app` as the start command.
- Set one of:
  - `FIREBASE_CREDS_PATH=serviceAccountKey.json` (and upload file via dashboard if supported)
  - **or** `FIREBASE_CREDS_JSON=<entire JSON content>` as an environment variable.
