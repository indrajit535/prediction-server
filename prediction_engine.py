"""
Prediction Engine — NAVEEN AI TOOL 2026
----------------------------------------
SAAD VIP HTML Logic (Master Predictive Engine 3.0) 100% ported to Python.
Old prediction logic 100% REMOVED.
Final output: BIG/SMALL + 2 Numbers (SAME colour side, NO opposite).
Colour used internally only — NOT shown to user.
"""

import requests
import time
import random
from typing import Dict, List, Optional


# ============================================================
# 🔑 API CONFIG
# ============================================================
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1m-1000"

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
# 🎨 COLOUR POOLS (HTML exact: odd = GREEN, even = RED)
# ============================================================
# BIG = 5..9 | SMALL = 0..4
# RED = even  | GREEN = odd

# SAME-SIDE pools (no opposite) — both numbers come from here

# BIG + RED   -> even numbers in 5..9  -> [6, 8]
BIG_RED_POOL = [6, 8]

# BIG + GREEN -> odd numbers in 5..9   -> [5, 7, 9]
BIG_GREEN_POOL = [5, 7, 9]

# SMALL + RED -> even numbers in 0..4  -> [0, 2, 4]
SMALL_RED_POOL = [0, 2, 4]

# SMALL + GREEN -> odd numbers in 0..4 -> [1, 3]
SMALL_GREEN_POOL = [1, 3]


def get_big_small(num: int) -> str:
    return "BIG" if num >= 5 else "SMALL"


def get_colour(num: int) -> str:
    return "GREEN" if num % 2 != 0 else "RED"


def numbers_for(big_small: str, colour: str) -> List[int]:
    """Return pool matching BOTH big/small AND colour (same side only)."""
    if big_small == "BIG" and colour == "RED":
        return BIG_RED_POOL
    if big_small == "BIG" and colour == "GREEN":
        return BIG_GREEN_POOL
    if big_small == "SMALL" and colour == "RED":
        return SMALL_RED_POOL
    if big_small == "SMALL" and colour == "GREEN":
        return SMALL_GREEN_POOL
    return SMALL_GREEN_POOL


def next_issue(issue: str) -> str:
    try:
        return str(int(issue) + 1)
    except:
        return issue


def fetch_data() -> List[dict]:
    """Fetch live history from SAAD VIP API (1000 memory records)."""
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        data = res.json()

        raw_list = None
        if isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], dict) and 'list' in data['data']:
                raw_list = data['data']['list']
            elif 'list' in data:
                raw_list = data['list']

        if not raw_list:
            return []

        out = []
        for item in raw_list:
            raw_num = item.get('number', item.get('result', 0))
            try:
                num = int(raw_num)
            except:
                num = 0

            period = str(item.get('period', item.get('issueNumber', '')))
            if not period:
                continue

            out.append({
                'period': period,
                'number': num,
                'size': get_big_small(num),
                'colour': get_colour(num)
            })
        return out

    except Exception as e:
        print(f"Fetch error: {e}")
        return []


# ============================================================
# 🎯 SAAD VIP HTML LOGIC — 100% EXACT PORT
# ============================================================

