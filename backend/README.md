# PulseAlpha Backend (Flask + SQLite3 + JWT)

## Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Server starts on `http://127.0.0.1:5000`.

Alternative (from project root):

```bash
python -m backend.app
```

## Uses Existing Model Artifacts

- `data/xgboost_model.pkl`
- `data/xgboost_metadata.pkl`

## SQLite Database

Database file is auto-created at:

- `backend/pulsealpha.db`

Tables:

- `users`
- `watchlist`
- `alerts`
- `saved_news`

## Auth Endpoints

- `POST /api/register`
- `POST /api/login`

## Public Endpoints

- `GET /api/overview`
- `GET /api/market-summary`
- `GET /api/company/<ticker>`
- `GET /api/company/<ticker>/news`
- `GET /api/company/<ticker>/sentiment`
- `GET /api/company/<ticker>/prediction`
- `GET /api/news`
- `GET /api/predictions/all`
- `GET /api/model-info`

## User Endpoints (JWT required)

- `GET /api/watchlist`
- `POST /api/watchlist`
- `GET /api/alerts`
- `POST /api/alerts`

Use `Authorization: Bearer <token>` for protected routes.
