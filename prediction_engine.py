"""
CYBER TAMILAN — SINGLE FILE PYTHON PORT
========================================
100% HTML <script> prediction logic.
Old Python engines (MAFIYA, RIFU, Bunny, 7-Layer, Ensemble,
Hyper, 11-Pattern, Ultimate Pro, etc.) — REMOVED.

Run:
    python cyber_tamilan.py
"""

import time
import math
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


# ============================================================
# CONSTANTS (mirrors HTML)
# ============================================================
CURRENT_API = "https://api.bdg88zf.com/api/webapi/GetGameIssue"
HISTORY_API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

REQUEST_DATA = {
    "typeId": 1,
    "language": 0,
    "random": "e7fe6c090da2495ab8290dac551ef1ed",
    "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
    "timestamp": 1723726679,
}

CONFIG = {
    "HISTORY_LIMIT": 45,
    "MIN_CONFIDENCE": 42,
    "MAX_CONFIDENCE": 77,
    "ANTI_LOSS_THRESHOLD": 3,
    "POLL_INTERVAL": 7.5,   # seconds (matches HTML setInterval 7500ms)
}


# ============================================================
# HELPERS
# ============================================================
def get_big_small(n: int) -> str:
    """JS: return n >= 5 ? "BIG" : "SMALL" """
    try:
        return "BIG" if int(n) >= 5 else "SMALL"
    except (ValueError, TypeError):
        return "SMALL"


