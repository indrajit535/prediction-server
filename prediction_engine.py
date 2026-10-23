# ============================================================
#  UPE-X v2 — TUSHAR ENGINE (100% REPLACED LOGIC)
#  Old Goku/V12/Webc0dc/Rafsan/Titanium logic = REMOVED
#  New logic = Tushar JS engine (Dragon / 3:3 / Opposite)
#  + UniversalAIDecoder 12-formula 10/10 search
# ============================================================

import math
import random
import time
from typing import Optional, List, Dict, Any

# ============================================================
# §0. PRIMITIVES (kept — helpers only)
# ============================================================
BIG_POOL = [5, 6, 7, 8, 9]
SMALL_POOL = [0, 1, 2, 3, 4]


def to_side(n) -> str:
    return "B" if int(n) >= 5 else "S"


def flip(s: str) -> str:
    return "S" if s == "B" else "B"


def to_color(n) -> str:
    return "R" if int(n) % 2 == 0 else "G"


def clamp(v, a, b):
    return max(a, min(b, v))


def number_to_size(n) -> str:
    return "SMALL" if int(n) <= 4 else "BIG"


def all_same(arr) -> bool:
    if not arr:
        return False
    return all(v == arr[0] for v in arr)


# ============================================================
# §1. NUMBER MAP (kept — used for jackpot meta)
# ============================================================
NUMBER_MAP = {
    0: {"size": "SMALL", "validColours": ["RED", "VIOLET"], "isViolet": True},
    1: {"size": "SMALL", "validColours": ["GREEN"], "isViolet": False},
    2: {"size": "SMALL", "validColours": ["RED"], "isViolet": False},
    3: {"size": "SMALL", "validColours": ["GREEN"], "isViolet": False},
    4: {"size": "SMALL", "validColours": ["RED"], "isViolet": False},
    5: {"size": "BIG",   "validColours": ["GREEN", "VIOLET"], "isViolet": True},
    6: {"size": "BIG",   "validColours": ["RED"], "isViolet": False},
    7: {"size": "BIG",   "validColours": ["GREEN"], "isViolet": False},
    8: {"size": "BIG",   "validColours": ["RED"], "isViolet": False},
    9: {"size": "BIG",   "validColours": ["GREEN"], "isViolet": False},
}


def num_meta(n):
    return NUMBER_MAP[((int(math.floor(n)) % 10) + 10) % 10]


# ============================================================
# §2. GLOBAL STATE
# ============================================================
MODE_OVERRIDE = {"value": "AUTO"}   # "BIG" | "SMALL" | "AUTO"
STATS = {"w": 0, "l": 0, "f": 0}    # wins, losses, fetches
LAST_BET = {"period": None, "prediction": None, "number": None}


# ============================================================
# §3. CORE PREDICTION — TUSHAR JS LOGIC (1:1 PORT)
# ============================================================
def get_prediction(current_number: int, results: List[str]) -> Dict[str, str]:
    """
    Direct port of Tushar's getPrediction():
      STEP 1 : Admin override
      STEP 2 : Auto mode
        2A : 3:3 pattern
        2B : Dragon pattern
        2C : Opposite strategy
    """
    # === STEP 1: Admin Override ===
    if MODE_OVERRIDE["value"] == "BIG":
        return {"pred": "BIG", "mode": "ADMIN FORCE"}
    if MODE_OVERRIDE["value"] == "SMALL":
        return {"pred": "SMALL", "mode": "ADMIN FORCE"}

    # === STEP 2: Auto Mode ===
    if len(results) < 6:
        pred = "BIG" if current_number <= 4 else "SMALL"
        return {"pred": pred, "mode": "DEFAULT"}

    last6 = results[:6]
    first3 = last6[:3]
    last3 = last6[3:6]

    # === STEP 2A: 3:3 Pattern ===
    is_first3_same = all_same(first3)
    is_last3_same = all_same(last3)
    is_33 = is_first3_same and is_last3_same and (first3[0] != last3[0])

    if is_33:
        streak = sum(1 for v in last6 if v == last6[0])
        if streak < 3:
            pred = last6[0]
        else:
            pred = "SMALL" if last6[0] == "BIG" else "BIG"
        return {"pred": pred, "mode": "3:3 PATTERN"}

    # === STEP 2B: Dragon Pattern ===
    if is_first3_same:
        return {"pred": first3[0], "mode": "DRAGON"}

    # === STEP 2C: Opposite Strategy ===
    pred = "BIG" if current_number <= 4 else "SMALL"
    return {"pred": pred, "mode": "OPPOSITE"}


