"""
TRION Prediction Engine — 100% JS Port
--------------------------------------
यह code JS file (index-DsHC_BbY.js) के अंदर से पूरा prediction system
100% port करता है। पुराना Python logic 100% हटा दिया गया है।

JS Reference:
  - ma()      → get_period_info()
  - Xx()      → split_period_id()
  - Zx()      → get_number_meta()
  - Qx()      → build_prediction()  ← CORE INVERTED LOGIC
  - Kx()      → verify_prediction()
  - Ix()      → run_analysis()      ← API + fallback
  - Jx()/a0() → fetch_wingo_history()
  - Lp.ha()   → generate_prediction() ← MAIN with focus rotation
"""

import requests
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ============================================================
# 🔑 API CONFIG (JS: Ix / Jx / a0 endpoints)
# ============================================================
ANALYSIS_API_URL = "/api/analysis/run"          # JS: Ix()
PREDICTIONS_API_URL = "/api/predictions"        # JS: l0()
WINGO_HISTORY_API_URL = "/api/wingo-history"    # JS: Jx()
WINGO_1000_API_URL = "/api/wingo-history-1000"  # JS: a0()

# Live external fallback (JS fetch से fallback था, यहाँ live API)
LIVE_WINGO_API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
LIVE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hgnice.biz",
}


# ============================================================
# 🗄️ CACHE (JS: _ENGINE_CACHE equivalent)
# ============================================================
_ENGINE_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 50

# 🔥 JS rotation state — Lp.js me `fe` state (SIZE/COLOUR/NUMBER)
_FOCUS_STATE = {
    "current": "SIZE",
    "rotation_index": 0,
    "rotation_cycle": ["SIZE", "COLOUR", "NUMBER"],
    "last_period": "",
}

# 🔥 Anti-repeat memory (JS: nl.current guard)
_LAST_PREDICTION = {"size": None, "colour": None, "focus": None}


# ============================================================
# 1) PERIOD / COUNTDOWN — JS: ma(date) 100% port
# ============================================================

def get_period_info(date: Optional[datetime] = None) -> dict:
    """
    JS ma() 100% port:
      prefix = YYYYMMDD + '1000'
      shortPeriod = 10000 + (UTC_hour*60 + UTC_minute)
      periodId = '#' + prefix + shortPeriod
    """
    if date is None:
        date = datetime.now(timezone.utc)

    year = date.year
    month = f"{date.month:02d}"
    day = f"{date.day:02d}"
    prefix = f"{year}{month}{day}1000"

    utc_hours = date.hour
    utc_minutes = date.minute
    utc_seconds = date.second

    # JS: g = 1e4 + (N*60 + M) + 1  → 10000 + (h*60+m) + 1
    short_period_num = 10000 + (utc_hours * 60 + utc_minutes) + 1
    short_period = str(short_period_num)
    raw_period_id = f"{prefix}{short_period}"
    period_id = f"#{raw_period_id}"

    # JS: F = k===0 ? 60 : 60 - k
    seconds_remaining = 60 if utc_seconds == 0 else 60 - utc_seconds

    minutes_left = seconds_remaining // 60
    secs_left = seconds_remaining % 60

    return {
        "periodId": period_id,
        "rawPeriodId": raw_period_id,
        "shortPeriod": short_period,
        "prefix": prefix,
        "secondsRemaining": seconds_remaining,
        "formattedTime": f"{minutes_left:02d}:{secs_left:02d}",
        "isUrgent": seconds_remaining <= 10,
    }


# ============================================================
# 2) PERIOD SPLIT — JS: Xx(periodId) 100% port
# ============================================================

def split_period_id(period_id: str) -> dict:
    """JS Xx(): '#' prefix और last 5 chars highlight।"""
    if not period_id:
        return {"prefix": "#", "highlight": "00000"}

    p = period_id if period_id.startswith("#") else f"#{period_id}"

    if len(p) > 5:
        return {
            "prefix": p[: len(p) - 5],
            "highlight": p[len(p) - 5:],
        }
    return {"prefix": "", "highlight": p}


# ============================================================
# 3) NUMBER METADATA — JS: t0 object + Zx(num) 100% port
# ============================================================

