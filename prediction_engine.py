"""
CYBER TAMILAN — RENDER-READY PYTHON PORT
=========================================
100% HTML <script> prediction logic port.
Old Python engines — REMOVED.

Run locally:
    python cyber_tamilan.py

Deploy on Render:
    - Web Service
    - Build Command:  pip install -r requirements.txt
    - Start Command:  gunicorn cyber_tamilan:app --bind 0.0.0.0:$PORT --timeout 120
    - Health check path: /health
"""

import os
import time
import math
import json
import random
import threading
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import requests
from flask import Flask, jsonify, render_template_string


# ============================================================
# CONSTANTS
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
    "POLL_INTERVAL": 7.5,
    "HTTP_TIMEOUT": 15,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.bdg88zf.com",
    "Referer": "https://www.bdg88zf.com/",
}


# ============================================================
# HELPERS
# ============================================================
def get_big_small(n: int) -> str:
    try:
        return "BIG" if int(n) >= 5 else "SMALL"
    except (ValueError, TypeError):
        return "SMALL"


def http_post_json(url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.post(
            url, json=payload, headers=HEADERS, timeout=CONFIG["HTTP_TIMEOUT"]
        )
        if resp.status_code == 200:
            return resp.json()
        print(f"[POST {resp.status_code}] {url}")
        return None
    except Exception as e:
        print(f"[POST ERROR] {url} -> {e}")
        return None


def http_get_json(url: str) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=CONFIG["HTTP_TIMEOUT"])
        if resp.status_code == 200:
            return resp.json()
        print(f"[GET {resp.status_code}] {url}")
        return None
    except Exception as e:
        print(f"[GET ERROR] {url} -> {e}")
        return None


# ============================================================
# STATE
# ============================================================
class State:
    def __init__(self):
        self.prediction_history: List[Dict[str, Any]] = []
        self.last_200_results: List[Dict[str, Any]] = []
        self.win_count: int = 0
        self.loss_count: int = 0
        self.consecutive_losses: int = 0
        self.current_period: str = "LOADING"
        self.last_tick: Optional[str] = None
        self.last_error: Optional[str] = None
        self.lock = threading.Lock()

    def reset(self):
        self.__init__()


STATE = State()


# ============================================================
# CORE ENGINE — 100% port of ultraPatternEngine()
# ============================================================
def ultra_pattern_engine(history: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    streak = 1
    limit = min(20, len(history))
    for i in range(1, limit):
        if history[i]["size"] == history[i - 1]["size"]:
            streak += 1
        else:
            break

    alt = 0
    alt_limit = min(18, len(history))
    for i in range(1, alt_limit):
        if history[i]["size"] != history[i - 1]["size"]:
            alt += 1
    alt_ratio = alt / max(1, min(17, len(history) - 1))

    ch = 0
    vl = min(14, len(history) - 1)
    for i in range(1, vl + 1):
        if history[i]["size"] != history[i - 1]["size"]:
            ch += 1
    volatility = ch / (vl if vl else 1)

    ms = 0
    mom_limit = min(12, len(history))
    for i in range(mom_limit):
        ms += (1 if history[i]["size"] == "BIG" else -1) * (12 - i)
    mb = ms / 78

    prediction = ""
    raw_conf = 50.0
    pattern_power = 45.0
    description = ""

    if streak >= 4:
        prediction = "SMALL" if history[0]["size"] == "BIG" else "BIG"
        raw_conf = 58 + min(30, streak * 5.5)
        pattern_power = 70 + (streak - 3) * 4
        description = f"REVERSAL: {streak}-streak exhaustion -> mean reversion"

    elif alt_ratio > 0.72 and length >= 10:
        prediction = "SMALL" if history[0]["size"] == "BIG" else "BIG"
        raw_conf = 62 + alt_ratio * 14
        pattern_power = 68
        description = f"ZIGZAG LOCK: {round(alt_ratio * 100)}% flip rate"

    elif big_pct > 0.70:
        prediction = "SMALL"
        b = (big_pct - 0.5) * 2.2
        raw_conf = 56 + min(22, b * 32)
        pattern_power = 60 + b * 25
        description = f"HEAVY BIG BIAS {round(big_pct * 100)}% -> SMALL"

    elif small_pct > 0.70:
        prediction = "BIG"
        b = (small_pct - 0.5) * 2.2
        raw_conf = 56 + min(22, b * 32)
        pattern_power = 60 + b * 25
        description = f"HEAVY SMALL BIAS {round(small_pct * 100)}% -> BIG"

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

    if STATE.consecutive_losses >= CONFIG["ANTI_LOSS_THRESHOLD"]:
        old = prediction
        prediction = "SMALL" if prediction == "BIG" else "BIG"
        description = (
            f"ANTI-LOSS: {old} -> {prediction} after "
            f"{STATE.consecutive_losses}L"
        )
        raw_conf = min(76, raw_conf + 8)

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
# SETTLE
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
# LIVE FETCHERS
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
# TICK
# ============================================================
def tick() -> None:
    with STATE.lock:
        try:
            current_period = fetch_current_period()
            STATE.current_period = current_period

            results = fetch_history()
            if not results:
                STATE.last_error = "No history data"
                print("[WARN] No history data. Retrying next tick...")
                return

            STATE.last_200_results = results
            engine_input = results[:40]
            engine = ultra_pattern_engine(engine_input)
            risk = assess_risk(engine)
            advice = get_smart_advice(risk, engine)

            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"period={current_period} "
                f"pred={engine['prediction']} "
                f"conf={engine['confidence']}% "
                f"risk={risk['level']} "
                f"| {engine['description']}"
            )

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
                            f"  [SETTLED] {ph['period']} "
                            f"pred={ph['prediction']} actual={ph['actual']} "
                            f"-> {ph['status']}"
                        )

            STATE.last_tick = datetime.now(timezone.utc).isoformat()
            STATE.last_error = None

        except Exception as e:
            STATE.last_error = str(e)
            print(f"[TICK ERROR] {e}")
            traceback.print_exc()