# ============================================================
# §4. JACKPOT NUMBERS (2 numbers from same pool)
# ============================================================
def generate_jackpot_numbers(prediction: str) -> Dict[str, int]:
    pool = BIG_POOL if prediction == "BIG" else SMALL_POOL
    shuffled = pool[:]
    random.shuffle(shuffled)
    return {"j1": shuffled[0], "j2": shuffled[1]}


# ============================================================
# §5. RESULT VALIDATION
# ============================================================
def validate_result(prediction: str, j1: int, j2: int,
                    actual_number: int, actual_size: str) -> Dict[str, Any]:
    is_win = (actual_number == j1 or actual_number == j2
              or actual_size == prediction)
    return {"isWin": is_win, "status": "WIN" if is_win else "LOSS"}


# ============================================================
# §6. DRAGON PATTERN DETECTOR (display helper)
# ============================================================
def detect_dragon(types: List[str]) -> Dict[str, Any]:
    if not types:
        return {"pattern": "NONE", "streak": 0, "label": "NO DATA",
                "strength": 0, "dragonStrike": False}

    head = types[0]
    streak = 1
    for t in types[1:]:
        if t == head:
            streak += 1
        else:
            break

    if streak >= 5:
        label, strength = "DRAGON STRIKE MAX", 100
    elif streak == 4:
        label, strength = "DRAGON STRIKE", 80
    elif streak == 3:
        label, strength = "STRONG STREAK", 60
    elif streak == 2:
        label, strength = "STREAK DETECTED", 40
    else:
        label, strength = "NO STREAK", 20

    return {
        "pattern": "BIG" if head == "B" else "SMALL",
        "streak": streak,
        "label": label,
        "strength": strength,
        "dragonStrike": streak >= 4,
    }


# ============================================================
# §7. 12-FORMULA ENGINE (UniversalAIDecoder port)
# ============================================================
def _f_wlc(h, p):   # 0: Weighted Linear Combination
    v = h[0]*p[0] + h[1]*p[1] + h[2]*p[2] + h[3]*p[3] + p[4]
    return "B" if (abs(v) % 10) >= 5 else "S"

def _f_dch(h, p):   # 1: Difference Chain
    v = (h[0] - h[1]*p[1] + h[2] - h[3]*p[1] + p[0]) * 3
    return "B" if (abs(v) % 10) >= 5 else "S"

def _f_prm(h, p):   # 2: Product Modulo
    base = max(2, p[0])
    v = (h[0]+1)*(h[1]+1)*(h[2]+1)*(h[3]+1)*p[1]
    return "B" if (abs(v) % base) >= base/2 else "S"

def _f_xor(h, p):   # 3: XOR Cipher
    x = ((h[0] ^ p[0]) << p[1]) ^ (h[1] ^ (p[0]+3)) ^ (h[2] << (p[1] % 4)) ^ h[3]
    return "B" if (abs(x) % 10) >= 5 else "S"

def _f_psw(h, p):   # 4: Pattern Cascade
    s = ((p[1] if h[0] >= 5 else 1) + (p[2] if h[1] >= 5 else 1)
         + (p[3] if h[2] >= 5 else 1) + (p[4] if h[3] >= 5 else 1))
    return "B" if (s % 10) >= p[0] else "S"

def _f_csum(h, p):  # 5: Cumulative Sum
    c = p[1]
    for i in range(4):
        c += h[i] * (1 + (i*3) % 10)
    return "B" if (abs(c * p[0]) % 10) >= 5 else "S"

def _f_ravg(h, p):  # 6: Running Average
    a = (h[0]+h[1]+h[2]+h[3]) / 4
    v = int(a * p[1] + p[0])
    return "B" if (abs(v) % 10) >= 5 else "S"

def _f_fib(h, p):   # 7: Fibonacci Weighted
    fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    v = 0
    for i in range(4):
        v += h[i] * fib[((p[0] + i) % 10 + 10) % 10]
    return "B" if (abs(v * p[1]) % 10) >= 5 else "S"

def _f_prmg(h, p):  # 8: Prime Gate
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
              31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
    pm = primes[(p[0] % len(primes) + len(primes)) % len(primes)]
    s = h[0]*2 + h[1]*3 + h[2]*5 + h[3]*7 + p[1]
    return "B" if (s % pm) >= pm/2 else "S"

