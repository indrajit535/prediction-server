"""
FastAPI Prediction Server — Wingo 1 Min Mode (v8.0 ULTRA SECURE)
-----------------------------------------------------------------
🚀 DEPLOYED ON: Render
🌐 FRONTEND: AI Studio + Netlify
🔐 SECURITY LAYERS:
  1. Session Token System (HMAC-signed, 30 min TTL)
  2. One-Time Token (nonce) — ek token = ek prediction
  3. Device Binding (IP + Device ID)
  4. Origin Validation (Netlify domain only)
  5. App Signature Validation (optional)
  6. HMAC Signature on every prediction
  7. Time-Lock Nonce (replay attack protection)
  8. Rate Limiting + Auto-Block
  9. Anti-Echo + Strict Next Period
  10. Realistic Confidence (92.5–98.8%)
"""

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
import urllib.request
import json
import random
import time
import os
import hmac
import hashlib
import secrets
from collections import defaultdict

from firebase_config import (
    FIREBASE_WEB_CONFIG,
    check_key_active,
    get_server_status,
    create_withdrawal_request,
    get_user_withdrawals,
    get_user_balance,
    update_user_balance,
    init_firebase,
)

# ✅ NAVEEN AI PREDICTION ENGINE (with fallback)
try:
    from prediction_engine import sddgamer263_predict
    ENGINE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ prediction_engine import failed: {e}")
    print("   Fallback engine will be used.")
    ENGINE_AVAILABLE = False

    def sddgamer263_predict(current_number: int, period: str) -> dict:
        """Fallback engine agar prediction_engine.py না থাকে।"""
        big_small = "BIG" if current_number >= 5 else "SMALL"
        pool = [5, 6, 7, 8, 9] if big_small == "BIG" else [0, 1, 2, 3, 4]
        num = random.choice([n for n in pool if n != current_number])
        return {
            "bigSmall": big_small,
            "prediction": num,
            "confidence": 94.0 + random.random() * 4.0,
            "numbers": [num],
            "steps": ["fallback-engine"],
            "source": "fallback",
        }

# Firebase init on startup
init_firebase()

app = FastAPI(
    title="Wingo Prediction API",
    description="Wingo 1M prediction server — SDD AI MATRIX v2026 (ULTRA SECURE)",
    version="8.0.0"
)


# ============================================================
# 🌐 CORS CONFIG — Netlify + Local
# ============================================================
ALLOWED_ORIGINS = [
    "https://your-site.netlify.app",         # ← apna Netlify URL
    "https://your-custom-domain.com",        # ← custom domain (agar hai)
    "http://localhost:3000",                 # ← local testing
    "http://localhost:5173",                 # ← Vite dev server
    "http://127.0.0.1:5500",                 # ← VS Code Live Server
    "http://localhost:8000",                 # ← FastAPI local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================
# 🔐 SECURITY CONFIG
# ============================================================
SERVER_MASTER_SECRET = os.environ.get(
    "SERVER_MASTER_SECRET",
    "SDD263_MASTER_SECRET_CHANGE_THIS_IN_PRODUCTION_9f8e7d6c"
)

APP_VERIFY_SECRET = os.environ.get(
    "APP_VERIFY_SECRET",
    "SDD263_APP_VERIFY_CHANGE_THIS_5b4a3c2d1e0f"
)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "SDD263@@")

REQUIRE_APP_SIGNATURE = os.environ.get(
    "REQUIRE_APP_SIGNATURE", "false"
).lower() == "true"

ALLOWED_APP_SIGNATURES = []

SESSION_TTL_SEC = 1800       # 30 minutes
RATE_LIMIT_PER_MIN = 15      # Max 15 requests per minute
BLOCK_DURATION_SEC = 600     # Auto-block 10 min
PREDICTION_TTL_SEC = 35      # Cache TTL


# ============================================================
# 🌐 HISTORY API ENDPOINTS
# ============================================================
PRIMARY_HISTORY_API = (
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
)
BACKUP_HISTORY_API = (
    "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-1000"
)
HISTORY_APIS = [PRIMARY_HISTORY_API, BACKUP_HISTORY_API]

IST = timezone(timedelta(hours=5, minutes=30))


# ============================================================
# 🔐 SECURITY STATE (in-memory)
# ============================================================
ACTIVE_SESSIONS: Dict[str, dict] = {}
REQUEST_LOG: Dict[str, list] = defaultdict(list)
BLOCKED_KEYS: Dict[str, float] = {}
USED_TOKENS: set = set()


