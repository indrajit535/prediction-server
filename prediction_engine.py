"""
============================================================
  WINGO PREDICTION ENGINE v12.0 — NEW LOGIC
  Two Detectors:
    1. Alternating Pattern Detector
    2. Dragon Streak Detector
============================================================
"""

import json
import time
import random
import urllib.request
from collections import defaultdict

# ============================================================
# SECTION 1: CONFIGURATION
# ============================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

CONFIG = {
    "HISTORY_LIMIT": 50,
    "ALT_PATTERN_MIN": 4,      # minimum N for alternating check
    "ALT_PATTERN_MAX": 8,      # maximum N for alternating check
    "DRAGON_THRESHOLD": 4,     # streak >= this = DRAGON
    "STRONG_THRESHOLD": 3,     # streak == this = STRONG
    "STREAK_THRESHOLD": 2,     # streak == this = STREAK
}

BIG_POOL = [5, 6, 7, 8, 9]
SMALL_POOL = [0, 1, 2, 3, 4]


# ============================================================
# SECTION 2: UTILITY FUNCTIONS
# ============================================================
def get_size(num):
    return "BIG" if int(num) >= 5 else "SMALL"


def to_bs(num):
    return "B" if int(num) >= 5 else "S"


def bs_to_side(bs):
    return "BIG" if bs == "B" else "SMALL"


# ============================================================
# SECTION 3: ALTERNATING PATTERN DETECTOR
# ============================================================
def detect_alternating(seq, n=None):
    """
    STEP 1: Store last N (4-8) completed results.
    STEP 2: Check alternation.
    STEP 3: If alternating → Pattern Type = ALTERNATING / REVERSE ALTERNATING
    STEP 4: Next Expected = opposite of last element.
    STEP 5: If NOT alternating → PATTERN BREAK / NO CLEAR PATTERN, Next = null
    STEP 6: Strength = (alternating transitions / (N-1)) × 100
    """
    if not seq:
        return {
            "pattern_type": "NO DATA",
            "strength": 0,
            "next_expected": None,
            "recent_pattern": [],
            "is_alternating": False
        }

    # Choose N between min and max
    if n is None:
        n = min(CONFIG["ALT_PATTERN_MAX"], max(CONFIG["ALT_PATTERN_MIN"], len(seq)))
    n = min(n, len(seq))
    recent = seq[:n]  # most recent first (as fetched)

    # Reverse to chronological: oldest → newest
    chrono = list(reversed(recent))

    # STEP 2: Check alternation
    is_alternating = True
    transitions = 0
    for i in range(1, len(chrono)):
        if chrono[i] == chrono[i - 1]:
            is_alternating = False
            break
        transitions += 1

    total_transitions = len(chrono) - 1

    # STEP 6: Strength
    if is_alternating and total_transitions > 0:
        strength = int((transitions / total_transitions) * 100)
    else:
        strength = 0

    # STEP 3 & 4: Pattern type & next expected
    if is_alternating:
        if chrono[0] == "B":
            pattern_type = "ALTERNATING"
        else:
            pattern_type = "REVERSE ALTERNATING"

        last = chrono[-1]
        next_expected = "SMALL" if last == "B" else "BIG"
    else:
        pattern_type = "PATTERN BREAK / NO CLEAR PATTERN"
        next_expected = None

    return {
        "pattern_type": pattern_type,
        "strength": strength,
        "next_expected": next_expected,
        "recent_pattern": [bs_to_side(x) for x in recent],
        "is_alternating": is_alternating
    }


