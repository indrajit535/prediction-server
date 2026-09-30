"""
TRION Prediction Engine — NAVEEN AI TOOL 2026
---------------------------------------------
100% JS TRION logic ported to Python.
✅ SIZE / COLOUR / NUMBER focus rotation ADDED (JS same).
"""

import requests
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ============================================================
# 🔑 API CONFIG
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hgnice.biz",
}

# ============================================================
# 🗄️ CACHE + FOCUS MEMORY
# ============================================================
_ENGINE_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 50

# 🔥 JS rotation state — हर scan पर focus बदलता है
_FOCUS_STATE = {
    "current": "SIZE",           # SIZE | COLOUR | NUMBER
    "rotation_index": 0,
    "rotation_cycle": ["SIZE", "COLOUR", "NUMBER"],  # JS order
    "last_period": "",
}

# 🔥 Prediction history memory (anti-repeat)
_LAST_PREDICTION = {"size": None, "colour": None, "focus": None}


# ============================================================
# 1) PERIOD / COUNTDOWN HELPERS
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
# 2) NUMBER → SIZE / COLOUR MAP
# ============================================================

NUMBER_MAP = {
    0: {"number": 0, "size": "SMALL", "primaryColour": "RED",   "isViolet": True,  "validColours": ["RED", "VIOLET"],   "label": "0 (Small • Red/Violet)"},
    1: {"number": 1, "size": "SMALL", "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"],           "label": "1 (Small • Green)"},
    2: {"number": 2, "size": "SMALL", "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"],             "label": "2 (Small • Red)"},
    3: {"number": 3, "size": "SMALL", "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"],           "label": "3 (Small • Green)"},
    4: {"number": 4, "size": "SMALL", "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"],             "label": "4 (Small • Red)"},
    5: {"number": 5, "size": "BIG",   "primaryColour": "GREEN", "isViolet": True,  "validColours": ["GREEN", "VIOLET"], "label": "5 (Big • Green/Violet)"},
    6: {"number": 6, "size": "BIG",   "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"],             "label": "6 (Big • Red)"},
    7: {"number": 7, "size": "BIG",   "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"],           "label": "7 (Big • Green)"},
    8: {"number": 8, "size": "BIG",   "primaryColour": "RED",   "isViolet": False, "validColours": ["RED"],             "label": "8 (Big • Red)"},
    9: {"number": 9, "size": "BIG",   "primaryColour": "GREEN", "isViolet": False, "validColours": ["GREEN"],           "label": "9 (Big • Green)"},
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
# 3) INVERTED COUNTER-RESONANCE (CORE LOGIC)
# ============================================================

def build_prediction(raw_size: str = "SMALL", raw_colour: str = "RED") -> dict:
    """
    JS buildPrediction() 100% port.
    """
    r_size   = "BIG"   if (raw_size   or "").upper() == "BIG"   else "SMALL"
    r_colour = "GREEN" if (raw_colour or "").upper() == "GREEN" else "RED"

    predicted_size   = "BIG"   if r_size   == "SMALL" else "SMALL"
    predicted_colour = "GREEN" if r_colour == "RED"   else "RED"

    if predicted_size == "BIG" and predicted_colour == "GREEN":
        pn, sn = 7, 9
    elif predicted_size == "BIG" and predicted_colour == "RED":
        pn, sn = 8, 6
    elif predicted_size == "SMALL" and predicted_colour == "GREEN":
        pn, sn = 3, 1
    else:
        pn, sn = 2, 4

    reason = (
        f"TRION Inverted Counter-Resonance: Raw {r_size}/{r_colour} ➔ "
        f"Invert to {predicted_size}/{predicted_colour} [{pn}, {sn}]"
    )

    return {
        "predictedSize": predicted_size,
        "predictedColour": predicted_colour,
        "predictedNumber": pn,
        "secondaryNumber": sn,
        "predictedNumbers": [pn, sn],
        "prediction": predicted_size,
        "rawAnalysisSize": r_size,
        "rawAnalysisColour": r_colour,
        "reason": reason,
    }


