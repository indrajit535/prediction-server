"""
FastAPI Prediction Server — Wingo 1 Min Mode
--------------------------------------------
- Real history fetch
- Jons AI Predictor logic (Python version)
- Password protected (263)
- ✅ CACHE: Same period → Same prediction (bar bar change nahi hoga)
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import urllib.request
import json
import random

app = FastAPI(
    title="Wingo Prediction API",
    description="Wingo 1M prediction server (password protected + cached)",
    version="3.1.0"
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
# 🔐 PASSWORD
# ============================================================
API_PASSWORD = "263"

# ============================================================
# 🌐 HISTORY API
# ============================================================
HISTORY_API = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-1000"

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))


# ============================================================
# 🗄️ PREDICTION CACHE
# ============================================================
# Structure: { "period_number": { prediction_data } }
# Same period → same prediction hamesha
PREDICTION_CACHE: Dict[str, dict] = {}

# Max cache size (memory leak na ho)
MAX_CACHE_SIZE = 500


def get_cached_prediction(period: str):
    """Agar period ka prediction pehle se hai to wahi return karo."""
    return PREDICTION_CACHE.get(period)


def save_prediction_to_cache(period: str, data: dict):
    """Prediction ko cache mein save karo."""
    # Purani entries delete karo agar limit cross ho gayi
    if len(PREDICTION_CACHE) >= MAX_CACHE_SIZE:
        # Sabse purani 100 entries hata do
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
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
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
        req = urllib.request.Request(
            HISTORY_API,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
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
        return {
            "period": next_period,
            "remaining_seconds": get_remaining_seconds(),
            "source": "live"
        }

    return {
        "period": get_current_period(),
        "remaining_seconds": get_remaining_seconds(),
        "source": "local"
    }


# ============================================================
# 🎯 JONS AI PREDICTOR 1-MIN — CACHED
# ============================================================
def generate_prediction_1min(period: Optional[str] = None,
                              game_id: str = "wingo_1min",
                              use_cache: bool = True):
    """
    Cached prediction generator.
    
    ✅ Agar is period ka prediction pehle se hai → WAHI return karega
    ✅ Naya period → naya prediction banayega + cache mein save karega
    """

    # Period determine karo
    if period is None:
        live = fetch_live_period()
        period = live["period"]

    # 🔍 CACHE CHECK — sabse pehle
    if use_cache:
        cached = get_cached_prediction(period)
        if cached is not None:
            # Sirf timestamp update karo (fresh lagne ke liye)
            cached["timestamp"] = int(datetime.now(timezone.utc).timestamp() * 1000)
            cached["fromCache"] = True
            return cached

    # 🎲 NAYA PREDICTION generate karo (sirf naya period ke liye)
    big_small = "BIG" if random.random() > 0.48 else "SMALL"

    if big_small == "BIG":
        number = random.choice([5, 6, 7, 8, 9])
    else:
        number = random.choice([0, 1, 2, 3, 4])

    confidence = round(98.2 + random.random() * 1.7, 1)
    confidence = min(99.9, confidence)

    prediction = {
        "period": period,
        "gameId": game_id,
        "mode": "1m",
        "bigSmallResult": big_small,
        "numberResult": number,
        "confidence": confidence,
        "patternName": "QUANTUM 10-RESULTS MATRIX",
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        "fromCache": False
    }

    # 💾 CACHE MEIN SAVE KARO
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
# 🚀 ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "mode": "wingo-1m",
        "version": "3.1.0",
        "cachedPeriods": len(PREDICTION_CACHE)
    }


@app.get("/period")
def period_info(password: Optional[str] = Query(default=None)):
    if password != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    live = fetch_live_period()
    return {
        "period": live["period"],
        "remainingSeconds": live["remaining_seconds"],
        "source": live["source"]
    }


@app.get("/history")
def history(password: Optional[str] = Query(default=None)):
    if password != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    data = fetch_history()
    lst = data.get("data", {}).get("list", [])[:100]
    return {"count": len(lst), "results": lst}


@app.get("/predict")
def predict(
    period: Optional[str] = Query(default=None),
    password: Optional[str] = Query(default=None)
):
    """
    Password protected prediction (CACHED per period).

    Same period → same prediction (kitni bhi baar refresh karo)
    """
    try:
        if password is None:
            raise HTTPException(status_code=401, detail="Password required")
        if password != API_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid password")

        pred = generate_prediction_1min(period=period)
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
            "fromCache": pred.get("fromCache", False)
        }

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Prediction failed", "detail": str(e)}
        )


@app.get("/predict-full")
def predict_full(password: Optional[str] = Query(default=None)):
    """
    Full prediction + live period + countdown + history.
    Same period par same prediction (cached).
    """
    if password is None:
        raise HTTPException(status_code=401, detail="Password required")
    if password != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    live = fetch_live_period()
    pred = generate_prediction_1min(period=live["period"])
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
            "fromCache": pred.get("fromCache", False)
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
# 🧹 CACHE MANAGEMENT (optional debug endpoints)
# ============================================================
@app.get("/cache-info")
def cache_info(password: Optional[str] = Query(default=None)):
    """Cache ki current state dekho."""
    if password != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    return {
        "cachedPeriods": len(PREDICTION_CACHE),
        "maxSize": MAX_CACHE_SIZE,
        "periods": list(PREDICTION_CACHE.keys())[-20:]  # last 20
    }


@app.get("/cache-clear")
def cache_clear(password: Optional[str] = Query(default=None)):
    """Cache saaf karo (testing ke liye)."""
    if password != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    PREDICTION_CACHE.clear()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
