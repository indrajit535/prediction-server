"""
============================================================
  WINGO PREDICTION ENGINE v13.0
  3-LOGIC VOTING SYSTEM
  
  Logic 1: Pattern Master (from ANSH BHAI HTML)
  Logic 2: SHIKAARI Engine (from SHIKAARI BOSS HTML)
  Logic 3: Crack by Aarish (from CRACK BY AARISH HTML)
  
  Voting: 3 logics vote → majority wins (2-1 or 3-0)
============================================================
"""

import json
import time
import random
import urllib.request
from collections import Counter

# ============================================================
# SECTION 1: CONFIGURATION
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

CONFIG = {
    "HISTORY_LIMIT": 50,
    "PATTERN_MASTER_LOOKBACK": 15,
    "STREAK_THRESHOLD": 3,
    "ALTERNATION_THRESHOLD": 5,
}

BIG_POOL = [5, 6, 7, 8, 9]
SMALL_POOL = [0, 1, 2, 3, 4]

PAIR_MAP = {
    0: "0/2", 1: "1/3", 2: "2/4",
    5: "5/7", 6: "6/8", 7: "7/9",
    8: "6/8", 9: "7/9"
}


# ============================================================
# SECTION 2: UTILITY FUNCTIONS
# ============================================================
def get_size(num):
    """BIG if >= 5 else SMALL"""
    return "BIG" if int(num) >= 5 else "SMALL"


def to_bs(num):
    """Convert to B/S notation"""
    return "B" if int(num) >= 5 else "S"


def bs_to_side(bs):
    """Convert B/S to BIG/SMALL"""
    return "BIG" if bs == "B" else "SMALL"


# ============================================================
# SECTION 3: LOGIC 1 — PATTERN MASTER (from ANSH BHAI HTML)
# ============================================================
def logic_pattern_master(history_nums):
    """
    Original Logic from ANSH BHAI HTML:
    - Analyzes recent 15 results
    - Tracks streak and alternations
    - If streak >= 3 OR alternations > 5 → predict opposite of last
    - Else → random Big/Small
    
    Returns: "BIG" or "SMALL"
    """
    if not history_nums or len(history_nums) < 3:
        return random.choice(["BIG", "SMALL"])
    
    recent = history_nums[:CONFIG["PATTERN_MASTER_LOOKBACK"]]
    
    streak = 0
    alternations = 0
    last_size = None
    
    for i in range(min(len(recent), CONFIG["PATTERN_MASTER_LOOKBACK"])):
        num = recent[i]
        size = "BIG" if num >= 5 else "SMALL"
        
        if i > 0:
            prev_size = "BIG" if recent[i - 1] >= 5 else "SMALL"
            if size == prev_size:
                streak += 1
            else:
                alternations += 1
        
        last_size = size
    
    # Original condition from ANSH HTML
    if streak >= CONFIG["STREAK_THRESHOLD"] or alternations > CONFIG["ALTERNATION_THRESHOLD"]:
        return "SMALL" if last_size == "BIG" else "BIG"
    else:
        return random.choice(["BIG", "SMALL"])


# ============================================================
# SECTION 4: LOGIC 2 — SHIKAARI ENGINE (from SHIKAARI BOSS HTML)
# ============================================================
def logic_shikaari(history_nums):
    """
    Original Logic from SHIKAARI BOSS HTML:
    
    NORMAL RULE: Last Number − 1
    If result < 0 → Result = 9
    
    REPEAT RULE: If last two numbers are same → 11 − Last Number
    
    Returns: "BIG" or "SMALL"
    """
    if not history_nums or len(history_nums) < 1:
        return random.choice(["BIG", "SMALL"])
    
    last = history_nums[0]  # Most recent first
    
    # REPEAT RULE (if last two are same)
    if len(history_nums) >= 2 and history_nums[0] == history_nums[1]:
        result_num = 11 - last
        # Clamp to 0-9
        if result_num > 9:
            result_num = result_num - 10
        if result_num < 0:
            result_num = 0
    else:
        # NORMAL RULE: last - 1
        result_num = last - 1
        if result_num < 0:
            result_num = 9
    
    return get_size(result_num)


def logic_shikaari_with_number(history_nums):
    """
    Same as logic_shikaari but also returns the actual number predicted.
    """
    if not history_nums or len(history_nums) < 1:
        num = random.choice(BIG_POOL + SMALL_POOL)
        return get_size(num), num
    
    last = history_nums[0]
    
    if len(history_nums) >= 2 and history_nums[0] == history_nums[1]:
        result_num = 11 - last
        if result_num > 9:
            result_num = result_num - 10
        if result_num < 0:
            result_num = 0
    else:
        result_num = last - 1
        if result_num < 0:
            result_num = 9
    
    return get_size(result_num), result_num


