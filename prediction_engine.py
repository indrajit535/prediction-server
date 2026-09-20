"""
============================================================
  WINGO PREDICTION ENGINE v14.0
  SHIKAARI BOSS LOGIC (from SHIKAARI BOSS HTML)
  
  Exact HTML logic:
  - NORMAL RULE: Last Number − 1
  - REPEAT RULE: 11 − Last Number (if last 2 same)
  - If result < 0 → Result = 9
  - BIG = 5-9, SMALL = 0-4
  - PAIR MAP included
============================================================
"""

import json
import time
import urllib.request

# ============================================================
# SECTION 1: CONFIGURATION
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

CONFIG = {
    "HISTORY_LIMIT": 50,
}

# Exact PAIR MAP from HTML
PAIR_MAP = {
    0: "0/2",
    1: "1/3",
    2: "2/4",
    5: "5/7",
    6: "6/8",
    7: "7/9",
    8: "6/8",
    9: "7/9",
}


# ============================================================
# SECTION 2: UTILITY FUNCTIONS
# ============================================================
def get_size(num):
    """BIG if >= 5 else SMALL — exact HTML logic"""
    return "BIG" if int(num) >= 5 else "SMALL"


def get_type(num):
    """Same as get_size, alias for compatibility"""
    return get_size(num)


# ============================================================
# SECTION 3: SHIKAARI ENGINE (EXACT HTML LOGIC)
# ============================================================
def calculate_result(nums):
    """
    Exact HTML 'calculateResult' function.
    
    HTML code:
    ----------------
    const last = nums[nums.length - 1];
    
    // REPEAT RULE
    if (nums.length >= 2 && nums[nums.length - 1] === nums[nums.length - 2]) {
        return { result: 11 - last, rule: "REPEAT RULE" };
    }
    
    // NORMAL RULE
    let result = last - 1;
    if (result < 0) { result = 9; }
    return { result: result, rule: "NORMAL RULE" };
    ----------------
    
    NOTE: HTML me 'nums' ka last element = most recent number
    (kyunki HTML 'list' ko slice(0,10).reverse() karta hai)
    """
    if not nums or len(nums) < 1:
        return {"result": 9, "rule": "NORMAL RULE"}

    last = nums[-1]  # most recent number

    # REPEAT RULE
    if len(nums) >= 2 and nums[-1] == nums[-2]:
        return {
            "result": 11 - last,
            "rule": "REPEAT RULE"
        }

    # NORMAL RULE
    result = last - 1
    if result < 0:
        result = 9

    return {
        "result": result,
        "rule": "NORMAL RULE"
    }


def logic_shikaari(history_nums):
    """
    HTML wala exact SHIKAARI logic.
    history_nums: most recent FIRST (API order me)
    """
    if not history_nums:
        return 9

    # HTML: list.slice(0,10).map(n => Number(n.number)).reverse()
    # i.e. recent 10 → reverse → oldest first
    recent_10 = history_nums[:10]
    reversed_nums = list(reversed(recent_10))

    calc = calculate_result(reversed_nums)
    return calc["result"]


def logic_shikaari_with_number(history_nums):
    """Same as above but returns (side, number, rule, pair)"""
    if not history_nums:
        return "SMALL", 9, "NORMAL RULE", None

    recent_10 = history_nums[:10]
    reversed_nums = list(reversed(recent_10))

    calc = calculate_result(reversed_nums)
    num = calc["result"]
    rule = calc["rule"]
    pair = PAIR_MAP.get(num, None)

    return get_size(num), num, rule, pair


