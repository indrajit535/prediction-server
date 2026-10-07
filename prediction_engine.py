"""
CYBER TAMILAN — prediction_engine.py

Prediction engine — 1:1 Python port of the Java MainActivity.java
prediction logic (package com.example.sddvippvt).

The old EaglePredictionEngine / BMW / Markov / priority-pattern logic
has been 100% REMOVED and replaced with the Java algorithm:

  - generatePrediction()  -> generate_prediction()
  - generateOpposites()   -> generate_opposites()
  - checkResult()         -> check_result()
  - processApiData()      -> process_api_data()

Java rule (verbatim port):
  - Look at last 5 results, count BIG.
  - If bigCount > 2 -> predict "BIG", else "SMALL".
  - Opposites = 2 random numbers from the OPPOSITE pool.
  - WIN     = prediction matches actual size OR opposites contain actual number.
  - JACKPOT = both conditions true.
"""

from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    "period_seconds": 60,                # Java uses 60-second periods
    "cache_ttl": 3,                      # Java polls every 3000 ms
    "engine_name": "SDD VIP PVT",
    "engine_code": "sddvip-pvt",
}

# Java: API_URLS array — three fallback endpoints
API_URLS = [
    "https://easy-share-server.lovable.app/api/public/WinGo_1M",
    "https://api-wingo1min.randorona.workers.dev/",
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
]

# Java: B_POOL / S_POOL
B_POOL = [5, 6, 7, 8, 9]
S_POOL = [0, 1, 2, 3, 4]


# ============================================================
# INTERNAL MUTABLE STATE (mirrors Java fields)
# ============================================================

# Java: private ArrayList<HashMap<String, String>> apiHistory
api_history: List[Dict[str, str]] = []

# Java: private String currentPeriod
current_period: str = ""

# Java: fixed period tracking fields
last_seen_api_period: Optional[str] = None
predicted_for_period: Optional[str] = None
saved_prediction: Optional[str] = None
saved_opposites: List[int] = []
result_checked_for_period: bool = False

# Java counters
win_count: int = 0
loss_count: int = 0
total_count: int = 0

# Java historyList (for UI table)
history_list: List[Dict[str, str]] = []

# Fetch cache
_last_fetch_ts: float = 0.0
_last_fetch_json: Optional[str] = None


# ============================================================
# HELPERS
# ============================================================

