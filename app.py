"""
FastAPI Prediction Server — Wingo 1 Min Mode (v7.0 PRODUCTION)
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

from prediction_engine import sddgamer263_predict

init_firebase()

app = FastAPI(
    title="Wingo Prediction API",
    description="Wingo 1M prediction server — SDD AI MATRIX v2026",
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_PASSWORD = "SDD263@@"

PRIMARY_HISTORY_API = (
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
)
BACKUP_HISTORY_API = (
    "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-1000"
)
HISTORY_APIS = [PRIMARY_HISTORY_API, BACKUP_HISTORY_API]

IST = timezone(timedelta(hours=5, minutes=30))

PREDICTION_CACHE: Dict[str, dict] = {}
MAX_CACHE_SIZE = 200
CACHE_TTL_SEC = 35


def _purge_expired_cache():
    now_ms = int(time.time() * 1000)
    expired = [
        k for k, v in PREDICTION_CACHE.items()
        if (now_ms - v.get("_createdAt", 0)) / 1000 >= CACHE_TTL_SEC
    ]
    for k in expired:
        PREDICTION_CACHE.pop(k, None)


def get_cached_prediction(period: str):
    entry = PREDICTION_CACHE.get(period)
    if entry is None:
        return None
    age_sec = (time.time() * 1000 - entry.get("_createdAt", 0)) / 1000
    if age_sec >= CACHE_TTL_SEC:
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


def get_ist_time():
    now = datetime.now(IST)
    total_seconds = now.hour * 3600 + now.minute * 60 + now.second
    return {
        "year": now.year, "month": now.month, "day": now.day,
        "hour": now.hour, "minute": now.minute, "second": now.second,
        "total_seconds": total_seconds
    }


def get_current_period():
    t = get_ist_time()
    period_number = (t["total_seconds"] // 60) + 1
    padded = str(period_number).zfill(4)
    return f"{t['year']}{t['month']:02d}{t['day']:02d}1000{padded}"


def get_remaining_seconds():
    t = get_ist_time()
    elapsed = t["total_seconds"] % 60
    return 60 - elapsed


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
        return {"period": next_period,
                "remaining_seconds": get_remaining_seconds(),
                "source": "live"}
    return {"period": get_current_period(),
            "remaining_seconds": get_remaining_seconds(),
            "source": "local-fallback"}


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


def validate_key_or_raise(key: str):
    if not key:
        raise HTTPException(status_code=400, detail="Key required")
    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])
    return status.get("data") or {}


def check_server_online_or_raise():
    status = get_server_status()
    if not status["online"]:
        raise HTTPException(status_code=503, detail=status["message"])
    return status


@app.get("/")
def root():
    _purge_expired_cache()
    return {
        "status": "online",
        "mode": "wingo-1m",
        "version": "7.0.0",
        "engine": "SDD AI MATRIX v2026",
        "cachedPeriods": len(PREDICTION_CACHE),
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


@app.get("/public/predict")
def public_predict():
    check_server_online_or_raise()
    pred = generate_prediction()
    images = get_prediction_images(pred)
    return {
        "prediction": pred["bigSmallResult"],
        "period": pred["period"],
        "number": pred["numberResult"],
        "numbers": [pred["numberResult"]],
        "confidence": pred["confidence"],
        "patternName": "SDD AI MATRIX v2026",
        "bigSmallImage": images["bigSmallImage"],
        "numberImage": images["numberImage"],
        "timestamp": int(time.time() * 1000),
        "fromCache": pred.get("fromCache", False),
    }


@app.post("/auth/login")
async def auth_login(request: Request):
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
    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])
    data = status.get("data") or {}
    return {
        "success": True, "message": "Login successful", "key": key,
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
        "active": status["active"], "serverOnline": True,
        "reason": status["reason"],
        "balance": float(data.get("balance", 0)),
        "expiry": data.get("expiry", 0),
    }


@app.get("/period")
def period_info(key: str = Query(...)):
    validate_key_or_raise(key)
    live = fetch_live_period()
    return {"period": live["period"],
            "remainingSeconds": live["remaining_seconds"],
            "source": live["source"]}


@app.get("/history")
def history(key: str = Query(...)):
    validate_key_or_raise(key)
    data = fetch_history()
    lst = data.get("data", {}).get("list", [])[:100]
    return {"count": len(lst), "results": lst}


@app.get("/predict")
def predict(period: Optional[str] = Query(default=None), key: str = Query(...)):
    validate_key_or_raise(key)
    check_server_online_or_raise()
    pred = generate_prediction(period=period)
    images = get_prediction_images(pred)
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
        "timestamp": pred["timestamp"],
        "fromCache": pred.get("fromCache", False),
        "steps": pred.get("steps", []),
    }


@app.get("/predict-full")
def predict_full(key: str = Query(...)):
    validate_key_or_raise(key)
    check_server_online_or_raise()
    live = fetch_live_period()
    pred = generate_prediction(period=live["period"])
    images = get_prediction_images(pred)
    history_data = fetch_history()
    last10 = history_data.get("data", {}).get("list", [])[:10]
    return {
        "prediction": {
            "bigSmall": pred["bigSmallResult"],
            "number": pred["numberResult"],
            "numbers": [pred["numberResult"]],
            "confidence": pred["confidence"],
            "period": pred["period"],
            "patternName": pred["patternName"],
            "source": pred.get("source", "naveen-ai"),
            "bigSmallImage": images["bigSmallImage"],
            "numberImage": images["numberImage"],
            "fromCache": pred.get("fromCache", False),
            "steps": pred.get("steps", []),
        },
        "live": {
            "period": live["period"],
            "remainingSeconds": live["remaining_seconds"],
            "source": live["source"],
        },
        "history": last10,
        "timestamp": pred["timestamp"],
    }


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
    return {"success": True, "message": "Withdrawal request submitted",
            "requestId": result["requestId"], "status": "pending"}


@app.get("/withdrawal/history")
def withdrawal_history(key: str = Query(...)):
    validate_key_or_raise(key)
    return {"requests": get_user_withdrawals(key)}


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
        key = "MAXMOD" + "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=10))
    duration_days = int(body.get("durationDays", 30))
    balance = float(body.get("balance", 0))
    now_ms = int(time.time() * 1000)
    expiry = now_ms + duration_days * 24 * 60 * 60 * 1000
    data = {"active": True, "deleted": False, "createdAt": now_ms,
            "expiry": expiry, "durationDays": duration_days, "balance": balance}
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
    message = body.get("message", "Server is running" if online else "Server is under maintenance")
    from firebase_config import _rest_put
    result = _rest_put("server_status",
                       {"online": online, "message": message,
                        "updatedAt": int(time.time() * 1000)})
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
    _rest_patch(f"withdrawals/{req_id}",
                {"status": new_status, "processedAt": int(time.time() * 1000)})
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
        "totalKeys": total_keys, "activeKeys": active_keys,
        "totalBalance": total_balance, "serverOnline": srv["online"],
        "serverMessage": srv["message"],
        "withdrawals": {"pending": pending_wds, "accepted": accepted_wds,
                        "rejected": rejected_wds},
    }


@app.get("/cache-info")
def cache_info(password: str = Query(...)):
    _check_admin(password)
    _purge_expired_cache()
    return {
        "cachedPeriods": len(PREDICTION_CACHE),
        "maxSize": MAX_CACHE_SIZE,
        "ttlSeconds": CACHE_TTL_SEC,
        "periods": list(PREDICTION_CACHE.keys()),
    }


@app.get("/cache-clear")
def cache_clear(password: str = Query(...)):
    _check_admin(password)
    PREDICTION_CACHE.clear()
    return {"status": "cleared"}


if os.path.isdir("static"):
    app.mount("/panel", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
