"""
FastAPI Prediction Server — Wingo 1 Min Mode (v4.0)
----------------------------------------------------
✅ Firebase Integration (Key validation, Server status, Withdrawal)
✅ Admin Panel Control
✅ User Panel Auto Login/Logout
✅ New SDDGAMER263 Prediction Algorithm
✅ Same period → Same prediction (cached)
"""

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict
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
)
from prediction_engine import sddgamer263_predict

app = FastAPI(
    title="Wingo Prediction API",
    description="Wingo 1M prediction server with Firebase auth + new algorithm",
    version="4.0.0"
)

# CORS enable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 🔐 ADMIN PASSWORD (Firebase se bhi control kar sakte ho)
# ============================================================
ADMIN_PASSWORD = "263@"   # Admin panel login password


# ============================================================
# 🌐 HISTORY API
# ============================================================
HISTORY_API = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-1000"

IST = timezone(timedelta(hours=5, minutes=30))


# ============================================================
# 🗄️ PREDICTION CACHE
# ============================================================
PREDICTION_CACHE: Dict[str, dict] = {}
MAX_CACHE_SIZE = 500


def get_cached_prediction(period: str):
    return PREDICTION_CACHE.get(period)


def save_prediction_to_cache(period: str, data: dict):
    if len(PREDICTION_CACHE) >= MAX_CACHE_SIZE:
        old_keys = list(PREDICTION_CACHE.keys())[:100]
        for k in old_keys:
            del PREDICTION_CACHE[k]
    PREDICTION_CACHE[period] = data


# ============================================================
# 🕐 TIME HELPERS
# ============================================================
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


# ============================================================
# 🌐 LIVE HISTORY FETCH
# ============================================================
def fetch_history():
    try:
        req = urllib.request.Request(HISTORY_API, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"code": -1, "msg": str(e), "data": {"list": []}}


def fetch_live_period():
    data = fetch_history()
    lst = data.get("data", {}).get("list", [])
    if lst and lst[0].get("issueNumber"):
        current_issue = str(lst[0]["issueNumber"])
        try:
            next_period = str(int(current_issue) + 1)
        except ValueError:
            next_period = get_current_period()
        return {"period": next_period, "remaining_seconds": get_remaining_seconds(), "source": "live"}
    return {"period": get_current_period(), "remaining_seconds": get_remaining_seconds(), "source": "local"}


def get_last_result_number():
    """Last result ka number nikalo (0-9)."""
    data = fetch_history()
    lst = data.get("data", {}).get("list", [])
    if lst and lst[0].get("number") is not None:
        try:
            return int(lst[0]["number"]) % 10
        except (ValueError, TypeError):
            pass
    return random.randint(0, 9)


# ============================================================
# 🎯 NEW PREDICTION (SDDGAMER263) — CACHED
# ============================================================
def generate_prediction(period: Optional[str] = None,
                        game_id: str = "wingo_1min",
                        use_cache: bool = True):
    if period is None:
        live = fetch_live_period()
        period = live["period"]

    # Cache check
    if use_cache:
        cached = get_cached_prediction(period)
        if cached is not None:
            cached["timestamp"] = int(time.time() * 1000)
            cached["fromCache"] = True
            return cached

    # New prediction using SDDGAMER263
    last_number = get_last_result_number()
    result = sddgamer263_predict(current_number=last_number, period=period)

    prediction = {
        "period": period,
        "gameId": game_id,
        "mode": "1m",
        "bigSmallResult": result["bigSmall"],
        "numberResult": result["prediction"],
        "confidence": result["confidence"],
        "patternName": "SDDGAMER263 QUANTUM MATRIX",
        "steps": result["steps"],
        "inputNumber": last_number,
        "timestamp": int(time.time() * 1000),
        "fromCache": False
    }

    if use_cache:
        save_prediction_to_cache(period, prediction)

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
    return {
        "bigSmallImage": ASSETS["bigSmall"][prediction["bigSmallResult"]],
        "numberImage": ASSETS["numbers"][prediction["numberResult"]]
    }


# ============================================================
# 🔐 KEY VALIDATION DEPENDENCY
# ============================================================
def validate_key_or_raise(key: str):
    """Key validate karo, warna HTTPException raise karo."""
    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])
    return status["data"]


def check_server_online_or_raise():
    """Server status check karo."""
    status = get_server_status()
    if not status["online"]:
        raise HTTPException(status_code=503, detail=status["message"])
    return status


# ============================================================
# 🚀 PUBLIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "mode": "wingo-1m",
        "version": "4.0.0",
        "cachedPeriods": len(PREDICTION_CACHE)
    }


@app.get("/firebase-config")
def firebase_config():
    """Client-side Firebase config (public)."""
    return FIREBASE_WEB_CONFIG


