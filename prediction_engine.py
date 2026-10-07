"""
RAJPUT V9 ULTRA - prediction_engine.py  (v2.0)

v2.0 = ALL of the v1 HTML logic (kept untouched) + new layers:

  KEPT (v1, from HTML):
    - Pattern scan len 5..1, RECUR (>60% and >=3), BIAS, DELTA-20
    - Strict OPPOSITE flip, STREAK BREAK (last 3 preds), SEED INIT
    - Weighted Sure Number (decay 0.9, unseen x2)
    - JACKPOT 9x / WIN 2x / LOSS, +1 NEXT PERIOD tracking

  NEW (v2):
    - Multi-pattern detector: STREAK, ALTERNATING (ABAB), DOUBLE (AABB),
      PERIODIC cycles (period 2..6), N-gram memory (len 1..6, recency weighted)
    - Break detection: learns from history how often a streak of length L
      (or an alternating chain of length A) ended vs continued, then
      signals BREAK / RUN with a confidence value
    - Ensemble vote: v1 result + all v2 detectors -> final side + confidence
    - Real accuracy tracker (wins / losses / jackpots, per-logic accuracy)
    - backtest(): walk-forward test of the engine on real history

NOTE: Draw results are random. No detector can reach 100% accuracy.
Use backtest() / stats to see the real hit-rate of this engine.
"""

from __future__ import annotations

import json
import math
import random
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# CONFIG
# ============================================================

CONFIG = {
    "version": "2.0",
    "cache_ttl": 2.5,
    "engine_name": "RAJPUT V9 ULTRA 2.0",
    "engine_code": "rajput-v9-ultra-2",
    "v2_min_history": 30,      # v2 layer starts after this many results
    "v2_min_confidence": 0.20, # ensemble confidence needed to override v1
}

API_URLS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    "https://easy-share-server.lovable.app/api/public/WinGo_1M",
    "https://api-wingo1min.randorona.workers.dev/",
]

B_POOL = [5, 6, 7, 8, 9]
S_POOL = [0, 1, 2, 3, 4]
MAX_HISTORY = 200
MAX_HISTORY_LIST = 40

# ============================================================
# STATE
# ============================================================

history_buffer: List[Dict[str, Any]] = []   # newest first
last_preds: List[str] = []
history_list: List[Dict[str, Any]] = []

predicted_period: Optional[str] = None
active_pred: Optional[str] = None
active_sure: Optional[int] = None
active_logic: Optional[str] = None

last_processed_draw: Optional[str] = None

current_pred: str = "WAIT"
current_sure: Optional[int] = None
current_logic: str = "AI MATRIX"
current_period: str = ""

last_analysis: Dict[str, Any] = {}

stats: Dict[str, Any] = {
    "total": 0, "wins": 0, "losses": 0, "jackpots": 0,
    "by_logic": {},   # logic -> {"n": int, "hit": int}
}

_last_fetch_ts: float = 0.0
_last_fetch_body: Optional[str] = None


# ============================================================
# HELPERS
# ============================================================

def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _flip(side: str) -> str:
    return "SMALL" if side == "BIG" else "BIG"