# JS `t0` exact port
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
    """JS Zx(num) 100% port."""
    n = ((int(num) % 10) + 10) % 10
    return NUMBER_MAP.get(n, NUMBER_MAP[0])


def get_size(num: int) -> str:
    return get_number_meta(num)["size"]


def get_colour(num: int) -> str:
    """JS: n===0||n===5 → VIOLET, n%2===0 → RED, else GREEN."""
    n = ((int(num) % 10) + 10) % 10
    if n == 0 or n == 5:
        return "VIOLET"
    return "RED" if n % 2 == 0 else "GREEN"


# ============================================================
# 4) 🔥 CORE INVERTED COUNTER-RESONANCE — JS: Qx() 100% port
# ============================================================

def build_prediction(raw_size: str = "SMALL", raw_colour: str = "RED") -> dict:
    """
    JS Qx() 100% port:
      raw BIG   → predicted SMALL
      raw SMALL → predicted BIG
      raw RED   → predicted GREEN
      raw GREEN → predicted RED

    Number mapping:
      BIG + GREEN   → 7, 9
      BIG + RED     → 8, 6
      SMALL + GREEN → 3, 1
      SMALL + RED   → 2, 4
    """
    r_size = "BIG" if (raw_size or "").upper() == "BIG" else "SMALL"
    r_colour = "GREEN" if (raw_colour or "").upper() == "GREEN" else "RED"

    # Inversion
    predicted_size = "BIG" if r_size == "SMALL" else "SMALL"
    predicted_colour = "GREEN" if r_colour == "RED" else "RED"

    # JS number mapping
    if predicted_size == "BIG" and predicted_colour == "GREEN":
        pn, sn = 7, 9
    elif predicted_size == "BIG" and predicted_colour == "RED":
        pn, sn = 8, 6
    elif predicted_size == "SMALL" and predicted_colour == "GREEN":
        pn, sn = 3, 1
    else:
        pn, sn = 2, 4

    reason = (
        f"TRION Inverted Counter-Resonance Strategy (OPPOSITE PREDICTION): "
        f"Raw analysis showed {r_size}/{r_colour} ➔ Inverted to "
        f"{predicted_size} ({'5-9' if predicted_size == 'BIG' else '0-4'}) & "
        f"{predicted_colour} [{pn}, {sn}] to counter pattern break."
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
# 5) 🔥 FOCUS ROTATION — JS: Lp.js me focusedTarget rotate
# ============================================================

def rotate_focus(period: str) -> str:
    """
    JS में हर नए period पर focus rotate होता है:
      SIZE → COLOUR → NUMBER → SIZE → ...

    JS Lp component me:
      onSelectTargetType("SIZE") / "COLOUR" / "NUMBER"
      जो प्रत्येक round पर auto-rotate होता है।
    """
    if _FOCUS_STATE["last_period"] != period:
        _FOCUS_STATE["rotation_index"] = (_FOCUS_STATE["rotation_index"] + 1) % 3
        _FOCUS_STATE["current"] = _FOCUS_STATE["rotation_cycle"][_FOCUS_STATE["rotation_index"]]
        _FOCUS_STATE["last_period"] = period

    return _FOCUS_STATE["current"]


def get_current_focus() -> str:
    return _FOCUS_STATE["current"]


def force_set_focus(focus: str):
    """JS: onSelectTargetType() manual override."""
    focus = (focus or "").upper()
    if focus in ("SIZE", "COLOUR", "NUMBER"):
        _FOCUS_STATE["current"] = focus
        _FOCUS_STATE["rotation_index"] = _FOCUS_STATE["rotation_cycle"].index(focus)


# ============================================================
# 6) ANTI-REPEAT FLIP (JS: same prediction पर flip)
# ============================================================

def anti_repeat_flip(base: dict) -> dict:
    """JS Lp.js जैसा — same prediction same focus पर flip करता है।"""
    last = _LAST_PREDICTION

    if (last["size"] == base["predictedSize"]
            and last["colour"] == base["predictedColour"]
            and last["focus"] == get_current_focus()):

        new_raw_size = "BIG" if base["rawAnalysisSize"] == "SMALL" else "SMALL"
        new_raw_colour = "GREEN" if base["rawAnalysisColour"] == "RED" else "RED"
        base = build_prediction(new_raw_size, new_raw_colour)

    _LAST_PREDICTION["size"] = base["predictedSize"]
    _LAST_PREDICTION["colour"] = base["predictedColour"]
    _LAST_PREDICTION["focus"] = get_current_focus()
    return base


# ============================================================
# 7) VERIFICATION — JS: Kx(prediction, actualNum) 100% port
# ============================================================

def verify_prediction(prediction: dict, actual_num: int) -> bool:
    """JS Kx() 100% port — WIN/LOSS verification with focus awareness."""
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

    # Size gate
    if pred_size == "BIG" and actual_size != "BIG":
        return False
    if pred_size == "SMALL" and actual_size != "SMALL":
        return False

    focus = str(
        prediction.get("focusedTarget")
        or prediction.get("primaryTargetType")
        or "SIZE"
    ).upper()

    # JS exact branching
    if focus == "SIZE":
        if pred_size == "BIG":
            return actual_size == "BIG"
        if pred_size == "SMALL":
            return actual_size == "SMALL"
        return False

    if focus == "COLOUR":
        if pred_colour == "RED":
            return "RED" in actual_meta["validColours"]
        if pred_colour == "GREEN":
            return "GREEN" in actual_meta["validColours"]
        if pred_colour == "VIOLET":
            return actual_meta["isViolet"]
        return False

    if focus == "NUMBER" or isinstance(prediction.get("prediction"), int):
        # Number-based strike check
        sel4 = prediction.get("selected4Numbers")
        if isinstance(sel4, list) and len(sel4) > 0:
            return n in sel4
        nums = prediction.get("predictedNumbers") or []
        if nums:
            return n in nums
        return actual_size == pred_size

    return actual_size == pred_size


# ============================================================
# 8) 4-NUMBER STRIKE (JS Ap component `2 TARGET NUMBERS`)
# ============================================================

def pick4_numbers(size: str = "SMALL", colour: str = "RED") -> List[int]:
    """JS dual sniper + 4-number strike port."""
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
# 9) NODE MATRIX — JS Cp component (10-Node Analysis Matrix)
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
# 10) TREND HELPERS — JS Rp component
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
# 11) LIVE HISTORY FETCH — JS: Jx() + a0() ports
# ============================================================

def fetch_wingo_history() -> dict:
    """
    JS Jx() 100% port:
      - पहले /api/wingo-history try करता है
      - Fail होने पर fallback synthetic history generate करता है
    """
    try:
        res = requests.get(WINGO_HISTORY_API_URL, timeout=5)
        if res.ok:
            return res.json()
    except Exception:
        pass

    # Live external API fallback (JS Jx fallback pattern)
    try:
        res = requests.get(LIVE_WINGO_API, headers=LIVE_HEADERS, timeout=8)
        data = res.json()
        if "data" in data and "list" in data["data"]:
            history = []
            for item in data["data"]["list"][:20]:
                num = int(item["number"])
                history.append({
                    "period": f"#{item['issueNumber']}",
                    "number": num,
                    "colour": get_colour(num),
                    "size": get_size(num),
                    "timestamp": datetime.now().strftime("%I:%M %p"),
                })
            period = get_period_info()
            return {
                "history": history,
                "nextPeriod": period["periodId"],
                "countdownSeconds": period["secondsRemaining"],
            }
    except Exception as e:
        print(f"[fetch_wingo_history] Live API failed: {e}")

    # JS Jx final fallback — synthetic history
    now = datetime.now()
    period = get_period_info()
    short_num = int(period["shortPeriod"])
    prefix = period["prefix"]

    synthetic = []
    for i in range(20):
        p_num = short_num - i - 1
        p_id = f"{prefix}{p_num}"
        num = random.randint(0, 9)
        colour = "VIOLET" if num in (0, 5) else ("RED" if num % 2 == 0 else "GREEN")
        size = "BIG" if num >= 5 else "SMALL"
        synthetic.append({
            "period": f"#{p_id}",
            "number": num,
            "colour": colour,
            "size": size,
            "timestamp": now.strftime("%I:%M %p"),
        })

    return {
        "history": synthetic,
        "nextPeriod": period["periodId"],
        "countdownSeconds": period["secondsRemaining"],
    }


def fetch_1000_history() -> dict:
    """JS a0() 100% port — 1000-round history."""
    try:
        res = requests.get(WINGO_1000_API_URL, timeout=5)
        if res.ok:
            return res.json()
    except Exception:
        pass
    return fetch_wingo_history()


# ============================================================
# 12) ANALYSIS API CALL — JS: Ix() 100% port
# ============================================================

def run_analysis(engine_id: str = "2000 LOGIC",
                 user_choice=None,
                 target_mode: str = "AUTO_OPTIMAL",
                 timeout_ms: int = 4500) -> Optional[dict]:
    """
    JS Ix() 100% port:
      1. /api/analysis/run call with 4500ms timeout
      2. Fail होने पर 3000ms retry
      3. दोनों fail होने पर instant client-side fallback
    """
    payload = {
        "engineId": engine_id,
        "userChoice": user_choice,
        "targetMode": target_mode,
    }

    # First attempt (4500ms)
    try:
        res = requests.post(
            ANALYSIS_API_URL,
            json=payload,
            timeout=timeout_ms / 1000.0,
        )
        if res.ok:
            data = res.json()
            if data and data.get("prediction"):
                return data["prediction"]
    except Exception as e:
        print(f"[run_analysis] Primary timeout/error: {e}")

    # Retry (3000ms)
    try:
        res = requests.post(
            ANALYSIS_API_URL,
            json=payload,
            timeout=3.0,
        )
        if res.ok:
            data = res.json()
            if data and data.get("prediction"):
                return data["prediction"]
    except Exception as e:
        print(f"[run_analysis] Retry failed, applying fallback: {e}")

    # JS instant client-side fallback
    period = get_period_info()
    base = build_prediction("SMALL", "RED")

    return {
        "id": f"pred_{int(time.time() * 1000)}",
        "roundId": period["periodId"],
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "engine": "2000 LOGIC",
        "prediction": base["predictedSize"],
        "primaryTargetType": "SIZE",
        "targetMode": target_mode,
        "focusedTarget": "SIZE",
        "predictedSize": base["predictedSize"],
        "predictedNumber": base["predictedNumber"],
        "secondaryNumber": base["secondaryNumber"],
        "predictedNumbers": base["predictedNumbers"],
        "predictedColour": base["predictedColour"],
        "rawAnalysisSize": base["rawAnalysisSize"],
        "rawAnalysisColour": base["rawAnalysisColour"],
        "signalStrength": 96,
        "cycleLocked": True,
        "isSkip": False,
        "riskLevel": "LOW",
        "reason": base["reason"],
        "activeLogicsMatched": 48,
        "totalLogicsEvaluated": 60,
        "lossStreakState": 0,
        "prngSeedIndex": 0,
        "status": "UNVERIFIED",
        "dataSampleRounds": 1000,
        "breakdown": {
            "patternSignal": 24,
            "sequenceSignal": 20,
            "historicalSimilarity": 18,
            "frequencySignal": 16,
            "otherSignals": 18,
        },
        "consensusDetails": {
            "supportingGreen": 1450,
            "supportingRed": 550,
            "supportingViolet": 0,
            "consensusState": "STRONG_CONSENSUS",
            "explanation": "Dynamic 100-round simulation verified strong consensus.",
        },
        "testedLogicInfo": {
            "logicId": "L01_Markov",
            "logicName": "1st-Order Markov State Transition",
            "testedRounds": 100,
            "backtestWinRate": 88.5,
            "backtestMaxLossStreak": 1,
            "recent20WinRate": 90,
            "candidatesEvaluated": 52,
            "eligibleLogicsCount": 48,
        },
    }


# ============================================================
# 13) RAW BIAS EXTRACTOR (JS main `ha()` logic)
# ============================================================

def extract_raw_bias(history: List[dict]) -> dict:
    """JS main `ha()` के अंदर raw bias extraction।"""
    if not history:
        return {"rawSize": "SMALL", "rawColour": "RED"}

    last5 = history[:5]

    big_count = sum(1 for h in last5 if h.get("size") == "BIG")
    raw_size = "BIG" if big_count > 2 else "SMALL"

    red_count = sum(1 for h in last5 if h.get("colour") == "RED")
    green_count = sum(1 for h in last5 if h.get("colour") == "GREEN")
    raw_colour = "RED" if red_count >= green_count else "GREEN"

    return {"rawSize": raw_size, "rawColour": raw_colour}


# ============================================================
# 14) 🔥 MAIN PREDICTION GENERATOR — JS Lp.ha() 100% port
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
    """
    JS Lp.ha() 100% port — full prediction with focusedTarget,
    anti-repeat, and inverted counter-resonance.
    """
    now = datetime.now(timezone.utc)
    period = get_period_info(now)
    base = build_prediction(raw_size, raw_colour)

    # Anti-repeat flip (JS: nl.current guard)
    base = anti_repeat_flip(base)

    strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

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
        "strike4": strike4,

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
# 15) 🔥 MAIN WRAPPER — app.py compatible
# ============================================================

def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    app.py compatible wrapper — 100% JS TRION logic।

    Features:
      ✅ Inverted Counter-Resonance (JS Qx)
      ✅ Focus Rotation: SIZE → COLOUR → NUMBER (हर नए period)
      ✅ Anti-Repeat Flip
      ✅ Live History Fetch (JS Jx + a0)
      ✅ Cache with TTL (JS _ENGINE_CACHE)

    हर नए period पर:
      Round 1 → SIZE  prediction (BIG / SMALL)
      Round 2 → COLOUR prediction (RED / GREEN)
      Round 3 → NUMBER prediction (Dual Sniper [7,9] etc.)
      Round 4 → SIZE...
    """

    # Cache hit
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {k: v for k, v in cached.items() if k != "_ts"}

    # Focus rotate (हर नए period पर)
    focus = rotate_focus(period)

    # Live history
    history = fetch_wingo_history().get("history", [])

    if not history:
        # Fallback — period seed with deterministic PRNG
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

    # JS TRION LOGIC
    raw = extract_raw_bias(history)
    base = build_prediction(raw["rawSize"], raw["rawColour"])
    base = anti_repeat_flip(base)

    strike4 = pick4_numbers(base["predictedSize"], base["predictedColour"])

    # Dynamic confidence (JS: min(70 + abs(bigCount-2)*5, 95))
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
    Focus के हिसाब से main prediction चुनता है (JS focusedTarget behaviour)।
    """
    if focus == "SIZE":
        main_prediction = base["predictedSize"]
    elif focus == "COLOUR":
        main_prediction = base["predictedColour"]
    else:  # NUMBER
        main_prediction = base["predictedNumbers"]

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
        "predictedNumber": base["predictedNumber"],
        "secondaryNumber": base["secondaryNumber"],
        "predictedNumbers": base["predictedNumbers"],
        "opposites": base["predictedNumbers"],
        "strike4": strike4,

        # Meta
        "confidence": confidence,
        "rawAnalysisSize": base["rawAnalysisSize"],
        "rawAnalysisColour": base["rawAnalysisColour"],
        "reason": base["reason"],

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
    """JS cache clear logic."""
    _ENGINE_CACHE.clear()
    _LAST_PREDICTION["size"] = None
    _LAST_PREDICTION["colour"] = None
    _LAST_PREDICTION["focus"] = None
    _FOCUS_STATE["rotation_index"] = 0
    _FOCUS_STATE["current"] = "SIZE"
    _FOCUS_STATE["last_period"] = ""


# ============================================================
# 🧪 TEST — 6 periods, focus rotation verify करें
# ============================================================

if __name__ == "__main__":
    print("=== TRION Focus Rotation Test (6 periods) ===\n")
    for i in range(6):
        period = f"#202609301000100{i}"
        res = sddgamer263_predict(current_number=i, period=period)
        print(f"[{i+1}] Period={period[-5:]}  Focus={res['focus']:6s}  "
              f"Main={res['prediction']}")
        print(f"     Big/Small={res['bigSmall']:5s}  "
              f"Colour={res['colour']:5s}  "
              f"Numbers={res['numbers']}  Strike4={res['strike4']}")
        print()