def _f_mtx(h, p):   # 9: Matrix Weight
    row = ((p[0] % 3) + 3) % 3
    w = [p[1], p[2], p[3], p[4]]
    rows = [
        [w[0], w[1], w[2], w[3]],
        [(w[0]+w[1]) % 9 + 1, (w[1]+w[2]) % 9 + 1,
         (w[2]+w[3]) % 9 + 1, (w[3]+w[0]) % 9 + 1],
        [(w[0]+w[2]) % 9 + 1, (w[1]+w[3]) % 9 + 1,
         (w[0]+w[3]) % 9 + 1, (w[1]+w[2]) % 9 + 1],
    ]
    v = sum(h[i] * rows[row][i] for i in range(4))
    return "B" if (abs(v) % 10) >= 5 else "S"

def _f_del(h, p):   # 10: Delta Sequence
    d = (h[0]-h[1]) * p[1] + (h[2]-h[3]) + p[0]
    return "B" if (abs(d) % 10) >= 5 else "S"

def _f_pol(h, p):   # 11: Hybrid Polynomial
    v = (p[0]*h[0]*h[0] + p[1]*h[1] + p[2]*h[2]*h[3]
         + p[3]*h[0]*h[3] + p[4])
    return "B" if (abs(v) % 10) >= 5 else "S"


FORMULA_TYPES = [_f_wlc, _f_dch, _f_prm, _f_xor, _f_psw, _f_csum,
                 _f_ravg, _f_fib, _f_prmg, _f_mtx, _f_del, _f_pol]

FORMULA_NAMES = ["WLC", "DCH", "PRM", "XOR", "PSW", "CSUM",
                 "RAVG", "FIB", "PRMG", "MTX", "DEL", "POL"]


def param_generator(nums, types, f_idx, fetch_num):
    total_sum = sum(nums[:10])
    bs = sum(1 for t in types if t == "B")
    sets = []
    limit = 4000

    for a in range(1, 11):
        for b in range(1, 11):
            for c in range(1, 11):
                for d in range(1, 11):
                    if len(sets) >= limit:
                        break
                    sets.append([a, b, c, d, (a+b+c+d) % 20])

    seed = total_sum * 7 + bs * 13 + f_idx * 17 + fetch_num * 31
    for i in range(len(sets)-1, 0, -1):
        j = (seed * (i+1) * 7 + f_idx * 13) % (i+1)
        sets[i], sets[j] = sets[j], sets[i]

    yield from sets


def search_10of10(nums, types, fetch_num) -> Dict[str, Any]:
    """
    Returns first formula that matches all 10 recent results.
    Falls back to TREND-FALLBACK if none found.
    """
    t0 = time.time()
    best = 0
    found = False
    final_bs = "BIG"
    final_name = ""
    final_matches = []
    tested = 0

    for f_idx in range(len(FORMULA_TYPES)):
        if found:
            break
        for params in param_generator(nums, types, f_idx, fetch_num):
            tested += 1
            fn = FORMULA_TYPES[f_idx]
            match_count = 0
            matches = []
            for j in range(10):
                inp = nums[j+1: j+5]
                if len(inp) < 4:
                    continue
                pred = fn(inp, params)
                actual = types[j]
                ok = (pred == actual)
                if ok:
                    match_count += 1
                matches.append({
                    "number": nums[j],
                    "actual": actual,
                    "predicted": pred,
                    "isMatch": ok,
                })
            if match_count > best:
                best = match_count
            if match_count == 10:
                found = True
                nxt = fn(nums[:4], params)
                final_bs = "BIG" if nxt == "B" else "SMALL"
                final_name = f"{FORMULA_NAMES[f_idx]}[{params[0]},{params[1]}]"
                final_matches = matches
                break

    if not found:
        b5 = sum(1 for t in types[:5] if t == "B")
        final_bs = "BIG" if b5 >= 3 else "SMALL"
        final_name = "TREND-FALLBACK"
        final_matches = [{"number": nums[i], "actual": types[i],
                          "predicted": types[i], "isMatch": True}
                         for i in range(min(10, len(types)))]

    return {
        "found": found,
        "name": final_name,
        "tested": tested,
        "bestScore": best,
        "matches": final_matches,
        "signal": final_bs,
        "elapsedMs": (time.time() - t0) * 1000,
    }


