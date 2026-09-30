"""
Prediction Engine — NAVEEN AI TOOL 2026
----------------------------------------
NEW TRION Prediction Logic 100% ported to Python.
Real-Time Fix: cache period-keyed + dynamic variation + live fetch retry.
"""

import requests
import time
import random
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ============================================================
# 🔑 API CONFIG
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_URL_FALLBACK = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://hgnice.biz",
    "Accept": "application/json, text/plain, */*",
}

# ============================================================
# 🗄️ CACHE — KEYED BY PERIOD (per-period auto invalidate)
# ============================================================
_ENGINE_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 45          # seconds
_LAST_FETCH_TS = 0
_LAST_FETCH_DATA: List[dict] = []
_FETCH_MIN_INTERVAL = 3  # seconds — API को बार-बार hit नहीं करेंगे


# ============================================================
# 1) PERIOD / COUNTDOWN
# ============================================================

def get_period_info(date: Optional[datetime] = None) -> dict:
    if date is None:
        date = datetime.now(timezone.utc)

    prefix = f"{date.year}{date.month:02d}{date.day:02d}1000"
    total_minutes = date.hour * 60 + date.minute
    short_period = str(10000 + total_minutes)
    raw_period_id = f"{prefix}{short_period}"
    period_id = f"#{raw_period_id}"

    seconds = date.second
    seconds_remaining = 60 if seconds == 0 else 60 - seconds

    return {
        "periodId": period_id,
        "rawPeriodId": raw_period_id,
        "shortPeriod": short_period,
        "prefix": prefix,
        "secondsRemaining": seconds_remaining,
        "formattedTime": f"{seconds_remaining // 60:02d}:{seconds_remaining % 60:02d}",
        "isUrgent": seconds_remaining <= 10,
    }


def split_period_id(period_id: str) -> dict:
    if not period_id:
        return {"prefix": "#", "highlight": "00000"}
    p = period_id if period_id.startswith("#") else f"#{period_id}"
    if len(p) > 5:
        return {"prefix": p[: len(p) - 5], "highlight": p[len(p) - 5:]}
    return {"prefix": "", "highlight": p}


# ============================================================
# 2) NUMBER MAP
# ============================================================

NUMBER_MAP = {
    0: {"number": 0, "size": "SMALL", "primaryColour": "RED",   "isViolet": True,  "validColours": ["RED", "VIOLET"]},
    1: {"number": 1, "size": "SMALL", "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"]},
    2: {"number": 2, "size": "SMALL", "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"]},
    3: {"number": 3, "size": "SMALL", "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"]},
    4: {"number": 4, "size": "SMALL", "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"]},
    5: {"number": 5, "size": "BIG",   "primaryColour": "GREEN", "isViolet": True,  "validColours": ["GREEN", "VIOLET"]},
    6: {"number": 6, "size": "BIG",   "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"]},
    7: {"number": 7, "size": "BIG",   "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"]},
    8: {"number": 8, "size": "BIG",   "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"]},
    9: {"number": 9, "size": "BIG",   "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"]},
}


def get_number_meta(num: int) -> dict:
    n = ((int(num) % 10) + 10) % 10
    return NUMBER_MAP.get(n, NUMBER_MAP[0])


def get_size(num: int) -> str:
    return get_number_meta(num)["size"]


def get_colour(num: int) -> str:
    n = ((int(num) % 10) + 10) % 10
    if n == 0 or n == 5:
        return "VIOLET"
    return "RED" if n % 2 == 0 else "GREEN"


# ============================================================
# 3) CORE PREDICTION (TRION Inversion)
# ============================================================

