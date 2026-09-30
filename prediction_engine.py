"""
Prediction Engine — NAVEEN AI TOOL 2026
----------------------------------------
TRION Logic + Real-Time Anti-Repeat Engine
"""

import requests
import time
import random
import hashlib
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ============================================================
# 🔑 API
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://hgnice.biz",
    "Accept": "application/json, text/plain, */*",
}

# ============================================================
# 🗄️ CACHE
# ============================================================
_ENGINE_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 45

# Anti-repeat memory — पिछले 5 predictions याद रखो
_RECENT_PREDICTIONS: deque = deque(maxlen=5)

# API throttle
_LAST_FETCH_TS = 0
_LAST_FETCH_DATA: List[dict] = []
_FETCH_MIN_INTERVAL = 2


# ============================================================
# 1) PERIOD
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
    if n in (0, 5):
        return "VIOLET"
    return "RED" if n % 2 == 0 else "GREEN"


# ============================================================
# 3) FETCH (throttled)
# ============================================================

def fetch_data(force: bool = False) -> List[dict]:
    global _LAST_FETCH_TS, _LAST_FETCH_DATA
    now = time.time()
    if not force and (now - _LAST_FETCH_TS) < _FETCH_MIN_INTERVAL:
        return _LAST_FETCH_DATA
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=8)
        data = res.json()
        lst = None
        if isinstance(data, dict):
            lst = data.get("data", {}).get("list") or data.get("list")
        if lst:
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
        print(f"[fetch] error: {e}")
    return _LAST_FETCH_DATA


# ============================================================
# 4) 🔥 DYNAMIC ANALYZER — यही असली fix है
# ============================================================

def analyze_history(history: List[dict], period_seed: str = "") -> dict:
    """
    🔥 अब हर बार dynamic result देगा।
    period_seed (period ID) को hash में mix करके unique raw bias बनाता है।
    """
    if not history:
        # Period seed से ही bias निकालो — varying
        seed = int(hashlib.md5((period_seed or str(time.time())).encode()).hexdigest(), 16)
        rng = random.Random(seed)
        return {
            "rawSize": rng.choice(["BIG", "SMALL"]),
            "rawColour": rng.choice(["RED", "GREEN"]),
        }

    # --- Step 1: Weighted last-7 analysis ---
    win = min(len(history), 7)
    sl = history[:win]

    big_w = small_w = 0.0
    red_w = green_w = violet_w = 0.0

    for i, h in enumerate(sl):
        w = 1.0 + (win - i) * 0.4
        if h.get("size") == "BIG":
            big_w += w
        else:
            small_w += w

        c = h.get("colour")
        if c == "RED":
            red_w += w
        elif c == "GREEN":
            green_w += w
        else:
            violet_w += w

    # --- Step 2: Recent 3 streak override ---
    recent3 = [h.get("size") for h in history[:3]]
    if recent3.count("BIG") >= 2:
        big_w *= 1.5      # streak → same side को boost
    elif recent3.count("SMALL") >= 2:
        small_w *= 1.5

    # --- Step 3: Period-seed dynamic jitter (यहीं magic है) ---
    seed_src = (period_seed or "") + "|" + "".join(str(h.get("number", 0)) for h in history[:10])
    seed = int(hashlib.md5(seed_src.encode()).hexdigest(), 16)
    rng = random.Random(seed)

    # ±18% jitter — ताकि हर period पर bias बदले
    jitter_size = 1.0 + rng.uniform(-0.18, 0.18)
    jitter_colour = 1.0 + rng.uniform(-0.18, 0.18)

    big_w *= jitter_size
    small_w *= jitter_size
    red_w *= jitter_colour
    green_w *= jitter_colour

    raw_size = "BIG" if big_w > small_w else "SMALL"

    if red_w >= green_w and red_w >= violet_w:
        raw_colour = "RED"
    elif green_w >= red_w and green_w >= violet_w:
        raw_colour = "GREEN"
    else:
        raw_colour = "RED"

    return {"rawSize": raw_size, "rawColour": raw_colour}


# ============================================================
# 5) BUILD PREDICTION (Inversion)
# ============================================================