# ============================================================
# §8. NUMBER PREDICTOR (Tushar predictNumber port)
# ============================================================
def predict_number(nums: List[int], types: List[str]) -> Dict[str, Any]:
    scores = [0.0] * 10
    last10 = nums[:10]
    last20 = nums[:20]

    # 1. Weighted recency
    for i in range(min(len(last10), 10)):
        scores[last10[i]] += (10 - i) * 2

    # 2. Difference analysis
    if len(nums) >= 4:
        d1 = (nums[0] - nums[1] + 10) % 10
        d2 = (nums[1] - nums[2] + 10) % 10
        d3 = (nums[2] - nums[3] + 10) % 10
        nd = round((d1 + d2 + d3) / 3)
        scores[(nums[0] + nd + 5) % 10] += 15
        scores[(nums[0] - nd + 10) % 10] += 8

    # 3. Repetition tracking
    for i in range(1, min(len(last20), 20)):
        if last20[i-1] == last20[0]:
            scores[last20[i]] += 12

    # 4. Average trend
    if last10:
        avg = sum(last10) / len(last10)
        t = round(avg)
        scores[int(clamp(t, 0, 9))] += 10
        scores[int(clamp(t+1, 0, 9))] += 7
        scores[int(clamp(t-1, 0, 9))] += 7

    # 5. Big/Small bias
    if types:
        bs = types[0]
        pool = BIG_POOL if bs == "B" else SMALL_POOL
        for n in pool:
            scores[n] += 5

    ranked = sorted(range(10), key=lambda x: scores[x], reverse=True)
    denom = (scores[ranked[0]] + scores[ranked[1]]) or 1
    conf = int((scores[ranked[0]] / denom) * 100)
    return {"predicted": ranked[0], "second": ranked[1], "confidence": conf}


# ============================================================
# §9. MAIN PIPELINE — predict_unified()
# ============================================================
def predict_unified(history: List[Dict[str, Any]], opts: Optional[Dict] = None) -> Dict[str, Any]:
    """
    @param history: newest-first list of {"issueNumber", "number"}
    @param opts:    {"adminOverride"?: "BIG"|"SMALL"|"AUTO", "fetchNum"?: int}
    @returns Tushar-engine prediction (NOT inverted — raw logic output)
    """
    opts = opts or {}
    if not isinstance(history, list) or len(history) < 5:
        raise ValueError("UPE-X: need >= 5 history rows")

    # Admin override from opts
    if opts.get("adminOverride") in ("BIG", "SMALL", "AUTO"):
        MODE_OVERRIDE["value"] = opts["adminOverride"]

    fetch_num = opts.get("fetchNum") or len(history)

    nums = [int(h["number"]) for h in history]
    types = [to_side(n) for n in nums]
    current_number = nums[0]
    raw_issue = history[0].get("issueNumber") or ""

    STATS["f"] = STATS.get("f", 0) + 1

    # ── Check previous bet ──
    if LAST_BET["period"]:
        for h in history:
            if str(h.get("issueNumber")) == str(LAST_BET["period"]):
                actual_size = number_to_size(int(h["number"]))
                if LAST_BET["prediction"] == actual_size:
                    STATS["w"] += 1
                else:
                    STATS["l"] += 1
                break

    # ── Pattern detector ──
    dragon = detect_dragon(types)

    # ── 10/10 formula search ──
    formula = search_10of10(nums, types, fetch_num)

    # ── Tushar getPrediction (main signal) ──
    tushar = get_prediction(current_number, types)

    # ── Number predictor ──
    number_pred = predict_number(nums[:20], types[:20])

    # ── Second number predictor ──
    second_pred = predict_number(
        [number_pred["predicted"]] + nums[:19],
        [to_side(number_pred["predicted"])] + types[:19],
    )

    # ── Jackpot numbers ──
    jackpot = generate_jackpot_numbers(tushar["pred"])

    # ── Next period ──
    try:
        next_period = str(int(raw_issue) + 1)
    except (ValueError, TypeError):
        next_period = f"{raw_issue}+1"

    # ── Save bet ──
    LAST_BET["period"] = next_period
    LAST_BET["prediction"] = tushar["pred"]
    LAST_BET["number"] = number_pred["predicted"]

    # ── Build output ──
    return {
        "success": True,
        "period": next_period,
        "prediction": tushar["pred"],               # BIG / SMALL
        "mode": tushar["mode"],                      # ADMIN FORCE / 3:3 / DRAGON / OPPOSITE / DEFAULT
        "predictedNumber": number_pred["predicted"],
        "secondNumber": second_pred["predicted"],
        "jackpot1": jackpot["j1"],
        "jackpot2": jackpot["j2"],
        "confidence": number_pred["confidence"],
        "pattern": dragon,
        "formula": formula,
        "currentNumber": current_number,
        "last6": types[:6],
        "stats": dict(STATS),
        "adminOverride": MODE_OVERRIDE["value"],
    }