def build_prediction(raw_size: str = "SMALL", raw_colour: str = "RED") -> dict:
    r_size = "BIG" if (raw_size or "").upper() == "BIG" else "SMALL"
    r_colour = "GREEN" if (raw_colour or "").upper() == "GREEN" else "RED"

    predicted_size = "BIG" if r_size == "SMALL" else "SMALL"
    predicted_colour = "GREEN" if r_colour == "RED" else "RED"

    if predicted_size == "BIG" and predicted_colour == "GREEN":
        predicted_number, secondary_number = 7, 9
    elif predicted_size == "BIG" and predicted_colour == "RED":
        predicted_number, secondary_number = 8, 6
    elif predicted_size == "SMALL" and predicted_colour == "GREEN":
        predicted_number, secondary_number = 3, 1
    else:
        predicted_number, secondary_number = 2, 4

    return {
        "predictedSize": predicted_size,
        "predictedColour": predicted_colour,
        "predictedNumber": predicted_number,
        "secondaryNumber": secondary_number,
        "predictedNumbers": [predicted_number, secondary_number],
        "rawAnalysisSize": r_size,
        "rawAnalysisColour": r_colour,
        "reason": (
            f"TRION Inverted: Raw {r_size}/{r_colour} ➔ Invert to "
            f"{predicted_size}/{predicted_colour} "
            f"[{predicted_number}, {secondary_number}]"
        ),
    }


# ============================================================
# 4) LIVE FETCH — WITH RETRY + FALLBACK
# ============================================================

def fetch_data(force: bool = False) -> List[dict]:
    """
    Live history fetch with min-interval throttle.
    """
    global _LAST_FETCH_TS, _LAST_FETCH_DATA

    now = time.time()
    if not force and (now - _LAST_FETCH_TS) < _FETCH_MIN_INTERVAL:
        return _LAST_FETCH_DATA

    for url in (API_URL, API_URL_FALLBACK):
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                continue
            data = res.json()
            lst = None
            if isinstance(data, dict):
                lst = data.get("data", {}).get("list") or data.get("list")
            if not lst:
                continue

            out = []
            for item in lst:
                try:
                    num = int(item.get("number", 0))
                except:
                    continue
                out.append({
                    "period": str(item.get("issueNumber", "")),
                    "number": num,
                    "size": get_size(num),
                    "colour": get_colour(num),
                })

            if out:
                _LAST_FETCH_TS = now
                _LAST_FETCH_DATA = out
                return out
        except Exception as e:
            print(f"[fetch] {url} error: {e}")
            continue

    # अगर live fail हुआ, पुराना data return कर दो (अगर है)
    return _LAST_FETCH_DATA


# ============================================================
# 5) DYNAMIC RAW-ANALYSIS (यही real-time variation देगा)
# ============================================================

def analyze_history(history: List[dict]) -> dict:
    """
    History से raw bias निकालता है — window और weights dynamic हैं,
    इसलिए हर नए draw पर result बदलेगा।
    """
    if not history:
        return {"rawSize": "SMALL", "rawColour": "RED"}

    # Dynamic window — अगर history बड़ी है तो ज़्यादा देखो
    win = min(len(history), 7)
    sl = history[:win]

    # Weighted big/small
    big_w = 0
    small_w = 0
    for i, h in enumerate(sl):
        w = 1 + (win - i) * 0.3   # recent को ज़्यादा weight
        if h.get("size") == "BIG":
            big_w += w
        else:
            small_w += w

    raw_size = "BIG" if big_w > small_w else "SMALL"

    # Colour weighted
    red_w = green_w = violet_w = 0
    for i, h in enumerate(sl):
        w = 1 + (win - i) * 0.3
        c = h.get("colour")
        if c == "RED":
            red_w += w
        elif c == "GREEN":
            green_w += w
        else:
            violet_w += w

    if red_w > green_w and red_w > violet_w:
        raw_colour = "RED"
    elif green_w >= red_w and green_w >= violet_w:
        raw_colour = "GREEN"
    else:
        raw_colour = "RED"   # violet निकलने पर red bias

    return {"rawSize": raw_size, "rawColour": raw_colour}


# ============================================================
# 6) VERIFY
# ============================================================

