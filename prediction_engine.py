"""
RAJPUT V9 ULTRA — prediction_engine.py

Prediction engine — 1:1 Python port of the HTML/JavaScript
RAJPUT V9 ULTRA prediction logic (from the <script> block).

100% HTML ENGINE — OLD PYTHON LOGIC REMOVED:
  - generatePrediction()  -> generate_prediction()
  - checkResult()         -> check_result()
  - updatePredictionUI()  -> update_prediction_ui_state()
  - appendHistoryItem()   -> append_history_item()
  - getNextPeriodString() -> get_next_period_string()

HTML rules (verbatim port):
  - Pattern scan len 5..1 over size sequence (newest first).
  - Recurrence: dominant side > 60% AND >= 3 matches -> pick it.
  - Bias fallback: majority side for that pattern len.
  - DELTA-20 fallback: majority of last 20.
  - Strict OPPOSITE flip (BIG<->SMALL).
  - STREAK BREAK: if last 3 predictions identical -> flip.
  - Weighted Sure Number: decay=0.9 on relevant nums, unseen nums doubled.
  - JACKPOT 9x if num == sureNumber
  - WIN 2x    if size == prediction
  - LOSS      otherwise
  - +1 NEXT PERIOD tracking (window.predictedPeriod)
"""

from __future__ import annotations

import json
import math
import random
import time
import urllib.request
from typing import Any, Dict, List, Optional


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    "period_seconds": 60,
    "cache_ttl": 3,                # HTML polls every 2500 ms
    "engine_name": "RAJPUT V9 ULTRA",
    "engine_code": "rajput-v9-ultra",
}

API_URLS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    "https://easy-share-server.lovable.app/api/public/WinGo_1M",
    "https://api-wingo1min.randorona.workers.dev/",
]

# HTML: pools used for weighted sure-number fallback
B_POOL = [5, 6, 7, 8, 9]
S_POOL = [0, 1, 2, 3, 4]

MAX_HISTORY = 200


# ============================================================
# INTERNAL MUTABLE STATE (mirrors HTML JS globals)
# ============================================================

# HTML: historyBuffer
history_buffer: List[Dict[str, Any]] = []

# HTML: window.lastPreds  (streak-break tracker, max 3)
last_preds: List[str] = []

# HTML: fullHistoryList (rendered history)
history_list: List[Dict[str, Any]] = []

# HTML: window.predictedPeriod / activePred / activeSure / activeLogic
predicted_period: Optional[str] = None
active_pred: Optional[str] = None
active_sure: Optional[int] = None
active_logic: Optional[str] = None

# HTML: currentPred / currentSure / currentLogic / currentPeriod
current_pred: str = "WAIT"
current_sure: Optional[int] = None
current_logic: str = "AI MATRIX"
current_period: str = ""

# HTML: lastProcessedDraw
last_processed_draw: Optional[str] = None

# HTML: lastIssue / prevIssue tracking
last_issue: Optional[str] = None
prev_issue: Optional[str] = None
prev_pred: Optional[str] = None
prev_sure: Optional[int] = None
prev_logic: Optional[str] = None

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
# HTML: getNextPeriodString(issueStr)
# ============================================================

def get_next_period_string(issue_str: str) -> str:
    """
    1:1 port of HTML getNextPeriodString().
    Safely calculates NEXT (+1) period.
    """
    try:
        # BigInt behaviour for large numbers
        return str(int(issue_str) + 1)
    except (ValueError, TypeError):
        try:
            return str(int(issue_str) + 1)
        except Exception:
            return issue_str


# ============================================================
# API FETCH
# ============================================================

def fetch_api_data() -> Optional[str]:
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


# ============================================================
# 🎯 PREDICTION ENGINE — 100% HTML JS PORT
# ============================================================