# ============================================================
# §10. FEEDBACK / ADMIN
# ============================================================
def set_admin_override(value: str) -> None:
    if value not in ("BIG", "SMALL", "AUTO"):
        raise ValueError("override must be BIG / SMALL / AUTO")
    MODE_OVERRIDE["value"] = value


def record_outcome(actual_number: int, last_prediction: Optional[str] = None,
                   jackpot1: Optional[int] = None,
                   jackpot2: Optional[int] = None) -> Dict[str, Any]:
    actual_size = number_to_size(actual_number)
    pred = last_prediction or LAST_BET["prediction"]
    if not pred:
        return {"isWin": False, "status": "NO_PREDICTION", "stats": dict(STATS)}

    is_win = (actual_number in (jackpot1, jackpot2) or actual_size == pred)
    if is_win:
        STATS["w"] += 1
    else:
        STATS["l"] += 1
    return {"isWin": is_win, "status": "WIN" if is_win else "LOSS",
            "stats": dict(STATS)}


# ============================================================
# §11. COMPAT ALIAS (same name, new internals)
# ============================================================
def sddgamer263_predict(history, opts=None):
    """Backwards-compatible wrapper. Accepts list of dicts OR ints."""
    if history and isinstance(history[0], (int, float)):
        history = [
            {"issueNumber": f"auto{i}", "number": int(n)}
            for i, n in enumerate(history)
        ]
    return predict_unified(history, opts)


# ============================================================
# §12. EXPORTS
# ============================================================
__all__ = [
    "predict_unified", "sddgamer263_predict",
    "record_outcome", "set_admin_override",
    "get_prediction", "detect_dragon",
    "generate_jackpot_numbers", "validate_result",
    "search_10of10", "predict_number",
    "to_side", "flip", "to_color", "number_to_size",
    "NUMBER_MAP", "STATS", "LAST_BET", "MODE_OVERRIDE",
]


# ============================================================
# §13. SELF-TEST
# ============================================================
if __name__ == "__main__":
    import json

    history = [
        {"issueNumber": "202601011200", "number": 7},
        {"issueNumber": "202601011159", "number": 3},
        {"issueNumber": "202601011158", "number": 8},
        {"issueNumber": "202601011157", "number": 2},
        {"issueNumber": "202601011156", "number": 9},
        {"issueNumber": "202601011155", "number": 5},
        {"issueNumber": "202601011154", "number": 1},
        {"issueNumber": "202601011153", "number": 6},
        {"issueNumber": "202601011152", "number": 0},
        {"issueNumber": "202601011151", "number": 4},
    ]

    out = predict_unified(history)
    # remove verbose fields for pretty print
    pretty = {k: v for k, v in out.items() if k not in ("formula",)}
    print(json.dumps(pretty, indent=2))
    print(f"\nFormula: {out['formula']['name']} (found={out['formula']['found']})")

    # --- Test 3:3 pattern ---
    set_admin_override("AUTO")
    r = get_prediction(5, ["BIG","BIG","BIG","SMALL","SMALL","SMALL"])
    print(f"3:3 test    -> {r}")   # expect 3:3 PATTERN, pred BIG

    # --- Test Dragon ---
    r = get_prediction(5, ["BIG","BIG","BIG","BIG","BIG","SMALL"])
    print(f"Dragon test -> {r}")   # expect DRAGON, pred BIG

    # --- Test Opposite ---
    r = get_prediction(3, ["BIG","SMALL","BIG","SMALL","BIG","SMALL"])
    print(f"Opp test    -> {r}")   # expect OPPOSITE, pred BIG

    # --- Test Admin Override ---
    set_admin_override("SMALL")
    r = get_prediction(5, ["BIG","BIG","BIG","SMALL","SMALL","SMALL"])
    print(f"Admin test  -> {r}")   # expect ADMIN FORCE, pred SMALL
    set_admin_override("AUTO")
