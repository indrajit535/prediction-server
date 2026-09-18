"""
============================================================
  ULTIMATE WINGO PREDICTION ENGINE v11.0 — 100% NEW
  14 Engines Combined:
  Dragon + Zigzag + 1-1 + 2-2 + 3-3 + 4-4 + 1+3 + Mirror
  + Triangle + N-Gram + Markov + Fibonacci + 30-Ratio
  + Ultimate-Pro + RENOX Quantum
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
    "MIN_CONFIDENCE": 72,
    "MAX_CONFIDENCE": 99,
    "EMERGENCY_WAIT": 1,
    "BREAK_STREAK": 1,
    "FIB": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610],
    "PRIMES": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37],
}

BIG_POOL = [5, 6, 7, 8, 9]
SMALL_POOL = [0, 1, 2, 3, 4]

SAFE_POOLS = {
    "BIG_HIGH": [8, 9, 7],
    "SMALL_HIGH": [1, 2, 3],
    "BIG_CRITICAL": [8, 9],
    "SMALL_CRITICAL": [1, 2],
    "BIG_ULTRA": [8],
    "SMALL_ULTRA": [1],
}

# ============================================================
# SECTION 2: PATTERN DATABASE
# ============================================================
PATTERNS_DB = {
    'B': ('S', 50), 'S': ('B', 50),
    'BB': ('S', 60), 'SS': ('B', 60),
    'BS': ('B', 55), 'SB': ('S', 55),
    'BBB': ('S', 78), 'SSS': ('B', 78),
    'BBS': ('B', 70), 'SSB': ('S', 70),
    'BSB': ('S', 74), 'SBS': ('B', 74),
    'BSS': ('B', 69), 'SBB': ('S', 69),
    'BBBB': ('S', 88), 'SSSS': ('B', 88),
    'BBBS': ('S', 76), 'SSSB': ('B', 76),
    'BBSB': ('S', 74), 'SSBS': ('B', 74),
    'BSBB': ('S', 74), 'SBSS': ('B', 74),
    'BSBS': ('S', 78), 'SBSB': ('B', 78),
    'BBSS': ('B', 70), 'SSBB': ('S', 70),
    'BBBBB': ('S', 92), 'SSSSS': ('B', 92),
    'BBBBS': ('S', 80), 'SSSSB': ('B', 80),
    'BBSBB': ('S', 78), 'SSBSS': ('B', 78),
    'BSBBB': ('S', 79), 'SBSSS': ('B', 79),
    'BBBBBB': ('S', 95), 'SSSSSS': ('B', 95),
    'BBBBBS': ('S', 84), 'SSSSSB': ('B', 84),
    'BBBBBBB': ('S', 97), 'SSSSSSS': ('B', 97),
    'BBBBBBBB': ('S', 98), 'SSSSSSSS': ('B', 98),
    'BSBSBS': ('B', 82), 'SBSBSB': ('S', 82),
    'BSBSBSB': ('B', 86), 'SBSBSBS': ('S', 86),
    'BSBSBSBS': ('B', 89), 'SBSBSBSB': ('S', 89),
    'BBSBBS': ('S', 76), 'SSBSSB': ('B', 76),
    'BBSSBB': ('S', 74), 'SSBBSS': ('B', 74),
    'BSSSB': ('S', 78), 'SBBBS': ('B', 78),
    'SBBB': ('S', 90), 'BSSS': ('B', 90),
    'SSSB': ('S', 88), 'BBBS': ('B', 88),
    'BBBSSS': ('B', 86), 'SSSBBB': ('S', 86),
    'BBBBSSSS': ('B', 90), 'SSSSBBBB': ('S', 90),
    'BBSSB': ('B', 82), 'SSBBS': ('S', 82),
    'BSS': ('B', 84), 'SBB': ('S', 84),
}


# ============================================================
# SECTION 3: UTILITY FUNCTIONS
# ============================================================
def get_size(num):
    return "BIG" if int(num) >= 5 else "SMALL"


def to_bs(num):
    return "B" if int(num) >= 5 else "S"


def digit_sum(n):
    return sum(int(d) for d in str(abs(int(n))))


def reverse_digits(n):
    return int(str(abs(int(n)))[::-1])


# ============================================================
# SECTION 4: PATTERN DETECTORS
# ============================================================
def detect_dragon(seq):
    if not seq:
        return None
    streak = 1
    for i in range(1, min(len(seq), 12)):
        if seq[i] == seq[0]:
            streak += 1
        else:
            break
    if streak >= 4:
        return {"side": "SMALL" if seq[0] == "B" else "BIG",
                "confidence": min(97, 75 + streak * 3),
                "pattern": f"DRAGON_BREAK_{streak}"}
    if streak == 3:
        return {"side": "BIG" if seq[0] == "B" else "SMALL",
                "confidence": 82, "pattern": "TRIPLE_REVERSAL"}
    return None


def detect_zigzag(seq):
    if len(seq) < 4:
        return None
    alt = all(seq[i] != seq[i + 1] for i in range(min(7, len(seq) - 1)))
    if alt:
        return {"side": "SMALL" if seq[0] == "B" else "BIG",
                "confidence": 86, "pattern": "ZIGZAG"}
    return None


def detect_1_1_pattern(seq):
    if len(seq) < 6:
        return None
    p6 = "".join(seq[:6])
    if p6 in ("BSBSBS", "SBSBSB"):
        return {"side": "SMALL" if seq[0] == "B" else "BIG",
                "confidence": 84, "pattern": "1-1_ALT"}
    return None


def detect_2_2_pattern(seq):
    if len(seq) < 4:
        return None
    p4 = "".join(seq[:4])
    if p4 == "BBSS":
        return {"side": "BIG", "confidence": 82, "pattern": "2-2_BBSS"}
    if p4 == "SSBB":
        return {"side": "SMALL", "confidence": 82, "pattern": "2-2_SSBB"}
    return None


def detect_3_3_pattern(seq):
    if len(seq) < 6:
        return None
    p6 = "".join(seq[:6])
    if p6 == "BBBSSS":
        return {"side": "BIG", "confidence": 86, "pattern": "3-3_BBBSSS"}
    if p6 == "SSSBBB":
        return {"side": "SMALL", "confidence": 86, "pattern": "3-3_SSSBBB"}
    return None


def detect_4_4_pattern(seq):
    if len(seq) < 8:
        return None
    p8 = "".join(seq[:8])
    if p8 == "BBBBSSSS":
        return {"side": "BIG", "confidence": 90, "pattern": "4-4_BBBBSSSS"}
    if p8 == "SSSSBBBB":
        return {"side": "SMALL", "confidence": 90, "pattern": "4-4_SSSSBBBB"}
    return None


def detect_1_3_pattern(seq):
    if len(seq) < 4:
        return None
    p4 = "".join(seq[:4])
    rules = {
        "SBBB": ("SMALL", 90, "1S+3B_REVERSAL"),
        "BSSS": ("BIG",   90, "1B+3S_REVERSAL"),
        "SSSB": ("SMALL", 88, "3S+1B_TREND"),
        "BBBS": ("BIG",   88, "3B+1S_TREND"),
    }
    if p4 in rules:
        s, c, n = rules[p4]
        return {"side": s, "confidence": c, "pattern": n}
    return None


def detect_mirror(seq):
    if len(seq) < 8:
        return None
    s = "".join(seq[:13]) if len(seq) >= 13 else "".join(seq)
    if s.startswith("SSSSBBSBBSSSS"):
        return {"side": "BIG", "confidence": 92, "pattern": "MIRROR_FULL_BIG"}
    if s.startswith("BBBBSSBSSBBBB"):
        return {"side": "SMALL", "confidence": 92, "pattern": "MIRROR_FULL_SMALL"}
    if s.startswith("SSSSBBSS"):
        return {"side": "BIG", "confidence": 84, "pattern": "MIRROR_PARTIAL_BIG"}
    if s.startswith("BBBBSSBB"):
        return {"side": "SMALL", "confidence": 84, "pattern": "MIRROR_PARTIAL_SMALL"}
    return None


def detect_triangle(seq):
    if len(seq) < 3:
        return None
    p3 = "".join(seq[:3])
    if p3 == "BSS":
        return {"side": "BIG", "confidence": 84, "pattern": "TRIANGLE_BSS"}
    if p3 == "SBB":
        return {"side": "SMALL", "confidence": 84, "pattern": "TRIANGLE_SBB"}
    return None


def detect_n_gram(seq):
    if len(seq) < 3:
        return None
    seq_str = "".join(seq)
    best = None
    for length in range(min(8, len(seq_str)), 2, -1):
        sub = seq_str[:length]
        if sub in PATTERNS_DB:
            side, conf = PATTERNS_DB[sub]
            if best is None or conf > best["confidence"]:
                best = {"side": side, "confidence": conf,
                        "pattern": f"NGRAM_{sub}"}
    return best


def detect_markov(seq):
    if len(seq) < 10:
        return None
    bs = "".join(seq)
    t3 = defaultdict(lambda: {"B": 0, "S": 0})
    for i in range(len(bs) - 3):
        key = bs[i:i + 3]
        t3[key][bs[i + 3]] += 1
    key = bs[:3]
    total = t3[key]["B"] + t3[key]["S"]
    if total >= 2:
        if t3[key]["B"] > t3[key]["S"]:
            return {"side": "BIG",
                    "confidence": min(95, 62 + int(t3[key]["B"] / total * 33)),
                    "pattern": "MARKOV_B"}
        elif t3[key]["S"] > t3[key]["B"]:
            return {"side": "SMALL",
                    "confidence": min(95, 62 + int(t3[key]["S"] / total * 33)),
                    "pattern": "MARKOV_S"}
    return None


def detect_fibonacci(seq):
    if len(seq) < 8:
        return None
    weights = [8, 5, 3, 2, 1, 1, 0, 0]
    score = 0
    for i in range(min(len(seq), 8)):
        score += (1 if seq[i] == "B" else -1) * weights[i]
    if abs(score) >= 10:
        side = "BIG" if score > 0 else "SMALL"
        return {"side": side, "confidence": min(92, 70 + abs(score)),
                "pattern": f"FIB_{score}"}
    return None


def detect_ratio_30(seq):
    if len(seq) < 20:
        return None
    recent = seq[:30]
    bigs = recent.count("B")
    ratio = bigs / len(recent)
    if ratio >= 0.68:
        return {"side": "SMALL",
                "confidence": min(95, int(72 + (ratio - 0.5) * 60)),
                "pattern": f"30RATIO_{int(ratio * 100)}"}
    if ratio <= 0.32:
        return {"side": "BIG",
                "confidence": min(95, int(72 + (0.5 - ratio) * 60)),
                "pattern": f"30RATIO_{int(ratio * 100)}"}
    return None


def detect_ultimate_pro(seq):
    if len(seq) < 8:
        return None
    score = {"BIG": 0, "SMALL": 0}
    if len(seq) >= 5 and seq[0] == seq[4] and seq[1] == seq[3]:
        vote = "SMALL" if seq[0] == "B" else "BIG"
        score[vote] += 5
    fib_s = 0
    for i in range(min(len(seq), 8)):
        w = [8, 5, 3, 2, 1, 1, 0, 0][i]
        fib_s += (1 if seq[i] == "B" else -1) * w
    score["BIG" if fib_s > 0 else "SMALL"] += 3
    streak = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[0]:
            streak += 1
        else:
            break
    if streak >= 5:
        score["SMALL" if seq[0] == "B" else "BIG"] += 5
    diff = abs(score["BIG"] - score["SMALL"])
    conf = 68 + min(30, int(diff * 5))
    side = "BIG" if score["BIG"] >= score["SMALL"] else "SMALL"
    return {"side": side, "confidence": conf, "pattern": "ULTIMATE_PRO"}


def engine_renox_hyper(last_num, period_str):
    try:
        p_salt = int(str(period_str)[-3:]) if len(str(period_str)) >= 3 else 0
    except (ValueError, TypeError):
        p_salt = 0

    digits = [int(d) for d in str(int(last_num)).zfill(5)]
    fib = CONFIG["FIB"]
    primes = CONFIG["PRIMES"]

    A = (sum(digits[i] * fib[i + 5] for i in range(5)) + p_salt * 11) % 17
    B = (A * primes[p_salt % 10] + (digits[0] ^ digits[4])) % 13
    if B == 0:
        B = 11
    C = (((B << 3) | (B >> 2)) & 0xFF) % 19
    D = ((19 - C) ^ (17 - A) ^ (13 + B)) % 11
    E = reverse_digits(D * 23 + C * 7) % 13
    F = digit_sum(E * fib[A % 10]) % 9 or 9
    L = (A + B + C + D + E + F) % 10
    final = (L + 3) % 10 if p_salt % 2 == 0 else (L * 7) % 10
    final = abs(final) % 10

    return {
        "side": "BIG" if final >= 5 else "SMALL",
        "number": final,
        "confidence": min(99, max(80, 82 + (final * 2 - int(last_num) % 10))),
        "pattern": f"RENOX_V21_{L}"
    }


# ============================================================
# SECTION 5: ENSEMBLE VOTER
# ============================================================
def ensemble_vote(seq, last_num, period):
    engines = [
        (detect_dragon(seq),        1.6),
        (detect_zigzag(seq),        1.5),
        (detect_1_1_pattern(seq),   1.4),
        (detect_2_2_pattern(seq),   1.4),
        (detect_3_3_pattern(seq),   1.5),
        (detect_4_4_pattern(seq),   1.6),
        (detect_1_3_pattern(seq),   1.5),
        (detect_mirror(seq),        1.5),
        (detect_triangle(seq),      1.3),
        (detect_n_gram(seq),        1.4),
        (detect_markov(seq),        1.3),
        (detect_fibonacci(seq),     1.2),
        (detect_ratio_30(seq),      1.0),
        (detect_ultimate_pro(seq),  1.4),
    ]

    renox = engine_renox_hyper(last_num, period)
    engines.append((renox, 1.3))

    big_score, small_score = 0.0, 0.0
    votes = []
    for res, weight in engines:
        if not res:
            continue
        side = res.get("side")
        conf = res.get("confidence", 70)
        votes.append({
            "engine": res.get("pattern", "?"),
            "side": side,
            "confidence": conf,
            "weighted": round(conf * weight, 1)
        })
        if side == "BIG":
            big_score += conf * weight
        elif side == "SMALL":
            small_score += conf * weight

    total = big_score + small_score
    if total == 0:
        return {"side": "BIG", "confidence": 72, "votes": votes,
                "big_score": 0, "small_score": 0}

    final_side = "BIG" if big_score >= small_score else "SMALL"
    confidence = int(min(99, max(72, (max(big_score, small_score) / total) * 100)))

    return {
        "side": final_side,
        "confidence": confidence,
        "votes": votes,
        "big_score": round(big_score, 1),
        "small_score": round(small_score, 1)
    }


# ============================================================
# SECTION 6: ANTI-LOSS PROTECTION
# ============================================================
class AntiLoss:
    def __init__(self):
        self.consecutive_loss = 0
        self.wait_rounds = 0
        self.emergency = False
        self.inverse = False
        self.last_loss_side = None

    def process(self, pred_side, pred_conf, last_num):
        pred_conf = pred_conf if pred_conf is not None else 72

        if self.consecutive_loss >= CONFIG["BREAK_STREAK"]:
            if self.wait_rounds < CONFIG["EMERGENCY_WAIT"]:
                self.wait_rounds += 1
                return {
                    "skip": True,
                    "reason": f"EMERGENCY_WAIT_{self.wait_rounds}/{CONFIG['EMERGENCY_WAIT']}"
                }
            self.wait_rounds = 0
            self.emergency = True
            self.inverse = True

            safe_side = "SMALL" if self.last_loss_side == "BIG" else "BIG"
            safe_pool = SAFE_POOLS["SMALL_CRITICAL"] if safe_side == "SMALL" else SAFE_POOLS["BIG_CRITICAL"]
            return {
                "side": safe_side,
                "number": safe_pool[0],
                "confidence": 95,
                "adjusted": True,
                "reason": "EMERGENCY_RECOVERY",
                "bet_size": 0.5
            }

        if pred_conf < CONFIG["MIN_CONFIDENCE"]:
            return {"skip": True, "reason": f"LOW_CONF_{pred_conf}%"}

        if self.inverse:
            final = "SMALL" if pred_side == "BIG" else "BIG"
            pool = SAFE_POOLS["SMALL_CRITICAL"] if final == "SMALL" else SAFE_POOLS["BIG_CRITICAL"]
            return {
                "side": final,
                "number": pool[0],
                "confidence": min(99, pred_conf + 5),
                "adjusted": True,
                "reason": "INVERSE_MODE",
                "bet_size": 0.75
            }

        return {
            "side": pred_side,
            "confidence": pred_conf,
            "adjusted": False,
            "reason": "NORMAL",
            "bet_size": 1
        }

    def settle(self, predicted_side, actual_num):
        actual_side = get_size(actual_num)
        if actual_side == predicted_side:
            self.consecutive_loss = 0
            self.emergency = False
            self.inverse = False
            return "WIN"
        else:
            self.consecutive_loss += 1
            self.last_loss_side = predicted_side
            return "LOSS"


# ============================================================
# SECTION 7: NUMBER SELECTOR
# ============================================================
def pick_numbers(side, history_nums):
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
# SECTION 9: MAIN PREDICTOR CLASS
# ============================================================
class PredictionEngine:
    def __init__(self):
        self.anti_loss = AntiLoss()
        self.history = []
        self.stats = {"wins": 0, "losses": 0, "jackpots": 0, "total": 0}
        self.last_period = None
        self.last_pred = None
        self.last_nums = None
        self.last_side = None

    def validate(self, latest):
        if not self.last_period or self.last_period == latest["issue"]:
            return
        if self.last_pred is None:
            return

        actual_num = latest["number"]
        actual_side = latest["size"]
        jackpot = self.last_nums and actual_num in self.last_nums
        side_win = actual_side == self.last_side
        final_win = side_win or jackpot

        self.stats["total"] += 1
        if final_win:
            self.stats["wins"] += 1
            if jackpot:
                self.stats["jackpots"] += 1
        else:
            self.stats["losses"] += 1

        self.anti_loss.settle(self.last_side, actual_num)

        self.history.insert(0, {
            "period": self.last_period[-6:],
            "pred_side": self.last_side,
            "pred_nums": self.last_nums,
            "actual": actual_num,
            "actual_side": actual_side,
            "result": "JACKPOT" if jackpot else ("WIN" if side_win else "LOSS"),
            "confidence": self.last_pred.get("confidence", 0)
        })
        self.history = self.history[:50]

    def predict(self, list_data):
        latest = list_data[0]
        self.validate(latest)

        nums = [x["number"] for x in list_data[:50]]
        seq = [to_bs(n) for n in nums]
        last_num = nums[0]
        next_period = str(int(latest["issue"]) + 1)

        ens = ensemble_vote(seq, last_num, next_period)
        prot = self.anti_loss.process(ens["side"], ens["confidence"], last_num)

        if prot.get("skip"):
            return {
                "period": next_period,
                "skip": True,
                "reason": prot["reason"],
                "ensemble": ens,
                "stats": dict(self.stats)
            }

        final_side = prot["side"]
        n1, n2 = pick_numbers(final_side, nums)
        if prot.get("number") is not None:
            n1 = prot["number"]
            others = [x for x in (BIG_POOL if final_side == "BIG" else SMALL_POOL) if x != n1]
            n2 = random.choice(others) if others else n1

        if final_side == "BIG" and n1 < 5:
            n1 = 7
        if final_side == "SMALL" and n1 >= 5:
            n1 = 2

        self.last_period = latest["issue"]
        self.last_side = final_side
        self.last_nums = [n1, n2]
        self.last_pred = {
            "side": final_side,
            "confidence": prot["confidence"],
            "reason": prot["reason"]
        }

        return {
            "period": next_period,
            "side": final_side,
            "numbers": [n1, n2],
            "confidence": prot["confidence"],
            "adjusted": prot.get("adjusted", False),
            "reason": prot.get("reason", "NORMAL"),
            "bet_size": prot.get("bet_size", 1),
            "ensemble_votes": ens["votes"],
            "big_score": ens.get("big_score", 0),
            "small_score": ens.get("small_score", 0),
            "anti_loss": {
                "consecutive_loss": self.anti_loss.consecutive_loss,
                "emergency": self.anti_loss.emergency,
                "inverse": self.anti_loss.inverse
            },
            "stats": dict(self.stats),
            "history": self.history[:10]
        }

    def run_once(self):
        data = fetch_history_from_api()
        if not data or len(data) < 5:
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
    """
    engine = _get_engine()
    data = fetch_history_from_api()

    if data and len(data) >= 5:
        result = engine.predict(data)
        if result and not result.get("skip"):
            return {
                "bigSmall": result["side"],
                "prediction": result["numbers"][0],
                "numbers": result["numbers"],
                "confidence": result["confidence"],
                "steps": [
                    f"Ensemble: B={result['big_score']} S={result['small_score']}",
                    f"Reason: {result['reason']}",
                    f"Votes: {len(result['ensemble_votes'])} engines",
                    f"Bet: {result['bet_size']}x"
                ]
            }
        if result and result.get("skip"):
            ens = result.get("ensemble", {})
            side = ens.get("side", "BIG")
            return {
                "bigSmall": side,
                "prediction": random.choice(BIG_POOL if side == "BIG" else SMALL_POOL),
                "numbers": [random.choice(BIG_POOL if side == "BIG" else SMALL_POOL),
                            random.choice(BIG_POOL if side == "BIG" else SMALL_POOL)],
                "confidence": ens.get("confidence", 72),
                "steps": [f"Skipped: {result['reason']} — fallback"]
            }

    renox = engine_renox_hyper(current_number, period)
    return {
        "bigSmall": renox["side"],
        "prediction": renox["number"],
        "numbers": [renox["number"]],
        "confidence": renox["confidence"],
        "steps": [f"RENOX fallback: {renox['pattern']}"]
    }