def _http_get(url: str, timeout: float = 8.0) -> Optional[str]:
    try:
        req = urllib.request.Request(
            url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def get_next_period_string(issue_str: str) -> str:
    try:
        return str(int(issue_str) + 1)
    except (ValueError, TypeError):
        return str(issue_str)


def fetch_api_data() -> Optional[str]:
    global _last_fetch_ts, _last_fetch_body
    now = time.time()
    if _last_fetch_body is not None and (now - _last_fetch_ts) < CONFIG["cache_ttl"]:
        return _last_fetch_body
    for url in API_URLS:
        body = _http_get(url)
        if body:
            _last_fetch_ts = now
            _last_fetch_body = body
            return body
    return None


def _parse_history(body: str) -> List[Dict[str, Any]]:
    try:
        obj = json.loads(body)
    except Exception:
        return []
    if not isinstance(obj, dict):
        return []
    arr = None
    if isinstance(obj.get("data"), dict) and "list" in obj["data"]:
        arr = obj["data"]["list"]
    elif "Data" in obj:
        arr = obj["Data"]
    elif "list" in obj:
        arr = obj["list"]
    if not arr:
        return []
    out: List[Dict[str, Any]] = []
    for item in arr:
        issue = item.get("issueNumber") or item.get("PeriodNo") or item.get("period") or ""
        num = _to_int(item.get("number", item.get("Number")))
        out.append({"issue": str(issue), "num": num, "size": "BIG" if num >= 5 else "SMALL"})
    return out


# ============================================================
# v1 CORE  (HTML generatePrediction - side selection, unchanged)
# Returns the pattern read BEFORE the strict-opposite flip.
# ============================================================

def _v1_raw_side(history: List[Dict[str, Any]]) -> Tuple[str, str]:
    best_size: Optional[str] = None
    logic_applied = "AI MATRIX"

    if len(history) < 5:
        return ("BIG" if random.random() > 0.5 else "SMALL"), "SEED INIT"

    size_seq = [h["size"] for h in history]

    for length in range(5, 0, -1):
        if len(size_seq) < length + 1:
            continue
        recent = size_seq[-length:]
        matches: List[str] = []
        for i in range(len(size_seq) - length):
            ok = True
            for j in range(length):
                if size_seq[i + j] != recent[j]:
                    ok = False
                    break
            if ok and (i + length < len(size_seq)):
                matches.append(size_seq[i + length])
        if not matches:
            continue

        big_count = matches.count("BIG")
        small_count = matches.count("SMALL")
        total = len(matches)

        if big_count / total > 0.6 and big_count >= 3:
            return "BIG", f"P-{length} RECUR"
        if small_count / total > 0.6 and small_count >= 3:
            return "SMALL", f"P-{length} RECUR"

        if best_size is None:
            if big_count > small_count:
                best_size, logic_applied = "BIG", f"P-{length} BIAS"
            elif small_count > big_count:
                best_size, logic_applied = "SMALL", f"P-{length} BIAS"

    if best_size is None:
        recent20 = size_seq[-20:]
        big = recent20.count("BIG")
        small = len(recent20) - big
        if big > small:
            best_size = "BIG"
        elif small > big:
            best_size = "SMALL"
        else:
            best_size = "BIG" if random.random() > 0.5 else "SMALL"
        logic_applied = "DELTA-20"

    return best_size, logic_applied


# ============================================================
# v2 DETECTORS  (work on chronological list: oldest -> newest)
# ============================================================

def _chron(history: List[Dict[str, Any]]) -> List[str]:
    return [h["size"] for h in reversed(history)]


def _tail_run(c: List[str]) -> Tuple[str, int]:
    side, n = c[-1], 1
    while n < len(c) and c[-1 - n] == side:
        n += 1
    return side, n


def _tail_alt(c: List[str]) -> int:
    n = 1
    while n < len(c) and c[-1 - n] != c[-n]:
        n += 1
    return n


def _streak_stats(c: List[str], side: str, length: int) -> Tuple[int, int]:
    """History: when a run of `side` reached `length`, did it continue or break?"""
    cont = brk = run = 0
    for i in range(len(c) - 1):
        run = run + 1 if c[i] == side else 0
        if run == length:
            if c[i + 1] == side:
                cont += 1
            else:
                brk += 1
    return cont, brk


def _alt_stats(c: List[str], length: int) -> Tuple[int, int]:
    """History: when an alternating chain reached `length`, did it continue or break?"""
    cont = brk = 0
    alt = 1
    for i in range(1, len(c) - 1):
        alt = alt + 1 if c[i] != c[i - 1] else 1
        if alt == length:
            if c[i + 1] != c[i]:
                cont += 1
            else:
                brk += 1
    return cont, brk


def _ngram_counts(c: List[str], k: int) -> Tuple[Dict[str, float], int]:
    """Recency-weighted next-side counts after the last-k context."""
    ctx = c[-k:]
    cnt = {"BIG": 0.0, "SMALL": 0.0}
    n = 0
    last_start = len(c) - k - 1
    for i in range(0, len(c) - k):
        if c[i:i + k] == ctx:
            cnt[c[i + k]] += math.pow(0.985, last_start - i)
            n += 1
    return cnt, n


def _periodic(c: List[str]) -> Optional[Tuple[str, int, int]]:
    """Detect repeating cycle (e.g. BBS BBS BBS). Returns (next_side, period, reps)."""
    best = None
    for p in range(2, 7):
        if len(c) < p * 2:
            continue
        block = c[-p:]
        if len(set(block)) < 2:
            continue
        reps = 1
        pos = len(c) - p
        while pos - p >= 0 and c[pos - p:pos] == block:
            reps += 1
            pos -= p
        if reps >= 2 and (best is None or reps * p > best[2] * best[1]):
            best = (block[0], p, reps)  # next element of the cycle = first of block
    return best


def _double_pattern(c: List[str]) -> Optional[str]:
    """AABB style pairs: AA BB AA -> BB next ; AA BB A -> A next."""
    if len(c) >= 6:
        t = c[-6:]
        if t[0] == t[1] == t[4] == t[5] and t[2] == t[3] and t[0] != t[2]:
            return t[2]
    if len(c) >= 5:
        t = c[-5:]
        if t[0] == t[1] == t[4] and t[2] == t[3] and t[0] != t[2]:
            return t[4]
    return None


def analyze_patterns(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    v2 ensemble. Returns:
      {"side","confidence","detected":[names],"scores":{...},"break":{...}}
    """
    c = _chron(history)
    scores = {"BIG": 0.0, "SMALL": 0.0}
    detected: List[str] = []
    brk_info: Dict[str, Any] = {"state": "NONE"}

    def vote(side: str, w: float, name: str) -> None:
        if w <= 0:
            return
        scores[side] += w
        detected.append(name)

    if len(c) < CONFIG["v2_min_history"]:
        return {"side": None, "confidence": 0.0, "detected": [], "scores": scores, "break": brk_info}

    # 1) N-gram memory (len 1..6)
    for k in range(1, 7):
        cnt, n = _ngram_counts(c, k)
        tot = cnt["BIG"] + cnt["SMALL"]
        if n < 4 or tot <= 0:
            continue
        p_big = (cnt["BIG"] + 1) / (tot + 2)
        edge = abs(p_big - 0.5) * 2
        if edge < 0.2:
            continue
        side = "BIG" if p_big > 0.5 else "SMALL"
        vote(side, edge * (0.4 + 0.1 * k), f"NG{k}")

    # 2) STREAK RUN / BREAK detection
    s_side, s_len = _tail_run(c)
    if s_len >= 2:
        cont, brk = _streak_stats(c, s_side, s_len)
        n = cont + brk
        if n >= 3:
            p_break = (brk + 1) / (n + 2)
            brk_info = {"state": "RUN", "kind": "STREAK", "side": s_side,
                        "length": s_len, "p_break": round(p_break, 3), "samples": n}
            if p_break >= 0.6:
                brk_info["state"] = "BREAK"
                vote(_flip(s_side), (p_break - 0.5) * 4, f"BREAK-{s_len}")
            elif p_break <= 0.4:
                vote(s_side, (0.5 - p_break) * 4, f"RUN-{s_len}")

    # 3) ALTERNATING (ABAB) run / break
    a_len = _tail_alt(c)
    if a_len >= 4:
        cont, brk = _alt_stats(c, a_len)
        n = cont + brk
        if n >= 3:
            p_break = (brk + 1) / (n + 2)
            nxt_alt = _flip(c[-1])
            if brk_info.get("state") == "NONE":
                brk_info = {"state": "RUN", "kind": "ALT", "length": a_len,
                            "p_break": round(p_break, 3), "samples": n}
            if p_break >= 0.6:
                brk_info["state"] = "BREAK"
                vote(c[-1], (p_break - 0.5) * 4, f"ALT-BREAK-{a_len}")
            elif p_break <= 0.4:
                vote(nxt_alt, (0.5 - p_break) * 4, f"ALT-{a_len}")

    # 4) Periodic cycle
    per = _periodic(c)
    if per:
        side, p, reps = per
        vote(side, min(0.9, 0.4 + 0.15 * reps), f"CYCLE-{p}x{reps}")

    # 5) Double pairs (AABB)
    dbl = _double_pattern(c)
    if dbl:
        vote(dbl, 0.35, "DOUBLE")

    total = scores["BIG"] + scores["SMALL"]
    if total <= 0:
        return {"side": None, "confidence": 0.0, "detected": detected, "scores": scores, "break": brk_info}

    side = "BIG" if scores["BIG"] > scores["SMALL"] else "SMALL"
    if scores["BIG"] == scores["SMALL"]:
        side = None  # type: ignore
        conf = 0.0
    else:
        conf = abs(scores["BIG"] - scores["SMALL"]) / total
    return {"side": side, "confidence": round(conf, 3), "detected": detected,
            "scores": {k: round(v, 3) for k, v in scores.items()}, "break": brk_info}


# ============================================================
# SURE NUMBER  (HTML weighted logic, unchanged)
# ============================================================

def _sure_number(history: List[Dict[str, Any]], side: str) -> int:
    pool = B_POOL if side == "BIG" else S_POOL
    relevant = [h["num"] for h in history if (h["num"] >= 5 if side == "BIG" else h["num"] < 5)]
    if not relevant:
        return pool[random.randrange(len(pool))]

    decay = 0.9
    n = len(relevant)
    weights = [math.pow(decay, n - 1 - i) for i in range(n)]
    total_weight = sum(weights)

    weighted: List[int] = []
    for i in range(n):
        weighted.extend([relevant[i]] * math.ceil(weights[i] * 10 / total_weight))
    for num in pool:
        if num not in relevant:
            weighted.append(num)
            weighted.append(num)
    return weighted[random.randrange(len(weighted))]


# ============================================================
# MAIN PREDICTION  (v1 + v2 ensemble)
# ============================================================

def generate_prediction(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    global last_preds, last_analysis

    # --- v1: HTML pattern read + strict opposite ---
    raw_side, logic = _v1_raw_side(history)
    best_size = _flip(raw_side)

    # --- v2: multi-pattern + break detection ensemble ---
    analysis = analyze_patterns(history)
    last_analysis = analysis
    confidence = analysis["confidence"]

    if analysis["side"] and confidence >= CONFIG["v2_min_confidence"]:
        best_size = analysis["side"]
        top = "+".join(analysis["detected"][:3]) if analysis["detected"] else "ENSEMBLE"
        logic = f"V2 {top}"

    # --- v1: anti-repeat streak breaker ---
    if len(last_preds) >= 3 and all(p == best_size for p in last_preds):
        best_size = _flip(best_size)
        logic = "STREAK BREAK"

    last_preds.append(best_size)
    if len(last_preds) > 3:
        last_preds.pop(0)

    sure_number = _sure_number(history, best_size)

    return {
        "prediction": best_size,
        "sureNumber": sure_number,
        "logic": logic,
        "confidence": confidence,
        "analysis": analysis,
    }


# ============================================================
# RESULT CHECK / HISTORY / STATS
# ============================================================

def append_history_item(item: Dict[str, Any]) -> None:
    history_list.insert(0, item)
    while len(history_list) > MAX_HISTORY_LIST:
        history_list.pop()


def _record_stats(hit: bool, jackpot: bool, logic: str) -> None:
    stats["total"] += 1
    if hit:
        stats["wins"] += 1
    else:
        stats["losses"] += 1
    if jackpot:
        stats["jackpots"] += 1
    key = logic.split(" ")[0] if logic.startswith("V2") else logic
    d = stats["by_logic"].setdefault(key, {"n": 0, "hit": 0})
    d["n"] += 1
    d["hit"] += 1 if hit else 0


def get_stats() -> Dict[str, Any]:
    t = stats["total"]
    return {
        "total": t,
        "wins": stats["wins"],
        "losses": stats["losses"],
        "jackpots": stats["jackpots"],
        "win_rate": round(stats["wins"] * 100.0 / t, 2) if t else 0.0,
        "by_logic": {k: {"n": v["n"], "hit_rate": round(v["hit"] * 100.0 / v["n"], 2)}
                     for k, v in stats["by_logic"].items()},
    }


def check_result(current_number: int, prev_issue: str, prev_pred: str,
                 prev_sure: int, prev_logic: str) -> Dict[str, Any]:
    num = int(current_number)
    size = "BIG" if num >= 5 else "SMALL"

    status_text, status_class, strip_class = "LOSS 🍂", "badge-loss", "loss-status"
    if num == prev_sure:
        status_text, status_class, strip_class = "JACKPOT 9x", "badge-jackpot", "jackpot-status"
    elif size == prev_pred:
        status_text, status_class, strip_class = "WIN 2x", "badge-win", "win-status"

    t = time.localtime()
    time_str = f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"

    _record_stats(size == prev_pred or num == prev_sure, num == prev_sure, prev_logic or "AI MATRIX")

    append_history_item({
        "issue": prev_issue, "pred": prev_pred, "sure": prev_sure,
        "actualNum": num, "actualSize": size,
        "statusText": status_text, "statusClass": status_class,
        "logic": prev_logic or "AI MATRIX", "time": time_str,
    })

    return {
        "issue": prev_issue, "prediction": prev_pred, "sure": prev_sure,
        "actualNum": num, "actualSize": size,
        "statusText": f"{status_text} ({num} {size})",
        "statusClass": status_class, "stripClass": strip_class,
        "logic": prev_logic, "time": time_str,
        "isJackpot": num == prev_sure,
        "isWin": size == prev_pred or num == prev_sure,
    }


def update_prediction_ui_state(prediction: str, target_num: int, logic: str,
                               period_id: str) -> Dict[str, Any]:
    global current_pred, current_sure, current_logic, current_period
    current_pred, current_sure = prediction, target_num
    current_logic, current_period = logic, period_id
    display_period = str(period_id)[-5:] if (period_id and period_id != "SYNC") else "SYNCING..."
    return {
        "prediction": prediction,
        "predClass": "pred-big" if prediction == "BIG" else "pred-small",
        "targetNum": target_num,
        "logic": logic,
        "periodId": display_period,
        "fullPeriodId": period_id,
    }


# ============================================================
# ENGINE TICK (HTML run() loop body)
# ============================================================

def engine_pro() -> Dict[str, Any]:
    global last_processed_draw, predicted_period
    global active_pred, active_sure, active_logic

    def offline(reason: str) -> Dict[str, Any]:
        ui = None
        if not predicted_period:
            fb = generate_prediction(history_buffer)
            ui = update_prediction_ui_state(fb["prediction"], fb["sureNumber"], fb["logic"], "SYNC")
        return {"ok": False, "reason": reason, "active": ui,
                "history": list(history_list), "stats": get_stats()}

    body = fetch_api_data()
    if body is None:
        return offline("no_api")
    api_list = _parse_history(body)
    if not api_list:
        return offline("no_history")

    current = api_list[0]
    issue, num, size = current["issue"], current["num"], current["size"]

    ui_signal: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

    if issue != last_processed_draw:
        if predicted_period and predicted_period == issue:
            result = check_result(
                num, predicted_period,
                active_pred or "SMALL",
                active_sure if active_sure is not None else -1,
                active_logic or "AI MATRIX",
            )

        # First run: preload older draws so v2 has data immediately (newest first)
        if not history_buffer:
            history_buffer.extend(api_list[1:MAX_HISTORY])

        if not history_buffer or history_buffer[0]["issue"] != issue:
            history_buffer.insert(0, {"issue": issue, "num": num, "size": size})
            if len(history_buffer) > MAX_HISTORY:
                history_buffer.pop()

        last_processed_draw = issue
        next_period = get_next_period_string(issue)
        pred = generate_prediction(history_buffer)

        predicted_period = next_period
        active_pred = pred["prediction"]
        active_sure = pred["sureNumber"]
        active_logic = pred["logic"]

        ui_signal = update_prediction_ui_state(
            pred["prediction"], pred["sureNumber"], pred["logic"], next_period
        )
        ui_signal["confidence"] = pred["confidence"]
        ui_signal["detected"] = pred["analysis"].get("detected", [])
        ui_signal["break"] = pred["analysis"].get("break", {})

    return {
        "ok": True,
        "issue": issue,
        "nextPeriod": predicted_period or issue,
        "active": ui_signal,
        "result": result,
        "latest": {"number": num, "size": size},
        "history": list(history_list),
        "stats": get_stats(),
        "analysis": last_analysis,
        "engine": {"name": CONFIG["engine_name"], "code": CONFIG["engine_code"],
                   "version": CONFIG["version"]},
    }


# ============================================================
# BACKTEST (walk-forward, honest accuracy)
# ============================================================

def backtest(history: List[Dict[str, Any]], min_hist: int = 30) -> Dict[str, Any]:
    """history: newest first. Predict each draw using only older draws."""
    global last_preds
    saved = list(last_preds)
    last_preds = []
    wins = total = 0
    for t in range(len(history) - min_hist - 1, -1, -1):
        past = history[t + 1:]
        p = generate_prediction(past)["prediction"]
        total += 1
        wins += 1 if p == history[t]["size"] else 0
    last_preds = saved
    return {"tests": total, "wins": wins,
            "win_rate": round(wins * 100.0 / total, 2) if total else 0.0}


# ============================================================
# PUBLIC API
# ============================================================

def sddgamer263_predict() -> Dict[str, Any]:
    return engine_pro()


def reset() -> None:
    global history_buffer, last_preds, history_list, last_analysis
    global predicted_period, active_pred, active_sure, active_logic
    global current_pred, current_sure, current_logic, current_period
    global last_processed_draw, _last_fetch_ts, _last_fetch_body

    history_buffer, last_preds, history_list = [], [], []
    last_analysis = {}
    stats.update({"total": 0, "wins": 0, "losses": 0, "jackpots": 0, "by_logic": {}})
    predicted_period = active_pred = active_sure = active_logic = None
    current_pred, current_sure, current_logic, current_period = "WAIT", None, "AI MATRIX", ""
    last_processed_draw = None
    _last_fetch_ts, _last_fetch_body = 0.0, None


def clear_engine_cache() -> None:
    global _last_fetch_ts, _last_fetch_body
    _last_fetch_ts, _last_fetch_body = 0.0, None


# ============================================================
# SELF-TEST / LIVE LOOP
# ============================================================

if __name__ == "__main__":
    reset()
    print(f"{CONFIG['engine_name']} v{CONFIG['version']}\n")

    # Pattern detection demo: cycle BBS BBS BBS ...
    cyc = []
    seq = ["BIG", "BIG", "SMALL"] * 14
    for i, s in enumerate(reversed(seq)):          # newest first
        cyc.append({"issue": str(1000 + i), "num": 7 if s == "BIG" else 2, "size": s})
    a = analyze_patterns(cyc)
    print("cycle test  ->", a["side"], a["confidence"], a["detected"][:4])

    # Honest backtest on random data (expect ~50%)
    rnd = []
    for i in range(300):
        n = random.randint(0, 9)
        rnd.append({"issue": str(5000 - i), "num": n, "size": "BIG" if n >= 5 else "SMALL"})
    bt = backtest(rnd)
    print("random data backtest ->", bt, "(randomness => ~50% expected)\n")

    reset()
    print("Live ticks (Ctrl+C to stop)...")
    try:
        while True:
            out = sddgamer263_predict()
            if not out["ok"]:
                print("no data:", out["reason"])
            else:
                act = out["active"]
                if act:
                    print(f"issue={out['issue']} next={out['nextPeriod']} "
                          f"signal={act['prediction']} sure={act['targetNum']} "
                          f"logic={act['logic']} conf={act.get('confidence')}")
                if out["result"]:
                    print("   ->", out["result"]["statusText"], "| real win rate:",
                          out["stats"]["win_rate"], "%")
            time.sleep(2.5)
    except KeyboardInterrupt:
        pass