# ============================================================
# SECTION 4: DRAGON STREAK DETECTOR
# ============================================================
def detect_dragon_streak(seq):
    """
    STEP 1: Maintain chronological array of completed results.
    STEP 2: Calculate current streak.
    STEP 3: Classify streak:
            count == 1  → NO STREAK
            count == 2  → STREAK DETECTED
            count == 3  → STRONG STREAK
            count >= 4  → DRAGON <SIDE> STRIKE
    STEP 4: Direction = current streak side.
    STEP 5: Strength = min(100, streak_count × 20) %
    """
    if not seq:
        return {
            "current_pattern": None,
            "streak_count": 0,
            "pattern_label": "NO DATA",
            "strength": 0,
            "dragon_strike": False,
            "recent_history": [],
            "direction": None
        }

    # seq is most recent first
    current = seq[0]
    streak_count = 1
    for i in range(1, len(seq)):
        if seq[i] == current:
            streak_count += 1
        else:
            break

    # STEP 3: Classify
    if streak_count >= CONFIG["DRAGON_THRESHOLD"]:
        pattern_label = f"DRAGON {bs_to_side(current)} STRIKE"
        dragon_strike = True
    elif streak_count == CONFIG["STRONG_THRESHOLD"]:
        pattern_label = "STRONG STREAK"
        dragon_strike = False
    elif streak_count == CONFIG["STREAK_THRESHOLD"]:
        pattern_label = "STREAK DETECTED"
        dragon_strike = False
    else:
        pattern_label = "NO STREAK"
        dragon_strike = False

    # STEP 5: Strength
    strength = min(100, streak_count * 20)

    # Recent history (most recent first, up to 8)
    recent_history = [bs_to_side(x) for x in seq[:8]]

    return {
        "current_pattern": bs_to_side(current),
        "streak_count": streak_count,
        "pattern_label": pattern_label,
        "strength": strength,
        "dragon_strike": dragon_strike,
        "recent_history": recent_history,
        "direction": bs_to_side(current)
    }


# ============================================================
# SECTION 5: PREDICTION COMBINER
# ============================================================
def combine_predictions(alt_result, dragon_result):
    """
    Combine both detectors into a single prediction.
    Priority:
      1. If alternating pattern is active (strength > 0) → use it
      2. Else if dragon streak is active (streak >= 2) → follow the streak
      3. Else → no clear signal
    """
    alt_strength = alt_result.get("strength", 0)
    alt_next = alt_result.get("next_expected")

    dragon_streak = dragon_result.get("streak_count", 0)
    dragon_dir = dragon_result.get("direction")
    dragon_strength = dragon_result.get("strength", 0)

    # Priority 1: Alternating pattern
    if alt_strength > 0 and alt_next:
        return {
            "side": alt_next,
            "confidence": alt_strength,
            "source": "ALTERNATING_PATTERN",
            "reason": f"{alt_result['pattern_type']} ({alt_strength}%)"
        }

    # Priority 2: Dragon / Streak
    if dragon_streak >= CONFIG["STREAK_THRESHOLD"] and dragon_dir:
        return {
            "side": dragon_dir,
            "confidence": dragon_strength,
            "source": "DRAGON_STREAK",
            "reason": f"{dragon_result['pattern_label']} (x{dragon_streak})"
        }

    # No clear signal
    return {
        "side": None,
        "confidence": 0,
        "source": "NO_SIGNAL",
        "reason": "No clear pattern detected"
    }