# ============================================================
# SECTION 11: ENTRY POINT
# ============================================================
if __name__ == "__main__":
    engine = PredictionEngine()
    print("=" * 60)
    print("  ULTIMATE WINGO PREDICTION ENGINE v11.0")
    print("  14 Engines Combined — All Patterns Working")
    print("=" * 60)
    while True:
        try:
            r = engine.run_once()
            if r:
                if r.get("skip"):
                    print(f"\n⏸️  SKIP: {r['reason']}")
                else:
                    print(f"\n{'─' * 60}")
                    print(f"  PERIOD: {r['period']}")
                    print(f"  🎯 SIGNAL: {r['side']}")
                    print(f"  🔢 NUMBERS: {r['numbers'][0]} , {r['numbers'][1]}")
                    print(f"  📊 CONFIDENCE: {r['confidence']}%")
                    print(f"  🧠 REASON: {r['reason']}")
                    print(f"  🗳️  VOTES:")
                    for v in r["ensemble_votes"][:6]:
                        print(f"      • {v['engine']:22s} → {v['side']:5s} ({v['confidence']}%)")
                    s = r["stats"]
                    wr = round(s["wins"] / s["total"] * 100, 1) if s["total"] else 0
                    print(f"  📈 Stats → W:{s['wins']} L:{s['losses']} J:{s['jackpots']} | WR:{wr}%")
        except KeyboardInterrupt:
            print("\n[!] Stopped.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")
        time.sleep(5)
