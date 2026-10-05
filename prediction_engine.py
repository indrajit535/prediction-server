"""
CYBER TAMILAN — prediction_engine.py
=====================================
Prediction logic:
  1. Last 3 results me jo zyada ho (BIG/SMALL) wahi final prediction.
  2. Zig-Zag detection (BSB / SBS) -> last result ka opposite.
  3. Zig-Zag se normal switch jab BSS / SBB aaye.
  4. Predicted number: last 10 results me jo numbers missing hain,
     unme se highest frequency wala pick karo (BIG/SMALL category ke hisaab se).
Exposes: sddgamer263_predict(current_number, period)
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import requests


# ============================================================
# CONSTANTS
# ============================================================
CONFIG = {
    "HTTP_TIMEOUT": 15,
    "CACHE_TTL": 50,
    "HISTORY_LIMIT": 10,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


# ============================================================
# HELPERS
# ============================================================
def get_big_small(n) -> str:
    """0-4 = SMALL (RED), 5-9 = BIG (GREEN)"""
    try:
        return "BIG" if int(n) >= 5 else "SMALL"
    except (ValueError, TypeError):
        return "SMALL"


def get_color(n) -> str:
    """5-9 = GREEN, 0-4 = RED"""
    try:
        return "GREEN" if int(n) >= 5 else "RED"
    except (ValueError, TypeError):
        return "RED"


def opposite(size: str) -> str:
    return "SMALL" if size == "BIG" else "BIG"


# ============================================================
# STATE
# ============================================================
class _State:
    def __init__(self):
        self.prediction_history: List[Dict[str, Any]] = []
        self.win_count: int = 0
        self.loss_count: int = 0
        self.consecutive_losses: int = 0
        self.last_mode: str = "NORMAL"

    def reset(self):
        self.__init__()


STATE = _State()
_CACHE: Dict[str, Dict[str, Any]] = {}

# Rolling window of sizes (BIG/SMALL)
_RESULT_WINDOW: List[str] = []
# Full history of actual numbers
_RESULT_NUMBERS: List[int] = []
# Zig-zag mode track
_ZIGZAG_ACTIVE: bool = False


# ============================================================
# NUMBER PICKING (NEW LOGIC)
# ============================================================
def _get_missing_numbers(last_n: int = 10) -> List[int]:
    """
    Last N results me jo numbers (0-9) nahi aaye, unki list.
    Agar history chhoti hai to jo available hai usi se check karo.
    """
    if not _RESULT_NUMBERS:
        return list(range(10))
    recent = _RESULT_NUMBERS[-last_n:]
    present = set(recent)
    return [n for n in range(10) if n not in present]


def _get_frequency(number: int) -> int:
    """Full history me number ki frequency."""
    return _RESULT_NUMBERS.count(number)


def _pick_predicted_number(prediction: str) -> int:
    """
    Prediction (BIG/SMALL) ke hisaab se number pick karo:
      1. Last 10 results me missing numbers nikalo.
      2. BIG prediction -> missing BIG numbers (5-9) me se
         highest frequency wala lo.
      3. SMALL prediction -> missing SMALL numbers (0-4) me se
         highest frequency wala lo.
      4. Agar us category me koi missing nahi, to us category ke
         sabhi numbers me se highest frequency wala lo.
    """
    missing = _get_missing_numbers(10)

    if prediction == "BIG":
        candidates = [n for n in missing if n >= 5]
        if not candidates:
            candidates = list(range(5, 10))
    else:
        candidates = [n for n in missing if n < 5]
        if not candidates:
            candidates = list(range(0, 5))

    # Highest frequency; tie pe chhota number pehle
    best = max(candidates, key=lambda n: (_get_frequency(n), -n))
    return best


# ============================================================
# CORE PREDICTION LOGIC (BIG/SMALL)
# ============================================================
def _detect_zigzag(last3: List[str]) -> bool:
    """BSB ya SBS = zig-zag pattern."""
    if len(last3) < 3:
        return False
    return last3[0] == last3[2] and last3[0] != last3[1]


def _zigzag_broken(last3: List[str]) -> bool:
    """BSS ya SBB = zig-zag toota."""
    if len(last3) < 3:
        return False
    return last3[0] == last3[1] and last3[0] != last3[2]


def _normal_prediction(last3: List[str]) -> str:
    """Last 3 me jo zyada ho wahi prediction."""
    big_count = last3.count("BIG")
    small_count = last3.count("SMALL")

    if big_count > small_count:
        return "BIG"
    elif small_count > big_count:
        return "SMALL"
    else:
        return opposite(last3[-1])


def _build_prediction(last3: List[str]) -> Dict[str, Any]:
    """
    Main decision function (BIG/SMALL):
      - Zig-zag detect karo
      - Zig-zag active hai to last ka opposite
      - Zig-zag toota to normal pe switch
      - Warna normal: last 3 me jo zyada
    """
    global _ZIGZAG_ACTIVE

    reason = ""
    mode = "NORMAL"
    pred = None

    # --- Zig-Zag check ---
    if _detect_zigzag(last3):
        _ZIGZAG_ACTIVE = True
        mode = "ZIGZAG"
        pred = opposite(last3[-1])
        reason = (
            f"ZIGZAG detected ({''.join(last3)}) -> "
            f"opposite of last ({last3[-1]}) = {pred}"
        )
        STATE.last_mode = "ZIGZAG"
        return {"prediction": pred, "mode": mode, "reason": reason}

    # --- Zig-Zag broken? ---
    if _ZIGZAG_ACTIVE and _zigzag_broken(last3):
        _ZIGZAG_ACTIVE = False
        mode = "NORMAL"
        reason = f"ZIGZAG broken ({''.join(last3)}) -> switching to NORMAL"

    # --- Normal prediction ---
    if not _ZIGZAG_ACTIVE:
        pred = _normal_prediction(last3)
        if not reason:
            big_c = last3.count("BIG")
            small_c = last3.count("SMALL")
            reason = (
                f"NORMAL: last3={''.join(last3)} "
                f"(BIG={big_c}, SMALL={small_c}) -> {pred}"
            )
        mode = "NORMAL"
        STATE.last_mode = "NORMAL"

    return {"prediction": pred, "mode": mode, "reason": reason}


# ============================================================
# MAIN WRAPPER
# ============================================================
def sddgamer263_predict(current_number: int, period: str) -> Dict[str, Any]:
    """
    app.py compatible wrapper.
    current_number: 0-9
    period: issue number / period string
    """
    global _RESULT_WINDOW, _RESULT_NUMBERS

    # Cache check
    cached = _CACHE.get(period)
    if cached and (time.time() - cached.get("_ts", 0)) < CONFIG["CACHE_TTL"]:
        return {k: v for k, v in cached.items() if k != "_ts"}

    current_size = get_big_small(current_number)
    current_color = get_color(current_number)

    # Rolling window update (sizes)
    _RESULT_WINDOW.append(current_size)
    if len(_RESULT_WINDOW) > CONFIG["HISTORY_LIMIT"]:
        _RESULT_WINDOW = _RESULT_WINDOW[-CONFIG["HISTORY_LIMIT"]:]

    # Full history update (numbers)
    _RESULT_NUMBERS.append(int(current_number))
    # Cap history to avoid unbounded growth (keep last 500)
    if len(_RESULT_NUMBERS) > 500:
        _RESULT_NUMBERS = _RESULT_NUMBERS[-500:]

    # Last 3 sizes
    last3 = _RESULT_WINDOW[-3:] if len(_RESULT_WINDOW) >= 3 else _RESULT_WINDOW[:]

    # Not enough data
    if len(last3) < 3:
        result = {
            "predictedSize": "ANALYZING",
            "predictedNumber": int(current_number),
            "confidence": 40,
            "reason": f"Building window... ({len(last3)}/3)",
            "riskLevel": "MEDIUM",
            "riskScore": 50,
            "advice": "Wait for 3 results.",
            "mode": "NORMAL",
            "period": period,
            "currentNumber": int(current_number),
            "currentSize": current_size,
            "currentColor": current_color,
            "timestamp": datetime.now(timezone.utc).strftime("%I:%M %p"),
            "_ts": time.time(),
        }
        _CACHE[period] = result
        return {k: v for k, v in result.items() if k != "_ts"}

    # BIG/SMALL prediction
    pred_data = _build_prediction(last3)

    # Predicted NUMBER using new logic
    predicted_number = _pick_predicted_number(pred_data["prediction"])

    # Confidence
    if pred_data["mode"] == "ZIGZAG":
        confidence = 72
    else:
        big_c = last3.count("BIG")
        small_c = last3.count("SMALL")
        diff = abs(big_c - small_c)
        confidence = 55 + diff * 8
    confidence = max(42, min(77, confidence))

    # Risk
    if pred_data["mode"] == "ZIGZAG":
        risk_level, risk_score = "LOW", 28
    elif confidence >= 70:
        risk_level, risk_score = "LOW", 25
    elif confidence >= 58:
        risk_level, risk_score = "MEDIUM", 50
    else:
        risk_level, risk_score = "HIGH", 72

    # Advice
    if pred_data["mode"] == "ZIGZAG":
        advice = "ZIGZAG active: play opposite of last result."
    elif risk_level == "LOW":
        advice = "LOW RISK: Strong setup. Follow plan."
    elif risk_level == "MEDIUM":
        advice = "MEDIUM RISK: Moderate stake."
    else:
        advice = "HIGH RISK: Small stake or skip."

    total = STATE.win_count + STATE.loss_count
    win_rate = round(STATE.win_count / total * 100) if total > 0 else 0

    # Missing info (for transparency)
    missing = _get_missing_numbers(10)
    missing_freq = {n: _get_frequency(n) for n in missing}

    result = {
        "predictedSize": pred_data["prediction"],
        "predictedNumber": predicted_number,
        "confidence": confidence,
        "reason": pred_data["reason"],
        "riskLevel": risk_level,
        "riskScore": risk_score,
        "advice": advice,
        "mode": pred_data["mode"],
        "last3": "".join(last3),
        "missingNumbers": missing,
        "missingFreq": missing_freq,
        "winCount": STATE.win_count,
        "lossCount": STATE.loss_count,
        "winRate": win_rate,
        "consecutiveLosses": STATE.consecutive_losses,
        "period": period,
        "currentNumber": int(current_number),
        "currentSize": current_size,
        "currentColor": current_color,
        "timestamp": datetime.now(timezone.utc).strftime("%I:%M %p"),
        "_ts": time.time(),
    }

    _CACHE[period] = result
    if len(_CACHE) > 200:
        keys = sorted(_CACHE.keys(), key=lambda k: _CACHE[k].get("_ts", 0))
        for k in keys[:100]:
            _CACHE.pop(k, None)

    return {k: v for k, v in result.items() if k != "_ts"}


def clear_engine_cache():
    _CACHE.clear()


def reset():
    global _RESULT_WINDOW, _RESULT_NUMBERS, _ZIGZAG_ACTIVE
    STATE.reset()
    _RESULT_WINDOW = []
    _RESULT_NUMBERS = []
    _ZIGZAG_ACTIVE = False


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    print("Testing prediction_engine.py ...")
    reset()
    # Simulate a sequence
    test_nums = [7, 5, 2, 8, 1, 9, 0, 6, 3, 4, 7, 8, 2, 5, 9]
    for i, num in enumerate(test_nums):
        out = sddgamer263_predict(num, f"P{i}")
        print(
            f"  num={num} size={out['currentSize']:5s} "
            f"last3={out.get('last3','---'):3s} "
            f"mode={out['mode']:6s} "
            f"-> {out['predictedSize']:6s} #{out['predictedNumber']} "
            f"({out['confidence']}%)"
        )
        print(f"     reason: {out['reason']}")
        if "missingNumbers" in out:
            print(f"     missing: {out['missingNumbers']} freq: {out['missingFreq']}")