# ============================================================
# SECTION 5: LOGIC 3 — CRACK BY AARISH (from CRACK BY AARISH HTML)
# ============================================================
def logic_crack_by_aarish(history_nums, period=""):
    """
    Original Logic from CRACK BY AARISH HTML:
    
    - Takes recent 10 results
    - Counts BIG vs SMALL
    - If big > small → predict SMALL
    - If small > big → predict BIG
    - If equal → use period last digit parity (odd → SMALL, even → BIG)
    
    Returns: "BIG" or "SMALL"
    """
    if not history_nums or len(history_nums) < 5:
        return random.choice(["BIG", "SMALL"])
    
    nums = history_nums[:10]
    
    big = 0
    small = 0
    
    for n in nums:
        if n >= 5:
            big += 1
        else:
            small += 1
    
    if big > small:
        return "SMALL"
    elif small > big:
        return "BIG"
    else:
        # Tie-breaker using period last digit
        if period and period.isdigit():
            last_digit = int(period[-1])
            return "SMALL" if last_digit % 2 == 1 else "BIG"
        return random.choice(["BIG", "SMALL"])


# ============================================================
# SECTION 6: VOTING SYSTEM
# ============================================================
def vote_predictions(logic1_side, logic2_side, logic3_side):
    """
    3-Logic Voting System:
    - 2 or 3 votes for same side → that side wins
    - If all 3 different → fallback to Logic 1 (Pattern Master)
    
    Returns: (final_side, vote_details)
    """
    votes = [logic1_side, logic2_side, logic3_side]
    counter = Counter(votes)
    
    vote_details = {
        "pattern_master": logic1_side,
        "shikaari": logic2_side,
        "crack_aarish": logic3_side,
        "vote_count": dict(counter)
    }
    
    # Check for majority (2 or 3)
    most_common = counter.most_common(1)[0]
    
    if most_common[1] >= 2:
        final_side = most_common[0]
        vote_details["method"] = "MAJORITY"
        vote_details["votes_for_winner"] = most_common[1]
    else:
        # All 3 different → use Pattern Master as tiebreaker
        final_side = logic1_side
        vote_details["method"] = "TIEBREAKER_PATTERN_MASTER"
        vote_details["votes_for_winner"] = 1
    
    return final_side, vote_details


# ============================================================
# SECTION 7: NUMBER SELECTOR
# ============================================================
def pick_numbers(side, history_nums):
    """Pick 2 numbers from the predicted side, avoiding recent numbers."""
    if side is None:
        return None, None
    
    pool = BIG_POOL if side == "BIG" else SMALL_POOL
    used = history_nums[:6]
    fresh = [n for n in pool if n not in used]
    
    if len(fresh) >= 2:
        n1 = random.choice(fresh)
        n2 = random.choice([n for n in fresh if n != n1])
    elif len(fresh) == 1:
        n1 = fresh[0]
        n2 = random.choice([n for n in pool if n != n1])
    else:
        n1, n2 = random.sample(pool, 2)
    
    return n1, n2