# ============================================================
# 4) 🔥 FOCUS ROTATION — यही JS वाला system है
# ============================================================

def rotate_focus(period: str) -> str:
    """
    JS में हर नए period पर focusedTarget rotate होता है:
    SIZE → COLOUR → NUMBER → SIZE → ...

    यही logic यहाँ port किया गया है।
    """
    # अगर नया period है तो rotation advance करो
    if _FOCUS_STATE["last_period"] != period:
        _FOCUS_STATE["rotation_index"] = (_FOCUS_STATE["rotation_index"] + 1) % 3
        _FOCUS_STATE["current"] = _FOCUS_STATE["rotation_cycle"][_FOCUS_STATE["rotation_index"]]
        _FOCUS_STATE["last_period"] = period

    return _FOCUS_STATE["current"]


def get_current_focus() -> str:
    return _FOCUS_STATE["current"]


def force_set_focus(focus: str):
    """Manual override (जैसे JS में onSelectTargetType)."""
    focus = (focus or "").upper()
    if focus in ("SIZE", "COLOUR", "NUMBER"):
        _FOCUS_STATE["current"] = focus
        _FOCUS_STATE["rotation_index"] = _FOCUS_STATE["rotation_cycle"].index(focus)


# ============================================================
# 5) FULL PREDICTION GENERATOR (JS: generatePrediction)
# ============================================================

def generate_prediction(
    engine: str = "2000 LOGIC",
    target_mode: str = "AUTO_OPTIMAL",
    raw_size: str = "SMALL",
    raw_colour: str = "RED",
    focused_target: str = "SIZE",
    signal_strength: int = 96,
    risk_level: str = "LOW",
) -> dict:
    """JS generatePrediction() 100% port + focusedTarget."""
    now = datetime.now(timezone.utc)
    period = get_period_info(now)
    base = build_prediction(raw_size, raw_colour)

    return {
        "id": f"pred_{int(time.time() * 1000)}",
        "roundId": period["periodId"],
        "timestamp": now.strftime("%I:%M %p"),
        "engine": engine,
        "prediction": base["predictedSize"],
        "primaryTargetType": focused_target,
        "targetMode": target_mode,
        "focusedTarget": focused_target,

        "predictedSize": base["predictedSize"],
        "predictedColour": base["predictedColour"],
        "predictedNumber": base["predictedNumber"],
        "secondaryNumber": base["secondaryNumber"],
        "predictedNumbers": base["predictedNumbers"],
        "selected4Numbers": base["predictedNumbers"],

        "rawAnalysisSize": base["rawAnalysisSize"],
        "rawAnalysisColour": base["rawAnalysisColour"],

        "signalStrength": signal_strength,
        "cycleLocked": True,
        "isSkip": False,
        "riskLevel": risk_level,
        "reason": base["reason"],
        "activeLogicsMatched": 48,
        "totalLogicsEvaluated": 60,
        "status": "UNVERIFIED",
        "dataSampleRounds": 1000,
    }


# ============================================================
# 6) VERIFICATION (JS: verifyPrediction)
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
# 8) NODE MATRIX
# ============================================================

NODE_MATRIX = [
    {"num": 0, "prob": 12, "type": "blue",   "label": "Violet/Red (0)"},
    {"num": 1, "prob": 8,  "type": "green",  "label": "Green (1)"},
    {"num": 2, "prob": 6,  "type": "red",    "label": "Red (2)"},
    {"num": 3, "prob": 9,  "type": "green",  "label": "Green (3)"},
    {"num": 4, "prob": 7,  "type": "red",    "label": "Red (4)"},
    {"num": 5, "prob": 8,  "type": "violet", "label": "Violet/Green (5)"},
    {"num": 6, "prob": 10, "type": "blue",   "label": "Red (6)"},
    {"num": 7, "prob": 11, "type": "green",  "label": "Green (7)"},
    {"num": 8, "prob": 9,  "type": "red",    "label": "Red (8)"},
    {"num": 9, "prob": 10, "type": "violet", "label": "Green (9)"},
]


