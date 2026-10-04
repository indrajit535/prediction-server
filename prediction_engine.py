"""
CYBER TAMILAN — PYTHON PORT
================================
100% port of the HTML <script> prediction engine.

REMOVED (old Python logic):
  ❌ MAFIYA AI Engine
  ❌ 250+ Pattern Database
  ❌ 200+ CPU Patterns (Bunny AI)
  ❌ RIFU Engine
  ❌ Ultimate Pro Engine
  ❌ Hyper Engine (8 Logic Modes)
  ❌ Ensemble Voting
  ❌ 7-Layer WEBC0DC V2 Engine
  ❌ 11-Pattern Engine
  ❌ 30-Round Ratio
  ❌ 2-Level Fixed Win
  ❌ Anti-Loss Strategy (old style)

ADDED (new HTML logic, 100%):
  ✅ ultraPatternEngine()
  ✅ assessRisk()
  ✅ getSmartAdvice()
  ✅ Live streak / volatility / pattern-power
  ✅ ANTI-LOSS reversal (after 3 consecutive losses)
"""

import time
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


# ============================================================
# CONSTANTS (mirrors HTML)
# ============================================================
CONFIG = {
    "HISTORY_LIMIT": 45,       # engine uses slice(0, 45)
    "MIN_CONFIDENCE": 42,
    "MAX_CONFIDENCE": 77,
    "ANTI_LOSS_THRESHOLD": 3,  # consecutiveLosses >= 3 triggers reversal
    "CACHE_TTL": 50,
}


# ============================================================
# HELPERS
# ============================================================

def get_big_small(n: int) -> str:
    """Mirrors JS:  return n >= 5 ? "BIG" : "SMALL" """
    try:
        return "BIG" if int(n) >= 5 else "SMALL"
    except (ValueError, TypeError):
        return "SMALL"


# ============================================================
# STATE (mirrors HTML variables)
# ============================================================
class State:
    def __init__(self):
        self.prediction_history: List[Dict[str, Any]] = []
        self.last_200_results: List[Dict[str, Any]] = []
        self.win_count: int = 0
        self.loss_count: int = 0
        self.consecutive_losses: int = 0

    def reset(self):
        self.__init__()


STATE = State()


