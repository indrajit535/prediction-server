"""
CYBER TAMILAN — prediction_engine.py

Prediction engine requested behavior:

1. Build the BIG/SMALL decision from the last three observed results.
2. If the latest three sizes are BSB or SBS, enable ZIGZAG mode and
   predict the opposite of the newest size.
3. When a zig-zag sequence breaks (BSS or SBB), return to NORMAL mode.
4. Select a predicted number independently from the current result.  Among
   numbers matching the predicted size, prefer the least frequent numbers in
   the last ten observed results.  Missing numbers therefore get priority.

This is a heuristic only; it cannot guarantee future outcomes.
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CONFIG = {
    "CACHE_TTL": 50,
    "HISTORY_LIMIT": 10,
    "CACHE_LIMIT": 200,
}


# The engine stores actual observed results, not synthetic copies of the
# current number.  This fixes the original last3_numbers bug.
_RESULT_NUMBERS: List[int] = []
_ZIGZAG_ACTIVE = False
_CACHE: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_number(number: Any) -> int:
    """Return a valid digit in the range 0..9."""
    value = int(number)
    if not 0 <= value <= 9:
        raise ValueError("current_number must be an integer from 0 to 9")
    return value


def get_big_small(number: Any) -> str:
    """0-4 = SMALL; 5-9 = BIG."""
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except (TypeError, ValueError):
        return "SMALL"


def get_color(number: Any) -> str:
    """0-4 = RED; 5-9 = GREEN."""
    try:
        return "GREEN" if int(number) >= 5 else "RED"
    except (TypeError, ValueError):
        return "RED"


def opposite(size: str) -> str:
    return "SMALL" if size == "BIG" else "BIG"


def _sizes(numbers: List[int]) -> List[str]:
    return [get_big_small(number) for number in numbers]


def _short_size(size: str) -> str:
    return "B" if size == "BIG" else "S"


def _pattern(sizes: List[str]) -> str:
    return "".join(_short_size(size) for size in sizes)


# ---------------------------------------------------------------------------
# Size prediction
# ---------------------------------------------------------------------------


def _detect_zigzag(last3: List[str]) -> bool:
    """Return True for BSB or SBS."""
    return len(last3) == 3 and last3[0] == last3[2] and last3[0] != last3[1]


def _zigzag_broken(last3: List[str]) -> bool:
    """Return True for BSS or SBB: first two equal, newest differs."""
    return len(last3) == 3 and last3[0] == last3[1] and last3[0] != last3[2]


def _normal_prediction(last3: List[str]) -> str:
    """Choose the majority size; use the opposite of newest on a tie."""
    big_count = last3.count("BIG")
    small_count = last3.count("SMALL")

    if big_count > small_count:
        return "BIG"
    if small_count > big_count:
        return "SMALL"
    return opposite(last3[-1])


def _build_size_prediction(last3: List[str]) -> Dict[str, str]:
    """Build the size prediction and maintain zig-zag mode."""
    global _ZIGZAG_ACTIVE

    if _detect_zigzag(last3):
        _ZIGZAG_ACTIVE = True
        prediction = opposite(last3[-1])
        return {
            "prediction": prediction,
            "mode": "ZIGZAG",
            "reason": (
                f"ZIGZAG detected ({_pattern(last3)}) -> "
                f"opposite of newest {last3[-1]} = {prediction}"
            ),
        }

    if _ZIGZAG_ACTIVE and _zigzag_broken(last3):
        _ZIGZAG_ACTIVE = False
        prediction = _normal_prediction(last3)
        return {
            "prediction": prediction,
            "mode": "NORMAL",
            "reason": (
                f"ZIGZAG broken ({_pattern(last3)}) -> NORMAL majority "
                f"prediction = {prediction}"
            ),
        }

    if _ZIGZAG_ACTIVE:
        # Keep the mode only while the latest three remain alternating.  This
        # prevents a stale zig-zag flag from forcing unrelated future results.
        _ZIGZAG_ACTIVE = False

    prediction = _normal_prediction(last3)
    return {
        "prediction": prediction,
        "mode": "NORMAL",
        "reason": (
            f"NORMAL: last3={_pattern(last3)} "
            f"(BIG={last3.count('BIG')}, SMALL={last3.count('SMALL')}) "
            f"-> {prediction}"
        ),
    }


# ---------------------------------------------------------------------------
# Number selection
# ---------------------------------------------------------------------------


def _select_prediction_number(predicted_size: str, history: List[int]) -> Dict[str, Any]:
    """Choose a low-frequency number matching the predicted size.

    Missing numbers have frequency zero and are preferred automatically.  A
    deterministic tie-breaker makes the output stable: newer-looking digits
    are not preferred; the smallest digit wins ties.
    """
    recent = history[-CONFIG["HISTORY_LIMIT"] :]
    frequencies = Counter(recent)
    candidates = [
        number
        for number in range(10)
        if get_big_small(number) == predicted_size
    ]
    candidates.sort(key=lambda number: (frequencies[number], number))
    selected = candidates[0]

    return {
        "number": selected,
        "color": get_color(selected),
        "frequencyInLast10": frequencies[selected],
        "candidateFrequencies": {
            str(number): frequencies[number] for number in candidates
        },
        "recentNumbers": recent,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sddgamer263_predict(current_number: int, period: str) -> Dict[str, Any]:
    """Record one observed result and predict the next result.

    Args:
        current_number: The newly observed digit, 0..9.
        period: Unique issue/period identifier. Repeated periods are served
            from the short-lived cache.
    """
    number = normalize_number(current_number)
    period = str(period)

    cached = _CACHE.get(period)
    if cached and time.time() - cached["_ts"] < CONFIG["CACHE_TTL"]:
        return {key: value for key, value in cached.items() if key != "_ts"}

    _RESULT_NUMBERS.append(number)
    del _RESULT_NUMBERS[:-CONFIG["HISTORY_LIMIT"]]

    current_size = get_big_small(number)
    current_color = get_color(number)
    sizes = _sizes(_RESULT_NUMBERS)
    last3 = sizes[-3:]

    if len(last3) < 3:
        result: Dict[str, Any] = {
            "predictedSize": "ANALYZING",
            "predictedNumber": None,
            "predictedColor": None,
            "confidence": 40,
            "reason": f"Building window... ({len(last3)}/3)",
            "riskLevel": "MEDIUM",
            "riskScore": 50,
            "advice": "Wait for three observed results.",
            "mode": "NORMAL",
            "last3": _pattern(last3),
            "last10Numbers": _RESULT_NUMBERS[-CONFIG["HISTORY_LIMIT"] :],
            "period": period,
            "currentNumber": number,
            "currentSize": current_size,
            "currentColor": current_color,
            "timestamp": datetime.now(timezone.utc).strftime("%I:%M %p"),
            "_ts": time.time(),
        }
        _CACHE[period] = result
        return {key: value for key, value in result.items() if key != "_ts"}

    size_data = _build_size_prediction(last3)
    predicted_size = size_data["prediction"]
    number_data = _select_prediction_number(predicted_size, _RESULT_NUMBERS)

    if size_data["mode"] == "ZIGZAG":
        confidence = 72
    else:
        difference = abs(last3.count("BIG") - last3.count("SMALL"))
        confidence = 55 + difference * 8
    confidence = max(42, min(77, confidence))

    if size_data["mode"] == "ZIGZAG":
        risk_level, risk_score = "LOW", 28
        advice = "ZIGZAG mode: predicted size is opposite to the newest size."
    elif confidence >= 70:
        risk_level, risk_score = "LOW", 25
        advice = "LOW RISK: majority setup is stronger; use caution."
    elif confidence >= 58:
        risk_level, risk_score = "MEDIUM", 50
        advice = "MEDIUM RISK: moderate confidence; consider skipping."
    else:
        risk_level, risk_score = "HIGH", 72
        advice = "HIGH RISK: low confidence; skip or use minimal exposure."

    result = {
        "predictedSize": predicted_size,
        "predictedNumber": number_data["number"],
        "predictedColor": number_data["color"],
        "predictedNumberFrequencyInLast10": number_data["frequencyInLast10"],
        "candidateFrequencies": number_data["candidateFrequencies"],
        "confidence": confidence,
        "reason": size_data["reason"],
        "riskLevel": risk_level,
        "riskScore": risk_score,
        "advice": advice,
        "mode": size_data["mode"],
        "last3": _pattern(last3),
        "last10Numbers": number_data["recentNumbers"],
        "period": period,
        "currentNumber": number,
        "currentSize": current_size,
        "currentColor": current_color,
        "timestamp": datetime.now(timezone.utc).strftime("%I:%M %p"),
        "_ts": time.time(),
    }

    _CACHE[period] = result
    if len(_CACHE) > CONFIG["CACHE_LIMIT"]:
        oldest = sorted(_CACHE, key=lambda key: _CACHE[key]["_ts"])
        for key in oldest[: len(oldest) - CONFIG["CACHE_LIMIT"]]:
            del _CACHE[key]

    return {key: value for key, value in result.items() if key != "_ts"}


def clear_engine_cache() -> None:
    _CACHE.clear()


def reset() -> None:
    global _ZIGZAG_ACTIVE
    _RESULT_NUMBERS.clear()
    _CACHE.clear()
    _ZIGZAG_ACTIVE = False


if __name__ == "__main__":
    reset()
    print("Testing prediction_engine.py ...")
    for index, number in enumerate([7, 5, 2, 8, 1, 9, 0, 6, 3, 4], start=1):
        output = sddgamer263_predict(number, f"P{index}")
        print(
            f"num={number} size={output['currentSize']} "
            f"last3={output['last3']} mode={output['mode']} "
            f"-> {output['predictedSize']} / {output['predictedNumber']} "
            f"({output['confidence']}%) | {output['reason']}"
        )