def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _http_get(url: str, timeout: float = 8.0) -> Optional[str]:
    """Java's HttpURLConnection GET — Python equivalent."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


# ============================================================
# API FETCH — exact port of Java fetchApiData()
# ============================================================

def fetch_api_data() -> Optional[str]:
    """
    1:1 port of Java fetchApiData().
    Tries each URL in API_URLS, returns first successful JSON body.
    Caches for CONFIG['cache_ttl'] seconds.
    """
    global _last_fetch_ts, _last_fetch_json

    now = time.time()
    if _last_fetch_json is not None and (now - _last_fetch_ts) < CONFIG["cache_ttl"]:
        return _last_fetch_json

    for api_url in API_URLS:
        body = _http_get(api_url)
        if body:
            _last_fetch_ts = now
            _last_fetch_json = body
            return body

    return None


def get_api_short(url: str) -> str:
    """Java: getApiShort()"""
    if url and "lovable" in url:
        return "API-1"
    if url and "randorona" in url:
        return "API-2"
    if url and "ar-lottery" in url:
        return "API-3"
    return "API"


# ============================================================
# PREDICTION LOGIC — exact port of Java
# ============================================================

def generate_prediction(history: List[Dict[str, str]]) -> str:
    """
    1:1 port of Java generatePrediction().

    Last 5 results, count BIG. If bigCount > 2 -> "BIG", else "SMALL".
    """
    big_count = 0
    count = min(5, len(history))
    for i in range(count):
        try:
            if _to_int(history[i].get("number")) >= 5:
                big_count += 1
        except Exception:
            pass
    return "BIG" if big_count > 2 else "SMALL"


def generate_opposites(prediction: str) -> List[int]:
    """
    1:1 port of Java generateOpposites().

    prediction == "BIG"  -> pick 2 random numbers from S_POOL (0-4)
    prediction == "SMALL" -> pick 2 random numbers from B_POOL (5-9)
    """
    pool = S_POOL if prediction == "BIG" else B_POOL
    shuffled = list(pool)
    random.shuffle(shuffled)
    return [shuffled[0], shuffled[1]]


def check_result(
    prediction: str,
    opposites: List[int],
    actual_number: int,
    period: str,
) -> Dict[str, Any]:
    """
    1:1 port of Java checkResult().

    WIN     = prediction matches actual size OR opposites contain actual number.
    JACKPOT = both conditions true.
    """
    global win_count, loss_count, total_count

    actual_size = "BIG" if actual_number >= 5 else "SMALL"
    is_win = (prediction == actual_size) or (actual_number in opposites)
    is_jackpot = is_win and (actual_number in opposites)

    total_count += 1
    if is_win:
        win_count += 1
    else:
        loss_count += 1

    result_str = "JACKPOT" if is_jackpot else ("WIN" if is_win else "LOSS")
    add_to_history(period, prediction, result_str, actual_number)

    return {
        "period": period,
        "prediction": prediction,
        "result": result_str,
        "actual": actual_number,
        "isWin": is_win,
        "isJackpot": is_jackpot,
    }


def add_to_history(period: str, prediction: str, result: str, actual: int) -> None:
    """Java: addToHistory() — keeps last 50 entries."""
    global history_list
    history_list.append({
        "period": period,
        "prediction": prediction,
        "result": result,
        "actual": str(actual),
    })
    if len(history_list) > 50:
        history_list.pop(0)


def update_stats() -> Dict[str, Any]:
    """Java: updateStats() — exposes counts + accuracy."""
    acc = (win_count * 100 // total_count) if total_count > 0 else 0
    return {
        "totalWins": win_count,
        "totalLoss": loss_count,
        "total": total_count,
        "accuracy": acc,
    }


# ============================================================
# PROCESS API DATA — exact port of Java processApiData()
# ============================================================

def process_api_data(json_data: str) -> Dict[str, Any]:
    """
    1:1 port of Java processApiData().

    Returns the current active signal dict (or {} if not enough data).
    """
    global api_history, current_period
    global last_seen_api_period, predicted_for_period
    global saved_prediction, saved_opposites, result_checked_for_period

    try:
        json_object = json.loads(json_data)
    except Exception:
        return {}

    # Java JSON extraction branches:
    #   jsonObject.data.list  -> dataArray
    #   jsonObject.Data       -> dataArray
    #   jsonObject.list       -> dataArray
    data_array = None
    if isinstance(json_object.get("data"), dict) and "list" in json_object["data"]:
        data_array = json_object["data"]["list"]
    elif "Data" in json_object:
        data_array = json_object["Data"]
    elif "list" in json_object:
        data_array = json_object["list"]

    if not data_array or len(data_array) < 5:
        return {}

    # Rebuild apiHistory (newest first, as Java does)
    api_history = []
    for item in data_array:
        issue = ""
        num = ""
        if "issueNumber" in item:
            issue = str(item["issueNumber"])
        elif "PeriodNo" in item:
            issue = str(item["PeriodNo"])
        elif "period" in item:
            issue = str(item["period"])

        if "number" in item:
            num = str(item["number"])
        elif "Number" in item:
            num = str(item["Number"])

        api_history.append({"issueNumber": issue, "number": num})

    if len(api_history) < 5:
        return {}

    latest_period = api_history[0]["issueNumber"]
    latest_number = api_history[0]["number"]
    actual_num = _to_int(latest_number)
    actual_size = "BIG" if actual_num >= 5 else "SMALL"

    # Java: currentPeriod = latestPeriod + 1
    try:
        current_period = str(int(latest_period) + 1)
    except Exception:
        current_period = latest_period

    popup_payload: Optional[Dict[str, Any]] = None

    # ===== Java: CHECK RESULT ONLY WHEN API PERIOD ACTUALLY CHANGES =====
    if last_seen_api_period is not None and last_seen_api_period != latest_period:
        if predicted_for_period is not None and not result_checked_for_period:
            for i in range(len(api_history)):
                hist_period = api_history[i]["issueNumber"]
                if hist_period == predicted_for_period:
                    predicted_actual = _to_int(api_history[i]["number"])
                    outcome = check_result(
                        saved_prediction or "SMALL",
                        saved_opposites,
                        predicted_actual,
                        predicted_for_period,
                    )
                    result_checked_for_period = True
                    if outcome["isWin"]:
                        popup_payload = {
                            "period": predicted_for_period[-5:] if len(predicted_for_period) > 5 else predicted_for_period,
                            "prediction": saved_prediction,
                            "predNum": f"{saved_opposites[0]}, {saved_opposites[1]}" if len(saved_opposites) >= 2 else "",
                            "actual": {"color": actual_size, "number": predicted_actual},
                            "isJackpot": outcome["isJackpot"],
                        }
                    break

    # ===== Java: GENERATE NEW PREDICTION ONLY IF NEEDED =====
    active_signal: Dict[str, Any] = {}
    if predicted_for_period is None or predicted_for_period != current_period:
        prediction = generate_prediction(api_history)
        opposites = generate_opposites(prediction)

        saved_prediction = prediction
        saved_opposites = opposites
        predicted_for_period = current_period
        result_checked_for_period = False

        active_signal = {
            "period": current_period,
            "size": prediction,
            "n1": opposites[0],
            "n2": opposites[1],
            "prediction": prediction,
            "opposites": opposites,
        }

    # Java: lastSeenApiPeriod = latestPeriod
    last_seen_api_period = latest_period

    return {
        "active": active_signal,
        "popup": popup_payload,
        "latestPeriod": latest_period,
        "latestNumber": latest_number,
        "latestSize": actual_size,
        "currentPeriod": current_period,
    }


# ============================================================
# TIMER — Java: syncTimer() / updateTimer()
# ============================================================

def update_timer() -> Dict[str, Any]:
    """
    Java: timerSeconds = 60 - Calendar.SECOND.
    """
    now = int(time.time())
    rem = CONFIG["period_seconds"] - (now % CONFIG["period_seconds"])
    if rem >= CONFIG["period_seconds"]:
        rem = 0
    return {
        "secondsLeft": rem,
        "periodSeconds": CONFIG["period_seconds"],
        "ringFraction": rem / CONFIG["period_seconds"],
    }


# ============================================================
# MAIN ENGINE TICK — replaces old engine_pro()
# ============================================================

def engine_pro() -> Dict[str, Any]:
    """
    One tick: fetch API, process data, return state.
    Port of Java startGame() + fetchApiData() + processApiData()
    + updateTimer() + updateStats() combined into a single call.
    """
    body = fetch_api_data()

    if body is None:
        return {
            "ok": False,
            "reason": "no_history",
            "timer": update_timer(),
            "stats": update_stats(),
            "history": list(history_list),
        }

    processed = process_api_data(body)

    return {
        "ok": True,
        "issue": processed.get("latestPeriod", ""),
        "nextPeriod": processed.get("currentPeriod", ""),
        "active": processed.get("active") or None,
        "popup": processed.get("popup"),
        "latest": {
            "number": processed.get("latestNumber", ""),
            "size": processed.get("latestSize", ""),
        },
        "timer": update_timer(),
        "stats": update_stats(),
        "history": list(history_list),
        "engine": {
            "name": CONFIG["engine_name"],
            "code": CONFIG["engine_code"],
        },
    }


# ============================================================
# STATS ACCESSOR
# ============================================================

def get_stats() -> Dict[str, Any]:
    return update_stats()


# ============================================================
# PUBLIC API — same entry point as before
# ============================================================

def sddgamer263_predict() -> Dict[str, Any]:
    """
    Run one engine tick. Returns full state dict.
    Callers invoke this once per tick (e.g. once per second).
    """
    return engine_pro()


def reset() -> None:
    """Clear all engine state (matches a page refresh / app restart)."""
    global api_history, current_period
    global last_seen_api_period, predicted_for_period
    global saved_prediction, saved_opposites, result_checked_for_period
    global win_count, loss_count, total_count, history_list
    global _last_fetch_ts, _last_fetch_json

    api_history = []
    current_period = ""
    last_seen_api_period = None
    predicted_for_period = None
    saved_prediction = None
    saved_opposites = []
    result_checked_for_period = False

    win_count = 0
    loss_count = 0
    total_count = 0
    history_list = []

    _last_fetch_ts = 0.0
    _last_fetch_json = None


def clear_engine_cache() -> None:
    """Clear only the fetch cache."""
    global _last_fetch_ts, _last_fetch_json
    _last_fetch_ts = 0.0
    _last_fetch_json = None


# ============================================================
# CLI / SELF-TEST
# ============================================================

if __name__ == "__main__":
    reset()
    print("Testing prediction_engine.py (Java SDD VIP PVT port) ...\n")

    # ---- Offline unit test of pure functions ----
    print("=== Unit test: generate_prediction / generate_opposites / check_result ===")

    # Fake history: 3 BIG in last 5 -> predict BIG
    fake = [
        {"issueNumber": "1005", "number": "7"},
        {"issueNumber": "1004", "number": "6"},
        {"issueNumber": "1003", "number": "8"},
        {"issueNumber": "1002", "number": "2"},
        {"issueNumber": "1001", "number": "1"},
    ]
    pred = generate_prediction(fake)
    opps = generate_opposites(pred)
    print(f"  generate_prediction({[h['number'] for h in fake]}) = {pred}")
    print(f"  generate_opposites('{pred}') = {opps}")

    # Fake history: only 1 BIG in last 5 -> predict SMALL
    fake2 = [
        {"issueNumber": "2005", "number": "1"},
        {"issueNumber": "2004", "number": "2"},
        {"issueNumber": "2003", "number": "9"},
        {"issueNumber": "2002", "number": "3"},
        {"issueNumber": "2001", "number": "0"},
    ]
    pred2 = generate_prediction(fake2)
    print(f"  generate_prediction({[h['number'] for h in fake2]}) = {pred2}")

    # check_result test
    out = check_result("BIG", [1, 2], 7, "1005")
    print(f"  check_result(BIG, [1,2], 7) = {out['result']}  (expect WIN)")
    out = check_result("BIG", [1, 2], 1, "1004")
    print(f"  check_result(BIG, [1,2], 1) = {out['result']}  (expect JACKPOT)")
    out = check_result("BIG", [1, 2], 3, "1003")
    print(f"  check_result(BIG, [1,2], 3) = {out['result']}  (expect LOSS)")

    print(f"  stats after 3 checks = {update_stats()}\n")

    # ---- Live test ----
    print("=== Live Engine Test ===")
    for i in range(3):
        out = sddgamer263_predict()
        timer = out.get("timer", {})
        active = out.get("active")
        stats = out.get("stats", {})

        if not out.get("ok"):
            print(f"tick {i}: no history available ({out.get('reason')})")
        else:
            if active:
                print(
                    f"tick {i}: issue={out.get('issue')} "
                    f"next={out.get('nextPeriod')} "
                    f"signal={active.get('size')} "
                    f"[{active.get('n1')} & {active.get('n2')}] "
                    f"| secLeft={timer.get('secondsLeft')} "
                    f"| W/L/T={stats.get('totalWins')}/{stats.get('totalLoss')}/{stats.get('total')} "
                    f"| acc={stats.get('accuracy')}%"
                )
            else:
                print(
                    f"tick {i}: issue={out.get('issue')} — no active signal "
                    f"| secLeft={timer.get('secondsLeft')}"
                )

        if out.get("popup"):
            p = out["popup"]
            tag = "JACKPOT" if p["isJackpot"] else "WIN"
            print(f"        -> {tag}! period={p['period']} pred={p['prediction']} actual={p['actual']}")

        time.sleep(2)