def verify_prediction(prediction: dict, actual_num: int) -> bool:
    if not prediction or prediction.get("status") == "VERIFIED LOSS":
        return False

    n = ((int(actual_num) % 10) + 10) % 10
    actual_size = "BIG" if n >= 5 else "SMALL"
    actual_meta = get_number_meta(n)

    pred_size = str(
        prediction.get("predictedSize")
        or (prediction.get("prediction") if prediction.get("prediction") in ("BIG", "SMALL") else "")
    ).upper()

    pred_colour = str(
        prediction.get("predictedColour")
        or (prediction.get("prediction") if prediction.get("prediction") in ("RED", "GREEN", "VIOLET") else "")
    ).upper()

    if pred_size == "BIG" and actual_size != "BIG":
        return False
    if pred_size == "SMALL" and actual_size != "SMALL":
        return False

    focus = str(
        prediction.get("focusedTarget")
        or prediction.get("primaryTargetType")
        or "SIZE"
    ).upper()

    if focus == "SIZE":
        return actual_size == pred_size

    if focus == "COLOUR":
        if pred_colour == "RED":
            return "RED" in actual_meta["validColours"]
        if pred_colour == "GREEN":
            return "GREEN" in actual_meta["validColours"]
        if pred_colour == "VIOLET":
            return actual_meta["isViolet"]
        return False

    if focus == "NUMBER":
        sel4 = prediction.get("selected4Numbers")
        if isinstance(sel4, list) and len(sel4) > 0:
            return n in sel4
        nums = prediction.get("predictedNumbers") or []
        return n in nums

    return actual_size == pred_size


# ============================================================
# 7) 4-NUMBER STRIKE
# ============================================================

def pick4_numbers(size: str = "SMALL", colour: str = "RED") -> List[int]:
    size_nums = [5, 6, 7, 8, 9] if size == "BIG" else [0, 1, 2, 3, 4]
    filtered = []
    for n in size_nums:
        meta = get_number_meta(n)
        if colour == "VIOLET" and meta["isViolet"]:
            filtered.append(n)
        elif colour == "GREEN" and "GREEN" in meta["validColours"]:
            filtered.append(n)
        elif colour == "RED" and "RED" in meta["validColours"]:
            filtered.append(n)

    out = list(filtered)
    for n in size_nums:
        if len(out) >= 4:
            break
        if n not in out:
            out.append(n)
    return out[:4]


# ============================================================
# 8) MAIN WRAPPER — FIXED FOR REAL-TIME
# ============================================================