# ============================================================
# SECTION 4: FETCH HISTORY
# ============================================================
def fetch_history_from_api():
    """Fetch live history from API — exact same as HTML"""
    try:
        req = urllib.request.Request(
            API_URL + f"?ts={int(time.time() * 1000)}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())

        lst = data["data"]["list"]
        return [{
            "issue": str(x["issueNumber"]),
            "number": int(x["number"]),
            "size": get_size(x["number"])
        } for x in lst]
    except Exception as e:
        print(f"[!] Fetch error: {e}")
        return None


# ============================================================
# SECTION 5: MAIN PREDICTOR CLASS
# ============================================================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.stats = {"wins": 0, "losses": 0, "total": 0}
        self.last_period = None
        self.last_pred_side = None
        self.last_pred_number = None
        self.last_rule = None
        self.last_pair = None
        self.prediction_log = []

    # --------------------------------------------------------
    # VALIDATE PREVIOUS PREDICTION
    # --------------------------------------------------------
    def validate(self, latest):
        """
        Exact HTML logic:
        Prediction belongs to exact period.
        WIN/LOSS decide only when API gives SAME period.
        """
        if not self.last_period or self.last_period == latest["issue"]:
            return
        if self.last_pred_side is None:
            return

        actual_side = latest["size"]
        actual_num = latest["number"]

        is_win = (actual_side == self.last_pred_side)
        is_jackpot = (self.last_pred_number == actual_num)

        self.stats["total"] += 1
        if is_win:
            self.stats["wins"] += 1
        else:
            self.stats["losses"] += 1

        status = "JACKPOT" if is_jackpot else ("WIN" if is_win else "LOSS")

        self.prediction_log.insert(0, {
            "period": self.last_period[-6:],
            "predicted_side": self.last_pred_side,
            "predicted_number": self.last_pred_number,
            "actual_side": actual_side,
            "actual_number": actual_num,
            "result": status
        })
        self.prediction_log = self.prediction_log[:20]

        self.history.insert(0, {
            "period": self.last_period[-6:],
            "pred_side": self.last_pred_side,
            "pred_num": self.last_pred_number,
            "actual": actual_num,
            "actual_side": actual_side,
            "result": status
        })
        self.history = self.history[:50]

    # --------------------------------------------------------
    # MAIN PREDICT — EXACT HTML LOGIC
    # --------------------------------------------------------
    def predict(self, list_data):
        latest = list_data[0]
        self.validate(latest)

        # HTML: list.slice(0,10).map(item => Number(item.number))
        #       .reverse()
        nums = [x["number"] for x in list_data[:10]]

        # HTML: BigInt(latest.issueNumber) + 1n
        next_period = str(int(latest["issue"]) + 1)

        # SHIKAARI ENGINE — exact HTML calculation
        side, pred_num, rule, pair = logic_shikaari_with_number(nums)

        # Save state for validation
        self.last_period = latest["issue"]
        self.last_pred_side = side
        self.last_pred_number = pred_num
        self.last_rule = rule
        self.last_pair = pair

        return {
            "period": next_period,
            "side": side,
            "number": pred_num,
            "rule": rule,
            "pair": pair,
            "source": "SHIKAARI_ENGINE",
            "stats": dict(self.stats),
            "prediction_log": self.prediction_log[:5],
            "history": self.history[:10]
        }

    # --------------------------------------------------------
    def run_once(self):
        data = fetch_history_from_api()
        if not data or len(data) < 4:
            return None
        return self.predict(data)


# ============================================================
# SECTION 6: PUBLIC WRAPPER for FastAPI
# ============================================================
_shared_engine = None


def _get_engine():
    global _shared_engine
    if _shared_engine is None:
        _shared_engine = PredictionEngine()
    return _shared_engine


def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    FastAPI ke liye single-shot prediction.
    SHIKAARI BOSS exact HTML logic use karta hai.
    """
    engine = _get_engine()
    data = fetch_history_from_api()

    if data and len(data) >= 4:
        result = engine.predict(data)
        if result:
            return {
                "bigSmall": result["side"],
                "prediction": result["number"],
                "numbers": [result["number"]],
                "rule": result["rule"],
                "pair": result["pair"],
                "confidence": 75,
                "source": "SHIKAARI_ENGINE",
                "steps": [
                    f"Rule: {result['rule']}",
                    f"Predicted Number: {result['number']}",
                    f"Side: {result['side']}",
                    f"Pair: {result['pair']}"
                ]
            }

    # Fallback — exact HTML logic on current number
    pred_num = current_number - 1
    if pred_num < 0:
        pred_num = 9

    return {
        "bigSmall": get_size(pred_num),
        "prediction": pred_num,
        "numbers": [pred_num],
        "rule": "NORMAL RULE (fallback)",
        "pair": PAIR_MAP.get(pred_num, None),
        "confidence": 50,
        "steps": ["Fallback: no API data"]
    }


# ============================================================
# SECTION 7: ENTRY POINT
# ============================================================
if __name__ == "__main__":
    engine = PredictionEngine()
    print("=" * 60)
    print("  WINGO PREDICTION ENGINE v14.0")
    print("  SHIKAARI BOSS LOGIC")
    print("=" * 60)
    print("  NORMAL RULE: Last Number − 1")
    print("  REPEAT RULE: 11 − Last Number")
    print("  If result < 0 → Result = 9")
    print("  BIG = 5-9, SMALL = 0-4")
    print("=" * 60)

    while True:
        try:
            r = engine.run_once()
            if r:
                print(f"\n{'─' * 60}")
                print(f"  PERIOD: {r['period']}")
                print(f"  🎯 PREDICTION: {r['side']}")
                print(f"  🔢 NUMBER: {r['number']}")
                print(f"  📐 RULE: {r['rule']}")
                print(f"  🔗 PAIR: {r['pair']}")
                print(f"  📈 Stats → W:{r['stats']['wins']} L:{r['stats']['losses']}")
                if r.get("prediction_log"):
                    print(f"  📋 Recent:")
                    for p in r["prediction_log"][:3]:
                        print(f"     [{p['period']}] "
                              f"{p['predicted_side']}({p['predicted_number']}) → "
                              f"{p['actual_side']}({p['actual_number']}) | "
                              f"{p['result']}")
        except KeyboardInterrupt:
            print("\n[!] Stopped.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")
        time.sleep(5)
