import time
import requests
from typing import Dict, Any, List
from .config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REDIRECT_URI

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE = "https://www.strava.com/api/v3"

def build_auth_url() -> str:
    params = {
        "client_id": STRAVA_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": STRAVA_REDIRECT_URI,
        "approval_prompt": "auto",
        "scope": "read,activity:read_all",
    }
    return requests.Request("GET", AUTH_URL, params=params).prepare().url

def exchange_code_for_token(code: str) -> Dict[str, Any]:
    resp = requests.post(TOKEN_URL, data={
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()

def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    resp = requests.post(TOKEN_URL, data={
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()

def ensure_access_token(tokens: Dict[str, Any]) -> Dict[str, Any]:
    now = int(time.time())
    if now < int(tokens["expires_at"]) - 30:
        return tokens

    refreshed = refresh_access_token(tokens["refresh_token"])
    return {
        "athlete_id": refreshed["athlete"]["id"],
        "access_token": refreshed["access_token"],
        "refresh_token": refreshed["refresh_token"],
        "expires_at": refreshed["expires_at"],
    }

def list_activities(access_token: str, after: int, page: int, per_page: int = 200) -> List[Dict[str, Any]]:
    url = f"{API_BASE}/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"after": after, "page": page, "per_page": per_page}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