# ============================================================
# SECTION 8: FETCH HISTORY
# ============================================================
def fetch_history_from_api():
    """Fetch live history from API."""
    try:
        req = urllib.request.Request(
            API_URL + f"?t={int(time.time())}",
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
# SECTION 9: MAIN PREDICTOR CLASS
# ============================================================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.stats = {"wins": 0, "losses": 0, "total": 0}
        self.last_period = None
        self.last_pred_side = None
        self.last_nums = None
        self.prediction_log = []
        self.logic_stats = {
            "pattern_master": {"wins": 0, "losses": 0},
            "shikaari": {"wins": 0, "losses": 0},
            "crack_aarish": {"wins": 0, "losses": 0},
            "voted": {"wins": 0, "losses": 0}
        }

    # --------------------------------------------------------
    # VALIDATE PREVIOUS PREDICTION
    # --------------------------------------------------------
    def validate(self, latest):
        if not self.last_period or self.last_period == latest["issue"]:
            return
        if self.last_pred_side is None:
            return

        actual_side = latest["size"]
        win = (actual_side == self.last_pred_side)

        self.stats["total"] += 1
        if win:
            self.stats["wins"] += 1
            self.logic_stats["voted"]["wins"] += 1
        else:
            self.stats["losses"] += 1
            self.logic_stats["voted"]["losses"] += 1

        self.prediction_log.insert(0, {
            "period": self.last_period[-6:],
            "predicted_side": self.last_pred_side,
            "actual_side": actual_side,
            "result": "WIN" if win else "LOSS"
        })
        self.prediction_log = self.prediction_log[:20]

        self.history.insert(0, {
            "period": self.last_period[-6:],
            "pred_side": self.last_pred_side,
            "pred_nums": self.last_nums,
            "actual": latest["number"],
            "actual_side": actual_side,
            "result": "WIN" if win else "LOSS"
        })
        self.history = self.history[:50]

    # --------------------------------------------------------
    # MAIN PREDICT — 3 LOGIC VOTING
    # --------------------------------------------------------
    def predict(self, list_data):
        latest = list_data[0]
        self.validate(latest)

        nums = [x["number"] for x in list_data[:CONFIG["HISTORY_LIMIT"]]]
        next_period = str(int(latest["issue"]) + 1)

        # ============================================
        # RUN ALL 3 LOGICS
        # ============================================
        logic1_side = logic_pattern_master(nums)
        logic2_side = logic_shikaari(nums)
        logic3_side = logic_crack_by_aarish(nums, next_period)

        # ============================================
        # VOTING SYSTEM
        # ============================================
        final_side, vote_details = vote_predictions(
            logic1_side, logic2_side, logic3_side
        )

        # ============================================
        # PICK NUMBERS
        # ============================================
        n1, n2 = pick_numbers(final_side, nums)

        # ============================================
        # SAVE STATE
        # ============================================
        self.last_period = latest["issue"]
        self.last_pred_side = final_side
        self.last_nums = [n1, n2]

        # Get Shikaari predicted number for display
        _, shikaari_num = logic_shikaari_with_number(nums)

        return {
            "period": next_period,
            "side": final_side,
            "numbers": [n1, n2],
            "source": "3_LOGIC_VOTING",
            "confidence": vote_details["votes_for_winner"] * 33 + 1,
            "vote_details": vote_details,
            "logic1_pattern_master": {
                "side": logic1_side,
                "name": "Pattern Master"
            },
            "logic2_shikaari": {
                "side": logic2_side,
                "number": shikaari_num,
                "name": "SHIKAARI Engine"
            },
            "logic3_crack_aarish": {
                "side": logic3_side,
                "name": "Crack by Aarish"
            },
            "stats": dict(self.stats),
            "logic_stats": self.logic_stats,
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
# SECTION 10: PUBLIC WRAPPER for FastAPI
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
    3 Logic Voting System use karta hai.
    """
    engine = _get_engine()
    data = fetch_history_from_api()

    if data and len(data) >= 4:
        result = engine.predict(data)
        if result:
            return {
                "bigSmall": result["side"],
                "prediction": result["numbers"][0],
                "numbers": result["numbers"],
                "confidence": result["confidence"],
                "source": "3_LOGIC_VOTING",
                "steps": [
                    f"Logic 1 (Pattern Master): {result['logic1_pattern_master']['side']}",
                    f"Logic 2 (SHIKAARI): {result['logic2_shikaari']['side']} (num: {result['logic2_shikaari']['number']})",
                    f"Logic 3 (Crack by Aarish): {result['logic3_crack_aarish']['side']}",
                    f"Votes: {result['vote_details']['vote_count']}",
                    f"Winner: {result['side']} ({result['vote_details']['method']})"
                ]
            }

    # Fallback
    side = get_size(current_number)
    pool = BIG_POOL if side == "BIG" else SMALL_POOL
    return {
        "bigSmall": side,
        "prediction": random.choice(pool),
        "numbers": [random.choice(pool), random.choice(pool)],
        "confidence": 50,
        "steps": ["Fallback: no API data"]
    }


# ============================================================
# SECTION 11: ENTRY POINT
# ============================================================
if __name__ == "__main__":
    engine = PredictionEngine()
    print("=" * 60)
    print("  WINGO PREDICTION ENGINE v13.0")
    print("  3-LOGIC VOTING SYSTEM")
    print("=" * 60)
    print("  Logic 1: Pattern Master (ANSH BHAI)")
    print("  Logic 2: SHIKAARI Engine (SHIKAARI BOSS)")
    print("  Logic 3: Crack by Aarish (CRACK BY AARISH)")
    print("  Voting: Majority wins (2-1 or 3-0)")
    print("=" * 60)

    while True:
        try:
            r = engine.run_once()
            if r:
                print(f"\n{'─' * 60}")
                print(f"  PERIOD: {r['period']}")
                print(f"  🎯 FINAL PREDICTION: {r['side']}")
                print(f"  🔢 NUMBERS: {r['numbers'][0]} , {r['numbers'][1]}")
                print(f"  📊 CONFIDENCE: {r['confidence']}%")
                print(f"  🗳️  VOTING BREAKDOWN:")
                print(f"     ├─ Pattern Master (ANSH): {r['logic1_pattern_master']['side']}")
                print(f"     ├─ SHIKAARI Engine: {r['logic2_shikaari']['side']} (num: {r['logic2_shikaari']['number']})")
                print(f"     └─ Crack by Aarish: {r['logic3_crack_aarish']['side']}")
                print(f"  📈 VOTE COUNT: {r['vote_details']['vote_count']}")
                print(f"  🏆 METHOD: {r['vote_details']['method']}")
                print(f"  📈 Stats → W:{r['stats']['wins']} L:{r['stats']['losses']}")
                if r.get("prediction_log"):
                    print(f"  📋 Recent Predictions:")
                    for p in r["prediction_log"][:3]:
                        print(f"     [{p['period']}] {p['predicted_side']} → {p['actual_side']} | {p['result']}")
        except KeyboardInterrupt:
            print("\n[!] Stopped.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")
        time.sleep(5)
