import time
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from .config import FRONTEND_ORIGIN, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
from .db import init_db, get_tokens, upsert_tokens, get_last_sync, set_last_sync, upsert_summary, fetch_summaries
from .strava import build_auth_url, exchange_code_for_token, ensure_access_token, list_activities
from .aggregate import build_period_aggregates

app = FastAPI(title="Strava Personal Report (Local)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/callback")
def callback(code: str = Query(...)):
    data = exchange_code_for_token(code)
    athlete_id = data["athlete"]["id"]
    upsert_tokens(
        athlete_id=athlete_id,
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=data["expires_at"],
    )
    return RedirectResponse(url=f"{FRONTEND_ORIGIN}/")

@app.get("/sync")
def sync():
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Missing STRAVA_CLIENT_ID/SECRET in backend .env"},
        )

    tokens = get_tokens()
    if not tokens:
        return {"status": "needs_auth", "auth_url": build_auth_url()}

    refreshed = ensure_access_token(tokens)
    if refreshed != tokens:
        upsert_tokens(**refreshed)
        tokens = refreshed

    after = get_last_sync()
    all_new = []
    page = 1

    while True:
        batch = list_activities(tokens["access_token"], after=after, page=page, per_page=200)
        if not batch:
            break
        all_new.extend(batch)
        page += 1
        if page > 50:
            break

    weekly, monthly, yearly = build_period_aggregates(all_new)

    for period_start, agg in weekly.items():
        upsert_summary("week", period_start, agg.run_count, agg.total_meters, agg.total_seconds,
                       agg.avg_hr_time_weighted(), agg.elev_gain)

    for period_start, agg in monthly.items():
        upsert_summary("month", period_start, agg.run_count, agg.total_meters, agg.total_seconds,
                       agg.avg_hr_time_weighted(), agg.elev_gain)

    for period_start, agg in yearly.items():
        upsert_summary("year", period_start, agg.run_count, agg.total_meters, agg.total_seconds,
                       agg.avg_hr_time_weighted(), agg.elev_gain)

    now = int(time.time())
    set_last_sync(now)

    return {
        "status": "ok",
        "last_sync": now,
        "new_activities_fetched": len(all_new),
        "summaries": {
            "weekly": fetch_summaries("week"),
            "monthly": fetch_summaries("month"),
            "yearly": fetch_summaries("year"),
        },
    }

@app.get("/summaries/{period_type}")
def summaries(period_type: str):
    if period_type not in ("week", "month", "year"):
        return JSONResponse(status_code=400, content={"error": "period_type must be week|month|year"})
    return {"period_type": period_type, "rows": fetch_summaries(period_type)}
