import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback")

CLIENT_CONFIG = {
    "web": {
        "client_id":     os.getenv("YOUTUBE_CLIENT_ID"),
        "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
        "redirect_uris": [REDIRECT_URI],
        "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
        "token_uri":     "https://oauth2.googleapis.com/token",
    }
}


def _new_flow() -> Flow:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    return flow


_flow_store: dict[str, Flow] = {}

def yt_get_auth_url(state: str) -> str:
    flow = _new_flow()
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
        state=state,
    )
    _flow_store[state] = flow
    return auth_url

def yt_exchange_code(code: str, state: str) -> dict:
    flow = _flow_store.pop(state, None) or _new_flow()
    flow.fetch_token(code=code)
    return json.loads(flow.credentials.to_json())

def yt_credentials_from_token(token: dict) -> tuple[Credentials | None, dict]:
    """Rebuild Credentials from a stored token, refreshing if expired.
    Returns (creds_or_None, token_dict_to_persist). The token dict is returned
    (possibly refreshed) so the caller can write the new access token back.
    """
    creds = Credentials.from_authorized_user_info(token, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token = json.loads(creds.to_json())
    if creds and creds.valid:
        return creds, token
    return None, token