@app.get("/server-status")
def server_status():
    """Server on/off status check."""
    return get_server_status()


# ============================================================
# 🔑 KEY AUTH ENDPOINTS
# ============================================================

@app.post("/auth/login")
async def auth_login(request: Request):
    """
    User login with key.
    Body: {"key": "USER_KEY"}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    key = body.get("key", "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key required")

    # Server status check
    srv = get_server_status()
    if not srv["online"]:
        raise HTTPException(status_code=503, detail=srv["message"])

    # Key validation
    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(status_code=403, detail=status["reason"])

    data = status["data"]
    return {
        "success": True,
        "message": "Login successful",
        "key": key,
        "balance": float(data.get("balance", 0)),
        "expiry": data.get("expiry", 0),
        "createdAt": data.get("createdAt", 0)
    }


@app.get("/auth/check")
def auth_check(key: str = Query(...)):
    """
    Har 3 sec check ke liye — key active hai ya nahi + server status.
    """
    srv = get_server_status()
    if not srv["online"]:
        return {
            "active": False,
            "serverOnline": False,
            "message": srv["message"]
        }

    status = check_key_active(key)
    data = status["data"] or {}
    return {
        "active": status["active"],
        "serverOnline": True,
        "reason": status["reason"],
        "balance": float(data.get("balance", 0)),
        "expiry": data.get("expiry", 0)
    }


# ============================================================
# 🎯 PREDICTION ENDPOINTS (Key protected)
# ============================================================

@app.get("/period")
def period_info(key: str = Query(...)):
    validate_key_or_raise(key)
    live = fetch_live_period()
    return {
        "period": live["period"],
        "remainingSeconds": live["remaining_seconds"],
        "source": live["source"]
    }


@app.get("/history")
def history(key: str = Query(...)):
    validate_key_or_raise(key)
    data = fetch_history()
    lst = data.get("data", {}).get("list", [])[:100]
    return {"count": len(lst), "results": lst}


@app.get("/predict")
def predict(
    period: Optional[str] = Query(default=None),
    key: str = Query(...)
):
    validate_key_or_raise(key)
    check_server_online_or_raise()

    pred = generate_prediction(period=period)
    images = get_prediction_images(pred)

    return {
        "prediction": pred["bigSmallResult"],
        "period": pred["period"],
        "number": pred["numberResult"],
        "confidence": pred["confidence"],
        "mode": pred["mode"],
        "patternName": pred["patternName"],
        "bigSmallImage": images["bigSmallImage"],
        "numberImage": images["numberImage"],
        "timestamp": pred["timestamp"],
        "fromCache": pred.get("fromCache", False),
        "steps": pred.get("steps", [])
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
            "confidence": pred["confidence"],
            "period": pred["period"],
            "patternName": pred["patternName"],
            "bigSmallImage": images["bigSmallImage"],
            "numberImage": images["numberImage"],
            "fromCache": pred.get("fromCache", False),
            "steps": pred.get("steps", [])
        },
        "live": {
            "period": live["period"],
            "remainingSeconds": live["remaining_seconds"],
            "source": live["source"]
        },
        "history": last10,
        "timestamp": pred["timestamp"]
    }


# ============================================================
# 💰 WITHDRAWAL ENDPOINTS (User)
# ============================================================

@app.get("/withdrawal/balance")
def withdrawal_balance(key: str = Query(...)):
    validate_key_or_raise(key)
    return {"balance": get_user_balance(key)}


@app.post("/withdrawal/request")
async def withdrawal_request(request: Request):
    """
    Body: {"key": "...", "amount": 100, "method": "UPI", "account": "user@upi"}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    key = body.get("key", "").strip()
    amount = float(body.get("amount", 0))
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
        "status": "pending"
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
    """Saari keys list karo."""
    _check_admin(password)
    from firebase_config import _rest_get
    data = _rest_get("keys") or {}
    keys = []
    for k, v in data.items():
        keys.append({"key": k, **v})
    keys.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return {"count": len(keys), "keys": keys}