def get_top_nodes(count: int = 4) -> List[dict]:
    return sorted(NODE_MATRIX, key=lambda x: x["prob"], reverse=True)[:count]


# ============================================================
# 9) TREND HELPERS
# ============================================================

def get_big_small_rates(history: List[dict], window_size: int = 50) -> dict:
    sl = history[:window_size]
    if not sl:
        return {"bigRate": 42, "smallRate": 58}
    big = sum(1 for h in sl if (h.get("size") or get_size(h.get("number", 0))) == "BIG")
    big_rate = round(big / len(sl) * 100)
    return {"bigRate": big_rate, "smallRate": 100 - big_rate}


def get_colour_distribution(history: List[dict]) -> dict:
    dist = {"RED": 0, "GREEN": 0, "VIOLET": 0}
    for h in history:
        c = h.get("colour") or get_colour(h.get("number", 0))
        dist[c] = dist.get(c, 0) + 1
    return dist


# ============================================================
# 10) LIVE HISTORY FETCH
# ============================================================

def fetch_data() -> List[dict]:
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        data = res.json()
        if "data" in data and "list" in data["data"]:
            out = []
            for item in data["data"]["list"]:
                num = int(item["number"])
                out.append({
                    "period": str(item["issueNumber"]),
                    "number": num,
                    "size": get_size(num),
                    "colour": get_colour(num),
                })
            return out
    except Exception as e:
        print(f"Fetch error: {e}")
        return []
    return []


# ============================================================
# 11) RAW BIAS EXTRACTOR
# ============================================================

def extract_raw_bias(history: List[dict]) -> dict:
    if not history:
        return {"rawSize": "SMALL", "rawColour": "RED"}

    last5 = history[:5]

    big_count = sum(1 for h in last5 if h.get("size") == "BIG")
    raw_size = "BIG" if big_count > 2 else "SMALL"

    red_count   = sum(1 for h in last5 if h.get("colour") == "RED")
    green_count = sum(1 for h in last5 if h.get("colour") == "GREEN")
    raw_colour = "RED" if red_count >= green_count else "GREEN"

    return {"rawSize": raw_size, "rawColour": raw_colour}


# ============================================================
# 12) 🔥 ANTI-REPEAT (JS जैसा force flip)
# ============================================================

def anti_repeat_flip(base: dict) -> dict:
    """
    अगर पिछला prediction same है तो ज़बरदस्ती flip करो।
    """
    last = _LAST_PREDICTION

    if (last["size"] == base["predictedSize"]
        and last["colour"] == base["predictedColour"]
        and last["focus"] == get_current_focus()):

        # Flip raw
        new_raw_size = "BIG" if base["rawAnalysisSize"] == "SMALL" else "SMALL"
        new_raw_colour = "GREEN" if base["rawAnalysisColour"] == "RED" else "RED"
        base = build_prediction(new_raw_size, new_raw_colour)

    # Memory update
    _LAST_PREDICTION["size"] = base["predictedSize"]
    _LAST_PREDICTION["colour"] = base["predictedColour"]
    _LAST_PREDICTION["focus"] = get_current_focus()

    return base


# ============================================================
# 🔌 MAIN WRAPPER — app.py compatible
# ============================================================