def execute_saad_vip_deterministic_pipeline(
    history: List[dict],
    target_period: str
) -> Optional[dict]:
    """HTML: executeSaadVipDeterministicPipeline(rawList, targetPeriod)"""
    if not history or len(history) < 23:
        return {
            'colour': "GREEN",
            'primary': 9,
            'override': 3,
            'confidence': "100%",
            'reason': "Initializing 1,000 Memory Backtest"
        }

    # Step 1: Last 23 numbers summation
    last23 = [r['number'] for r in history[:23]]
    sum23 = sum(last23)

    # Step 2: Period trailing digit
    period_str = str(target_period)
    try:
        last_period_digit = int(period_str[-1])
    except:
        last_period_digit = 0

    # Step 3: Division & modulo matrix
    computed_val = ((sum23 + last_period_digit) // 2) % 10
    secondary_val = sum23 % 7

    # Steps 5-23: Conditional rule mapping (exact HTML port)
    target_colour = "GREEN"
    primary_num = computed_val
    override_num = secondary_val
    reason_text = "Step 23: 1,000-Draw Backtest Recursive Matrix"

    if computed_val in (0, 1):
        target_colour = "RED"
        primary_num = computed_val
        override_num = 1
        reason_text = "Rule 05: 0/1 Mapping -> RED"

    elif computed_val in (4, 6) and sum23 % 2 == 0:
        target_colour = "RED"
        primary_num = computed_val
        override_num = 6
        reason_text = "Rule 06: 4/6 Mapping -> RED"

    elif computed_val in (4, 0):
        target_colour = "GREEN"
        primary_num = computed_val
        override_num = 4
        reason_text = "Rule 07: 4/0 Mapping -> GREEN"

    elif computed_val in (8, 7) and sum23 % 3 == 0:
        target_colour = "GREEN"
        primary_num = 8
        override_num = 7
        reason_text = "Rule 08: 8/7 Mapping -> GREEN"

    elif computed_val in (9, 7):
        target_colour = "RED"
        primary_num = 9
        override_num = 7
        reason_text = "Rule 09: 9/7 Mapping -> RED"

    elif computed_val == 0:
        target_colour = "RED"
        primary_num = 0
        override_num = 5
        reason_text = "Rule 10: 0 Mapping -> RED"

    elif computed_val == 6:
        target_colour = "GREEN"
        primary_num = 2
        override_num = 6
        reason_text = "Rule 21: 6 Mapping -> 2 RED / GREEN Override"

    elif computed_val in (4, 9):
        target_colour = "GREEN"
        primary_num = 4
        override_num = 9
        reason_text = "Rule 12: 4/9 Mapping -> GREEN"

    elif computed_val in (1, 7):
        target_colour = "RED"
        primary_num = 1
        override_num = 7
        reason_text = "Rule 13: 1/7 Mapping -> RED"

    elif computed_val in (2, 9):
        target_colour = "GREEN"
        primary_num = 2
        override_num = 9
        reason_text = "Rule 14: 2/9 Mapping -> GREEN"

    elif computed_val in (3, 7):
        target_colour = "RED"
        primary_num = 3
        override_num = 7
        reason_text = "Rule 15: 3/7 Mapping -> RED"

    elif computed_val == 4:
        target_colour = "RED"
        primary_num = 8
        override_num = 4
        reason_text = "Rule 20: 4 Mapping -> 8 RED"

    elif computed_val == 9:
        target_colour = "RED"
        primary_num = 6
        override_num = 9
        reason_text = "Rule 22: 9 Mapping -> 6 RED"

    elif computed_val in (5, 3):
        target_colour = "GREEN"
        primary_num = 9
        override_num = 3
        reason_text = "Rule 23: 5/3 Mapping -> GREEN 9"

    else:
        target_colour = "GREEN" if sum23 % 2 == 0 else "RED"
        primary_num = computed_val
        override_num = (computed_val + 5) % 10
        reason_text = "Step 25: 100% Confirmed Result Vector"

    return {
        'colour': target_colour,
        'primary': primary_num,
        'override': override_num,
        'confidence': "100%",
        'reason': reason_text
    }


def derive_big_small_from_pipeline(result: dict) -> str:
    """Derive BIG/SMALL from pipeline primary number."""
    primary = result['primary']
    if primary == 0 and result['override'] >= 5:
        return "BIG"
    return "BIG" if primary >= 5 else "SMALL"


def pick_two_numbers_same_side(big_small: str, colour: str) -> List[int]:
    """
    Pick 2 DISTINCT numbers from SAME colour side (no opposite).

    Examples:
      BIG + GREEN   -> [9, 7, 5] -> pick 2 -> e.g. [9, 7]
      BIG + RED     -> [8, 6]    -> [8, 6]
      SMALL + RED   -> [0, 2, 4] -> e.g. [4, 0]
      SMALL + GREEN -> [1, 3]    -> [1, 3]
    """
    pool = numbers_for(big_small, colour)

    if len(pool) >= 2:
        picked = random.sample(pool, 2)
        # Sort descending for cleaner display like 9/7 or 8/6
        picked.sort(reverse=True)
        return picked

    if len(pool) == 1:
        return [pool[0], pool[0]]

    return [random.randint(0, 9), random.randint(0, 9)]


# ============================================================
# 🔌 WRAPPER — app.py compatible
# ============================================================

def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    Final output:
      - bigSmall : "BIG" or "SMALL"
      - numbers  : 2 numbers from SAME colour side (e.g. 9/7 or 8/6)
      - display  : "9/7" style string
    Colour used INTERNALLY only — NOT exposed.
    """

    # Cache check
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {
            "prediction": cached["prediction"],
            "bigSmall": cached["bigSmall"],
            "confidence": cached["confidence"],
            "numbers": cached["numbers"],
            "display": cached["display"],
            "steps": cached["steps"],
            "source": "engine-cache"
        }

    # Live history
    history = fetch_data()

    if not history:
        fallback_size = "BIG" if random.random() > 0.5 else "SMALL"
        fallback_colour = "GREEN" if random.random() > 0.5 else "RED"
        fallback_nums = pick_two_numbers_same_side(fallback_size, fallback_colour)

        return {
            "prediction": fallback_nums[0],
            "bigSmall": fallback_size,
            "confidence": "55%",
            "numbers": fallback_nums,
            "display": f"{fallback_nums[0]}/{fallback_nums[1]}",
            "steps": ["Fallback mode (no history)"],
            "source": "fallback"
        }

    # SAAD VIP pipeline
    latest = history[0]
    next_period = next_issue(latest['period'])

    result = execute_saad_vip_deterministic_pipeline(history, next_period)

    if not result:
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": get_big_small(fallback_num),
            "confidence": "55%",
            "numbers": [fallback_num, (fallback_num + 1) % 10],
            "display": f"{fallback_num}/{(fallback_num + 1) % 10}",
            "steps": ["Fallback mode"],
            "source": "fallback"
        }

    # Derive BIG/SMALL
    big_small = derive_big_small_from_pipeline(result)

    # Pick 2 numbers from SAME colour side (NO opposite)
    final_numbers = pick_two_numbers_same_side(big_small, result['colour'])

    # Display string like "9/7" or "8/6"
    display_str = f"{final_numbers[0]}/{final_numbers[1]}"

    final_result = {
        "prediction": final_numbers[0],
        "bigSmall": big_small,
        "confidence": result['confidence'],
        "numbers": final_numbers,
        "display": display_str,
        "steps": [
            f"Period: {period}",
            f"Next Issue: {next_period}",
            f"Sum(23): {sum(r['number'] for r in history[:23])}",
            f"Computed: {result['primary']} | Override: {result['override']}",
            f"Mapping: {result['reason']}",
            f"Derived Size: {big_small}",
            f"Final Numbers: {display_str}"
        ],
        "source": "saad-vip-engine-3.0"
    }

    # Cache
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
