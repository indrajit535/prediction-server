"""
CYBER TAMILAN — prediction_engine.py

Prediction engine — HTML logic transplant.

This engine is a 1:1 Python port of the HTML/JavaScript prediction logic
found in the 'SURESHOT SHUVO' signal page. The original Python zig-zag /
normal heuristic has been completely removed and replaced.

Ported from HTML/JS:
  - fetchHistoryData()      -> fetch_history_data()
  - enginePro()             -> engine_pro()
  - updateTimer()           -> update_timer() / period countdown
  - the signal generation block inside enginePro()

Logic summary (exactly as in the HTML):
  1. Fetch the latest issue list from the WinGo history endpoint
     (with the same 4-proxy fallback chain).
  2. If the newest issue differs from the last processed one AND we had a
     prior active prediction for that issue, grade it:
         win       = predicted size == actual size
         jackpot   = actual digit == n1 or n2
         winOrJackpot => reset lossCount, ++winStreak, ++totalWins
         else         => ++lossCount, winStreak = 0, ++totalLoss
  3. For the NEXT period:
         seed      = int(last 3 digits of issue)
         histSlice = first 10 digits of the history
         bigBias   = count(histSlice >= 5)
         trend     = BIG   if (seed even and bigBias >= 5)
                     SMALL if (seed even and bigBias <  5)
                     SMALL if (seed odd  and histSlice[0] >= 5)
                     BIG   if (seed odd  and histSlice[0] <  5)
         n1, n2 chosen from the arrays below (exact same index math).
  4. Emit the signal with confidence 0.92 (92%).

This is a heuristic only; it cannot guarantee future outcomes.
"""

from __future__ import annotations

import time
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Configuration — mirrors the HTML CONFIG block
# ---------------------------------------------------------------------------

CONFIG = {
    "period_seconds": 30,                       # HTML: CONFIG.periodSeconds
    "history_url": (
        "https://draw.ar-lottery01.com/WinGo/WinGo_1M/"
        "GetHistoryIssuePage.json"
    ),
    "cache_ttl": 2,                             # HTML polls every 2000 ms
    "signal_confidence": 0.92,                  # HTML: applyResult(..., 0.92, ...)
    "engine_name": "RDX OWNER PRO",
    "engine_code": "rdx-pro",
}


# ---------------------------------------------------------------------------
# Proxy chain — exact same four entries as the HTML PROXIES array
# ---------------------------------------------------------------------------

def _proxy_identity(url: str) -> str:
    return url


def _proxy_allorigins(url: str) -> str:
    return "https://api.allorigins.win/raw?url=" + urllib.parse.quote(url, safe="")


def _proxy_corsproxy(url: str) -> str:
    return "https://corsproxy.io/?" + urllib.parse.quote(url, safe="")


def _proxy_codetabs(url: str) -> str:
    return "https://api.codetabs.com/v1/proxy/?quest=" + urllib.parse.quote(url, safe="")


PROXIES = [
    _proxy_identity,
    _proxy_allorigins,
    _proxy_corsproxy,
    _proxy_codetabs,
]


# ---------------------------------------------------------------------------
# Internal mutable state — mirrors the HTML module-scope lets
# ---------------------------------------------------------------------------

_last_processed: str = ""
_current_active: Optional[Dict[str, Any]] = None
_history: List[Dict[str, Any]] = []
_pred_state: Dict[str, int] = {
    "level": 0,
    "lossCount": 0,
    "winStreak": 0,
    "bestStreak": 0,
    "totalWins": 0,
    "totalLoss": 0,
    "step": 1,
}

_last_fetch_ts: float = 0.0
_last_fetch_list: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_big_small(number: Any) -> str:
    """0-4 = SMALL; 5-9 = BIG — same as the HTML `n >= 5 ? 'BIG' : 'SMALL'`."""
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except (TypeError, ValueError):
        return "SMALL"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# fetchHistoryData() — direct 1:1 port
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: float = 6.0) -> Optional[str]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json,text/plain,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def fetch_history_data(mode: str = "30s") -> List[Dict[str, Any]]:
    """
    Port of HTML:

        async function fetchHistoryData(mode) {
            let directUrl = `https://draw.ar-lottery01.com/WinGo/WinGo_1M/
                             GetHistoryIssuePage.json?ts=${Date.now()}`;
            for (let proxy of PROXIES) { ... return list; }
            return [];
        }

    A tiny in-memory cache prevents hammering the proxy chain when the
    caller polls every 2 seconds (mirrors the browser's natural throttling).
    """
    global _last_fetch_ts, _last_fetch_list

    now = time.time()
    if _last_fetch_list and (now - _last_fetch_ts) < CONFIG["cache_ttl"]:
        return _last_fetch_list

    direct_url = (
        f"{CONFIG['history_url']}?ts={int(now * 1000)}"
    )

    for proxy in PROXIES:
        url = proxy(direct_url)
        body = _http_get(url)
        if not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue

        # HTML:  d?.data?.list ?? d?.data?.gameslist ?? d?.list ?? []
        candidate_lists = [
            (data.get("data") or {}).get("list") if isinstance(data.get("data"), dict) else None,
            (data.get("data") or {}).get("gameslist") if isinstance(data.get("data"), dict) else None,
            data.get("list"),
        ]
        for candidate in candidate_lists:
            if candidate:
                _last_fetch_ts = now
                _last_fetch_list = candidate
                return candidate

    return []