@app.post("/admin/keys/create")
async def admin_create_key(request: Request):
    """
    Body: {"password": "263", "key": "...", "durationDays": 30, "balance": 0}
    Agar key na diya jaaye to auto-generate karega.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))

    key = body.get("key", "").strip()
    if not key:
        key = "MAXMOD" + "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=10))

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
        "balance": balance
    }

    from firebase_config import _rest_put
    result = _rest_put(f"keys/{key}", data)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create key")

    return {"success": True, "key": key, "data": data}


@app.post("/admin/keys/delete")
async def admin_delete_key(request: Request):
    """Body: {"password": "263", "key": "..."}"""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    key = body.get("key", "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key required")

    from firebase_config import _rest_patch
    result = _rest_patch(f"keys/{key}", {"active": False, "deleted": True})
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to delete key")

    return {"success": True, "message": f"Key {key} deleted"}


@app.post("/admin/keys/toggle")
async def admin_toggle_key(request: Request):
    """Body: {"password": "263", "key": "...", "active": true/false}"""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    key = body.get("key", "").strip()
    active = bool(body.get("active", True))

    from firebase_config import _rest_patch
    result = _rest_patch(f"keys/{key}", {"active": active})
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update key")

    return {"success": True, "key": key, "active": active}


@app.post("/admin/keys/balance")
async def admin_update_balance(request: Request):
    """Body: {"password": "263", "key": "...", "balance": 500}"""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    key = body.get("key", "").strip()
    balance = float(body.get("balance", 0))

    ok = update_user_balance(key, balance)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update balance")

    return {"success": True, "key": key, "balance": balance}


@app.post("/admin/server/toggle")
async def admin_server_toggle(request: Request):
    """
    Body: {"password": "263", "online": true/false, "message": "..."}
    Server on/off karo.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    online = bool(body.get("online", True))
    message = body.get("message", "Server is running" if online else "Server is under maintenance")

    from firebase_config import _rest_put
    result = _rest_put("server_status", {
        "online": online,
        "message": message,
        "updatedAt": int(time.time() * 1000)
    })
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to update server status")

    return {"success": True, "online": online, "message": message}


@app.get("/admin/withdrawals")
def admin_list_withdrawals(password: str = Query(...)):
    """Saari withdrawal requests list karo."""
    _check_admin(password)
    from firebase_config import _rest_get
    data = _rest_get("withdrawals") or {}
    reqs = list(data.values())
    reqs.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return {"count": len(reqs), "requests": reqs}


@app.post("/admin/withdrawals/action")
async def admin_withdrawal_action(request: Request):
    """
    Body: {"password": "263", "requestId": "WD...", "action": "accept"/"reject"}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    _check_admin(body.get("password", ""))
    req_id = body.get("requestId", "").strip()
    action = body.get("action", "").strip().lower()

    if action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")

    from firebase_config import _rest_get, _rest_patch
    req = _rest_get(f"withdrawals/{req_id}")
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    new_status = "accepted" if action == "accept" else "rejected"
    _rest_patch(f"withdrawals/{req_id}", {
        "status": new_status,
        "processedAt": int(time.time() * 1000)
    })

    # Agar accept hua to balance deduct karo
    if action == "accept":
        key = req.get("key")
        amount = float(req.get("amount", 0))
        current_balance = get_user_balance(key)
        new_balance = max(0, current_balance - amount)
        update_user_balance(key, new_balance)

    return {"success": True, "requestId": req_id, "status": new_status}


@app.get("/admin/stats")
def admin_stats(password: str = Query(...)):
    """Admin dashboard stats."""
    _check_admin(password)
    from firebase_config import _rest_get
    keys_data = _rest_get("keys") or {}
    wd_data = _rest_get("withdrawals") or {}
    srv = get_server_status()

    total_keys = len(keys_data)
    active_keys = sum(1 for v in keys_data.values() if v.get("active") and not v.get("deleted"))
    total_balance = sum(float(v.get("balance", 0)) for v in keys_data.values())

    pending_wds = sum(1 for v in wd_data.values() if v.get("status") == "pending")
    accepted_wds = sum(1 for v in wd_data.values() if v.get("status") == "accepted")
    rejected_wds = sum(1 for v in wd_data.values() if v.get("status") == "rejected")

    return {
        "totalKeys": total_keys,
        "activeKeys": active_keys,
        "totalBalance": total_balance,
        "serverOnline": srv["online"],
        "serverMessage": srv["message"],
        "withdrawals": {
            "pending": pending_wds,
            "accepted": accepted_wds,
            "rejected": rejected_wds
        }
    }


# ============================================================
# 🧹 CACHE MANAGEMENT
# ============================================================

@app.get("/cache-info")
def cache_info(password: str = Query(...)):
    _check_admin(password)
    return {
        "cachedPeriods": len(PREDICTION_CACHE),
        "maxSize": MAX_CACHE_SIZE,
        "periods": list(PREDICTION_CACHE.keys())[-20:]
    }


@app.get("/cache-clear")
def cache_clear(password: str = Query(...)):
    _check_admin(password)
    PREDICTION_CACHE.clear()
    return {"status": "cleared"}


# ============================================================
# 🖼️ STATIC PANELS
# ============================================================
# Agar static folder exist kare to mount karo
if os.path.isdir("static"):
    app.mount("/panel", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