def _cleanup_sessions():
    now = time.time()
    expired = [
        t for t, s in ACTIVE_SESSIONS.items()
        if now > s.get("expires", 0)
    ]
    for t in expired:
        ACTIVE_SESSIONS.pop(t, None)
        USED_TOKENS.discard(t)


# ============================================================
# 🔑 SESSION TOKEN SYSTEM
# ============================================================
def generate_session_token(key: str, ip: str, device_id: str) -> str:
    now = int(time.time())
    expires = now + SESSION_TTL_SEC
    nonce = secrets.token_hex(8)

    payload = f"{key}|{expires}|{nonce}"
    signature = hmac.new(
        SERVER_MASTER_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    token = f"{payload}|{signature}"

    ACTIVE_SESSIONS[token] = {
        "key": key,
        "expires": expires,
        "createdAt": now,
        "ip": ip,
        "deviceId": device_id,
        "requests": 0,
    }

    return token


def verify_session_token(
    token: str,
    ip: str,
    device_id: str,
    consume: bool = False
) -> Optional[dict]:
    if not token or token.count("|") != 3:
        return None

    try:
        key, expires_str, nonce, signature = token.split("|")
        expires = int(expires_str)
    except ValueError:
        return None

    payload = f"{key}|{expires}|{nonce}"
    expected_sig = hmac.new(
        SERVER_MASTER_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        return None

    if time.time() > expires:
        ACTIVE_SESSIONS.pop(token, None)
        return None

    session = ACTIVE_SESSIONS.get(token)
    if not session:
        return None

    if session.get("ip") != ip:
        return None
    if session.get("deviceId") != device_id:
        return None

    if consume:
        if token in USED_TOKENS:
            return None
        USED_TOKENS.add(token)

    return session


# ============================================================
# 🛡️ RATE LIMITING + AUTO-BLOCK
# ============================================================
def is_blocked(key: str) -> bool:
    unblock_at = BLOCKED_KEYS.get(key)
    if unblock_at is None:
        return False
    if time.time() > unblock_at:
        del BLOCKED_KEYS[key]
        return False
    return True


def check_rate_limit(key: str):
    if is_blocked(key):
        remaining = int(BLOCKED_KEYS[key] - time.time())
        raise HTTPException(
            status_code=429,
            detail=f"Key blocked for {remaining}s due to abuse."
        )

    now = time.time()
    REQUEST_LOG[key] = [t for t in REQUEST_LOG[key] if now - t < 60]

    if len(REQUEST_LOG[key]) >= RATE_LIMIT_PER_MIN:
        BLOCKED_KEYS[key] = now + BLOCK_DURATION_SEC
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Blocked for {BLOCK_DURATION_SEC}s."
        )

    REQUEST_LOG[key].append(now)


# ============================================================
# 🛡️ ORIGIN VALIDATION
# ============================================================
def validate_origin(request: Request):
    origin = request.headers.get("Origin", "")
    referer = request.headers.get("Referer", "")

    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Unauthorized origin")

    if not origin and referer:
        if not any(o in referer for o in ALLOWED_ORIGINS):
            raise HTTPException(status_code=403, detail="Unauthorized referer")

    return True


def validate_app_signature(request: Request):
    if not REQUIRE_APP_SIGNATURE:
        return
    if not ALLOWED_APP_SIGNATURES:
        return
    app_sig = request.headers.get("X-App-Signature", "").strip()
    if app_sig not in ALLOWED_APP_SIGNATURES:
        raise HTTPException(status_code=403, detail="Unauthorized app")


# ============================================================
# ✍️ PREDICTION HMAC SIGNING
# ============================================================
def sign_prediction(period: str, number: int, bigsmall: str, confidence: float) -> str:
    payload = f"{period}|{number}|{bigsmall}|{confidence}"
    return hmac.new(
        APP_VERIFY_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def get_window_nonce() -> str:
    window = int(time.time()) // 60
    return hashlib.sha256(
        f"{window}|{SERVER_MASTER_SECRET}".encode()
    ).hexdigest()[:16]


# ============================================================
# 🗄️ PREDICTION CACHE
# ============================================================
PREDICTION_CACHE: Dict[str, dict] = {}
MAX_CACHE_SIZE = 200


def _purge_expired_cache():
    now_ms = int(time.time() * 1000)
    expired = [
        k for k, v in PREDICTION_CACHE.items()
        if (now_ms - v.get("_createdAt", 0)) / 1000 >= PREDICTION_TTL_SEC
    ]
    for k in expired:
        PREDICTION_CACHE.pop(k, None)


def get_cached_prediction(period: str):
    entry = PREDICTION_CACHE.get(period)
    if entry is None:
        return None
    age_sec = (time.time() * 1000 - entry.get("_createdAt", 0)) / 1000
    if age_sec >= PREDICTION_TTL_SEC:
        PREDICTION_CACHE.pop(period, None)
        return None
    return entry


def save_prediction_to_cache(period: str, data: dict):
    for k in list(PREDICTION_CACHE.keys()):
        if k != period:
            PREDICTION_CACHE.pop(k, None)
    if len(PREDICTION_CACHE) >= MAX_CACHE_SIZE:
        PREDICTION_CACHE.clear()
    data["_createdAt"] = int(time.time() * 1000)
    PREDICTION_CACHE[period] = data


# ============================================================
# 🕐 TIME HELPERS
# ============================================================
def get_ist_time():
    now = datetime.now(IST)
    total = now.hour * 3600 + now.minute * 60 + now.second
    return {
        "year": now.year, "month": now.month, "day": now.day,
        "hour": now.hour, "minute": now.minute, "second": now.second,
        "total_seconds": total
    }


def get_current_period():
    t = get_ist_time()
    period_number = (t["total_seconds"] // 60) + 1
    padded = str(period_number).zfill(4)
    return f"{t['year']}{t['month']:02d}{t['day']:02d}1000{padded}"


def get_remaining_seconds():
    t = get_ist_time()
    return 60 - (t["total_seconds"] % 60)


# ============================================================
# 🌐 LIVE HISTORY FETCH
# ============================================================
def _http_get_json(url: str, timeout: int = 8):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://draw.ar-lottery01.com/",
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_list(raw) -> List[dict]:
    if not isinstance(raw, dict):
        return []
    data = raw.get("data")
    if isinstance(data, dict) and isinstance(data.get("list"), list):
        return data["list"]
    if isinstance(raw.get("list"), list):
        return raw["list"]
    if isinstance(raw, list):
        return raw
    return []


def fetch_history(retries: int = 2):
    last_err = None
    for api in HISTORY_APIS:
        for attempt in range(retries + 1):
            try:
                raw = _http_get_json(api, timeout=6)
                lst = _extract_list(raw)
                if lst:
                    return {"code": 0, "msg": "ok", "data": {"list": lst}, "_src": api}
            except Exception as e:
                last_err = e
                time.sleep(0.25)
    return {"code": -1, "msg": str(last_err or "all endpoints failed"),
            "data": {"list": []}, "_src": None}


def get_latest_draw():
    data = fetch_history()
    lst = data.get("data", {}).get("list", []) or []
    if not lst:
        return None, None
    latest = lst[0]
    issue = str(latest.get("issueNumber") or latest.get("issue") or "").strip()
    raw_num = latest.get("number", latest.get("result", None))
    try:
        num = int(raw_num) % 10
    except (ValueError, TypeError):
        num = None
    if not issue:
        return None, None
    return issue, num


def fetch_live_period():
    issue, _ = get_latest_draw()
    if issue:
        try:
            next_period = str(int(issue) + 1)
        except ValueError:
            next_period = get_current_period()
        return {
            "period": next_period,
            "remaining_seconds": get_remaining_seconds(),
            "source": "live"
        }
    return {
        "period": get_current_period(),
        "remaining_seconds": get_remaining_seconds(),
        "source": "local-fallback"
    }


# ============================================================
# 🎯 ANTI-ECHO NUMBER PICKER
# ============================================================
def _pick_anti_echo_number(suggested: int, big_small: str, last_number: Optional[int]) -> int:
    big_set = [5, 6, 7, 8, 9]
    small_set = [0, 1, 2, 3, 4]
    pool = big_set if big_small == "BIG" else small_set

    if isinstance(suggested, int) and suggested in pool and suggested != last_number:
        return suggested

    candidates = [n for n in pool if n != last_number] or pool
    return random.choice(candidates)


def _realistic_confidence(raw_conf, has_live_data: bool) -> float:
    try:
        c = float(raw_conf)
    except (ValueError, TypeError):
        c = None

    if not has_live_data:
        c = 92.5 + random.random() * 3.0
    elif c is None or c < 90:
        c = 92.5 + random.random() * 6.3
    else:
        c = max(92.5, min(98.8, c))
    return round(c, 1)


# ============================================================
# 🎯 PREDICTION GENERATOR
# ============================================================
def generate_prediction(period: Optional[str] = None,
                        game_id: str = "wingo_1min",
                        use_cache: bool = True):
    latest_issue, last_number = get_latest_draw()
    has_live_data = latest_issue is not None

    if period is not None:
        target_period = str(period)
    elif latest_issue is not None:
        target_period = str(int(latest_issue) + 1)
    else:
        target_period = get_current_period()

    if use_cache:
        cached = get_cached_prediction(target_period)
        if cached is not None:
            out = dict(cached)
            out["timestamp"] = int(time.time() * 1000)
            out["fromCache"] = True
            return out

    try:
        result = sddgamer263_predict(
            current_number=(last_number if last_number is not None else 0),
            period=target_period,
        )
    except Exception as e:
        print(f"[ENGINE ERROR] {e}")
        result = {
            "bigSmall": "BIG" if (last_number or 0) >= 5 else "SMALL",
            "prediction": last_number if last_number is not None else 0,
            "confidence": 94.0,
            "numbers": [last_number if last_number is not None else 0],
            "steps": ["fallback: engine error"],
            "source": "engine-fallback",
        }

    big_small = result.get("bigSmall") or (
        "BIG" if (last_number or 0) >= 5 else "SMALL"
    )
    if big_small not in ("BIG", "SMALL"):
        big_small = "BIG" if (last_number or 0) >= 5 else "SMALL"

    suggested = result.get("prediction", last_number if last_number is not None else 0)
    final_number = _pick_anti_echo_number(suggested, big_small, last_number)

    if big_small == "BIG" and final_number not in (5, 6, 7, 8, 9):
        final_number = _pick_anti_echo_number(7, "BIG", last_number)
    if big_small == "SMALL" and final_number not in (0, 1, 2, 3, 4):
        final_number = _pick_anti_echo_number(2, "SMALL", last_number)

    confidence = _realistic_confidence(result.get("confidence"), has_live_data)

    prediction = {
        "period": target_period,
        "gameId": game_id,
        "mode": "1m",
        "bigSmallResult": big_small,
        "numberResult": final_number,
        "numbers": [final_number],
        "confidence": confidence,
        "patternName": "SDD AI MATRIX v2026",
        "steps": result.get("steps", []),
        "source": result.get("source", "naveen-ai"),
        "inputNumber": last_number,
        "lastDrawNumber": last_number,
        "timestamp": int(time.time() * 1000),
        "fromCache": False,
    }

    if use_cache:
        save_prediction_to_cache(target_period, prediction)

    return prediction


# ============================================================
# 🖼️ IMAGE ASSETS
# ============================================================
ASSETS = {
    "bigSmall": {
        "BIG":   "https://i.ibb.co/Pb3P55c/1776870190363.png",
        "SMALL": "https://i.ibb.co/pBcDXRFm/1776870218135.png"
    },
    "numbers": [
        "https://i.ibb.co/whKvd1bL/1776870264510.png",
        "https://i.ibb.co/GfmHk799/1776870297250.png",
        "https://i.ibb.co/zVrbGJ0H/1776870331500.png",
        "https://i.ibb.co/JFxdJCjb/1776870358256.png",
        "https://i.ibb.co/Z7N213k/1776870391192.png",
        "https://i.ibb.co/WNDx2qbx/1776870425087.png",
        "https://i.ibb.co/GQ04Y4Ds/1776870455662.png",
        "https://i.ibb.co/DPP7TJ95/1776870488109.png",
        "https://i.ibb.co/sdSgFGXj/1776870514631.png",
        "https://i.ibb.co/Xx401f6w/1776870543380.png"
    ]
}


def get_prediction_images(prediction):
    bs = prediction["bigSmallResult"]
    num = prediction["numberResult"]
    return {
        "bigSmallImage": ASSETS["bigSmall"].get(bs, ASSETS["bigSmall"]["BIG"]),
        "numberImage": (
            ASSETS["numbers"][num]
            if isinstance(num, int) and 0 <= num < len(ASSETS["numbers"])
            else ASSETS["numbers"][0]
        ),
    }


# ============================================================
# 🔐 VALIDATION HELPERS
# ============================================================
def validate_key_or_raise(key: str):
    if not key:
        raise HTTPException(status_code=400, detail="Key required")
    check_rate_limit(key)
    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])
    return status.get("data") or {}


def check_server_online_or_raise():
    status = get_server_status()
    if not status["online"]:
        raise HTTPException(status_code=503, detail=status["message"])
    return status


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============================================================
# 🚀 PUBLIC ENDPOINTS
# ============================================================
@app.get("/")
def root():
    _purge_expired_cache()
    _cleanup_sessions()
    return {
        "status": "online",
        "mode": "wingo-1m",
        "version": "8.0.0",
        "engine": "SDD AI MATRIX v2026",
        "engineLoaded": ENGINE_AVAILABLE,
        "security": "ULTRA",
        "cachedPeriods": len(PREDICTION_CACHE),
        "activeSessions": len(ACTIVE_SESSIONS),
    }


@app.get("/firebase-config")
def firebase_config():
    return FIREBASE_WEB_CONFIG


@app.get("/server-status")
def server_status():
    return get_server_status()


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": int(time.time() * 1000)}


# ============================================================
# 🔑 AUTH LOGIN
# ============================================================
@app.post("/auth/login")
async def auth_login(request: Request):
    validate_origin(request)
    validate_app_signature(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    key = (body.get("key") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key required")

    srv = get_server_status()
    if not srv["online"]:
        raise HTTPException(status_code=503, detail=srv["message"])

    check_rate_limit(key)

    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])

    data = status.get("data") or {}

    ip = _get_client_ip(request)
    device_id = request.headers.get("X-Device-Id", "web-" + ip)

    session_token = generate_session_token(key, ip, device_id)

    return {
        "success": True,
        "message": "Login successful",
        "key": key,
        "sessionToken": session_token,
        "expiresIn": SESSION_TTL_SEC,
        "windowNonce": get_window_nonce(),
        "balance": float(data.get("balance", 0)),
        "expiry": data.get("expiry", 0),
        "createdAt": data.get("createdAt", 0),
    }


@app.get("/auth/check")
def auth_check(key: str = Query(...)):
    srv = get_server_status()
    if not srv["online"]:
        return {"active": False, "serverOnline": False, "message": srv["message"]}

    status = check_key_active(key)
    data = status.get("data") or {}
    return {
        "active": status["active"],
        "serverOnline": True,
        "reason": status["reason"],
        "balance": float(data.get("balance", 0)),
        "expiry": data.get("expiry", 0),
    }


# ============================================================
# 🎯 SECURE PREDICTION
# ============================================================
@app.get("/predict")
def predict(
    request: Request,
    period: Optional[str] = Query(default=None),
    session: str = Query(...),
):
    validate_origin(request)
    validate_app_signature(request)

    ip = _get_client_ip(request)
    device_id = request.headers.get("X-Device-Id", "web-" + ip)

    session_data = verify_session_token(session, ip, device_id, consume=True)
    if not session_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or already-used session. Please login again."
        )

    key = session_data["key"]

    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])

    check_server_online_or_raise()

    pred = generate_prediction(period=period)
    images = get_prediction_images(pred)

    signature = sign_prediction(
        pred["period"],
        pred["numberResult"],
        pred["bigSmallResult"],
        pred["confidence"]
    )

    return {
        "prediction": pred["bigSmallResult"],
        "period": pred["period"],
        "number": pred["numberResult"],
        "numbers": [pred["numberResult"]],
        "confidence": pred["confidence"],
        "mode": pred["mode"],
        "patternName": pred["patternName"],
        "source": pred.get("source", "naveen-ai"),
        "bigSmallImage": images["bigSmallImage"],
        "numberImage": images["numberImage"],
        "signature": signature,
        "windowNonce": get_window_nonce(),
        "timestamp": pred["timestamp"],
        "fromCache": pred.get("fromCache", False),
    }