def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    app.py compatible wrapper — 100% JS TRION logic
    + FOCUS ROTATION (SIZE → COLOUR → NUMBER)
    + ANTI-REPEAT FLIP

    हर नए period पर:
      Round 1 → SIZE prediction (BIG/SMALL)
      Round 2 → COLOUR prediction (RED/GREEN)
      Round 3 → NUMBER prediction (Dual Sniper)
      Round 4 → SIZE...
    """

    # ✅ Cache — same period पर same result
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {k: v for k, v in cached.items() if k != "_ts"}

    # ✅ Focus rotate (हर नए period पर)
    focus = rotate_focus(period)

    # ✅ Live history
    history = fetch_data()

    if not history:
        # Fallback — vary with period seed
        seed = int(abs(hash(period)) % 100000)
        rng = random.Random(seed)
        raw_size = rng.choice(["BIG", "SMALL"])
        raw_colour = rng.choice(["RED", "GREEN"])
        base = build_prediction(raw_size, raw_colour)
        base = anti_repeat_flip(base)
        strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

        result = _make_result(base, strike4, period, focus, confidence=65, source="fallback")
        result["_ts"] = time.time()
        _ENGINE_CACHE[period] = result
        return {k: v for k, v in result.items() if k != "_ts"}

    # ✅ JS TRION LOGIC
    raw = extract_raw_bias(history)
    base = build_prediction(raw["rawSize"], raw["rawColour"])
    base = anti_repeat_flip(base)

    strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

    # Dynamic confidence
    big_count = sum(1 for h in history[:5] if h.get("size") == "BIG")
    confidence = min(70 + abs(big_count - 2) * 5, 95)

    result = _make_result(base, strike4, period, focus, confidence, source="naveen-ai-trion")

    # Cache save
    result["_ts"] = time.time()
    _ENGINE_CACHE[period] = result

    if len(_ENGINE_CACHE) > 100:
        keys = sorted(_ENGINE_CACHE.keys(), key=lambda k: _ENGINE_CACHE[k].get("_ts", 0))
        for k in keys[:50]:
            _ENGINE_CACHE.pop(k, None)

    return {k: v for k, v in result.items() if k != "_ts"}


def _make_result(base: dict, strike4: List[int], period: str, focus: str,
                 confidence: int, source: str) -> dict:
    """
    Focus के हिसाब से main prediction चुनता है — JS की तरह।
    """
    if focus == "SIZE":
        main_prediction = base["predictedSize"]           # BIG / SMALL
    elif focus == "COLOUR":
        main_prediction = base["predictedColour"]         # RED / GREEN
    else:  # NUMBER
        main_prediction = base["predictedNumbers"]        # [7, 9]

    return {
        # 🔥 MAIN prediction (focus के हिसाब से)
        "prediction": main_prediction,
        "focus": focus,
        "focusedTarget": focus,

        # ✅ हमेशा उपलब्ध fields (UI के लिए)
        "bigSmall": base["predictedSize"],
        "colour": base["predictedColour"],
        "size": base["predictedSize"],

        # Numbers
        "numbers": base["predictedNumbers"],
        "opposites": base["predictedNumbers"],
        "strike4": strike4,

        # Meta
        "confidence": confidence,
        "predictedNumber": base["predictedNumber"],
        "secondaryNumber": base["secondaryNumber"],
        "rawAnalysisSize": base["rawAnalysisSize"],
        "rawAnalysisColour": base["rawAnalysisColour"],

        "steps": [
            f"Period: {period}",
            f"Focus: {focus}",
            f"Raw Size: {base['rawAnalysisSize']}",
            f"Raw Colour: {base['rawAnalysisColour']}",
            f"Inverted Size: {base['predictedSize']}",
            f"Inverted Colour: {base['predictedColour']}",
            f"Dual Sniper: {base['predictedNumbers']}",
            f"4-Number Strike: {strike4}",
            base["reason"],
        ],
        "source": source,
    }


def clear_engine_cache():
    _ENGINE_CACHE.clear()
    _LAST_PREDICTION["size"] = None
    _LAST_PREDICTION["colour"] = None
    _LAST_PREDICTION["focus"] = None
    _FOCUS_STATE["rotation_index"] = 0
    _FOCUS_STATE["current"] = "SIZE"
    _FOCUS_STATE["last_period"] = ""


# ============================================================
# 🧪 TEST — 6 periods, देखो focus कैसे बदलता है
# ============================================================

if __name__ == "__main__":
    print("=== Focus Rotation Test (6 periods) ===\n")
    for i in range(6):
        period = f"#202609301000100{i}"
        res = sddgamer263_predict(current_number=i, period=period)
        print(f"[{i+1}] Period={period[-5:]}  Focus={res['focus']:6s}  "
              f"Main={res['prediction']}")
        print(f"     Big/Small={res['bigSmall']:5s}  "
              f"Colour={res['colour']:5s}  "
              f"Numbers={res['numbers']}  Strike4={res['strike4']}")
        print()