# ---------------------------------------------------------------------------
# engine_pro() — direct 1:1 port of the HTML enginePro()
# ---------------------------------------------------------------------------

def _grade_previous(issue: str, latest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Mirrors the grading block inside enginePro(). Returns a popup payload
    when the previous prediction wins (or jackpots), otherwise None.
    """
    global _current_active

    if not _current_active:
        return None
    if _current_active.get("period") != issue:
        return None
    if any(str(h.get("period")) == issue for h in _history):
        return None

    n = _to_int(latest.get("number") or latest.get("openCode") or latest.get("winNumber"))
    sz = "BIG" if n >= 5 else "SMALL"

    n1 = _current_active["n1"]
    n2 = _current_active["n2"]

    is_jackpot = (n == n1 or n == n2)
    was_win = (sz == _current_active["size"])
    is_win_or_jackpot = was_win or is_jackpot

    if is_win_or_jackpot:
        _pred_state["lossCount"] = 0
        _pred_state["winStreak"] += 1
        _pred_state["totalWins"] += 1
        if _pred_state["winStreak"] > _pred_state["bestStreak"]:
            _pred_state["bestStreak"] = _pred_state["winStreak"]
    else:
        _pred_state["lossCount"] += 1
        _pred_state["winStreak"] = 0
        _pred_state["totalLoss"] += 1

    _history.insert(0, {
        "period": issue,
        "mode": "30s",
        "prediction": _current_active["size"],
        "predNum": f"{n1} & {n2}",
        "actual": sz,
        "actualNum": n,
        "win": is_win_or_jackpot,
        "isJackpot": is_jackpot,
        "step": _pred_state["step"],
    })
    del _history[60:]

    if is_win_or_jackpot:
        return {
            "period": issue[-5:],
            "prediction": _current_active["size"],
            "predNum": f"{n1} & {n2}",
            "actual": {"color": sz, "number": n},
            "isJackpot": is_jackpot,
        }
    return None


def engine_pro(mode: str = "30s") -> Dict[str, Any]:
    """
    Direct port of the HTML enginePro(). Returns a dict describing either
    the current active signal or the "no data" state.
    """
    global _current_active, _last_processed

    list_ = fetch_history_data(mode)
    if not list_:
        return {"ok": False, "reason": "no_history"}

    latest = list_[0]
    issue_raw = latest.get("issueNumber")
    if issue_raw is None:
        issue_raw = latest.get("issue")
    if issue_raw is None:
        issue_raw = latest.get("periodNumber")
    issue = str(issue_raw)

    popup_payload: Optional[Dict[str, Any]] = None

    # ---- Grade the previous prediction (if this issue is new) ----
    if _last_processed and _last_processed != issue:
        popup_payload = _grade_previous(issue, latest)

    # ---- Build prediction for the NEXT period ----
    try:
        next_period = str(int(issue) + 1)
    except ValueError:
        next_period = issue  # fallback — non-numeric issue id

    result: Dict[str, Any] = {
        "ok": True,
        "issue": issue,
        "nextPeriod": next_period,
        "popup": popup_payload,
        "active": None,
    }

    if _current_active and _current_active.get("period") == next_period:
        result["active"] = dict(_current_active)
        _last_processed = issue
        return result

    # ---- Exact same math as the HTML block ----
    seed = _to_int(issue[-3:])
    hist_slice = [
        _to_int(x.get("number") or x.get("openCode") or x.get("winNumber"))
        for x in list_[:10]
    ]
    if not hist_slice:
        hist_slice = [0]

    big_bias = sum(1 for n in hist_slice if n >= 5)

    # HTML:
    #   trend = (seed % 2 === 0)
    #       ? (bigBias >= 5 ? "BIG" : "SMALL")
    #       : (histSlice[0] >= 5 ? "SMALL" : "BIG");
    if seed % 2 == 0:
        trend = "BIG" if big_bias >= 5 else "SMALL"
    else:
        trend = "SMALL" if hist_slice[0] >= 5 else "BIG"

    big_pool = [5, 6, 7, 8, 9]
    small_pool = [0, 1, 2, 3, 4]

    if trend == "BIG":
        n1 = big_pool[(seed + hist_slice[0]) % 5]
        n2 = small_pool[(seed * 3) % 5]
    else:
        n1 = small_pool[(seed + hist_slice[0]) % 5]
        n2 = big_pool[(seed * 7) % 5]

    _current_active = {
        "period": next_period,
        "size": trend,
        "n1": n1,
        "n2": n2,
    }
    _pred_state["step"] = _pred_state["lossCount"] + 1

    _last_processed = issue

    result["active"] = dict(_current_active)
    result["confidence"] = CONFIG["signal_confidence"]
    result["engine"] = {
        "name": CONFIG["engine_name"],
        "code": CONFIG["engine_code"],
    }
    return result


# ---------------------------------------------------------------------------
# update_timer() — port of the HTML countdown / ring logic
# ---------------------------------------------------------------------------

def update_timer() -> Dict[str, Any]:
    """
    HTML:
        let now = Math.floor(Date.now() / 1000);
        let rem = CONFIG.periodSeconds - now % CONFIG.periodSeconds;

    Returns the remaining seconds and the ring fraction for drawing.
    """
    now = int(time.time())
    rem = CONFIG["period_seconds"] - (now % CONFIG["period_seconds"])
    return {
        "secondsLeft": rem,
        "periodSeconds": CONFIG["period_seconds"],
        "ringFraction": rem / CONFIG["period_seconds"],
    }


# ---------------------------------------------------------------------------
# Stats — port of the HTML renderStats()/toolStats click handler
# ---------------------------------------------------------------------------

def get_stats() -> Dict[str, Any]:
    w = _pred_state["totalWins"]
    l = _pred_state["totalLoss"]
    t = w + l
    rate = round(w / t * 100) if t else None
    return {
        "totalWins": w,
        "totalLoss": l,
        "total": t,
        "winRate": rate,
        "winStreak": _pred_state["winStreak"],
        "bestStreak": _pred_state["bestStreak"],
        "lossCount": _pred_state["lossCount"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sddgamer263_predict() -> Dict[str, Any]:
    """
    Run one engine tick and return the full state dict.

    This is the main entry point. Callers typically invoke it once per
    second (or once per period boundary) to obtain:

        {
          "ok":            bool,
          "issue":         str,
          "nextPeriod":    str,
          "active":        {"period", "size", "n1", "n2"} | None,
          "popup":         win/jackpot payload | None,
          "confidence":    0.92,
          "engine":        {...},
          "timer":         {...},
          "stats":         {...},
          "history":       [...],
        }
    """
    engine_result = engine_pro()

    return {
        **engine_result,
        "confidence": engine_result.get("confidence", CONFIG["signal_confidence"]),
        "engine": engine_result.get("engine", {
            "name": CONFIG["engine_name"],
            "code": CONFIG["engine_code"],
        }),
        "timer": update_timer(),
        "stats": get_stats(),
        "history": list(_history),
    }


def reset() -> None:
    """Clear all engine state (matches a page refresh)."""
    global _last_processed, _current_active, _last_fetch_ts, _last_fetch_list
    _last_processed = ""
    _current_active = None
    _history.clear()
    _pred_state.update({
        "level": 0,
        "lossCount": 0,
        "winStreak": 0,
        "bestStreak": 0,
        "totalWins": 0,
        "totalLoss": 0,
        "step": 1,
    })
    _last_fetch_ts = 0.0
    _last_fetch_list = []


def clear_engine_cache() -> None:
    """Compatibility shim for callers that used the old API."""
    global _last_fetch_ts, _last_fetch_list
    _last_fetch_ts = 0.0
    _last_fetch_list = []


# ---------------------------------------------------------------------------
# CLI / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    reset()
    print("Testing prediction_engine.py (HTML logic port) ...\n")

    for i in range(5):
        out = sddgamer263_predict()
        timer = out.get("timer", {})
        active = out.get("active")
        stats = out.get("stats", {})

        if not out.get("ok"):
            print(f"tick {i}: no history available ({out.get('reason')})")
        else:
            if active:
                print(
                    f"tick {i}: issue={out['issue']} "
                    f"next={out['nextPeriod']} "
                    f"signal={active['size']} "
                    f"[{active['n1']} & {active['n2']}] "
                    f"conf={int(out['confidence']*100)}% "
                    f"| secLeft={timer.get('secondsLeft')} "
                    f"| W/L={stats.get('totalWins')}/{stats.get('totalLoss')}"
                )
            else:
                print(
                    f"tick {i}: issue={out['issue']} — no active signal "
                    f"| secLeft={timer.get('secondsLeft')}"
                )

        if out.get("popup"):
            p = out["popup"]
            tag = "JACKPOT" if p["isJackpot"] else "WIN"
            print(
                f"        -> {tag}! period={p['period']} "
                f"pred={p['prediction']} actual={p['actual']}"
            )

        time.sleep(2)