# ============================================================
# 📊 PERIOD INFO
# ============================================================
@app.get("/period")
def period_info(request: Request, session: str = Query(...)):
    validate_origin(request)
    validate_app_signature(request)

    ip = _get_client_ip(request)
    device_id = request.headers.get("X-Device-Id", "web-" + ip)

    session_data = verify_session_token(session, ip, device_id, consume=False)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    live = fetch_live_period()
    return {
        "period": live["period"],
        "remainingSeconds": live["remaining_seconds"],
        "source": live["source"],
    }


# ============================================================
# 📜 HISTORY
# ============================================================
@app.get("/history")
def history(request: Request, session: str = Query(...)):
    validate_origin(request)
    validate_app_signature(request)

    ip = _get_client_ip(request)
    device_id = request.headers.get("X-Device-Id", "web-" + ip)

    session_data = verify_session_token(session, ip, device_id, consume=False)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    data = fetch_history()
    lst = data.get("data", {}).get("list", [])[:100]
    return {"count": len(lst), "results": lst}


# ============================================================
# 💰 WITHDRAWAL ENDPOINTS
# ============================================================
@app.get("/withdrawal/balance")
def withdrawal_balance(key: str = Query(...)):
    validate_key_or_raise(key)
    return {"balance": get_user_balance(key)}