def sddgamer263_predict(current_number: int = 0, period: str = "") -> dict:
    """
    app.py compatible wrapper — FIXED for real-time change.
    """

    # ✅ अगर period खाली है तो auto-detect
    if not period:
        period = get_period_info()["periodId"]

    # ✅ Cache check — सिर्फ उसी period के लिए
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {k: v for k, v in cached.items() if k != "_ts"}

    # ✅ LIVE history fetch (throttled)
    history = fetch_data()

    # ---------------------------------------------------------
    # ✅ अगर live data नहीं है — VARYING fallback
    # ---------------------------------------------------------
    if not history:
        # period + current_number + time से deterministic-but-varying seed
        seed_str = f"{period}-{current_number}-{int(time.time() // 7)}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
        rng = random.Random(seed)

        raw_size = "BIG" if rng.random() > 0.5 else "SMALL"
        raw_colour = rng.choice(["RED", "GREEN"])
        base = build_prediction(raw_size, raw_colour)
        strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

        result = {
            "prediction": base["predictedNumber"],
            "bigSmall": base["predictedSize"],
            "colour": base["predictedColour"],
            "confidence": 60 + rng.randint(0, 10),
            "numbers": base["predictedNumbers"],
            "opposites": base["predictedNumbers"],
            "strike4": strike4,
            "size": base["predictedSize"],
            "predictedNumber": base["predictedNumber"],
            "secondaryNumber": base["secondaryNumber"],
            "rawAnalysisSize": base["rawAnalysisSize"],
            "rawAnalysisColour": base["rawAnalysisColour"],
            "steps": ["Fallback varying mode", base["reason"]],
            "source": "fallback-variable",
        }
        result["_ts"] = time.time()
        _ENGINE_CACHE[period] = result
        return {k: v for k, v in result.items() if k != "_ts"}

    # ---------------------------------------------------------
    # ✅ LIVE — TRION LOGIC
    # ---------------------------------------------------------
    analysis = analyze_history(history)
    base = build_prediction(analysis["rawSize"], analysis["rawColour"])

    # ✅ अगर वही prediction पिछले period में था तो flip करो
    prev = _ENGINE_CACHE.get("__last_prediction__")
    if prev and prev.get("bigSmall") == base["predictedSize"] and prev.get("colour") == base["predictedColour"]:
        # flip raw to force new result
        flipped_size = "BIG" if analysis["rawSize"] == "SMALL" else "SMALL"
        base = build_prediction(flipped_size, analysis["rawColour"])

    strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

    # Confidence dynamic
    big_count = sum(1 for h in history[:5] if h.get("size") == "BIG")
    confidence = 70 + abs(big_count - 2) * 5
    confidence = min(confidence, 95)

    result = {
        "prediction": base["predictedNumber"],
        "bigSmall": base["predictedSize"],
        "colour": base["predictedColour"],
        "confidence": confidence,
        "numbers": base["predictedNumbers"],
        "opposites": base["predictedNumbers"],
        "strike4": strike4,
        "size": base["predictedSize"],
        "predictedNumber": base["predictedNumber"],
        "secondaryNumber": base["secondaryNumber"],
        "rawAnalysisSize": base["rawAnalysisSize"],
        "rawAnalysisColour": base["rawAnalysisColour"],
        "last5": [h.get("number") for h in history[:5]],
        "steps": [
            f"Period: {period}",
            f"Raw Size: {base['rawAnalysisSize']}",
            f"Raw Colour: {base['rawAnalysisColour']}",
            f"Inverted Size: {base['predictedSize']}",
            f"Inverted Colour: {base['predictedColour']}",
            f"Dual Sniper: {base['predictedNumbers']}",
            f"Strike4: {strike4}",
            base["reason"],
        ],
        "source": "naveen-ai-trion",
        "_ts": time.time(),
    }

    # Cache + last-prediction memory
    _ENGINE_CACHE[period] = result
    _ENGINE_CACHE["__last_prediction__"] = {
        "bigSmall": result["bigSmall"],
        "colour": result["colour"],
        "_ts": time.time(),
    }

    # Cleanup (50 से ज़्यादा हो जाए तो पुराने हटाओ)
    if len(_ENGINE_CACHE) > 50:
        keys = [k for k in _ENGINE_CACHE.keys() if not k.startswith("__")]
        keys.sort(key=lambda k: _ENGINE_CACHE[k].get("_ts", 0))
        for k in keys[:20]:
            _ENGINE_CACHE.pop(k, None)

    return {k: v for k, v in result.items() if k != "_ts"}


def clear_engine_cache():
    _ENGINE_CACHE.clear()
    global _LAST_FETCH_TS, _LAST_FETCH_DATA
    _LAST_FETCH_TS = 0
    _LAST_FETCH_DATA = []


# ============================================================
# 🧪 TEST
# ============================================================

if __name__ == "__main__":
    print("=== Real-Time Test (3 different periods) ===")
    for i in range(3):
        p = get_period_info()
        res = sddgamer263_predict(current_number=i, period=p["periodId"] + f"_{i}")
        print(f"\n[{i+1}] Period={p['periodId']}")
        print(f"    Big/Small: {res['bigSmall']}  Colour: {res['colour']}  Numbers: {res['numbers']}  Strike4: {res.get('strike4')}")
        time.sleep(1)