def generate_prediction(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    1:1 port of HTML generatePrediction(history).

    Args:
        history: list of dicts with at least {"size": "BIG"|"SMALL",
                 "num": int} — NEWEST FIRST (index 0 = latest).

    Returns:
        {"prediction": "BIG"|"SMALL", "sureNumber": int, "logic": str}
    """
    global last_preds

    best_size: Optional[str] = None
    logic_applied = "AI MATRIX"

    # --- Seed init: fewer than 5 results ---
    if len(history) < 5:
        best_size = "BIG" if random.random() > 0.5 else "SMALL"
        logic_applied = "SEED INIT"
    else:
        # HTML: const sizeSeq = history.map(h => h.size);
        # NOTE: HTML history is NEWEST FIRST (index 0 = newest).
        # Python history_buffer is also NEWEST FIRST.
        size_seq = [h["size"] for h in history]

        # --- Pattern scan: len 5 -> 1 ---
        for length in range(5, 0, -1):
            if len(size_seq) < length + 1:
                continue

            # HTML: const recent = sizeSeq.slice(-len);
            # slice(-len) = LAST `len` items of array.
            # Since array is newest-first, slice(-len) = OLDEST `len` items.
            # We must mirror this EXACTLY.
            recent = size_seq[-length:] if length > 0 else []

            matches: List[str] = []

            # HTML: for (let i = 0; i < sizeSeq.length - len; i++) {
            #         let match = true;
            #         for (let j = 0; j < len; j++) {
            #           if (sizeSeq[i + j] !== recent[j]) { match = false; break; }
            #         }
            #         if (match && (i + len < sizeSeq.length)) {
            #           matches.push(sizeSeq[i + len]);
            #         }
            #       }
            for i in range(len(size_seq) - length):
                matched = True
                for j in range(length):
                    if size_seq[i + j] != recent[j]:
                        matched = False
                        break
                if matched and (i + length < len(size_seq)):
                    matches.append(size_seq[i + length])

            if not matches:
                continue

            # HTML: const bigCount = matches.filter(s => s === 'BIG').length;
            big_count = matches.count("BIG")
            small_count = matches.count("SMALL")
            total = len(matches)

            # HTML: if (bigCount / total > 0.6 && bigCount >= 3)
            if total > 0 and (big_count / total) > 0.6 and big_count >= 3:
                best_size = "BIG"
                logic_applied = f"P-{length} RECUR"
                break

            # HTML: if (smallCount / total > 0.6 && smallCount >= 3)
            if total > 0 and (small_count / total) > 0.6 and small_count >= 3:
                best_size = "SMALL"
                logic_applied = f"P-{length} RECUR"
                break

            # HTML: if (!bestSize) { bias fallback }
            if best_size is None:
                if big_count > small_count:
                    best_size = "BIG"
                    logic_applied = f"P-{length} BIAS"
                elif small_count > big_count:
                    best_size = "SMALL"
                    logic_applied = f"P-{length} BIAS"

        # --- HTML: DELTA-20 fallback ---
        # const recent20 = sizeSeq.slice(-20);
        if best_size is None:
            recent20 = size_seq[-20:] if len(size_seq) >= 20 else size_seq[:]
            big = recent20.count("BIG")
            small = len(recent20) - big
            if big > small:
                best_size = "BIG"
            elif small > big:
                best_size = "SMALL"
            else:
                best_size = "BIG" if random.random() > 0.5 else "SMALL"
            logic_applied = "DELTA-20"

    # --- HTML: Strict OPPOSITE flip ---
    # bestSize = bestSize === 'BIG' ? 'SMALL' : 'BIG';
    best_size = "SMALL" if best_size == "BIG" else "BIG"

    # --- HTML: Anti-repeat streak breaker ---
    # if (window.lastPreds && window.lastPreds.length >= 3) {
    #   if (window.lastPreds.every(p => p === bestSize)) {
    #     bestSize = bestSize === 'BIG' ? 'SMALL' : 'BIG';
    #     logicApplied = "STREAK BREAK";
    #   }
    # }
    if last_preds and len(last_preds) >= 3:
        if all(p == best_size for p in last_preds[-3:]):
            best_size = "SMALL" if best_size == "BIG" else "BIG"
            logic_applied = "STREAK BREAK"

    last_preds.append(best_size)
    if len(last_preds) > 3:
        last_preds.pop(0)

    # --- HTML: Weighted Sure Number calculation ---
    # const pool = bestSize === 'BIG' ? [5,6,7,8,9] : [0,1,2,3,4];
    pool = B_POOL if best_size == "BIG" else S_POOL

    # const relevantNums = history
    #   .filter(h => (bestSize === 'BIG' ? h.num >= 5 : h.num < 5))
    #   .map(h => h.num);
    relevant_nums: List[int] = []
    for h in history:
        n = _to_int(h.get("num") if "num" in h else h.get("number"))
        if best_size == "BIG" and n >= 5:
            relevant_nums.append(n)
        elif best_size == "SMALL" and n < 5:
            relevant_nums.append(n)

    # HTML: if (relevantNums.length === 0) { random from pool }
    if not relevant_nums:
        sure_number = pool[random.randint(0, len(pool) - 1)]
    else:
        # HTML: weighted distribution
        weights: List[float] = []
        total_weight = 0.0
        decay = 0.9

        for i in range(len(relevant_nums)):
            weight = math.pow(decay, len(relevant_nums) - 1 - i)
            weights.append(weight)
            total_weight += weight

        weighted_nums: List[int] = []
        for i in range(len(relevant_nums)):
            # HTML: const count = Math.ceil(weights[i] * 10 / totalWeight);
            if total_weight > 0:
                count = math.ceil(weights[i] * 10 / total_weight)
            else:
                count = 1
            for _ in range(count):
                weighted_nums.append(relevant_nums[i])

        # HTML: for (let num of pool) {
        #         if (!relevantNums.includes(num)) {
        #           weightedNums.push(num);
        #           weightedNums.push(num);
        #         }
        #       }
        for num in pool:
            if num not in relevant_nums:
                weighted_nums.append(num)
                weighted_nums.append(num)

        # HTML: sureNumber = weightedNums[Math.floor(Math.random() * weightedNums.length)];
        sure_number = weighted_nums[random.randint(0, len(weighted_nums) - 1)]

    return {
        "prediction": best_size,
        "sureNumber": sure_number,
        "logic": logic_applied,
    }


def check_result(
    current_number: int,
    prev_issue: str,
    prev_pred: str,
    prev_sure: int,
    prev_logic: str,
) -> Dict[str, Any]:
    """
    1:1 port of HTML checkResult(current, prevIssue, prevPred, prevSure, prevLogic).
    """
    num = current_number
    size = "BIG" if num >= 5 else "SMALL"

    # HTML: default LOSS
    status_text = "LOSS 🍂"
    status_class = "badge-loss"
    strip_class = "loss-status"

    # HTML: if (num === prevSure) -> JACKPOT 9x
    if num == prev_sure:
        status_text = "JACKPOT 9x"
        status_class = "badge-jackpot"
        strip_class = "jackpot-status"
    # HTML: else if (size === prevPred) -> WIN 2x
    elif size == prev_pred:
        status_text = "WIN 2x"
        status_class = "badge-win"
        strip_class = "win-status"

    # HTML: time string HH:MM:SS
    now = time.localtime()
    time_str = f"{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"

    append_history_item({
        "issue": prev_issue,
        "pred": prev_pred,
        "sure": prev_sure,
        "actualNum": num,
        "actualSize": size,
        "statusText": status_text,
        "statusClass": status_class,
        "logic": prev_logic or "AI MATRIX",
        "time": time_str,
    })

    return {
        "issue": prev_issue,
        "prediction": prev_pred,
        "sure": prev_sure,
        "actualNum": num,
        "actualSize": size,
        "statusText": status_text,
        "statusClass": status_class,
        "stripClass": strip_class,
        "logic": prev_logic,
        "time": time_str,
        "isJackpot": num == prev_sure,
        "isWin": (size == prev_pred) or (num == prev_sure),
    }


def append_history_item(item: Dict[str, Any]) -> None:
    """
    1:1 port of HTML appendHistoryItem(item).
    HTML inserts at BEGINNING and keeps max 40 items.
    """
    global history_list
    history_list.insert(0, item)
    if len(history_list) > 40:
        history_list.pop()


# ============================================================
# HTML: updatePredictionUI() equivalent
# ============================================================

def update_prediction_ui_state(
    prediction: str,
    target_num: int,
    logic: str,
    period_id: str,
) -> Dict[str, Any]:
    """
    1:1 port of HTML updatePredictionUI().
    Sets global current_* and returns UI-ready dict.
    """
    global current_pred, current_sure, current_logic, current_period
    current_pred = prediction
    current_sure = target_num
    current_logic = logic
    current_period = period_id

    # HTML: periodEl.innerText = (periodId && periodId !== "SYNC") ? String(periodId).slice(-5) : "SYNCING...";
    if period_id and period_id != "SYNC":
        display_period = str(period_id)[-5:]
    else:
        display_period = "SYNCING..."

    return {
        "prediction": prediction,
        "predClass": "pred-big" if prediction == "BIG" else "pred-small",
        "targetNum": target_num,
        "logic": logic,
        "periodId": display_period,
        "fullPeriodId": period_id,
    }


# ============================================================
# HISTORY PARSING FROM API JSON
# ============================================================

def _parse_history(json_data: str) -> List[Dict[str, Any]]:
    """
    Parse API JSON -> list of {"issue", "num", "size"} (NEWEST FIRST).
    Mirrors HTML: data?.data?.list
    """
    try:
        obj = json.loads(json_data)
    except Exception:
        return []

    data_array = None
    if isinstance(obj.get("data"), dict) and "list" in obj["data"]:
        data_array = obj["data"]["list"]
    elif "Data" in obj:
        data_array = obj["Data"]
    elif "list" in obj:
        data_array = obj["list"]

    if not data_array:
        return []

    out: List[Dict[str, Any]] = []
    for item in data_array:
        issue = (
            item.get("issueNumber")
            or item.get("PeriodNo")
            or item.get("period")
            or ""
        )
        num_raw = item.get("number") or item.get("Number")
        num = _to_int(num_raw)
        out.append({
            "issue": str(issue),
            "num": num,
            "size": "BIG" if num >= 5 else "SMALL",
        })
    return out


# ============================================================
# MAIN ENGINE TICK — mirrors HTML run() setInterval body
# ============================================================

def engine_pro() -> Dict[str, Any]:
    """
    1:1 port of HTML run() setInterval callback.

    Flow:
      1. Fetch API -> list[0] = current draw
      2. If current.issueNumber !== lastProcessedDraw:
         a. If predictedPeriod == current.issueNumber -> checkResult()
         b. Update historyBuffer (unshift if new issue)
         c. lastProcessedDraw = current.issueNumber
         d. nextPeriod = getNextPeriodString(current.issueNumber)
         e. generatePrediction(historyBuffer)
         f. Store predictedPeriod / activePred / activeSure / activeLogic
         g. updatePredictionUI(pred, sure, logic, nextPeriod)
    """
    global history_buffer, last_processed_draw
    global predicted_period, active_pred, active_sure, active_logic
    global last_issue, prev_issue, prev_pred, prev_sure, prev_logic
    global current_pred, current_sure, current_logic, current_period

    body = fetch_api_data()

    if body is None:
        # HTML: offline fallback — only if no predictedPeriod yet
        if not predicted_period:
            fallback = generate_prediction(history_buffer)
            ui = update_prediction_ui_state(
                fallback["prediction"],
                fallback["sureNumber"],
                fallback["logic"],
                "SYNC",
            )
            return {
                "ok": False,
                "reason": "no_api",
                "active": ui,
                "history": list(history_list),
            }
        return {
            "ok": False,
            "reason": "no_api",
            "active": None,
            "history": list(history_list),
        }

    api_list = _parse_history(body)
    if not api_list:
        if not predicted_period:
            fallback = generate_prediction(history_buffer)
            ui = update_prediction_ui_state(
                fallback["prediction"],
                fallback["sureNumber"],
                fallback["logic"],
                "SYNC",
            )
            return {
                "ok": False,
                "reason": "no_history",
                "active": ui,
                "history": list(history_list),
            }
        return {
            "ok": False,
            "reason": "no_history",
            "active": None,
            "history": list(history_list),
        }

    current = api_list[0]
    current_issue = current["issue"]
    current_num = current["num"]
    current_size = current["size"]

    ui_signal: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

    # HTML: if (current.issueNumber !== lastProcessedDraw) { ... }
    if current_issue != last_processed_draw:

        # 1. HTML: if (window.predictedPeriod && window.predictedPeriod === current.issueNumber)
        #         checkResult(current, window.predictedPeriod, window.activePred, window.activeSure, window.activeLogic);
        if predicted_period and predicted_period == current_issue:
            result = check_result(
                current_num,
                predicted_period,
                active_pred or "SMALL",
                active_sure if active_sure is not None else 0,
                active_logic or "AI MATRIX",
            )

        # 2. HTML: historyBuffer.unshift if new issue
        if not history_buffer or history_buffer[0]["issue"] != current_issue:
            history_buffer.insert(0, {
                "issue": current_issue,
                "num": current_num,
                "size": current_size,
            })
            if len(history_buffer) > MAX_HISTORY:
                history_buffer.pop()

        last_processed_draw = current_issue

        # 3. HTML: const nextPeriod = getNextPeriodString(current.issueNumber);
        next_period = get_next_period_string(current_issue)

        # 4. HTML: const { prediction, sureNumber, logic } = generatePrediction(historyBuffer);
        pred = generate_prediction(history_buffer)

        # 5. HTML: window.predictedPeriod = nextPeriod;
        #         window.activePred = prediction;
        #         window.activeSure = sureNumber;
        #         window.activeLogic = logic;
        predicted_period = next_period
        active_pred = pred["prediction"]
        active_sure = pred["sureNumber"]
        active_logic = pred["logic"]

        # 6. HTML: updatePredictionUI(prediction, sureNumber, logic, nextPeriod);
        ui_signal = update_prediction_ui_state(
            pred["prediction"],
            pred["sureNumber"],
            pred["logic"],
            next_period,
        )

    # HTML: save prev = current (implicit in HTML via lastProcessedDraw)
    prev_issue = current_issue
    prev_pred = current_pred
    prev_sure = current_sure
    prev_logic = current_logic

    return {
        "ok": True,
        "issue": current_issue,
        "nextPeriod": predicted_period if predicted_period else current_issue,
        "active": ui_signal,
        "result": result,
        "latest": {"number": current_num, "size": current_size},
        "history": list(history_list),
        "engine": {
            "name": CONFIG["engine_name"],
            "code": CONFIG["engine_code"],
        },
    }


# ============================================================
# PUBLIC API
# ============================================================

def sddgamer263_predict() -> Dict[str, Any]:
    """Run one engine tick. Returns full state dict."""
    return engine_pro()


def reset() -> None:
    """Clear all engine state (page refresh / app restart)."""
    global history_buffer, last_preds, history_list
    global predicted_period, active_pred, active_sure, active_logic
    global current_pred, current_sure, current_logic, current_period
    global last_processed_draw
    global last_issue, prev_issue, prev_pred, prev_sure, prev_logic
    global _last_fetch_ts, _last_fetch_json

    history_buffer = []
    last_preds = []
    history_list = []

    predicted_period = None
    active_pred = None
    active_sure = None
    active_logic = None

    current_pred = "WAIT"
    current_sure = None
    current_logic = "AI MATRIX"
    current_period = ""

    last_processed_draw = None

    last_issue = None
    prev_issue = None
    prev_pred = None
    prev_sure = None
    prev_logic = None

    _last_fetch_ts = 0.0
    _last_fetch_json = None


def clear_engine_cache() -> None:
    global _last_fetch_ts, _last_fetch_json
    _last_fetch_ts = 0.0
    _last_fetch_json = None


# ============================================================
# CLI / SELF-TEST
# ============================================================

if __name__ == "__main__":
    reset()
    print("Testing prediction_engine.py (RAJPUT V9 ULTRA — 100% HTML port) ...\n")

    # ---- Offline unit test: generate_prediction ----
    print("=== Unit test: generate_prediction (HTML exact) ===")

    # HTML test: 5 items newest first
    fake = [
        {"issue": "1005", "num": 7, "size": "BIG"},
        {"issue": "1004", "num": 6, "size": "BIG"},
        {"issue": "1003", "num": 8, "size": "BIG"},
        {"issue": "1002", "num": 2, "size": "SMALL"},
        {"issue": "1001", "num": 1, "size": "SMALL"},
    ]
    pred = generate_prediction(fake)
    print(f"  input sizes (newest first) = {[h['size'] for h in fake]}")
    print(f"  -> prediction     = {pred['prediction']}")
    print(f"  -> sureNumber     = {pred['sureNumber']}")
    print(f"  -> logic          = {pred['logic']}\n")

    fake2 = [
        {"issue": "2005", "num": 1, "size": "SMALL"},
        {"issue": "2004", "num": 2, "size": "SMALL"},
        {"issue": "2003", "num": 9, "size": "BIG"},
        {"issue": "2002", "num": 3, "size": "SMALL"},
        {"issue": "2001", "num": 0, "size": "SMALL"},
    ]
    pred2 = generate_prediction(fake2)
    print(f"  -> prediction2    = {pred2['prediction']}")
    print(f"  -> sureNumber2    = {pred2['sureNumber']}")
    print(f"  -> logic2         = {pred2['logic']}\n")

    # ---- Unit test: check_result ----
    print("=== Unit test: check_result ===")
    r = check_result(7, "1005", "BIG", 7, "AI MATRIX")
    print(f"  check_result(7,'1005','BIG',7)   = {r['statusText']} (expect JACKPOT 9x)")
    r = check_result(6, "1004", "BIG", 3, "AI MATRIX")
    print(f"  check_result(6,'1004','BIG',3)   = {r['statusText']} (expect WIN 2x)")
    r = check_result(3, "1003", "BIG", 8, "AI MATRIX")
    print(f"  check_result(3,'1003','BIG',8)   = {r['statusText']} (expect LOSS 🍂)\n")

    # ---- Unit test: get_next_period_string ----
    print("=== Unit test: get_next_period_string ===")
    print(f"  '202610060088' -> {get_next_period_string('202610060088')}")
    print(f"  '1005'         -> {get_next_period_string('1005')}\n")

    # ---- Live test ----
    print("=== Live Engine Test ===")
    for i in range(3):
        out = sddgamer263_predict()
        if not out.get("ok"):
            print(f"tick {i}: no data ({out.get('reason')})")
        else:
            act = out.get("active")
            if act:
                print(
                    f"tick {i}: issue={out['issue']} "
                    f"next={out['nextPeriod']} "
                    f"signal={act['prediction']} sure={act['targetNum']} "
                    f"logic={act['logic']}"
                )
            else:
                print(f"tick {i}: issue={out['issue']} — no new signal")
            if out.get("result"):
                print(f"        -> {out['result']['statusText']} "
                      f"(actual {out['result']['actualNum']} {out['result']['actualSize']})")
        time.sleep(2)