# ============================================================
# BACKGROUND WORKER
# ============================================================
def worker():
    print("[WORKER] Background prediction loop started.")
    while True:
        try:
            tick()
        except Exception as e:
            print(f"[WORKER LOOP ERROR] {e}")
            traceback.print_exc()
        time.sleep(CONFIG["POLL_INTERVAL"])


# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CYBER TAMILAN — Live Signal API</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
*{font-family:system-ui,sans-serif}
body{background:#FFFEF7;color:#131313}
.dot-bg{background-image:radial-gradient(#F5C51833 1.5px,transparent 1.5px);background-size:22px 22px}
.card{background:#fff;border:1px solid #FFE082;border-radius:22px;box-shadow:0 10px 30px rgba(255,180,0,.12)}
.big-pred{font-size:clamp(3rem,8vw,5rem);line-height:1;letter-spacing:.04em;font-weight:900}
.bar-track{background:#FFF3C4;border:1px solid #FFD54F;border-radius:999px;height:16px;padding:3px}
.bar-fill{background:linear-gradient(90deg,#111 0%,#FFB300 55%,#FFD600 100%);border-radius:999px;height:100%;transition:width .7s}
</style>
</head>
<body class="dot-bg min-h-screen p-4">
<div class="max-w-4xl mx-auto">
  <div class="bg-white/95 border-2 border-yellow-400 rounded-2xl px-4 py-3 flex items-center justify-between shadow mb-4">
    <div class="flex items-center gap-3">
      <div class="w-11 h-11 rounded-xl bg-black flex items-center justify-center font-bold text-yellow-400 text-xl">CT</div>
      <div>
        <h1 class="font-black text-lg leading-none">CYBER <span class="text-yellow-500">TAMILAN</span></h1>
        <p class="text-[10px] font-bold tracking-[.25em] text-gray-500 mt-1">PYTHON ENGINE • LIVE</p>
      </div>
    </div>
    <div class="text-right">
      <div class="text-[10px] font-bold text-gray-400 tracking-widest">SERVER TIME</div>
      <div id="liveTime" class="font-black text-sm">--:--:--</div>
    </div>
  </div>

  <div class="card p-5">
    <div class="bg-black rounded-2xl p-6 text-center border-4 border-yellow-400">
      <div class="text-yellow-500 text-[11px] font-bold tracking-[.3em]">RECOMMENDED • BIG / SMALL</div>
      <div id="prediction" class="big-pred text-white mt-2">---</div>
      <div id="reason" class="text-yellow-200/90 text-xs font-mono mt-2">Connecting...</div>
      <div class="mt-4 flex items-center justify-center gap-2 text-[11px] font-bold">
        <span class="bg-yellow-400 text-black px-3 py-1 rounded-full">CONFIDENCE</span>
        <span id="confidence" class="text-white">--%</span>
      </div>
    </div>

    <div class="mt-4">
      <div class="flex justify-between text-[11px] font-extrabold tracking-widest text-gray-500 mb-1">
        <span>ACCURACY METER</span><span>CYBER TAMILAN</span>
      </div>
      <div class="bar-track"><div id="bar" class="bar-fill" style="width:0%"></div></div>
    </div>

    <div class="grid grid-cols-3 gap-3 mt-4">
      <div class="bg-yellow-50 border border-yellow-300 rounded-2xl p-3 text-center">
        <div class="text-[10px] font-extrabold text-yellow-700 tracking-widest">PATTERN</div>
        <div id="pattern" class="font-black text-lg">0%</div>
      </div>
      <div class="bg-black rounded-2xl p-3 text-center">
        <div class="text-[10px] font-extrabold text-yellow-500 tracking-widest">VOLATILITY</div>
        <div id="volatility" class="font-black text-lg text-white">0%</div>
      </div>
      <div class="bg-yellow-400 rounded-2xl p-3 text-center border-2 border-black">
        <div class="text-[10px] font-extrabold text-black tracking-widest">RISK</div>
        <div id="risk" class="font-black text-lg">--</div>
      </div>
    </div>

    <div class="mt-4 bg-yellow-50 border border-yellow-300 rounded-xl px-4 py-3 text-[12px] font-semibold" id="advice">
      Connecting to pattern stream...
    </div>

    <div class="grid grid-cols-2 gap-3 mt-4">
      <div class="bg-white border-2 border-yellow-400 rounded-xl p-3">
        <div class="text-[10px] font-extrabold text-gray-500 tracking-widest">PERIOD</div>
        <div id="period" class="font-black text-sm">--</div>
      </div>
      <div class="bg-white border-2 border-yellow-400 rounded-xl p-3">
        <div class="text-[10px] font-extrabold text-gray-500 tracking-widest">WIN RATE</div>
        <div id="winRate" class="font-black text-sm">0%</div>
      </div>
    </div>
  </div>

  <p class="text-center text-[10px] text-gray-400 mt-4">
    API: <code>/api/predict</code> • <code>/api/history</code> • <code>/health</code>
  </p>
</div>

<script>
function tick(){
  document.getElementById('liveTime').innerText = new Date().toLocaleTimeString('en-GB');
  fetch('/api/predict').then(r=>r.json()).then(d=>{
    document.getElementById('prediction').innerText = d.prediction || '---';
    document.getElementById('confidence').innerText = (d.confidence||0)+'%';
    document.getElementById('reason').innerText = d.description || '--';
    document.getElementById('pattern').innerText = (d.patternPower||0)+'%';
    document.getElementById('volatility').innerText = Math.round((d.volatility||0)*100)+'%';
    document.getElementById('risk').innerText = d.riskLevel || '--';
    document.getElementById('advice').innerText = d.advice || '--';
    document.getElementById('bar').style.width = (d.confidence||0)+'%';
    document.getElementById('period').innerText = d.period || '--';
    document.getElementById('winRate').innerText = (d.winRate||0)+'%';
  }).catch(e=>console.log(e));
}
tick();
setInterval(tick, 4000);
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(DASHBOARD_HTML)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "last_tick": STATE.last_tick,
        "last_error": STATE.last_error,
        "current_period": STATE.current_period,
    }), 200


@app.route("/api/predict")
def api_predict():
    with STATE.lock:
        if not STATE.last_200_results:
            return jsonify({
                "prediction": "ANALYZING",
                "confidence": 0,
                "description": "Waiting for live feed...",
                "period": STATE.current_period,
            }), 200

        engine_input = STATE.last_200_results[:40]
        engine = ultra_pattern_engine(engine_input)
        risk = assess_risk(engine)
        advice = get_smart_advice(risk, engine)

        total = STATE.win_count + STATE.loss_count
        win_rate = round(STATE.win_count / total * 100) if total > 0 else 0

        return jsonify({
            "prediction": engine["prediction"],
            "confidence": engine["confidence"],
            "patternPower": engine["patternPower"],
            "streak": engine["streak"],
            "volatility": engine["volatility"],
            "description": engine["description"],
            "riskLevel": risk["level"],
            "riskScore": risk["score"],
            "advice": advice,
            "winCount": STATE.win_count,
            "lossCount": STATE.loss_count,
            "winRate": win_rate,
            "consecutiveLosses": STATE.consecutive_losses,
            "antiLossActive": STATE.consecutive_losses >= CONFIG["ANTI_LOSS_THRESHOLD"],
            "period": STATE.current_period,
            "lastTick": STATE.last_tick,
        }), 200


@app.route("/api/history")
def api_history():
    with STATE.lock:
        return jsonify({
            "predictions": STATE.prediction_history[:30],
            "results": STATE.last_200_results[:30],
        }), 200


# ============================================================
# STARTUP — background worker (Render safe)
# ============================================================
def start_worker_once():
    if getattr(start_worker_once, "_started", False):
        return
    start_worker_once._started = True
    t = threading.Thread(target=worker, daemon=True, name="cyber-tamilan-worker")
    t.start()
    print("[STARTUP] Background worker launched.")


start_worker_once()


# ============================================================
# LOCAL RUN
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