def http_post_json(url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (CyberTamilan/1.0)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        print(f"[HTTP POST ERROR] {url} -> {e}")
        return None


def http_get_json(url: str) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (CyberTamilan/1.0)",
                "Accept": "application/json",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        print(f"[HTTP GET ERROR] {url} -> {e}")
        return None


# ============================================================
# STATE (mirrors HTML globals)
# ============================================================
class State:
    def __init__(self):
        self.prediction_history: List[Dict[str, Any]] = []   # like predictionHistory[]
        self.last_200_results: List[Dict[str, Any]] = []     # like last200Results[]
        self.win_count: int = 0                              # like winCount
        self.loss_count: int = 0                             # like lossCount
        self.consecutive_losses: int = 0                     # like consecutiveLosses

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
        if(!history||history.length<8) return {
          prediction:"ANALYZING", confidence:30, patternPower:25,
          streak:0, volatility:0.5, description:"Building matrix..."
        };
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

    big = sum(1 for r in recent if r.get("size") == "BIG")
    small = length - big
    big_pct = big / length
    small_pct = small / length

    # streak (from index 0)
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
    raw_conf = 50.0
    pattern_power = 45.0
    description = ""

    # Branch 1 — REVERSAL
    if streak >= 4:
        prediction = "SMALL" if history[0]["size"] == "BIG" else "BIG"
        raw_conf = 58 + min(30, streak * 5.5)
        pattern_power = 70 + (streak - 3) * 4
        description = f"REVERSAL: {streak}-streak exhaustion -> mean reversion"

    # Branch 2 — ZIGZAG LOCK
    elif alt_ratio > 0.72 and length >= 10:
        prediction = "SMALL" if history[0]["size"] == "BIG" else "BIG"
        raw_conf = 62 + alt_ratio * 14
        pattern_power = 68
        description = f"ZIGZAG LOCK: {round(alt_ratio * 100)}% flip rate"

    # Branch 3 — HEAVY BIG BIAS
    elif big_pct > 0.70:
        prediction = "SMALL"
        b = (big_pct - 0.5) * 2.2
        raw_conf = 56 + min(22, b * 32)
        pattern_power = 60 + b * 25
        description = f"HEAVY BIG BIAS {round(big_pct * 100)}% -> SMALL"

    # Branch 4 — HEAVY SMALL BIAS
    elif small_pct > 0.70:
        prediction = "BIG"
        b = (small_pct - 0.5) * 2.2
        raw_conf = 56 + min(22, b * 32)
        pattern_power = 60 + b * 25
        description = f"HEAVY SMALL BIAS {round(small_pct * 100)}% -> BIG"

    # Branch 5 — TREND FOLLOW
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

    # ANTI-LOSS REVERSAL (mirrors HTML)
    if STATE.consecutive_losses >= CONFIG["ANTI_LOSS_THRESHOLD"]:
        old = prediction
        prediction = "SMALL" if prediction == "BIG" else "BIG"
        description = (
            f"ANTI-LOSS: {old} -> {prediction} after "
            f"{STATE.consecutive_losses}L"
        )
        raw_conf = min(76, raw_conf + 8)

    # confidence clamp
    raw_conf = max(45, min(76, raw_conf - min(24, volatility * 45)))

    return {
        "prediction": prediction,
        "confidence": int(min(77, max(42, raw_conf))),
        "patternPower": int(min(84, pattern_power)),
        "streak": streak,
        "volatility": round(volatility, 2),
        "description": description,
        "altRatio": alt_ratio,
    }


# ============================================================
# RISK ENGINE — 100% port of assessRisk()
# ============================================================
def assess_risk(engine: Dict[str, Any]) -> Dict[str, Any]:
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

    if engine.get("altRatio", 0) > 0.7:
        s -= 14

    s += math.floor(engine.get("volatility", 0.5) * 48)
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
# UNIFIED PREDICT
# ============================================================
def predict(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    engine = ultra_pattern_engine(history)
    risk = assess_risk(engine)
    advice = get_smart_advice(risk, engine)

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
# SETTLE — update win/loss + consecutive losses
# ============================================================
def settle(prediction: str, actual: str) -> Dict[str, Any]:
    if prediction == actual:
        STATE.win_count += 1
        STATE.consecutive_losses = 0
        return {"win": True, "status": "WIN"}
    else:
        STATE.loss_count += 1
        STATE.consecutive_losses += 1
        return {"win": False, "status": "LOSS"}


# ============================================================
# LIVE FETCHERS (mirrors HTML fetchAndAnalyze)
# ============================================================
def fetch_current_period() -> str:
    payload = dict(REQUEST_DATA)
    payload["timestamp"] = int(time.time())
    data = http_post_json(CURRENT_API, payload)
    if not data:
        return "LOADING"
    try:
        return str(data.get("data", {}).get("issueNumber", "LOADING"))
    except Exception:
        return "LOADING"


def fetch_history() -> List[Dict[str, Any]]:
    url = f"{HISTORY_API}?ts={int(time.time() * 1000)}"
    data = http_get_json(url)
    if not data:
        return []
    try:
        raw = data.get("data", {}).get("list", [])
        results = []
        for it in raw[:200]:
            try:
                num = int(it.get("number"))
            except (ValueError, TypeError):
                continue
            results.append({
                "period": str(it.get("issueNumber")),
                "number": num,
                "size": get_big_small(num),
            })
        return results
    except Exception as e:
        print(f"[HISTORY PARSE ERROR] {e}")
        return []


# ============================================================
# MAIN TICK — mirrors HTML fetchAndAnalyze()
# ============================================================
def tick() -> None:
    current_period = fetch_current_period()
    print(f"\n[CURRENT PERIOD] {current_period}")

    results = fetch_history()
    if not results:
        print("[WARN] No history data. Retrying next tick...")
        return

    STATE.last_200_results = results

    # engine sees first 40 rows (like HTML: last200Results.slice(0,40))
    engine_input = results[:40]
    engine = ultra_pattern_engine(engine_input)
    risk = assess_risk(engine)
    advice = get_smart_advice(risk, engine)

    print(f"PREDICTION     : {engine['prediction']}")
    print(f"CONFIDENCE     : {engine['confidence']}%")
    print(f"PATTERN POWER  : {engine['patternPower']}%")
    print(f"STREAK         : {engine['streak']}")
    print(f"VOLATILITY     : {round(engine['volatility'] * 100)}%")
    print(f"REASON         : {engine['description']}")
    print(f"RISK           : {risk['level']} (score={risk['score']})")
    print(f"ADVICE         : {advice}")

    # Register new prediction (mirrors HTML)
    if (
        engine["prediction"] != "ANALYZING"
        and current_period != "LOADING"
        and not any(p["period"] == current_period for p in STATE.prediction_history)
    ):
        STATE.prediction_history.insert(0, {
            "period": current_period,
            "prediction": engine["prediction"],
            "actual": "--",
            "status": "Waiting",
            "confidence": engine["confidence"],
            "risk": risk["level"],
        })
        if len(STATE.prediction_history) > 45:
            STATE.prediction_history.pop()

    # Settle any waiting predictions
    for ph in STATE.prediction_history:
        if ph["status"] == "Waiting":
            found = next(
                (h for h in STATE.last_200_results if h["period"] == ph["period"]),
                None,
            )
            if found:
                ph["actual"] = found["size"]
                result = settle(ph["prediction"], found["size"])
                ph["status"] = "Win" if result["win"] else "Loss"
                print(
                    f"[SETTLED] period={ph['period']} "
                    f"pred={ph['prediction']} actual={ph['actual']} "
                    f"-> {ph['status']}"
                )

    total = STATE.win_count + STATE.loss_count
    win_rate = round(STATE.win_count / total * 100) if total > 0 else 0
    print(f"WIN RATE       : {win_rate}%  ({STATE.win_count}W / {STATE.loss_count}L)")


# ============================================================
# MAIN LOOP
# ============================================================
def main():
    print("=" * 65)
    print("CYBER TAMILAN — PYTHON PORT (100% HTML LOGIC)")
    print("=" * 65)
    print(f"Poll interval: {CONFIG['POLL_INTERVAL']}s")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                tick()
            except Exception as e:
                print(f"[TICK ERROR] {e}")

            time.sleep(CONFIG["POLL_INTERVAL"])
    except KeyboardInterrupt:
        print("\n[STOPPED] Shutting down...")
        print(f"Final: {STATE.win_count}W / {STATE.loss_count}L")
        total = STATE.win_count + STATE.loss_count
        if total > 0:
            print(f"Win rate: {round(STATE.win_count / total * 100)}%")


# ============================================================
# WRAPPER for external callers (app.py compatible)
# ============================================================
_CACHE: Dict[str, Dict[str, Any]] = {}


def cyber_tamilan_predict(current_number: int, period: str) -> Dict[str, Any]:
    """
    If your app.py calls this, pass current_number (0-9) + period string.
    Uses synthetic history seeded by period.
    """
    cached = _CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < CONFIG["POLL_INTERVAL"] * 6:
        return {k: v for k, v in cached.items() if k != "_ts"}

    import random
    seed = int(abs(hash(period)) % 100000)
    rng = random.Random(seed)

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
# ENTRY
# ============================================================
if __name__ == "__main__":
    main()