# ============================================================
# CORE ENGINE — 100% port of ultraPatternEngine()
# ============================================================
def ultra_pattern_engine(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    JS:
      function ultraPatternEngine(history){
        if(!history||history.length<8)return{prediction:"ANALYZING",confidence:30,
          patternPower:25,streak:0,volatility:0.5,description:"Building matrix..."};
        ...
      }
    """
    if not history or len(history) < 8:
        return {
            "prediction": "ANALYZING",
            "confidence": 30,
            "patternPower": 25,
            "streak": 0,
            "volatility": 0.5,
            "description": "Building matrix...",
        }

    length = min(45, len(history))
    recent = history[:length]

    big = 0
    small = 0
    for r in recent:
        if r.get("size") == "BIG":
            big += 1
        else:
            small += 1

    big_pct = big / length
    small_pct = small / length

    # streak (consecutive same results from index 0)
    streak = 1
    limit = min(20, len(history))
    for i in range(1, limit):
        if history[i]["size"] == history[i - 1]["size"]:
            streak += 1
        else:
            break

    # alternation ratio
    alt = 0
    alt_limit = min(18, len(history))
    for i in range(1, alt_limit):
        if history[i]["size"] != history[i - 1]["size"]:
            alt += 1
    alt_ratio = alt / max(1, min(17, len(history) - 1))

    # volatility
    ch = 0
    vl = min(14, len(history) - 1)
    for i in range(1, vl + 1):
        if history[i]["size"] != history[i - 1]["size"]:
            ch += 1
    volatility = ch / (vl if vl else 1)

    # momentum bias
    ms = 0
    mom_limit = min(12, len(history))
    for i in range(mom_limit):
        ms += (1 if history[i]["size"] == "BIG" else -1) * (12 - i)
    mb = ms / 78

    prediction = ""
    raw_conf = 50
    pattern_power = 45
    description = ""

    # ---- Branch 1: REVERSAL (streak >= 4)
    if streak >= 4:
        prediction = "SMALL" if history[0]["size"] == "BIG" else "BIG"
        raw_conf = 58 + min(30, streak * 5.5)
        pattern_power = 70 + (streak - 3) * 4
        description = f"REVERSAL: {streak}-streak exhaustion -> mean reversion"

    # ---- Branch 2: ZIGZAG LOCK
    elif alt_ratio > 0.72 and length >= 10:
        prediction = "SMALL" if history[0]["size"] == "BIG" else "BIG"
        raw_conf = 62 + alt_ratio * 14
        pattern_power = 68
        description = f"ZIGZAG LOCK: {round(alt_ratio * 100)}% flip rate"

    # ---- Branch 3: HEAVY BIG BIAS
    elif big_pct > 0.70:
        prediction = "SMALL"
        b = (big_pct - 0.5) * 2.2
        raw_conf = 56 + min(22, b * 32)
        pattern_power = 60 + b * 25
        description = f"HEAVY BIG BIAS {round(big_pct * 100)}% -> SMALL"

    # ---- Branch 4: HEAVY SMALL BIAS
    elif small_pct > 0.70:
        prediction = "BIG"
        b = (small_pct - 0.5) * 2.2
        raw_conf = 56 + min(22, b * 32)
        pattern_power = 60 + b * 25
        description = f"HEAVY SMALL BIAS {round(small_pct * 100)}% -> BIG"

    # ---- Branch 5: TREND FOLLOW
    else:
        if mb > 0.15:
            prediction = "BIG"
        elif mb < -0.15:
            prediction = "SMALL"
        else:
            prediction = "BIG" if big_pct > small_pct else "SMALL"
        e = abs(big_pct - 0.5) * 100
        raw_conf = 52 + min(18, e * 0.7)
        pattern_power = 52 + e * 0.6
        description = f"TREND FOLLOW: {prediction} favored"

    # ---- ANTI-LOSS (mirrors HTML)
    if STATE.consecutive_losses >= CONFIG["ANTI_LOSS_THRESHOLD"]:
        old = prediction
        prediction = "SMALL" if prediction == "BIG" else "BIG"
        description = (
            f"ANTI-LOSS: {old} -> {prediction} after "
            f"{STATE.consecutive_losses}L"
        )
        raw_conf = min(76, raw_conf + 8)

    # ---- Confidence clamp (mirrors JS)
    raw_conf = max(45, min(76, raw_conf - min(24, volatility * 45)))

    return {
        "prediction": prediction,
        "confidence": int(min(77, max(42, raw_conf))),
        "patternPower": int(min(84, pattern_power)),
        "streak": streak,
        "volatility": float(f"{volatility:.2f}"),
        "description": description,
        "altRatio": alt_ratio,
    }


# ============================================================
# RISK ENGINE — 100% port of assessRisk()
# ============================================================
def assess_risk(engine: Dict[str, Any]) -> Dict[str, Any]:
    """
    JS:
      function assessRisk(e){
        let s=0;
        if(e.streak>=5)s+=40;else if(e.streak>=3)s+=22;
        if(e.confidence<50)s+=28;else if(e.confidence<58)s+=14;else if(e.confidence>66)s-=8;
        if(e.altRatio>0.7)s-=14;
        s+=Math.floor(e.volatility*48);
        s=Math.min(98,Math.max(5,s));
        if(s<30)return{level:"LOW",cls:"text-green-600"};
        if(s<60)return{level:"MEDIUM",cls:"text-yellow-600"};
        return{level:"HIGH",cls:"text-red-600"};
      }
    """
    s = 0

    streak = engine.get("streak", 0)
    if streak >= 5:
        s += 40
    elif streak >= 3:
        s += 22

    confidence = engine.get("confidence", 50)
    if confidence < 50:
        s += 28
    elif confidence < 58:
        s += 14
    elif confidence > 66:
        s -= 8

    alt_ratio = engine.get("altRatio", 0)
    if alt_ratio > 0.7:
        s -= 14

    volatility = engine.get("volatility", 0.5)
    s += math.floor(volatility * 48)

    s = min(98, max(5, s))

    if s < 30:
        level, cls = "LOW", "text-green-600"
    elif s < 60:
        level, cls = "MEDIUM", "text-yellow-600"
    else:
        level, cls = "HIGH", "text-red-600"

    return {"level": level, "cls": cls, "score": s}


# ============================================================
# ADVICE ENGINE — 100% port of getSmartAdvice()
# ============================================================
def get_smart_advice(risk: Dict[str, Any], engine: Dict[str, Any]) -> str:
    """
    JS:
      function getSmartAdvice(risk,engine){
        if(consecutiveLosses>=3)return`ANTI-LOSS ACTIVE: ...`;
        if(risk.level==="HIGH")return engine.streak>=4
          ?"HIGH RISK + reversal zone: Skip this round."
          :"HIGH RISK: Wait 1-2 rounds.";
        if(risk.level==="MEDIUM")return engine.confidence>=58
          ?"MEDIUM RISK + decent confidence: Moderate stake."
          :"MEDIUM RISK: Small stake only.";
        return engine.confidence>=64
          ?"LOW RISK: Strong alignment. Stay disciplined."
          :"LOW RISK: Good setup. Follow plan.";
      }
    """
    if STATE.consecutive_losses >= CONFIG["ANTI_LOSS_THRESHOLD"]:
        return (
            f"ANTI-LOSS ACTIVE: {STATE.consecutive_losses} losses. "
            "Prediction reversed."
        )

    if risk["level"] == "HIGH":
        if engine.get("streak", 0) >= 4:
            return "HIGH RISK + reversal zone: Skip this round."
        return "HIGH RISK: Wait 1-2 rounds."

    if risk["level"] == "MEDIUM":
        if engine.get("confidence", 0) >= 58:
            return "MEDIUM RISK + decent confidence: Moderate stake."
        return "MEDIUM RISK: Small stake only."

    # LOW
    if engine.get("confidence", 0) >= 64:
        return "LOW RISK: Strong alignment. Stay disciplined."
    return "LOW RISK: Good setup. Follow plan."


# ============================================================
# SETTLE (updates win/loss + consecutive losses)
# ============================================================
def settle(prediction: str, actual: str) -> Dict[str, Any]:
    """
    Mirrors HTML modal trigger + counters.
    Updates STATE.winCount, lossCount, consecutiveLosses.
    """
    if prediction == actual:
        STATE.win_count += 1
        STATE.consecutive_losses = 0
        result = {"win": True, "status": "WIN"}
    else:
        STATE.loss_count += 1
        STATE.consecutive_losses += 1
        result = {"win": False, "status": "LOSS"}

    return result


# ============================================================
# MAIN PREDICT — combines all three HTML functions
# ============================================================
def predict(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    history: list of dicts like [{"period": "...", "number": 7, "size": "BIG"}, ...]
    Returns a full payload ready for UI / wrapper.
    """
    engine = ultra_pattern_engine(history)
    risk = assess_risk(engine)
    advice = get_smart_advice(risk, engine)

    # win-rate (mirrors HTML)
    total = STATE.win_count + STATE.loss_count
    win_rate = round(STATE.win_count / total * 100) if total > 0 else 0

    return {
        "prediction": engine["prediction"],
        "confidence": engine["confidence"],
        "patternPower": engine["patternPower"],
        "streak": engine["streak"],
        "volatility": engine["volatility"],
        "description": engine["description"],
        "riskLevel": risk["level"],
        "riskScore": risk["score"],
        "riskClass": risk["cls"],
        "advice": advice,
        "winCount": STATE.win_count,
        "lossCount": STATE.loss_count,
        "winRate": win_rate,
        "consecutiveLosses": STATE.consecutive_losses,
        "antiLossActive": STATE.consecutive_losses >= CONFIG["ANTI_LOSS_THRESHOLD"],
        "mode": "1M",
    }


# ============================================================
# CACHE + WRAPPER (app.py compatible)
# ============================================================
_CACHE: Dict[str, Dict[str, Any]] = {}


def cyber_tamilan_predict(current_number: int, period: str) -> Dict[str, Any]:
    """
    Drop-in compatible wrapper.
    Pass current_number (0-9) and period string.
    """
    cached = _CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < CONFIG["CACHE_TTL"]:
        return {k: v for k, v in cached.items() if k != "_ts"}

    # Build a synthetic history seed from period so results are stable per period
    seed = int(abs(hash(period)) % 100000)
    import random
    rng = random.Random(seed)

    # First element = current result (like HTML does with last200Results)
    current_size = get_big_small(current_number)
    history = [{"period": period, "number": current_number, "size": current_size}]
    for i in range(25):
        n = rng.randint(0, 9)
        history.append({
            "period": f"{period}-{i}",
            "number": n,
            "size": get_big_small(n),
        })

    result = predict(history)
    result["period"] = period
    result["currentNumber"] = current_number
    result["currentSize"] = current_size
    result["timestamp"] = datetime.now(timezone.utc).strftime("%I:%M %p")
    result["_ts"] = time.time()

    _CACHE[period] = result
    if len(_CACHE) > 100:
        keys = sorted(_CACHE.keys(), key=lambda k: _CACHE[k].get("_ts", 0))
        for k in keys[:50]:
            _CACHE.pop(k, None)

    return {k: v for k, v in result.items() if k != "_ts"}


def clear_engine_cache():
    _CACHE.clear()


def reset():
    STATE.reset()


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 65)
    print("CYBER TAMILAN — PYTHON PORT (100% HTML LOGIC)")
    print("=" * 65)

    # Simulate 25 rounds of history
    import random
    rng = random.Random(42)
    hist = []
    for i in range(25):
        n = rng.randint(0, 9)
        hist.append({"period": f"20250101{i:03d}", "number": n,
                     "size": get_big_small(n)})

    result = predict(hist)

    print(f"\nPrediction    : {result['prediction']}")
    print(f"Confidence    : {result['confidence']}%")
    print(f"Pattern Power : {result['patternPower']}%")
    print(f"Streak        : {result['streak']}")
    print(f"Volatility    : {round(result['volatility'] * 100)}%")
    print(f"Reason        : {result['description']}")
    print(f"Risk Level    : {result['riskLevel']} (score={result['riskScore']})")
    print(f"Advice        : {result['advice']}")
    print(f"Win / Loss    : {result['winCount']}W / {result['lossCount']}L")
    print(f"Win Rate      : {result['winRate']}%")
    print(f"Anti-Loss     : {result['antiLossActive']}")

    # Simulate 3 losses -> check anti-loss reversal
    print("\n--- Simulating 3 losses ---")
    for _ in range(3):
        settle(result["prediction"], "SMALL" if result["prediction"] == "BIG" else "BIG")
    result2 = predict(hist)
    print(f"Prediction after 3L: {result2['prediction']}")
    print(f"Consecutive Losses : {result2['consecutiveLosses']}")
    print(f"Anti-Loss Active   : {result2['antiLossActive']}")
    print(f"Advice             : {result2['advice']}")

    print("\n" + "=" * 65)
    print("All HTML logic ported. Old Python engines removed.")
    print("=" * 65)