# ============================================================
# SECTION 6: NUMBER SELECTOR
# ============================================================
def pick_numbers(side, history_nums):
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
# SECTION 7: FETCH HISTORY
# ============================================================
def fetch_history_from_api():
    try:
        req = urllib.request.Request(
            API_URL + f"?t={int(time.time())}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        lst = data["data"]["list"]
        return [{"issue": str(x["issueNumber"]),
                 "number": int(x["number"]),
                 "size": get_size(x["number"])} for x in lst]
    except Exception as e:
        print(f"[!] Fetch error: {e}")
        return None


# ============================================================
# SECTION 8: MAIN PREDICTOR CLASS
# ============================================================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.stats = {"wins": 0, "losses": 0, "total": 0}
        self.last_period = None
        self.last_pred_side = None
        self.last_nums = None
        self.prediction_log = []       # for dragon detector WIN/LOSS
        self.pattern_history = []      # for alternating detector log

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
        else:
            self.stats["losses"] += 1

        # Prediction log (STEP 7 of dragon detector)
        self.prediction_log.insert(0, {
            "period": self.last_period[-6:],
            "predicted_side": self.last_pred_side,
            "actual_side": actual_side,
            "result": "WIN" if win else "LOSS"
        })
        self.prediction_log = self.prediction_log[:20]

        # Main history
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
    # MAIN PREDICT
    # --------------------------------------------------------
    def predict(self, list_data):
        latest = list_data[0]
        self.validate(latest)

        nums = [x["number"] for x in list_data[:50]]
        seq = [to_bs(n) for n in nums]   # most recent first
        next_period = str(int(latest["issue"]) + 1)

        # ----- Run both detectors -----
        alt_result = detect_alternating(seq)
        dragon_result = detect_dragon_streak(seq)

        # ----- Combine -----
        combined = combine_predictions(alt_result, dragon_result)

        # ----- Log pattern history (alternating) -----
        if alt_result["is_alternating"]:
            self.pattern_history.insert(0, {
                "time": time.strftime("%H:%M:%S"),
                "type": alt_result["pattern_type"],
                "next": alt_result["next_expected"],
                "strength": alt_result["strength"]
            })
            self.pattern_history = self.pattern_history[:10]

        # ----- No signal → skip -----
        if combined["side"] is None:
            return {
                "period": next_period,
                "skip": True,
                "reason": combined["reason"],
                "alternating": alt_result,
                "dragon": dragon_result,
                "stats": dict(self.stats)
            }

        final_side = combined["side"]
        n1, n2 = pick_numbers(final_side, nums)

        # Save state
        self.last_period = latest["issue"]
        self.last_pred_side = final_side
        self.last_nums = [n1, n2]

        return {
            "period": next_period,
            "side": final_side,
            "numbers": [n1, n2],
            "confidence": combined["confidence"],
            "source": combined["source"],
            "reason": combined["reason"],
            "alternating": alt_result,
            "dragon": dragon_result,
            "stats": dict(self.stats),
            "prediction_log": self.prediction_log[:5],
            "pattern_history": self.pattern_history[:5],
            "history": self.history[:10]
        }

    # --------------------------------------------------------
    def run_once(self):
        data = fetch_history_from_api()
        if not data or len(data) < 4:
            return None
        return self.predict(data)


# ============================================================
# SECTION 9: PUBLIC WRAPPER for FastAPI
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
    """
    engine = _get_engine()
    data = fetch_history_from_api()

    if data and len(data) >= 4:
        result = engine.predict(data)
        if result and not result.get("skip"):
            return {
                "bigSmall": result["side"],
                "prediction": result["numbers"][0],
                "numbers": result["numbers"],
                "confidence": result["confidence"],
                "source": result["source"],
                "steps": [
                    f"Source: {result['source']}",
                    f"Reason: {result['reason']}",
                    f"Alternating: {result['alternating']['pattern_type']} ({result['alternating']['strength']}%)",
                    f"Dragon: {result['dragon']['pattern_label']} (x{result['dragon']['streak_count']})"
                ]
            }
        if result and result.get("skip"):
            return {
                "bigSmall": None,
                "prediction": None,
                "numbers": [],
                "confidence": 0,
                "steps": [f"Skipped: {result['reason']}"]
            }

    # Fallback: use current_number directly
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
# SECTION 10: ENTRY POINT
# ============================================================
if __name__ == "__main__":
    engine = PredictionEngine()
    print("=" * 60)
    print("  WINGO PREDICTION ENGINE v12.0 — NEW LOGIC")
    print("  Alternating Pattern + Dragon Streak")
    print("=" * 60)
    while True:
        try:
            r = engine.run_once()
            if r:
                if r.get("skip"):
                    print(f"\n⏸️  SKIP: {r['reason']}")
                    print(f"   Alternating: {r['alternating']['pattern_type']} ({r['alternating']['strength']}%)")
                    print(f"   Dragon: {r['dragon']['pattern_label']} (x{r['dragon']['streak_count']})")
                else:
                    print(f"\n{'─' * 60}")
                    print(f"  PERIOD: {r['period']}")
                    print(f"  🎯 SIGNAL: {r['side']}")
                    print(f"  🔢 NUMBERS: {r['numbers'][0]} , {r['numbers'][1]}")
                    print(f"  📊 CONFIDENCE: {r['confidence']}%")
                    print(f"  🧠 SOURCE: {r['source']}")
                    print(f"  📝 REASON: {r['reason']}")
                    print(f"  ── Alternating Detector ──")
                    print(f"     Type: {r['alternating']['pattern_type']}")
                    print(f"     Strength: {r['alternating']['strength']}%")
                    print(f"     Next: {r['alternating']['next_expected']}")
                    print(f"  ── Dragon Streak Detector ──")
                    print(f"     Pattern: {r['dragon']['pattern_label']}")
                    print(f"     Streak: x{r['dragon']['streak_count']}")
                    print(f"     Strength: {r['dragon']['strength']}%")
                    print(f"     Dragon: {'YES' if r['dragon']['dragon_strike'] else 'NO'}")
                    s = r["stats"]
                    wr = round(s["wins"] / s["total"] * 100, 1) if s["total"] else 0
                    print(f"  📈 Stats → W:{s['wins']} L:{s['losses']} | WR:{wr}%")
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