def build_prediction(raw_size: str = "SMALL", raw_colour: str = "RED") -> dict:
    r_size = "BIG" if (raw_size or "").upper() == "BIG" else "SMALL"
    r_colour = "GREEN" if (raw_colour or "").upper() == "GREEN" else "RED"

    predicted_size = "BIG" if r_size == "SMALL" else "SMALL"
    predicted_colour = "GREEN" if r_colour == "RED" else "RED"

    if predicted_size == "BIG" and predicted_colour == "GREEN":
        pn, sn = 7, 9
    elif predicted_size == "BIG" and predicted_colour == "RED":
        pn, sn = 8, 6
    elif predicted_size == "SMALL" and predicted_colour == "GREEN":
        pn, sn = 3, 1
    else:
        pn, sn = 2, 4

    return {
        "predictedSize": predicted_size,
        "predictedColour": predicted_colour,
        "predictedNumber": pn,
        "secondaryNumber": sn,
        "predictedNumbers": [pn, sn],
        "rawAnalysisSize": r_size,
        "rawAnalysisColour": r_colour,
        "reason": f"TRION: Raw {r_size}/{r_colour} ➔ Invert {predicted_size}/{predicted_colour} [{pn},{sn}]",
    }


# ============================================================
# 6) 🔥 ANTI-REPEAT — यह भी ज़रूरी है
# ============================================================

def force_change_if_repeated(base: dict, period: str) -> dict:
    """
    अगर पिछले 2 predictions जैसा ही है तो ज़बरदस्ती flip करो।
    """
    sig = f"{base['predictedSize']}|{base['predictedColour']}"

    # पिछले 2 signatures
    last2 = list(_RECENT_PREDICTIONS)[-2:]
    if len(last2) >= 2 and all(s == sig for s in last2):
        # Flip raw to force new result
        new_raw_size = "BIG" if base["rawAnalysisSize"] == "SMALL" else "SMALL"
        new_raw_colour = "GREEN" if base["rawAnalysisColour"] == "RED" else "RED"
        base = build_prediction(new_raw_size, new_raw_colour)
        sig = f"{base['predictedSize']}|{base['predictedColour']}"

    # Memory में add
    _RECENT_PREDICTIONS.append(sig)
    return base


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
# 8) MAIN WRAPPER — FIXED
# ============================================================

def sddgamer263_predict(current_number: int = 0, period: str = "") -> dict:
    if not period:
        period = get_period_info()["periodId"]

    # Cache check — same period पर same result (यह सही है)
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {k: v for k, v in cached.items() if k != "_ts"}

    history = fetch_data()

    # ✅ analyze_history में period_seed pass करो — यही असली fix है
    analysis = analyze_history(history, period_seed=period)
    base = build_prediction(analysis["rawSize"], analysis["rawColour"])

    # ✅ Anti-repeat force flip
    base = force_change_if_repeated(base, period)

    strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

    big_count = sum(1 for h in history[:5] if h.get("size") == "BIG") if history else 2
    confidence = min(70 + abs(big_count - 2) * 5, 95)

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
        "last5": [h.get("number") for h in history[:5]] if history else [],
        "steps": [
            f"Period: {period}",
            f"Raw: {base['rawAnalysisSize']}/{base['rawAnalysisColour']}",
            f"Final: {base['predictedSize']}/{base['predictedColour']}",
            f"Sniper: {base['predictedNumbers']}",
            f"Strike4: {strike4}",
        ],
        "source": "naveen-ai-trion" if history else "fallback-variable",
        "_ts": time.time(),
    }

    _ENGINE_CACHE[period] = result

    # Cleanup
    if len(_ENGINE_CACHE) > 50:
        keys = sorted(_ENGINE_CACHE.keys(), key=lambda k: _ENGINE_CACHE[k].get("_ts", 0))
        for k in keys[:20]:
            _ENGINE_CACHE.pop(k, None)

    return {k: v for k, v in result.items() if k != "_ts"}


def clear_engine_cache():
    _ENGINE_CACHE.clear()
    _RECENT_PREDICTIONS.clear()
    global _LAST_FETCH_TS, _LAST_FETCH_DATA
    _LAST_FETCH_TS = 0
    _LAST_FETCH_DATA = []


# ============================================================
# 🧪 TEST — 6 different periods, देखो बदल रहा है या नहीं
# ============================================================

if __name__ == "__main__":
    print("=== Anti-Repeat Test (6 periods) ===\n")
    for i in range(6):
        period = f"#202609301000100{i}"
        res = sddgamer263_predict(current_number=i, period=period)
        print(f"[{i+1}] Period={period[-5:]}")
        print(f"     Big/Small={res['bigSmall']:5s}  Colour={res['colour']:5s}  Numbers={res['numbers']}  Strike4={res['strike4']}")
        time.sleep(0.5)
