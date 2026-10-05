"""
CYBER TAMILAN — prediction_engine.py
=====================================
Prediction logic:
  1. Last 3 results me jo zyada ho (BIG/SMALL) wahi final prediction.
  2. Zig-Zag detection (BSB / SBS) -> last result ka opposite.
  3. Zig-Zag se normal switch jab BSS / SBB aaye.
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
        self.last_mode: str = "NORMAL"   # NORMAL or ZIGZAG

    def reset(self):
        self.__init__()


STATE = _State()
_CACHE: Dict[str, Dict[str, Any]] = {}

# Last few results ka rolling window (sizes)
_RESULT_WINDOW: List[str] = []
# Zig-zag mode track karne ke liye
_ZIGZAG_ACTIVE: bool = False


# ============================================================
# CORE PREDICTION LOGIC
# ============================================================
def _detect_zigzag(last3: List[str]) -> bool:
    """
    BSB ya SBS = zig-zag pattern.
    last3 = [oldest, middle, newest]
    """
    if len(last3) < 3:
        return False
    return last3[0] == last3[2] and last3[0] != last3[1]


def _zigzag_broken(last3: List[str]) -> bool:
    """
    Zig-zag tootne ka signal: BSS ya SBB (ya RSS/GBB type)
    Matlab pehle 2 same, teesra different.
    """
    if len(last3) < 3:
        return False
    return last3[0] == last3[1] and last3[0] != last3[2]


def _normal_prediction(last3: List[str], last3_numbers: List[int]) -> str:
    """
    Last 3 me jo zyada ho wahi prediction.
    Color check bhi: agar 5/7 (GREEN) zyada -> opposite RED -> SMALL? 
    Nahi, aapke hisaab se:
      7/5/2 -> BIG zyada -> BIG prediction
      Color 5/7 = GREEN -> opposite = RED -> matlab BIG (8/6)
    Matlab BIG ka opposite SMALL nahi, balki BIG hi rahega kyunki
    GREEN ka opposite RED hota hai jo SMALL hai... 
    
    Wait — aapne likha: "colour 5/7 matlab green to green ka opposite red 
    to final prediction asa hoga BIG 8/6 number"
    
    Matlab: agar GREEN zyada hai to prediction BIG hi hoga (8/6).
    Agar RED zyada hai to prediction SMALL hoga (2/4).
    """
    big_count = last3.count("BIG")
    small_count = last3.count("SMALL")

    if big_count > small_count:
        return "BIG"
    elif small_count > big_count:
        return "SMALL"
    else:
        # Tie: last result ka opposite (safe fallback)
        return opposite(last3[-1])


def _build_prediction(last3: List[str], last3_numbers: List[int]) -> Dict[str, Any]:
    """
    Main decision function:
      - Zig-zag detect karo
      - Zig-zag active hai to last ka opposite
      - Zig-zag toota to normal pe switch
      - Warna normal: last 3 me jo zyada
    """
    global _ZIGZAG_ACTIVE

    reason = ""
    mode = "NORMAL"

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
        pred = _normal_prediction(last3, last3_numbers)
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
    global _RESULT_WINDOW

    # Cache check
    cached = _CACHE.get(period)
    if cached and (time.time() - cached.get("_ts", 0)) < CONFIG["CACHE_TTL"]:
        return {k: v for k, v in cached.items() if k != "_ts"}

    current_size = get_big_small(current_number)
    current_color = get_color(current_number)

    # Rolling window update (max 10)
    _RESULT_WINDOW.append(current_size)
    if len(_RESULT_WINDOW) > CONFIG["HISTORY_LIMIT"]:
        _RESULT_WINDOW = _RESULT_WINDOW[-CONFIG["HISTORY_LIMIT"]:]

    # Last 3 sizes
    last3 = _RESULT_WINDOW[-3:] if len(_RESULT_WINDOW) >= 3 else _RESULT_WINDOW[:]
    # last3 numbers (sirf current number available hai, baaki synthetic nahi)
    last3_numbers = [int(current_number)] * len(last3)

    # Prediction
    if len(last3) < 3:
        # Not enough data
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

    pred_data = _build_prediction(last3, last3_numbers)

    # Confidence: zigzag me high, normal me medium
    if pred_data["mode"] == "ZIGZAG":
        confidence = 72
    else:
        big_c = last3.count("BIG")
        small_c = last3.count("SMALL")
        diff = abs(big_c - small_c)
        confidence = 55 + diff * 8   # 3-0 -> 79, 2-1 -> 63

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

    result = {
        "predictedSize": pred_data["prediction"],
        "predictedNumber": int(current_number),
        "confidence": confidence,
        "reason": pred_data["reason"],
        "riskLevel": risk_level,
        "riskScore": risk_score,
        "advice": advice,
        "mode": pred_data["mode"],
        "last3": "".join(last3),
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
    global _RESULT_WINDOW, _ZIGZAG_ACTIVE
    STATE.reset()
    _RESULT_WINDOW = []
    _ZIGZAG_ACTIVE = False


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    print("Testing prediction_engine.py ...")
    reset()
    # Simulate: 7(BIG), 5(BIG), 2(SMALL) -> BIG zyada -> BIG
    for num in [7, 5, 2, 8, 1, 9, 0, 6, 3, 4]:
        out = sddgamer263_predict(num, f"P{num}")
        print(f"  num={num} size={out['currentSize']} "
              f"last3={out['last3']} mode={out['mode']} "
              f"-> {out['predictedSize']} ({out['confidence']}%) "
              f"| {out['reason']}")
