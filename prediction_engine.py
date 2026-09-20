"""
Prediction Engine — NAVEEN AI TOOL 2026 (Python Port)
------------------------------------------------------
Prediction logic: 100% same as original NAVEEN AI TOOL code.
app.py isi ko call karta hai: sddgamer263_predict()
"""

import requests
import time
from typing import List, Dict, Optional


# ============================================================
# 🔑 API CONFIG
# ============================================================
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-100"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hgnice.biz"
}


# ============================================================
# 🎯 CORE PREDICTION LOGIC — JS ka exact port (NO CHANGE)
# ============================================================

def fnv1a_hash(s: str) -> int:
    """
    JS re() function ka exact port.
    FNV-1a 32-bit hash — deterministic randomness ke liye.
    """
    t = 2166136261
    for ch in s:
        t ^= ord(ch)
        t = (t * 16777619) & 0xFFFFFFFF   # Math.imul 32-bit wrap
    return abs(t)


def next_issue(issue: str) -> str:
    """
    JS ne() function ka exact port.
    Period number ko +1 karta hai, leading zeros preserve karte hue.
    """
    digits = ''.join(c for c in issue if c.isdigit())
    if not digits:
        return issue
    nxt = str(int(digits) + 1).zfill(len(digits))
    return issue.replace(digits, nxt)


def get_big_small(num: int) -> str:
    """Number >= 5 → BIG, warna SMALL."""
    return "BIG" if num >= 5 else "SMALL"


def predict(results, last_issue: str):
    """
    JS te() function ka exact port.

    Input:
        results    = list of dicts [{'period':..., 'number':int, 'size':...}, ...]
                     (latest pehle, matlab results[0] = sabse naya)
        last_issue = latest period number (string)

    Output:
        {
          'issue': next period number,
          'size': 'BIG' / 'SMALL',
          'confidence': 68..97,
          'score': float
        }
    """
    if not results:
        return None

    # ── Step 1: Next period number ──
    n = next_issue(last_issue)

    # ── Step 2: Last 10 results lo ──
    r = results[:10]
    if not r:
        return None

    # ── Step 3: Weighted trend score ──
    i = 0.0
    for idx, item in enumerate(r):
        weight = 1.0 / (idx + 1)                              # 1, 1/2, 1/3 ...
        size_sign = 1 if item['size'] == 'BIG' else -1
        i += size_sign * weight                               # BIG=+, SMALL=-
        i += (item['number'] - 4.5) / 4.5 * weight * 0.6      # number bias

    # ── Step 4: Streak reversal detection ──
    a = 1
    while a < len(r) and r[a]['size'] == r[0]['size']:
        a += 1
    if a >= 3:
        # 3+ same → reverse predict
        i += -1.4 if r[0]['size'] == 'BIG' else 1.4

    # ── Step 5: Deterministic hash noise ──
    o = fnv1a_hash(n) % 1000
    i += (o / 1000.0 - 0.5) * 0.5

    # ── Step 6: Final prediction ──
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
    
    Args:
        current_number: Last draw ka number (0-9) — ye directly use nahi hota,
                        kyunki hum live history fetch karte hain.
        period: Target period jiske liye predict karna hai.
    
    Returns:
        dict with keys: prediction, bigSmall, confidence, numbers, steps
    """

    # Live history fetch karo
    history = fetch_data()

    if not history:
        # Fallback — agar API fail ho jaye
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": get_big_small(fallback_num),
            "confidence": 55,
            "numbers": [fallback_num],
            "steps": [],
            "source": "fallback"
        }

    # Latest period nikalो history se (kyunki usi se next issue banega)
    last_issue = history[0]['period']

    # Original NAVEEN AI predict function call karo
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

    # ── Prediction number calculate karo ──
    # Original logic sirf BIG/SMALL deta hai, number nahi.
    # Isliye hash-based deterministic number generate kar rahe hain.
    # Big ke liye 5-9, Small ke liye 0-4.
    import random
    hash_val = fnv1a_hash(result['issue'] + result['size'])

    if result['size'] == 'BIG':
        number = 5 + (hash_val % 5)        # 5,6,7,8,9
    else:
        number = hash_val % 5              # 0,1,2,3,4

    # Alternate numbers (same range me)
    if result['size'] == 'BIG':
        alternates = [5 + ((hash_val + 1) % 5), 5 + ((hash_val + 2) % 5)]
    else:
        alternates = [(hash_val + 1) % 5, (hash_val + 2) % 5]

    numbers_list = [number] + alternates

    return {
        "prediction": number,
        "bigSmall": result['size'],
        "confidence": result['confidence'],
        "numbers": numbers_list,
        "steps": [
            f"Period: {result['issue']}",
            f"Score: {result['score']}",
            f"Confidence: {result['confidence']}%"
        ],
        "source": "naveen-ai"
    }
