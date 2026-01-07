# Strava Personal Report (Local)

Local web app (FastAPI + React/Vite) that syncs your Strava activities on frontend launch and shows weekly/monthly/yearly summaries.

## Setup

### 1) Backend
```bash
cd backend
cp .env.example .env
# edit .env and fill STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

First run will redirect you to Strava OAuth. After approval, you will be sent back and the app will auto-sync.
