"""
Prediction Engine — NAVEEN AI TOOL 2026
----------------------------------------
Original logic 100% same + app.py compatible wrapper.
Har period pe naya prediction dega.
"""

import requests
import time
from typing import Dict


# ============================================================
# 🔑 API CONFIG
# ============================================================
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-100"

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
# 🎯 CORE PREDICTION LOGIC (JS exact port — NO CHANGE)
# ============================================================

def fnv1a_hash(s: str) -> int:
    """JS re() function ka exact port."""
    t = 2166136261
    for ch in s:
        t ^= ord(ch)
        t = (t * 16777619) & 0xFFFFFFFF
    return abs(t)


def next_issue(issue: str) -> str:
    """JS ne() function ka exact port."""
    digits = ''.join(c for c in issue if c.isdigit())
    if not digits:
        return issue
    nxt = str(int(digits) + 1).zfill(len(digits))
    return issue.replace(digits, nxt)


def get_big_small(num: int) -> str:
    """Number >= 5 → BIG, warna SMALL."""
    return "BIG" if num >= 5 else "SMALL"


def predict(results, last_issue: str):
    """JS te() function ka exact port."""
    if not results:
        return None

    n = next_issue(last_issue)
    r = results[:10]
    if not r:
        return None

    # Weighted trend score
    i = 0.0
    for idx, item in enumerate(r):
        weight = 1.0 / (idx + 1)
        size_sign = 1 if item['size'] == 'BIG' else -1
        i += size_sign * weight
        i += (item['number'] - 4.5) / 4.5 * weight * 0.6

    # Streak reversal detection
    a = 1
    while a < len(r) and r[a]['size'] == r[0]['size']:
        a += 1
    if a >= 3:
        i += -1.4 if r[0]['size'] == 'BIG' else 1.4

    # Deterministic hash noise
    o = fnv1a_hash(n) % 1000
    i += (o / 1000.0 - 0.5) * 0.5

    # Final
    size = 'BIG' if i < 0 else 'SMALL'
    confidence = min(97, 68 + round(abs(i) * 9))

    return {
        'issue': n,
        'size': size,
        'confidence': confidence,
        'score': round(i, 4)
    }


# ============================================================
# 🌐 API FETCH
# ============================================================

def fetch_data():
    """Yaar Win server se last 100 WinGo results laata hai."""
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


# ============================================================
# 🔌 WRAPPER — app.py isi function ko call karta hai
# ============================================================

def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    app.py compatible wrapper.
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
            "steps": cached["steps"],
            "source": "engine-cache"
        }

    # Live history
    history = fetch_data()

    if not history:
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": get_big_small(fallback_num),
            "confidence": 55,
            "numbers": [fallback_num],
            "steps": [],
            "source": "fallback"
        }

    # Latest period se next issue banao
    last_issue = history[0]['period']
    result = predict(history, last_issue)

    if not result:
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": get_big_small(fallback_num),
            "confidence": 55,
            "numbers": [fallback_num],
            "steps": [],
            "source": "fallback"
        }

    # Deterministic number (period-based — har period pe alag)
    hash_val = fnv1a_hash(period + result['size'])

    if result['size'] == 'BIG':
        number = 5 + (hash_val % 5)
        alternates = [5 + ((hash_val + 1) % 5), 5 + ((hash_val + 2) % 5)]
    else:
        number = hash_val % 5
        alternates = [(hash_val + 1) % 5, (hash_val + 2) % 5]

    numbers_list = [number] + alternates

    final_result = {
        "prediction": number,
        "bigSmall": result['size'],
        "confidence": result['confidence'],
        "numbers": numbers_list,
        "steps": [
            f"Period: {period}",
            f"Score: {result['score']}",
            f"Confidence: {result['confidence']}%"
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
