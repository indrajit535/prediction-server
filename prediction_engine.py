"""
Prediction Engine — NAVEEN AI TOOL 2026
----------------------------------------
HTML Logic (NG MADMAX) 100% ported to Python.
Purana prediction logic 100% REMOVED.
BIG/SMALL + OPPOSITE NUMBERS prediction included.
"""

import requests
import time
import random
from typing import Dict, List


# ============================================================
# 🔑 API CONFIG
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hgnice.biz"
}

# ============================================================
# 🗄️ INTERNAL CACHE — 50 sec TTL (per period)
# ============================================================
_ENGINE_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 50


# ============================================================
# 🎯 HTML LOGIC — 100% EXACT PORT (NG MADMAX)
# ============================================================

B_POOL = [5, 6, 7, 8, 9]   # BIG numbers
S_POOL = [0, 1, 2, 3, 4]   # SMALL numbers


def get_big_small(num: int) -> str:
    """HTML: parseInt(x.number) >= 5 ? 'BIG' : 'SMALL'"""
    return "BIG" if num >= 5 else "SMALL"


def next_issue(issue: str) -> str:
    """HTML: (BigInt(latest.issueNumber) + 1n).toString()"""
    try:
        return str(int(issue) + 1)
    except:
        return issue


def fetch_data() -> List[dict]:
    """
    HTML fetch:
    https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json
    Returns latest history list (newest first).
    """
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        data = res.json()
        if 'data' in data and 'list' in data['data']:
            out = []
            for item in data['data']['list']:
                num = int(item['number'])
                out.append({
                    'period': str(item['issueNumber']),
                    'number': num,
                    'size': get_big_small(num)
                })
            return out
    except Exception as e:
        print(f"Fetch error: {e}")
        return []
    return []


def html_predict(history: List[dict]) -> dict:
    """
    HTML runLogic() ka 100% EXACT port:

    const last5 = json.data.list.slice(0, 5).map(
        x => parseInt(x.number) >= 5 ? "BIG" : "SMALL"
    );
    const nextPred = last5.filter(x => x === "BIG").length > 2
                     ? "BIG" : "SMALL";

    const pool = nextPred === "BIG" ? S_POOL : B_POOL;
    currentOpposites = pool.sort(() => 0.5 - Math.random()).slice(0, 2);
    """
    if not history:
        return None

    # last 5 results → BIG/SMALL mapping
    last5 = [item['size'] for item in history[:5]]

    # nextPred = BIG if BIG count > 2 else SMALL
    big_count = sum(1 for x in last5 if x == "BIG")
    next_pred = "BIG" if big_count > 2 else "SMALL"

    # Opposite pool logic (HTML exact)
    pool = S_POOL if next_pred == "BIG" else B_POOL
    pool_copy = pool[:]
    random.shuffle(pool_copy)                 # .sort(() => 0.5 - Math.random())
    opposites = pool_copy[:2]                 # .slice(0, 2)

    latest = history[0]
    next_period = next_issue(latest['period'])

    # Confidence based on BIG count strength (visual only)
    confidence = 70 + abs(big_count - 2) * 5
    confidence = min(confidence, 95)

    return {
        'issue': next_period,
        'size': next_pred,
        'confidence': confidence,
        'opposites': opposites,
        'big_count': big_count,
        'last5': last5
    }


# ============================================================
# 🔌 WRAPPER — app.py compatible
# ============================================================

def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    app.py compatible wrapper.
    HTML logic 100% ported — BIG/SMALL + Opposite Numbers.
    Har naye period pe naya prediction dega.
    """

    # Cache check
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {
            "prediction": cached["prediction"],
            "bigSmall": cached["bigSmall"],
            "confidence": cached["confidence"],
            "numbers": cached["numbers"],
            "opposites": cached["opposites"],
            "steps": cached["steps"],
            "source": "engine-cache"
        }

    # Live history
    history = fetch_data()

    if not history:
        # Fallback (same HTML pattern — 50/50)
        fallback_size = "BIG" if random.random() > 0.5 else "SMALL"
        pool = S_POOL if fallback_size == "BIG" else B_POOL
        pool_copy = pool[:]
        random.shuffle(pool_copy)
        fallback_opps = pool_copy[:2]
        fallback_num = fallback_opps[0] if fallback_opps else current_number

        return {
            "prediction": fallback_num,
            "bigSmall": fallback_size,
            "confidence": 55,
            "numbers": [fallback_num],
            "opposites": fallback_opps,
            "steps": ["Fallback mode (no history)"],
            "source": "fallback"
        }

    # HTML prediction
    result = html_predict(history)

    if not result:
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": get_big_small(fallback_num),
            "confidence": 55,
            "numbers": [fallback_num],
            "opposites": [],
            "steps": ["Fallback mode"],
            "source": "fallback"
        }

    # Prediction number — first opposite (same as HTML display order)
    number = result['opposites'][0] if result['opposites'] else current_number

    final_result = {
        "prediction": number,
        "bigSmall": result['size'],
        "confidence": result['confidence'],
        "numbers": result['opposites'],                 # Opposite numbers list
        "opposites": result['opposites'],               # NEW FIELD
        "steps": [
            f"Period: {period}",
            f"Next Issue: {result['issue']}",
            f"Last 5: {result['last5']}",
            f"BIG Count: {result['big_count']}",
            f"Prediction: {result['size']}",
            f"Opposites: {result['opposites']}"
        ],
        "source": "naveen-ai"
    }

    # Cache save
    final_result["_ts"] = time.time()
    _ENGINE_CACHE[period] = final_result

    # Cleanup
    if len(_ENGINE_CACHE) > 100:
        sorted_keys = sorted(
            _ENGINE_CACHE.keys(),
            key=lambda k: _ENGINE_CACHE[k].get("_ts", 0),
            reverse=True
        )
        for k in sorted_keys[50:]:
            _ENGINE_CACHE.pop(k, None)

    return final_result


def clear_engine_cache():
    _ENGINE_CACHE.clear()