@app.post("/withdrawal/request")
async def withdrawal_request(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    key = (body.get("key") or "").strip()
    try:
        amount = float(body.get("amount", 0))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid amount")
    method = body.get("method", "UPI")
    account = body.get("account", "")

    validate_key_or_raise(key)
    check_server_online_or_raise()

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    balance = get_user_balance(key)
    if amount > balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    result = create_withdrawal_request(key, amount, method, account)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed"))

    return {
        "success": True,
        "message": "Withdrawal request submitted",
        "requestId": result["requestId"],
        "status": "pending",
    }


@app.get("/withdrawal/history")
def withdrawal_history(key: str = Query(...)):
    validate_key_or_raise(key)
    return {"requests": get_user_withdrawals(key)}


# ============================================================
# 🛡️ ADMIN ENDPOINTS
# ============================================================
def _check_admin(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")


@app.get("/admin/keys")
def admin_list_keys(password: str = Query(...)):
    _check_admin(password)
    from firebase_config import _rest_get
    data = _rest_get("keys") or {}
    keys = []
    for k, v in data.items():
        if isinstance(v, dict):
            keys.append({"key": k, **v})
    keys.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return {"count": len(keys), "keys": keys}


@app.post("/admin/keys/create")
async def admin_create_key(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))

    key = (body.get("key") or "").strip()
    if not key:
        key = "MAXMOD" + "".join(random.choices(
            "ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=10))

    duration_days = int(body.get("durationDays", 30))
    balance = float(body.get("balance", 0))
    now_ms = int(time.time() * 1000)
    expiry = now_ms + duration_days * 24 * 60 * 60 * 1000

    data = {
        "active": True,
        "deleted": False,
        "createdAt": now_ms,
        "expiry": expiry,
        "durationDays": duration_days,
        "balance": balance,
    }

    from firebase_config import _rest_put
    result = _rest_put(f"keys/{key}", data)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create key")

    return {"success": True, "key": key, "data": data}


@app.post("/admin/keys/delete")
async def admin_delete_key(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    key = (body.get("key") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key required")

    from firebase_config import _rest_patch
    result = _rest_patch(f"keys/{key}", {"active": False, "deleted": True})
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to delete key")

    return {"success": True, "message": f"Key {key} deleted"}


@app.post("/admin/keys/toggle")
async def admin_toggle_key(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    key = (body.get("key") or "").strip()
    active = bool(body.get("active", True))

    from firebase_config import _rest_patch
    result = _rest_patch(f"keys/{key}", {"active": active})
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update key")

    return {"success": True, "key": key, "active": active}


@app.post("/admin/keys/balance")
async def admin_update_balance(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    key = (body.get("key") or "").strip()
    balance = float(body.get("balance", 0))

    ok = update_user_balance(key, balance)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update balance")

    return {"success": True, "key": key, "balance": balance}


@app.post("/admin/server/toggle")
async def admin_server_toggle(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    online = bool(body.get("online", True))
    message = body.get(
        "message", "Server is running" if online else "Server is under maintenance"
    )

    from firebase_config import _rest_put
    result = _rest_put(
        "server_status",
        {"online": online, "message": message,
         "updatedAt": int(time.time() * 1000)},
    )
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update server status")

    return {"success": True, "online": online, "message": message}


@app.get("/admin/withdrawals")
def admin_list_withdrawals(password: str = Query(...)):
    _check_admin(password)
    from firebase_config import _rest_get
    data = _rest_get("withdrawals") or {}
    reqs = [v for v in data.values() if isinstance(v, dict)]
    reqs.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return {"count": len(reqs), "requests": reqs}


@app.post("/admin/withdrawals/action")
async def admin_withdrawal_action(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    req_id = (body.get("requestId") or "").strip()
    action = (body.get("action") or "").strip().lower()

    if action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")

    from firebase_config import _rest_get, _rest_patch
    req = _rest_get(f"withdrawals/{req_id}")
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    new_status = "accepted" if action == "accept" else "rejected"
    _rest_patch(
        f"withdrawals/{req_id}",
        {"status": new_status, "processedAt": int(time.time() * 1000)},
    )

    if action == "accept":
        key = req.get("key")
        amount = float(req.get("amount", 0))
        current_balance = get_user_balance(key)
        new_balance = max(0, current_balance - amount)
        update_user_balance(key, new_balance)

    return {"success": True, "requestId": req_id, "status": new_status}


@app.get("/admin/stats")
def admin_stats(password: str = Query(...)):
    _check_admin(password)
    from firebase_config import _rest_get
    keys_data = _rest_get("keys") or {}
    wd_data = _rest_get("withdrawals") or {}
    srv = get_server_status()

    total_keys = len(keys_data)
    active_keys = sum(
        1 for v in keys_data.values()
        if isinstance(v, dict) and v.get("active") and not v.get("deleted")
    )
    total_balance = sum(
        float(v.get("balance", 0)) for v in keys_data.values() if isinstance(v, dict)
    )

    pending_wds = sum(
        1 for v in wd_data.values()
        if isinstance(v, dict) and v.get("status") == "pending"
    )
    accepted_wds = sum(
        1 for v in wd_data.values()
        if isinstance(v, dict) and v.get("status") == "accepted"
    )
    rejected_wds = sum(
        1 for v in wd_data.values()
        if isinstance(v, dict) and v.get("status") == "rejected"
    )

    return {
        "totalKeys": total_keys,
        "activeKeys": active_keys,
        "totalBalance": total_balance,
        "serverOnline": srv["online"],
        "serverMessage": srv["message"],
        "withdrawals": {
            "pending": pending_wds,
            "accepted": accepted_wds,
            "rejected": rejected_wds,
        },
        "security": {
            "activeSessions": len(ACTIVE_SESSIONS),
            "usedTokens": len(USED_TOKENS),
            "blockedKeys": len(BLOCKED_KEYS),
        },
    }


# ============================================================
# 🧹 SECURITY MANAGEMENT
# ============================================================
@app.get("/admin/security/sessions")
def admin_sessions(password: str = Query(...)):
    _check_admin(password)
    _cleanup_sessions()
    return {
        "activeSessions": len(ACTIVE_SESSIONS),
        "usedTokens": len(USED_TOKENS),
        "blockedKeys": list(BLOCKED_KEYS.keys()),
    }


@app.get("/admin/security/unblock")
def admin_unblock_key(password: str = Query(...), key: str = Query(...)):
    _check_admin(password)
    if key in BLOCKED_KEYS:
        del BLOCKED_KEYS[key]
    REQUEST_LOG.pop(key, None)
    return {"success": True, "message": f"Key {key} unblocked"}


@app.get("/admin/security/clear-sessions")
def admin_clear_sessions(password: str = Query(...)):
    _check_admin(password)
    ACTIVE_SESSIONS.clear()
    USED_TOKENS.clear()
    return {"success": True, "message": "All sessions cleared"}


# ============================================================
# 🧹 CACHE MANAGEMENT
# ============================================================
@app.get("/cache-info")
def cache_info(password: str = Query(...)):
    _check_admin(password)
    _purge_expired_cache()
    return {
        "cachedPeriods": len(PREDICTION_CACHE),
        "maxSize": MAX_CACHE_SIZE,
        "ttlSeconds": PREDICTION_TTL_SEC,
        "periods": list(PREDICTION_CACHE.keys()),
    }


@app.get("/cache-clear")
def cache_clear(password: str = Query(...)):
    _check_admin(password)
    PREDICTION_CACHE.clear()
    return {"status": "cleared"}


# ============================================================
# 🖼️ STATIC PANELS
# ============================================================
if os.path.isdir("static"):
    app.mount("/panel", StaticFiles(directory="static", html=True), name="static")


# ============================================================
# 🚀 ENTRY POINT
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
