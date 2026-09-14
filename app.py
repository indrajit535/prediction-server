"""
FastAPI Prediction Server — Wingo 1 Min Mode
--------------------------------------------
- Real history fetch from sky-predictor API
- Jons AI Predictor logic (Python version)
- Password protected (263)
- Real-time period + countdown
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timezone, timedelta
import urllib.request
import json
import random

app = FastAPI(
    title="Wingo Prediction API",
    description="Wingo 1M prediction server (password protected)",
    version="3.0.0"
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
# 🕐 TIME HELPERS (JS ka getISTTime equivalent)
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
    """Fallback local period generator (1 min mode)."""
    t = get_ist_time()
    duration = 60
    period_number = (t["total_seconds"] // duration) + 1
    padded = str(period_number).zfill(4)
    return f"{t['year']}{t['month']:02d}{t['day']:02d}1000{padded}"


def get_remaining_seconds():
    """Kitne second bache hain current period khatam hone mein."""
    t = get_ist_time()
    elapsed = t["total_seconds"] % 60
    return 60 - elapsed


# ============================================================
# 🌐 LIVE HISTORY FETCH
# ============================================================
def fetch_history():
    """Sky-predictor API se live history fetch karo."""
    try:
        req = urllib.request.Request(
            HISTORY_API,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return data
    except Exception as e:
        return {"code": -1, "msg": str(e), "data": {"list": []}}


def fetch_live_period():
    """
    Live period + remaining seconds.
    History API se latest issueNumber leta hai + 1 karta hai (next period).
    """
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
# 🎯 JONS AI PREDICTOR 1-MIN (Python version)
# ============================================================
def generate_prediction_1min(period: Optional[str] = None, game_id: str = "wingo_1min"):
    """
    Aapka original JS logic ka Python conversion:
      - BIG/SMALL: 48% BIG, 52% SMALL
      - BIG → 5,6,7,8,9 | SMALL → 0,1,2,3,4
      - Confidence: 98.2 - 99.9
    """
    if period is None:
        live = fetch_live_period()
        period = live["period"]

    # Step 1: BIG ya SMALL
    big_small = "BIG" if random.random() > 0.48 else "SMALL"

    # Step 2: Number
    if big_small == "BIG":
        number = random.choice([5, 6, 7, 8, 9])
    else:
        number = random.choice([0, 1, 2, 3, 4])

    # Step 3: Confidence
    confidence = round(98.2 + random.random() * 1.7, 1)
    confidence = min(99.9, confidence)

    return {
        "period": period,
        "gameId": game_id,
        "mode": "1m",
        "bigSmallResult": big_small,
        "numberResult": number,
        "confidence": confidence,
        "patternName": "QUANTUM 10-RESULTS MATRIX",
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
    }


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
    return {"status": "online", "mode": "wingo-1m", "version": "3.0.0"}


@app.get("/period")
def period_info(password: Optional[str] = Query(default=None)):
    """Real-time period + countdown (password protected)."""
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
    """Last 100 results from live API."""
    if password != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    data = fetch_history()
    lst = data.get("data", {}).get("list", [])[:100]
    return {"count": len(lst), "results": lst}


@app.get("/predict")
def predict(
    period: Optional[str] = Query(default=None, description="Target period (optional)"),
    password: Optional[str] = Query(default=None, description="API password")
):
    """
    Password protected prediction.

    Usage:
      /predict?password=263
      /predict?period=20260914100010530&password=263
    """
    try:
        # Password check
        if password is None:
            raise HTTPException(status_code=401, detail="Password required")
        if password != API_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid password")

        # Prediction generate
        pred = generate_prediction_1min(period=period)
        images = get_prediction_images(pred)

        return {
            "prediction": pred["bigSmallResult"],   # "BIG" | "SMALL" (simple)
            "period": pred["period"],
            "number": pred["numberResult"],
            "confidence": pred["confidence"],
            "mode": pred["mode"],
            "patternName": pred["patternName"],
            "bigSmallImage": images["bigSmallImage"],
            "numberImage": images["numberImage"],
            "timestamp": pred["timestamp"]
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
    Full prediction + live period + countdown + last 10 history.
    Ek hi call mein sab kuch — mobile app ke liye best.
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
            "numberImage": images["numberImage"]
        },
        "live": {
            "period": live["period"],
            "remainingSeconds": live["remaining_seconds"],
            "source": live["source"]
        },
        "history": last10,
        "timestamp": pred["timestamp"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
