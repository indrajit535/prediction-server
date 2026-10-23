# ============================================================
#  UPE-X — ULTIMATE PREDICTION ENGINE (100% Merged)
#  Sources (all prediction logic lifted 1:1):
#    1. RAFSAN BHAI HTML  -> aiBrain, 50-pattern, modeAI, 15-model vote array
#    2. GOKU MODES        -> 500-pattern rulebook, n-gram, Titanium, ZigZag, Dragon, V12
#    3. ANSH BHAI         -> TITANIUM combo, special triggers, trend engine
#    4. TUSHAR            -> UniversalAIDecoder, 12 formula types, 4000-param search
#    5. apex-engine.js    -> trend(3), pickNumbers, evaluateRound, engine loop
#    6. Replacement       -> getPrediction 3:3/dragon/opposite, predictFromHistory
#    7. TRION             -> NUMBER_MAP, inversion, NODE_MATRIX, pick4Numbers
#    8. WINGO 20-Logic    -> calculateBigSmall(20), calculateRedGreen(20)
#    9. WEBC0DC V2        -> 7-layer L1..L7 + self-learning updateWeights
#
#  ARCHITECTURE: Strict sequential filter pipeline.
#  NO VOTING. Each stage either CONFIRMS, OVERRIDES, or DEFERS to the next.
# ============================================================

import math
import random
import time
from typing import Optional, List, Dict, Any

# ============================================================
# §0. PRIMITIVES
# ============================================================
BIG_POOL = [5, 6, 7, 8, 9]
SMALL_POOL = [0, 1, 2, 3, 4]


def to_side(n) -> str:
    return "B" if int(n) >= 5 else "S"


def flip(s: str) -> str:
    return "S" if s == "B" else "B"


def to_color(n) -> str:
    return "R" if int(n) % 2 == 0 else "G"


def clamp(v, a, b):
    return max(a, min(b, v))


def hash_string(s: str) -> int:
    h = 0
    for ch in s:
        h = (h << 5) - h + ord(ch)
        h = h & h
    return abs(h)


# ============================================================
# §1. RAFSAN BHAI — NUMBER MAP (Wingo rules)
# ============================================================
NUMBER_MAP = {
    0: {"size": "SMALL", "validColours": ["RED", "VIOLET"], "isViolet": True},
    1: {"size": "SMALL", "validColours": ["GREEN"], "isViolet": False},
    2: {"size": "SMALL", "validColours": ["RED"], "isViolet": False},
    3: {"size": "SMALL", "validColours": ["GREEN"], "isViolet": False},
    4: {"size": "SMALL", "validColours": ["RED"], "isViolet": False},
    5: {"size": "BIG",   "validColours": ["GREEN", "VIOLET"], "isViolet": True},
    6: {"size": "BIG",   "validColours": ["RED"], "isViolet": False},
    7: {"size": "BIG",   "validColours": ["GREEN"], "isViolet": False},
    8: {"size": "BIG",   "validColours": ["RED"], "isViolet": False},
    9: {"size": "BIG",   "validColours": ["GREEN"], "isViolet": False},
}


def num_meta(n):
    return NUMBER_MAP[((int(math.floor(n)) % 10) + 10) % 10]


# ============================================================
# §2. GOKU MODES — 500-PATTERN RULEBOOK (verbatim subset)
# ============================================================
GOKU_500_PATTERNS = {
    "SBSBSBSB": "SMALL", "BSBSBSBS": "BIG", "SBSBSBSBSBS": "BIG", "SBSBSBSBS": "BIG",
    "BSBSBSBSB": "SMALL", "BSBSBSB": "BIG", "SBSBSBS": "SMALL",
    "BBSBSBSB": "BIG", "SBSBSBSB_": "SMALL",
    "SSBBSBBS": "BIG", "SBB SBBSS".replace(" ", ""): "SMALL",
    "BB SBBSSS".replace(" ", ""): "BIG", "SSBBSBBSSSB": "BIG",
    "SSBSSBBSBBS": "BIG", "SSBBSBB SBS".replace(" ", ""): "BIG",
    "BSSSSBBSBBS": "BIG", "SSBBSBBSB": "SMALL", "BSSBBSBBS": "BIG",
    "SSBBSBB": "SMALL", "BBSSBBSS": "BIG", "SBBSSBBS": "SMALL",
    "SSBBSBBSBSBB": "BIG", "SSBSSBBSSBB": "SMALL", "SSBBSSBBSS": "BIG",
    "BSSSSB BSSBB".replace(" ", ""): "SMALL", "SSBBSBBS": "SMALL",
    "BSSBBSBB": "SMALL", "BBS SBBSS".replace(" ", ""): "BIG",
    "SSBBS SBB".replace(" ", ""): "SMALL",
    "SSBBBS SBB B".replace(" ", ""): "BIG", "BB BSSBB BSS".replace(" ", ""): "BIG",
    "SB BBS SBB BS".replace(" ", ""): "BIG", "SSBBBS SBB B SS B".replace(" ", ""): "BIG",
    "BBS BB S S BB B".replace(" ", ""): "SMALL",
    "SBB SSBB S".replace(" ", ""): "BIG", "BBSSBBSS": "BIG",
    "BSSBB SSB".replace(" ", ""): "SMALL", "SBB SSBB S SBB".replace(" ", ""): "SMALL",
    "BBBBB": "BIG", "BBBBBBBB": "SMALL", "BBBBBS": "BIG", "SBBBBB": "BIG",
    "SSSSS": "SMALL", "SSSSSSSS": "BIG", "SSSSSB": "SMALL", "BSSSSS": "SMALL",
    "BBB SBB".replace(" ", ""): "BIG", "BB SBBB".replace(" ", ""): "BIG",
    "BSBBBB": "BIG", "BBBBBBBSBB".replace(" ", ""): "BIG",
    "BBBSBBSSBSBBBBS": "SMALL", "BSBBSB": "BIG", "SBSBBS": "SMALL",
    "BBBBSB": "BIG", "SSSSBS": "SMALL",
}

GOKU_NGRAM = {
    "BBBSBBSSBSBBBBS": {"prediction": "SMALL", "winRate": 99.4},
    "BBBBBBBB": {"prediction": "SMALL", "winRate": 98.8},
    "SSSSSSSS": {"prediction": "BIG", "winRate": 98.8},
    "SBSBSBSB": {"prediction": "SMALL", "winRate": 98.4},
    "BSBSBSBS": {"prediction": "BIG", "winRate": 98.4},
    "BBSSBBSS": {"prediction": "BIG", "winRate": 97.9},
    "SSBBSSBB": {"prediction": "SMALL", "winRate": 97.9},
    "BBBSSSB": {"prediction": "BIG", "winRate": 97.5},
    "SSSBBBS": {"prediction": "SMALL", "winRate": 97.5},
    "BSBBSB": {"prediction": "BIG", "winRate": 96.8},
    "SBSBBS": {"prediction": "SMALL", "winRate": 96.8},
    "BBBBSB": {"prediction": "BIG", "winRate": 97.2},
    "SSSSBS": {"prediction": "SMALL", "winRate": 97.2},
}


def match_goku_500(sides_str: str) -> dict:
    for seq in sorted(GOKU_NGRAM.keys(), key=len, reverse=True):
        if sides_str.startswith(seq):
            return {"hit": True, "prediction": GOKU_NGRAM[seq]["prediction"],
                    "strength": GOKU_NGRAM[seq]["winRate"], "source": "NGRAM"}
    for seq in sorted(GOKU_500_PATTERNS.keys(), key=len, reverse=True):
        if sides_str.startswith(seq):
            return {"hit": True, "prediction": GOKU_500_PATTERNS[seq],
                    "strength": 96.5, "source": "RULEBOOK"}
    return {"hit": False}


# ============================================================
# §3. GOKU MODES — SPECIAL TRIGGERS (Sn)
# ============================================================
def goku_special_triggers(nums) -> Optional[dict]:
    if len(nums) < 2:
        return None
    n0, n1 = nums[0], nums[1]
    if n0 == 5 and n1 == 5:
        return {"prediction": "BIG", "reason": "DOUBLE-5 VIOLET BRIDGE", "targets": [5, 7, 9]}
    if n0 == 4 and n1 == 4:
        return {"prediction": "SMALL", "reason": "DOUBLE-4 RED PIVOT", "targets": [4, 2, 0]}
    if n0 == 0 and (n1 == 0 or n1 == 5):
        return {"prediction": "BIG", "reason": "ZERO VIOLET GATE", "targets": [5, 7, 8]}
    if n0 == 9 and n1 == 9:
        return {"prediction": "SMALL", "reason": "9-9 CEILING BOUNCE", "targets": [3, 2, 1]}
    return None


# ============================================================
# §4. GOKU MODES — TITANIUM COMBO (Cn)
# ============================================================
def goku_titanium(nums, prediction) -> dict:
    color_seq = []
    for n in nums[:30]:
        m = num_meta(n)
        if m["isViolet"]:
            color_seq.append("VIOLET")
        elif "GREEN" in m["validColours"]:
            color_seq.append("GREEN")
        else:
            color_seq.append("RED")
    head = color_seq[0] if color_seq else "RED"
    streak = 1
    for i in range(1, len(color_seq)):
        if color_seq[i] == head:
            streak += 1
        else:
            break
    dominant = ("RED" if head == "GREEN" else "GREEN") if streak >= 4 else head
    if prediction == "BIG":
        cluster = [7, 9, 5] if dominant == "GREEN" else [6, 8]
    else:
        cluster = [1, 3, 5] if dominant == "GREEN" else [0, 2, 4]
    return {
        "combinationType": f"TITANIUM + {dominant}",
        "dominantColor": dominant,
        "streak": streak,
        "targetNumberCluster": cluster,
        "clusterConfidence": 98.2,
    }


# ============================================================
# §5. GOKU MODES — ZIGZAG 1K (bn) & DRAGON TRACKER (xn)
# ============================================================
def goku_zigzag(sides) -> dict:
    s = "".join(sides)
    steps = 1
    for i in range(1, len(sides)):
        if sides[i] != sides[i - 1]:
            steps += 1
        else:
            break
    is_zigzag = steps >= 2
    is_exhaustion = steps >= 7
    expected = sides[0] if is_exhaustion else flip(sides[0])
    if s.startswith("BSBSB"):
        ptype = "BSBSB"
    elif s.startswith("SBSBS"):
        ptype = "SBSBS"
    else:
        ptype = "GENERIC"
    return {
        "isZigZag": is_zigzag,
        "patternType": ptype,
        "steps": steps,
        "expectedSize": "BIG" if expected == "B" else "SMALL",
        "isExhaustionBreak": is_exhaustion,
        "confidence": 96.8 if is_exhaustion else (93.5 if is_zigzag else 0),
    }


def goku_dragon(sides) -> dict:
    head = sides[0]
    count = 1
    for i in range(1, len(sides)):
        if sides[i] == head:
            count += 1
        else:
            break
    label = "INACTIVE"
    reversal = 30
    expected = head
    if count >= 10:
        label, reversal, expected = "TITAN STREAK (EXTREME)", 98.5, flip(head)
    elif count >= 8:
        label, reversal, expected = "SUPER DRAGON (EXHAUSTION)", 95, flip(head)
    elif count >= 6:
        label, reversal, expected = "MEGA DRAGON (MID INFLECTION)", 75, flip(head)
    elif count >= 3:
        label, reversal, expected = "MOMENTUM DRAGON (CONTINUATION)", 25, head
    return {
        "isDragon": count >= 3,
        "streakSide": "BIG" if head == "B" else "SMALL",
        "streakCount": count,
        "dragonLabel": label,
        "expectedSize": "BIG" if expected == "B" else "SMALL",
        "reversalProbability": reversal,
        "confidence": min(98.5, max(93, 92 + count * 0.7)),
    }


# ============================================================
# §6. GOKU MODES — V12 ZERO-LOSS FORCED REVERSE (yn)
# ============================================================
V12_STATE = {"consecutiveLoss": 0, "lastPredictedSize": None}


def v12_predict(sides, nums) -> dict:
    seq = "".join(sides[:6])

    if V12_STATE["consecutiveLoss"] >= 1 and V12_STATE["lastPredictedSize"]:
        prediction = flip(V12_STATE["lastPredictedSize"])
        return {
            "prediction": "BIG" if prediction == "B" else "SMALL",
            "patternName": "V12 ZERO-LOSS FORCED REVERSE",
            "forcedReverse": True,
            "confidence": 99.2,
        }

    if seq.startswith("BBBB") or seq.startswith("SSSS"):
        prediction = "S" if seq.startswith("BBBB") else "B"
        pattern_name, confidence = "V12 DRAGON INFLECTION", 98.4
    elif seq.startswith("BSBS") or seq.startswith("SBSB"):
        prediction = "S" if seq.startswith("B") else "B"
        pattern_name, confidence = "V12 ZIGZAG HARMONIC", 97.8
    elif seq.startswith("BBSS") or seq.startswith("SSBB"):
        prediction = "B" if seq.startswith("BB") else "S"
        pattern_name, confidence = "V12 DUAL MIRROR", 97.2
    else:
        prediction = flip(sides[0])
        pattern_name, confidence = "V12 HARMONIC ACCORD", 96.5

    return {
        "prediction": "BIG" if prediction == "B" else "SMALL",
        "patternName": pattern_name,
        "forcedReverse": False,
        "confidence": confidence,
    }


# ============================================================
# §7. RAFSAN BHAI — modeAI (opposite/direct switch + cooldown)
# ============================================================
class ModeAI:
    def __init__(self):
        self.mode = "OPPOSITE"
        self.cooldown = 0
        self.simDirect = []
        self.simOpposite = []
        self.log = []

    def acc(self, arr, n) -> int:
        s = arr[: min(n, len(arr))]
        if not s:
            return 50
        return round(sum(1 for x in s if x) / len(s) * 100)

    def record_result(self, actual_size, ai_raw_pred, was_opposite):
        direct_win = ai_raw_pred == actual_size
        opposite_win = ai_raw_pred != actual_size
        self.simDirect.insert(0, direct_win)
        if len(self.simDirect) > 20:
            self.simDirect.pop()
        self.simOpposite.insert(0, opposite_win)
        if len(self.simOpposite) > 20:
            self.simOpposite.pop()
        win = opposite_win if was_opposite else direct_win
        self.log.insert(0, {"wasOpposite": was_opposite, "win": win})
        if len(self.log) > 30:
            self.log.pop()
        if self.cooldown > 0:
            self.cooldown -= 1

    def decide(self, sides, streak_len, confidence) -> str:
        opp5 = self.acc(self.simOpposite, 5)
        dir5 = self.acc(self.simDirect, 5)
        last8 = sides[:8]
        flips = 0
        for i in range(len(last8) - 1):
            if last8[i] != last8[i + 1]:
                flips += 1
        flip_rate = flips / max(len(last8) - 1, 1)
        phase = "ALT" if flip_rate >= 0.7 else ("TREND" if flip_rate <= 0.3 else "CHOP")
        if self.cooldown > 0:
            return self.mode
        if streak_len >= 4 and phase != "ALT":
            self.mode = "OPPOSITE"
            self.cooldown = 2
            return self.mode
        if phase == "ALT":
            self.mode = "OPPOSITE"
            self.cooldown = 3
            return self.mode
        if dir5 > opp5 + 15:
            self.mode = "DIRECT"
            self.cooldown = 3
            return self.mode
        if opp5 > dir5 + 15:
            self.mode = "OPPOSITE"
            self.cooldown = 3
            return self.mode
        if confidence >= 82 and streak_len <= 2:
            self.mode = "DIRECT"
            self.cooldown = 2
            return self.mode
        return self.mode


MODE_AI = ModeAI()


# ============================================================
# §8. RAFSAN — DEEP BRAIN
# ============================================================
class DeepBrain:
    def __init__(self):
        self.totalRecords = 0
        self.numFreq = [0] * 10
        self.sizeFreq = {"BIG": 0, "SMALL": 0}
        self.transMatrix = {}
        self.seq2: Dict[str, Dict[str, int]] = {}
        self.seq3: Dict[str, Dict[str, int]] = {}
        self.seq4: Dict[str, Dict[str, int]] = {}
        self.seq5: Dict[str, Dict[str, int]] = {}
        self.numAfterSize = {"BIG": {}, "SMALL": {}}
        self.numAfterNum = [[0] * 10 for _ in range(10)]
        self.streakStats = {"BIG": 0, "SMALL": 0, "BIGbreak": 0, "SMALLbreak": 0}
        self.streakLengths = {"BIG": [], "SMALL": []}
        self.bigBias = 0.5
        self.hotNumbers = []
        self.coldNumbers = []
        self.ready = False


DEEP = DeepBrain()


def deep_train(history):
    ordered = list(reversed(history))
    DEEP.totalRecords = len(ordered)
    sizes = ["BIG" if x["number"] >= 5 else "SMALL" for x in ordered]
    nums = [x["number"] for x in ordered]

    for n in nums:
        DEEP.numFreq[n] += 1
    for s in sizes:
        DEEP.sizeFreq[s] += 1

    for i in range(len(sizes) - 1):
        key = sizes[i][0] + sizes[i + 1][0]
        DEEP.transMatrix[key] = DEEP.transMatrix.get(key, 0) + 1

    for i in range(len(sizes) - 5):
        s2 = sizes[i] + "|" + sizes[i + 1]
        s3 = s2 + "|" + sizes[i + 2]
        s4 = s3 + "|" + sizes[i + 3]
        s5 = s4 + "|" + sizes[i + 4]
        nxt2 = sizes[i + 2]
        nxt3 = sizes[i + 3]
        nxt4 = sizes[i + 4]
        nxt5 = sizes[i + 5] if i + 5 < len(sizes) else sizes[i + 4]

        for store, key, nxt in [(DEEP.seq2, s2, nxt2), (DEEP.seq3, s3, nxt3),
                                (DEEP.seq4, s4, nxt4), (DEEP.seq5, s5, nxt5)]:
            if key not in store:
                store[key] = {"BIG": 0, "SMALL": 0}
            store[key][nxt] += 1

    for i in range(len(sizes) - 1):
        sz = sizes[i]
        n = nums[i + 1]
        if sz not in DEEP.numAfterSize:
            DEEP.numAfterSize[sz] = {}
        DEEP.numAfterSize[sz][n] = DEEP.numAfterSize[sz].get(n, 0) + 1

    for i in range(len(nums) - 1):
        DEEP.numAfterNum[nums[i]][nums[i + 1]] += 1

    streak = 1
    for i in range(1, len(sizes)):
        if sizes[i] == sizes[i - 1]:
            streak += 1
        else:
            if streak >= 3:
                DEEP.streakStats[sizes[i - 1] + "break"] += 1
            DEEP.streakLengths[sizes[i - 1]].append(streak)
            streak = 1
    if sizes and streak >= 3:
        DEEP.streakStats[sizes[-1]] += 1

    total = DEEP.sizeFreq["BIG"] + DEEP.sizeFreq["SMALL"]
    DEEP.bigBias = DEEP.sizeFreq["BIG"] / total if total > 0 else 0.5

    recent = nums[-min(100, len(nums)):]
    recent_freq = [0] * 10
    for n in recent:
        recent_freq[n] += 1
    avg = len(recent) / 10
    DEEP.hotNumbers = sorted([n for n in range(10) if recent_freq[n] > avg * 1.15],
                             key=lambda x: recent_freq[x], reverse=True)
    DEEP.coldNumbers = sorted([n for n in range(10) if recent_freq[n] < avg * 0.85],
                              key=lambda x: recent_freq[x])
    DEEP.ready = True


# ============================================================
# §9. RAFSAN — 15-model weighted signal (aiPredict core)
# ============================================================
def rafsan15_model(history) -> dict:
    def flip_side(s):
        return "SMALL" if s == "BIG" else "BIG"

    sizes = ["BIG" if x["number"] >= 5 else "SMALL" for x in history[:25]]
    streak_len = 1
    for i in range(1, len(sizes)):
        if sizes[i] == sizes[0]:
            streak_len += 1
        else:
            break

    votes = {"BIG": 0.0, "SMALL": 0.0}

    def add_vote(side, w):
        if side == "BIG" or side == "SMALL":
            votes[side] += w

    # M1-M4 Markov (seq5 -> seq2)
    key5 = "|".join([s for s in [sizes[4] if len(sizes) > 4 else None,
                                  sizes[3] if len(sizes) > 3 else None,
                                  sizes[2] if len(sizes) > 2 else None,
                                  sizes[1] if len(sizes) > 1 else None,
                                  sizes[0] if len(sizes) > 0 else None] if s])
    if key5 in DEEP.seq5:
        t = DEEP.seq5[key5]
        tot = t["BIG"] + t["SMALL"]
        if tot >= 5:
            add_vote("BIG", t["BIG"] / tot * 8)
            add_vote("SMALL", t["SMALL"] / tot * 8)

    key4 = "|".join([s for s in [sizes[3] if len(sizes) > 3 else None,
                                  sizes[2] if len(sizes) > 2 else None,
                                  sizes[1] if len(sizes) > 1 else None,
                                  sizes[0] if len(sizes) > 0 else None] if s])
    if key4 in DEEP.seq4:
        t = DEEP.seq4[key4]
        tot = t["BIG"] + t["SMALL"]
        if tot >= 3:
            add_vote("BIG", t["BIG"] / tot * 6)
            add_vote("SMALL", t["SMALL"] / tot * 6)

    key3 = "|".join([s for s in [sizes[2] if len(sizes) > 2 else None,
                                  sizes[1] if len(sizes) > 1 else None,
                                  sizes[0] if len(sizes) > 0 else None] if s])
    if key3 in DEEP.seq3:
        t = DEEP.seq3[key3]
        tot = t["BIG"] + t["SMALL"]
        if tot >= 2:
            add_vote("BIG", t["BIG"] / tot * 4.5)
            add_vote("SMALL", t["SMALL"] / tot * 4.5)

    key2 = "|".join([s for s in [sizes[1] if len(sizes) > 1 else None,
                                  sizes[0] if len(sizes) > 0 else None] if s])
    if key2 in DEEP.seq2:
        t = DEEP.seq2[key2]
        tot = t["BIG"] + t["SMALL"]
        add_vote("BIG", t["BIG"] / tot * 2)
        add_vote("SMALL", t["SMALL"] / tot * 2)

    # M5 Bayesian
    add_vote("BIG", DEEP.bigBias * 2)
    add_vote("SMALL", (1 - DEEP.bigBias) * 2)

    # M6 transition matrix
    tmBB = DEEP.transMatrix.get("BB", 1) or 1
    tmBS = DEEP.transMatrix.get("BS", 1) or 1
    tmSB = DEEP.transMatrix.get("SB", 1) or 1
    tmSS = DEEP.transMatrix.get("SS", 1) or 1
    if sizes[0] == "BIG":
        t = tmBB + tmBS
        add_vote("BIG", tmBB / t * 1.5)
        add_vote("SMALL", tmBS / t * 1.5)
    else:
        t = tmSB + tmSS
        add_vote("BIG", tmSB / t * 1.5)
        add_vote("SMALL", tmSS / t * 1.5)

    # M7 streak intelligence
    if streak_len >= 3:
        cont = DEEP.streakStats.get(sizes[0], 1) or 1
        brk = DEEP.streakStats.get(sizes[0] + "break", 1) or 1
        cont_rate = cont / (cont + brk)
        if sizes[0] == "BIG":
            add_vote("BIG", cont_rate * 1.5)
            add_vote("SMALL", (1 - cont_rate) * 1.5)
        else:
            add_vote("BIG", (1 - cont_rate) * 1.5)
            add_vote("SMALL", cont_rate * 1.5)

    # M9 recent 10 ratio
    rec10_big = sum(1 for x in sizes[:10] if x == "BIG")
    add_vote("BIG", rec10_big / 10)
    add_vote("SMALL", (10 - rec10_big) / 10)

    # M10 last 3 pattern
    last3 = sizes[:3]
    if len(last3) == 3 and last3[0] == last3[1] and last3[1] == last3[2]:
        add_vote(flip_side(last3[0]), 5)
    elif len(last3) == 3 and last3[0] != last3[1] and last3[1] != last3[2]:
        add_vote(flip_side(last3[0]), 4)

    # M11 5-result bias
    rec5_big = sum(1 for x in sizes[:5] if x == "BIG")
    if rec5_big >= 4:
        add_vote("SMALL", 5.5)
    elif rec5_big <= 1:
        add_vote("BIG", 5.5)

    # M12 streak break
    if streak_len == 2:
        add_vote(flip_side(sizes[0]), 1.5)
    elif streak_len == 3:
        add_vote(flip_side(sizes[0]), 3)
    elif streak_len == 4:
        add_vote(flip_side(sizes[0]), 4.5)
    elif streak_len == 5:
        add_vote(flip_side(sizes[0]), 6)
    elif streak_len >= 6:
        add_vote(flip_side(sizes[0]), 8)

    # M13 flip rate
    last15 = sizes[:15]
    flips15 = 0
    for i in range(1, len(last15)):
        if last15[i] != last15[i - 1]:
            flips15 += 1
    flip_rate = flips15 / (len(last15) - 1) if len(last15) > 1 else 0.5
    opp_last15 = flip_side(last15[0])
    if flip_rate >= 0.75:
        add_vote(opp_last15, 4)
    elif flip_rate <= 0.3:
        add_vote(opp_last15, 2.5)
    else:
        add_vote(opp_last15, 1.5)

    # M14 hot/cold
    if DEEP.ready and len(DEEP.hotNumbers):
        recent_nums15 = [x["number"] for x in history[:15]]
        hot_appear = sum(1 for n in recent_nums15 if n in DEEP.hotNumbers)
        if hot_appear / 15 > 0.4:
            add_vote(flip_side(sizes[0]), 2.5)
    if DEEP.ready and len(DEEP.coldNumbers):
        recent_nums10 = [x["number"] for x in history[:10]]
        cold_appear = sum(1 for n in recent_nums10 if n in DEEP.coldNumbers)
        if cold_appear == 0:
            add_vote("BIG" if DEEP.coldNumbers[0] >= 5 else "SMALL", 2)

    # M15 first-3
    r3 = sizes[:3]
    if len(r3) == 3:
        r3big = sum(1 for x in r3 if x == "BIG")
        if r3big == 3:
            add_vote("SMALL", 4.5)
        elif r3big == 0:
            add_vote("BIG", 4.5)
        elif r3big == 2 and r3[0] == "BIG":
            add_vote("SMALL", 2.5)
        elif r3big == 1 and r3[0] == "SMALL":
            add_vote("BIG", 2.5)

    total = votes["BIG"] + votes["SMALL"]
    if total > 0:
        signal = "BIG" if votes["BIG"] < votes["SMALL"] else "SMALL"
        confidence = round(max(votes["BIG"], votes["SMALL"]) / total * 100)
    else:
        signal = sizes[0] if sizes else "SMALL"
        confidence = 50
    return {"signal": signal, "confidence": confidence,
            "streakLen": streak_len, "votes": votes}


# ============================================================
# §10. WEBC0DC V2 — 7-layer L1..L7
# ============================================================
LAYER_KEYS = ["l1", "l2", "l3", "l4", "l5", "l6", "l7"]


def default_weights() -> Dict[str, float]:
    return {k: 1.0 for k in LAYER_KEYS}


def webc0dc7_layer(numbers, sides, weights=None) -> dict:
    weights = weights or default_weights()
    layers = []

    # L1 Streak
    streak = 0
    for s in sides:
        if s == sides[0]:
            streak += 1
        else:
            break
    if len(sides):
        head = sides[0]
        reversal = streak >= 4
        layers.append({
            "key": "l1",
            "vote": flip(head) if reversal else head,
            "strength": min(1, 0.45 + (streak - 4) * 0.12) if reversal else min(0.7, streak * 0.2),
        })

    # L2 Alternation
    flips = 0
    for i in range(1, min(len(sides), 8)):
        if sides[i] != sides[i - 1]:
            flips += 1
        else:
            break
    layers.append({
        "key": "l2",
        "vote": flip(sides[0]) if flips >= 3 else None,
        "strength": min(1, 0.4 + flips * 0.1) if flips >= 3 else 0,
    })

    # L3 Balance
    last20 = sides[:20]
    big_ratio = sum(1 for s in last20 if s == "B") / (len(last20) or 1)
    layers.append({
        "key": "l3",
        "vote": None if abs(big_ratio - 0.5) < 0.06 else ("S" if big_ratio > 0.5 else "B"),
        "strength": min(1, abs(big_ratio - 0.5) * 3),
    })

    # L4 Momentum
    def ratio(arr):
        return sum(1 for s in arr if s == "B") / len(arr) if arr else 0.5

    mom_delta = ratio(sides[:5]) - ratio(sides[5:10])
    layers.append({
        "key": "l4",
        "vote": None if abs(mom_delta) < 0.15 else ("B" if mom_delta > 0 else "S"),
        "strength": min(1, abs(mom_delta) * 1.6),
    })

    # L5 Markov 2-step
    mv, ms = None, 0
    if len(sides) >= 6:
        pair = f"{sides[1]}{sides[0]}"
        b = s = 0
        for i in range(1, len(sides) - 2):
            if f"{sides[i + 2]}{sides[i + 1]}" == pair:
                if sides[i] == "B":
                    b += 1
                else:
                    s += 1
        tot = b + s
        if tot >= 3:
            mv = None if b == s else ("B" if b > s else "S")
            ms = abs(b - s) / tot
    layers.append({"key": "l5", "vote": mv, "strength": ms})

    # L6 Gravity
    last6 = numbers[:6]
    avg6 = sum(last6) / len(last6) if last6 else 4.5
    layers.append({
        "key": "l6",
        "vote": None if abs(avg6 - 4.5) < 0.4 else ("S" if avg6 > 4.5 else "B"),
        "strength": min(1, abs(avg6 - 4.5) / 2.5),
    })

    # L7 Recency
    rec = 0.0
    for i, s in enumerate(sides[:12]):
        rec += (1 if s == "B" else -1) * (0.85 ** i)
    layers.append({
        "key": "l7",
        "vote": None if abs(rec) < 0.5 else ("B" if rec > 0 else "S"),
        "strength": min(1, abs(rec) / 4),
    })

    # Weighted (still inside a single pipeline — not external voting)
    B = S = 0.0
    for L in layers:
        if not L["vote"]:
            continue
        w = L["strength"] * weights.get(L["key"], 1.0)
        if L["vote"] == "B":
            B += w
        else:
            S += w
    total = B + S
    if total == 0 or B == S:
        signal = sides[0] if sides else None
        confidence = 0
    else:
        signal = "B" if B > S else "S"
        confidence = clamp(50 + (abs(B - S) / total) * 45, 0, 99)
    return {"layers": layers, "signal": signal, "confidence": confidence}


def update_weights(current_weights, layers_used, actual_side) -> Dict[str, float]:
    nxt = dict(current_weights)
    for L in layers_used:
        if not L.get("vote") or L.get("strength", 0) <= 0:
            continue
        delta = (0.05 if L["vote"] == actual_side else -0.05) * (0.5 + L["strength"])
        nxt[L["key"]] = clamp(nxt.get(L["key"], 1.0) + delta, 0.25, 2.5)
    return nxt


# ============================================================
# §11. TUSHAR — UniversalAIDecoder formula types (12) + param search
# ============================================================
def _f0(h, p):
    return "B" if abs(h[0]*p[0]+h[1]*p[1]+h[2]*p[2]+h[3]*p[3]+p[4]) % 10 >= 5 else "S"

def _f1(h, p):
    return "B" if abs((h[0]-h[1]*p[1]+h[2]-h[3]*p[1]+p[0])*3) % 10 >= 5 else "S"

def _f2(h, p):
    base = max(2, p[0])
    v = (h[0]+1)*(h[1]+1)*(h[2]+1)*(h[3]+1)*p[1]
    return "B" if abs(v) % base >= base / 2 else "S"

def _f3(h, p):
    x = ((h[0] ^ p[0]) << p[1]) ^ (h[1] ^ (p[0]+3)) ^ (h[2] << (p[1] % 4)) ^ h[3]
    return "B" if abs(x) % 10 >= 5 else "S"

def _f4(h, p):
    s = (p[1] if h[0] >= 5 else 1) + (p[2] if h[1] >= 5 else 1) + (p[3] if h[2] >= 5 else 1) + (p[4] if h[3] >= 5 else 1)
    return "B" if s % 10 >= p[0] else "S"

def _f5(h, p):
    c = p[1]
    for i in range(4):
        c += h[i] * (1 + (i * 3) % 10)
    return "B" if abs(c * p[0]) % 10 >= 5 else "S"

def _f6(h, p):
    v = int(((h[0]+h[1]+h[2]+h[3]) / 4) * p[1] + p[0])
    return "B" if abs(v) % 10 >= 5 else "S"

def _f7(h, p):
    fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    v = 0
    for i in range(4):
        v += h[i] * fib[((p[0] + i) % 10 + 10) % 10]
    return "B" if abs(v * p[1]) % 10 >= 5 else "S"

def _f8(h, p):
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
    pm = primes[((p[0] % len(primes)) + len(primes)) % len(primes)]
    s = h[0]*2 + h[1]*3 + h[2]*5 + h[3]*7 + p[1]
    return "B" if s % pm >= pm / 2 else "S"

def _f9(h, p):
    row = ((p[0] % 3) + 3) % 3
    ws = [
        [p[1], p[2], p[3], p[4]],
        [(p[1]+p[2]) % 9 + 1, (p[2]+p[3]) % 9 + 1, (p[3]+p[4]) % 9 + 1, (p[4]+p[1]) % 9 + 1],
        [(p[1]+p[3]) % 9 + 1, (p[2]+p[4]) % 9 + 1, (p[1]+p[4]) % 9 + 1, (p[2]+p[3]) % 9 + 1],
    ]
    v = 0
    for i in range(4):
        v += h[i] * ws[row][i]
    return "B" if abs(v) % 10 >= 5 else "S"

def _f10(h, p):
    d = (h[0]-h[1]) * p[1] + (h[2]-h[3]) + p[0]
    return "B" if abs(d) % 10 >= 5 else "S"

def _f11(h, p):
    v = p[0]*h[0]*h[0] + p[1]*h[1] + p[2]*h[2]*h[3] + p[3]*h[0]*h[3] + p[4]
    return "B" if abs(v) % 10 >= 5 else "S"


FORMULA_TYPES = [_f0, _f1, _f2, _f3, _f4, _f5, _f6, _f7, _f8, _f9, _f10, _f11]


def param_generator(nums, sides, f_idx, fetch_num):
    total_sum = sum(nums[:10])
    bs = sum(1 for t in sides if t == "B")
    sets = []
    limit = 4000
    for a in range(1, 11):
        if len(sets) >= limit:
            break
        for b in range(1, 11):
            if len(sets) >= limit:
                break
            for c in range(1, 11):
                if len(sets) >= limit:
                    break
                for d in range(1, 11):
                    if len(sets) >= limit:
                        break
                    sets.append([a, b, c, d, (a + b + c + d) % 20])
    seed = total_sum * 7 + bs * 13 + f_idx * 17 + fetch_num * 31
    for i in range(len(sets) - 1, 0, -1):
        j = (seed * (i + 1) * 7 + f_idx * 13) % (i + 1)
        sets[i], sets[j] = sets[j], sets[i]
    yield from sets


def tushar_10of10(numbers, sides, fetch_num) -> dict:
    t0 = time.time()
    found = False
    final_bs = "BIG"
    final_name = ""
    best = 0
    tested = 0
    for f_idx in range(len(FORMULA_TYPES)):
        if found:
            break
        for params in param_generator(numbers, sides, f_idx, fetch_num):
            tested += 1
            match_count = 0
            for j in range(10):
                inp = numbers[j + 1: j + 5]
                if len(inp) < 4:
                    continue
                if FORMULA_TYPES[f_idx](inp, params) == sides[j]:
                    match_count += 1
            if match_count > best:
                best = match_count
            if match_count == 10:
                found = True
                final_bs = "BIG" if FORMULA_TYPES[f_idx](numbers[:4], params) == "B" else "SMALL"
                final_name = f"FORMULA_{f_idx}"
                break
    return {
        "found": found,
        "signal": final_bs,
        "name": final_name,
        "tested": tested,
        "best": best,
        "elapsedMs": (time.time() - t0) * 1000,
    }


# ============================================================
# §12. apex-engine.js — trend(3) + pickNumbers
# ============================================================
def apex_trend(last3_numbers) -> str:
    trend = [to_side(n) for n in last3_numbers]
    big_count = trend.count("B")
    return "B" if big_count > 1 else "S"


def apex_pick_numbers(prediction) -> dict:
    same_pool = BIG_POOL if prediction == "BIG" else SMALL_POOL
    opp_pool = SMALL_POOL if prediction == "BIG" else BIG_POOL
    return {
        "num1": random.choice(same_pool),
        "num2": random.choice(opp_pool),
    }


# ============================================================
# §13. Replacement — getPrediction (3:3 / DRAGON / OPPOSITE)
# ============================================================
def replacement_prediction(current_number, results, override=None) -> dict:
    def flip_side(s):
        return "SMALL" if s == "BIG" else "BIG"

    if override == "BIG" or override == "SMALL":
        return {"pred": override, "mode": "ADMIN FORCE"}
    if not isinstance(results, list) or len(results) < 6:
        return {"pred": "BIG" if current_number <= 4 else "SMALL", "mode": "DEFAULT"}
    last6 = results[:6]
    first3 = last6[:3]
    last3 = last6[3:6]
    is_first3_same = all(v == first3[0] for v in first3)
    is_last3_same = all(v == last3[0] for v in last3)
    if is_first3_same and is_last3_same and first3[0] != last3[0]:
        streak = sum(1 for v in last6 if v == last6[0])
        return {"pred": last6[0] if streak < 3 else flip_side(last6[0]), "mode": "3:3 PATTERN"}
    if is_first3_same:
        return {"pred": first3[0], "mode": "DRAGON"}
    return {"pred": "BIG" if current_number <= 4 else "SMALL", "mode": "OPPOSITE"}


# ============================================================
# §14. TRION — inversion + NODE_MATRIX + pick4Numbers
# ============================================================
NODE_MATRIX = [
    {"num": 0, "prob": 12}, {"num": 1, "prob": 8}, {"num": 2, "prob": 6},
    {"num": 3, "prob": 9}, {"num": 4, "prob": 7}, {"num": 5, "prob": 8},
    {"num": 6, "prob": 10}, {"num": 7, "prob": 11}, {"num": 8, "prob": 9},
    {"num": 9, "prob": 10},
]


def trion_inversion(raw_size, raw_color) -> dict:
    r_size = "BIG" if (raw_size or "").upper() == "BIG" else "SMALL"
    r_color = "GREEN" if (raw_color or "").upper() == "GREEN" else "RED"
    predicted_size = "SMALL" if r_size == "BIG" else "BIG"
    predicted_color = "GREEN" if r_color == "RED" else "RED"
    if predicted_size == "BIG" and predicted_color == "GREEN":
        num, sec = 7, 9
    elif predicted_size == "BIG" and predicted_color == "RED":
        num, sec = 8, 6
    elif predicted_size == "SMALL" and predicted_color == "GREEN":
        num, sec = 3, 1
    else:
        num, sec = 2, 4
    return {"size": predicted_size, "color": predicted_color,
            "number": num, "secondary": sec}


def trion_pick4_numbers(size, color) -> List[int]:
    size_nums = BIG_POOL if size == "BIG" else SMALL_POOL
    filtered = []
    for n in size_nums:
        m = num_meta(n)
        if color == "VIOLET":
            if m["isViolet"]:
                filtered.append(n)
        elif color == "GREEN":
            if "GREEN" in m["validColours"]:
                filtered.append(n)
        elif color == "RED":
            if "RED" in m["validColours"]:
                filtered.append(n)
        else:
            filtered.append(n)
    out = list(filtered)
    for n in size_nums:
        if len(out) >= 4:
            break
        if n not in out:
            out.append(n)
    return out[:4]


# ============================================================
# §15. WINGO 20-Logic — calculateBigSmall(20) + calculateRedGreen(20)
# ============================================================
def wingo_big_small(numbers, sides, last_digits) -> dict:
    ld = list(last_digits) + [0, 0, 0, 0]
    d1 = ld[-1] if len(last_digits) >= 1 else 0
    d2 = ld[-2] if len(last_digits) >= 2 else 0
    d3 = ld[-3] if len(last_digits) >= 3 else 0
    d4 = ld[-4] if len(last_digits) >= 4 else 0
    last = numbers[0] if len(numbers) > 0 else 0
    last5 = numbers[:5]
    last3_s = sides[:3]
    results = []

    def push(side, conf):
        results.append({"side": side, "conf": conf})

    push("S" if (d3 + d2 + d1) % 10 <= 4 else "B", 75 + (d1 * 3) % 24)
    push("S" if abs(d2 - d1) % 2 == 0 else "B", 75 + (d2 * 3) % 24)
    push("S" if (d1 * 2) % 10 < 5 else "B", 75 + (d1 * 5) % 24)
    push("S" if (d3 + d2 * 2 + d1 * 3) % 10 < 5 else "B", 76)
    push("S" if ((d1 * d1) % 10) % 2 == 0 else "B", 77)
    push("S" if (d4 + d3 + d2 * 2 + d1 * 3) % 2 == 0 else "B", 78)
    push("B" if ((last + d1) / 2) % 1 == 0 else "S", 79)
    push("S" if (last + d1) % 10 < 5 else "B", 80)
    push("S" if (last + 1) % 2 == 0 else "B", 81)
    push("B" if (d2 * 3 + d1) % 2 == 0 else "S", 82)
    push("B" if ((last * last * last) % 10) > last else "S", 83)
    push("B" if int((math.sqrt(last if last > 0 else 1) * 10) % 10) >= 5 else "S", 84)
    push("B" if (sum(last5) / max(len(last5), 1)) > 4.5 else "S", 85)
    push("S" if int(math.floor(last * 1.618) % 2) == 0 else "B", 86)
    push("S" if (d1 % 2) + (last % 2) == 0 else "B", 87)
    pat = "".join(last3_s)
    if pat == "BSB":
        push("S", 88)
    elif pat == "SBS":
        push("B", 88)
    else:
        push("S" if last3_s and last3_s[0] == "B" else "B", 88)
    push(("S" if last >= 5 else "B") if (last == 0 or last == 5) else ("B" if last >= 5 else "S"), 89)
    push("B" if (d1 + last) % 10 >= 5 else "S", 90)
    push("S" if ((d1 * (last if last else 1)) % 10) % 2 == 0 else "B", 91)
    push("B" if ((d1 ^ last) % 10) >= 5 else "S", 92)

    results.sort(key=lambda x: x["conf"], reverse=True)
    return results[0]


def wingo_red_green(numbers, sides, last_digits) -> dict:
    ld = list(last_digits) + [0, 0, 0]
    d1 = ld[-1] if len(last_digits) >= 1 else 0
    d2 = ld[-2] if len(last_digits) >= 2 else 0
    d3 = ld[-3] if len(last_digits) >= 3 else 0
    n1 = numbers[0] if len(numbers) > 0 else 0
    n2 = numbers[1] if len(numbers) > 1 else 0
    n3 = numbers[2] if len(numbers) > 2 else 0
    last5 = numbers[:5]
    colors = [to_color(n) for n in numbers[:6]]

    def count_streak(c):
        cnt = 0
        for x in colors:
            if x == c:
                cnt += 1
            else:
                break
        return cnt

    rs = count_streak("R")
    gs = count_streak("G")
    results = []

    def push(color, conf):
        results.append({"color": color, "conf": conf})

    push("G" if rs >= 2 else ("R" if gs >= 2 else ("G" if n1 % 2 == 0 else "R")), 78)
    pat = "".join(colors[:3])
    if pat == "RGR":
        push("G", 79)
    elif pat == "GRG":
        push("R", 79)
    elif pat.startswith("RR"):
        push("G", 79)
    elif pat.startswith("GG"):
        push("R", 79)
    else:
        push("R" if n1 % 2 == 0 else "G", 79)
    push("R" if sum(1 for n in last5 if n % 2 == 0) > 2 else "G", 80)
    push("G" if (n1 % 2) * 3 + (n2 % 2) * 2 + (n3 % 2) >= 3 else "R", 81)
    push("R" if d1 % 2 == 0 else "G", 82)
    push(("R" if n1 % 2 == 0 else "G") if (d1 % 2 == 0) == (n1 % 2 == 0) else ("G" if n1 % 2 == 0 else "R"), 83)
    mod = (n1 + n2 + n3) % 3
    push("G" if mod == 0 else ("R" if mod == 1 else ("G" if n1 % 2 == 0 else "R")), 84)
    push("G" if rs >= 3 else ("R" if gs >= 3 else ("G" if (d1 + d2 + n1) % 4 < 2 else "R")), 85)
    push("G" if ((n1 + n2 + n3 * 2) % 10) % 2 == 0 else "R", 86)
    last4 = colors[:4]
    r = last4.count("R")
    g = last4.count("G")
    push("G" if r >= 3 else ("R" if g >= 3 else ("G" if colors and colors[0] == "R" else "R")), 87)
    push("R" if ((d1 * 2 + n1) % 10) % 2 == 0 else "G", 88)
    push("G" if (abs(n1 - n2) % 10) % 2 == 0 else "R", 89)
    push("R" if (((d3 + d2 * 2 + d1 * 3) % 10 + n1) % 2 == 0) else "G", 90)
    push("G" if (n1 + 1) % 10 % 2 == 0 else "R", 91)
    push("R" if (((n1 * n1 * n1) % 10) % 2 == 0) else "G", 92)
    avg = sum(last5) / len(last5) if last5 else 4.5
    push("G" if avg > 4.5 else "R", 93)
    push("G" if (d1 % 2) + (n1 % 2) + (n2 % 2) >= 2 else "R", 94)
    push("R" if ((d1 ^ n1) % 10) % 2 == 0 else "G", 95)
    push("R" if ((n1 * d1 + d2) % 10) % 2 == 0 else "G", 96)
    push("R" if sum(1 for c in colors[:3] if c == "G") >= 2 else "G", 97)

    results.sort(key=lambda x: x["conf"], reverse=True)
    return results[0]


# ============================================================
# §16. NUMBER PREDICTOR (merged from TUSHAR + RAFSAN)
# ============================================================
def predict_number_final(numbers, sides, target_side) -> dict:
    scores = [0.0] * 10
    last10 = numbers[:10]
    last20 = numbers[:20]

    for i in range(min(len(last10), 10)):
        scores[last10[i]] += (10 - i) * 2

    if len(numbers) >= 4:
        d1 = (numbers[0] - numbers[1] + 10) % 10
        d2 = (numbers[1] - numbers[2] + 10) % 10
        d3 = (numbers[2] - numbers[3] + 10) % 10
        nd = round((d1 + d2 + d3) / 3)
        scores[(numbers[0] + nd + 5) % 10] += 15
        scores[(numbers[0] - nd + 10) % 10] += 8

    for i in range(1, min(len(last20), 20)):
        if last20[i - 1] == last20[0]:
            scores[last20[i]] += 12

    avg = sum(last10) / len(last10) if last10 else 4.5
    t = round(avg)
    scores[int(clamp(t, 0, 9))] += 10
    scores[int(clamp(t + 1, 0, 9))] += 7
    scores[int(clamp(t - 1, 0, 9))] += 7

    # RAFSAN numAfterNum + numAfterSize
    if len(numbers) >= 2:
        prev = numbers[0]
        for n in range(10):
            scores[n] += DEEP.numAfterNum[prev][n] * 1.5

    pool = BIG_POOL if target_side == "B" else SMALL_POOL
    for n in pool:
        scores[n] += 5
    sorted_pool = sorted(pool, key=lambda x: scores[x], reverse=True)
    conf = int((scores[sorted_pool[0]] / (scores[sorted_pool[0]] + scores[sorted_pool[1]] or 1)) * 100)
    return {"primary": sorted_pool[0], "secondary": sorted_pool[1],
            "confidence": conf}


# ============================================================
# §17. THE SINGLE PIPELINE — UPE-X
# ============================================================
def _finalize(signal, confidence, stage, pattern_name, num, numbers, sides, extras=None):
    extras = extras or {}
    titanium = extras.get("titanium") or goku_titanium(numbers, "BIG" if signal == "B" else "SMALL")
    return {
        "success": True,
        "prediction": "BIG" if signal == "B" else "SMALL",
        "predictedNumber": num["primary"],
        "secondaryNumber": num["secondary"],
        "confidence": round(confidence),
        "stage": stage,
        "pattern": pattern_name,
        "colorPrediction": titanium["dominantColor"],
        "targetCluster": titanium["targetNumberCluster"]
                         if extras.get("titanium")
                         else ([5, 7, 9] if signal == "B" else [0, 2, 4]),
        # Diagnostics
        "diagnostics": extras,
    }


def predict_unified(history, opts=None) -> dict:
    """
    @param history: list of {"issueNumber": str|int, "number": int} — newest-first, >= 5 rows
    @param opts: dict { "weights"?: dict, "adminOverride"?: str, "fetchNum"?: int }
    @returns unified prediction
    """
    opts = opts or {}
    if not isinstance(history, list) or len(history) < 5:
        raise ValueError("UPE-X: need >= 5 history rows")

    weights = opts.get("weights") or default_weights()
    fetch_num = opts.get("fetchNum") or len(history)
    admin_override = opts.get("adminOverride")

    numbers = [int(h["number"]) for h in history]
    sides = [to_side(n) for n in numbers]
    sides_str = "".join(sides)
    raw_issue = history[0].get("issueNumber") or ""
    last_digits = [int(c) for c in str(raw_issue) if c.isdigit()]
    current_number = numbers[0]

    # ── ADMIN OVERRIDE (highest priority — apex/replacement/rafsan modeAI) ──
    if admin_override == "BIG" or admin_override == "SMALL":
        num = predict_number_final(numbers, sides, "B" if admin_override == "BIG" else "S")
        return _finalize("B" if admin_override == "BIG" else "S", 100,
                         "ADMIN_FORCE", "ADMIN_OVERRIDE", num, numbers, sides)

    # ── STAGE 1: GOKU n-gram / 500-rulebook (highest base accuracy) ──
    goku500 = match_goku_500(sides_str)
    if goku500["hit"] and goku500["strength"] >= 97.5:
        signal = "B" if goku500["prediction"] == "BIG" else "S"
        num = predict_number_final(numbers, sides, signal)
        return _finalize(signal, round(goku500["strength"]),
                         f"GOKU_{goku500['source']}",
                         sides_str[: min(8, len(sides_str))], num, numbers, sides)

    # ── STAGE 2: GOKU special triggers (double-5 / 9-9 etc.) ──
    special = goku_special_triggers(numbers)
    if special:
        signal = "B" if special["prediction"] == "BIG" else "S"
        num = predict_number_final(numbers, sides, signal)
        return _finalize(signal, 98.4, "GOKU_SPECIAL", special["reason"],
                         num, numbers, sides)

    # ── STAGE 3: V12 zero-loss forced reverse ──
    v12 = v12_predict(sides, numbers)
    if v12["forcedReverse"]:
        signal = "B" if v12["prediction"] == "BIG" else "S"
        num = predict_number_final(numbers, sides, signal)
        return _finalize(signal, 99, "V12_FORCED", v12["patternName"],
                         num, numbers, sides)

    # ── STAGE 4: RAFSAN 15-model deep AI (if trained) ──
    if not DEEP.ready:
        deep_train(history)
    rafsan = rafsan15_model(history)

    # Apply modeAI inversion
    mode_decision = MODE_AI.decide(sides, rafsan["streakLen"], rafsan["confidence"])
    rafsan_signal = "B" if rafsan["signal"] == "BIG" else "S"
    if mode_decision == "OPPOSITE":
        rafsan_signal = flip(rafsan_signal)

    # ── STAGE 5: WEBC0DC 7-layer ──
    webc = webc0dc7_layer(numbers, sides, weights)

    # ── STAGE 6: TUSHAR 10/10 formula search ──
    tushar = tushar_10of10(numbers, sides, fetch_num)

    # ── STAGE 7: GOKU dragon + zigzag ──
    dragon = goku_dragon(sides)
    zigzag = goku_zigzag(sides)

    # ── STAGE 8: apex trend(3) ──
    apex = apex_trend(numbers[:3])

    # ── STAGE 9: replacement (3:3 / dragon / opposite) ──
    repl = replacement_prediction(current_number, sides, None)

    # ── STAGE 10: TRION inversion ──
    raw_size = "BIG" if sides[0] == "B" else "SMALL"
    raw_color = "RED" if to_color(numbers[0]) == "R" else "GREEN"
    trion = trion_inversion(raw_size, raw_color)

    # ── STAGE 11: WINGO 20-logic big/small ──
    wingo_bs = wingo_big_small(numbers, sides, last_digits)

    # ── SEQUENTIAL FILTER — NOT voting ──
    # Priority: TUSHAR exact hit > V12 pattern > RAFSAN deep (with modeAI)
    #           > WEBC0DC > GOKU dragon/zigzag > WINGO 20 > APEX
    chosen = None
    stage = ""
    confidence = 0
    pattern_name = ""

    # (A) TUSHAR exact 10/10 formula -> highest algorithmic certainty
    if tushar["found"]:
        chosen = "B" if tushar["signal"] == "BIG" else "S"
        stage = "TUSHAR_10of10"
        confidence = 97
        pattern_name = tushar["name"]
    # (B) V12 non-forced pattern
    elif v12["confidence"] >= 97:
        chosen = "B" if v12["prediction"] == "BIG" else "S"
        stage = "V12_PATTERN"
        confidence = v12["confidence"]
        pattern_name = v12["patternName"]
    # (C) RAFSAN 15-model with modeAI — only if confidence strong
    elif rafsan["confidence"] >= 65:
        chosen = rafsan_signal
        stage = f"RAFSAN_{mode_decision}"
        confidence = rafsan["confidence"]
        pattern_name = f"MODE_{mode_decision}_SEQ{sides_str[:5]}"
    # (D) WEBC0DC 7-layer — if strong
    elif webc["signal"] and webc["confidence"] >= 60:
        chosen = webc["signal"]
        stage = "WEBC0DC_7L"
        confidence = webc["confidence"]
        pattern_name = f"FLOW_{sides_str[:4]}"
    # (E) GOKU dragon (mid inflection) or zigzag
    elif dragon["isDragon"] and dragon["reversalProbability"] >= 60:
        chosen = "B" if dragon["expectedSize"] == "BIG" else "S"
        stage = "GOKU_DRAGON"
        confidence = dragon["confidence"]
        pattern_name = dragon["dragonLabel"]
    elif zigzag["isZigZag"]:
        chosen = "B" if zigzag["expectedSize"] == "BIG" else "S"
        stage = "GOKU_ZIGZAG"
        confidence = zigzag["confidence"]
        pattern_name = zigzag["patternType"]
    # (F) WINGO 20-logic (highest-confidence single function)
    elif wingo_bs:
        chosen = wingo_bs["side"]
        stage = "WINGO_20L"
        confidence = wingo_bs["conf"]
        pattern_name = "WINGO_20LOGIC"
    # (G) APEX trend(3)
    else:
        chosen = apex
        stage = "APEX_TREND3"
        confidence = 55
        pattern_name = "TREND_3"

    # ── CONFIRMATION BONUS: if multiple stages agree ──
    stage_votes = {
        "rafsan": rafsan_signal,
        "webc": webc["signal"],
        "tushar": ("B" if tushar["signal"] == "BIG" else "S") if tushar["found"] else None,
        "dragon": ("B" if dragon["expectedSize"] == "BIG" else "S") if dragon["isDragon"] else None,
        "zigzag": ("B" if zigzag["expectedSize"] == "BIG" else "S") if zigzag["isZigZag"] else None,
        "wingo": wingo_bs["side"] if wingo_bs else None,
        "apex": apex,
        "repl": "B" if repl["pred"] == "BIG" else "S",
        "trion": "B" if trion["size"] == "BIG" else "S",
        "v12": "B" if v12["prediction"] == "BIG" else "S",
    }
    agree = sum(1 for v in stage_votes.values() if v == chosen)
    total_signals = sum(1 for v in stage_votes.values() if v is not None)
    if total_signals > 0 and agree >= math.ceil(total_signals * 0.6):
        confidence = clamp(confidence + 6, 0, 99)

    num = predict_number_final(numbers, sides, chosen)

    # ── Titanium combo (enriched output) ──
    titanium = goku_titanium(numbers, "BIG" if chosen == "B" else "SMALL")

    return _finalize(chosen, confidence, stage, pattern_name, num, numbers, sides, extras={
        "rafsan": rafsan,
        "modeDecision": mode_decision,
        "webc": webc,
        "tushar": tushar,
        "dragon": dragon,
        "zigzag": zigzag,
        "apex": apex,
        "repl": repl,
        "trion": trion,
        "wingoBS": wingo_bs,
        "v12": v12,
        "titanium": titanium,
        "goku500": goku500,
        "layersUsed": webc["layers"],
    })


# ============================================================
# §18. FEEDBACK — update weights after actual result
# ============================================================
def record_outcome(actual_number, opts=None) -> Dict[str, float]:
    opts = opts or {}
    actual_side = to_side(actual_number)
    layers = opts.get("layers") or []
    MODE_AI.record_result(
        "BIG" if actual_side == "B" else "SMALL",
        opts.get("aiRawPrediction") or ("SMALL" if actual_side == "B" else "BIG"),
        opts.get("wasOpposite", False),
    )
    if V12_STATE["lastPredictedSize"]:
        predicted = V12_STATE["lastPredictedSize"]
        if predicted == actual_side:
            V12_STATE["consecutiveLoss"] = 0
        else:
            V12_STATE["consecutiveLoss"] += 1
    V12_STATE["lastPredictedSize"] = actual_side
    return update_weights(opts.get("weights") or default_weights(), layers, actual_side)


# ============================================================
# §19. COMPAT ALIAS — app.py expects sddgamer263_predict
# ============================================================
def sddgamer263_predict(history, opts=None):
    """
    Backwards-compatible wrapper around predict_unified().
    Accepts either:
      - list of dicts:  [{"issueNumber": ..., "number": 7}, ...]
      - list of ints:   [7, 3, 8, 2, 9, ...]  (auto-wrapped)
    Returns the unified prediction dict.
    """
    # Normalize raw ints -> {"issueNumber": ..., "number": n}
    if history and isinstance(history[0], (int, float)):
        history = [
            {"issueNumber": f"auto{i}", "number": int(n)}
            for i, n in enumerate(history)
        ]
    return predict_unified(history, opts)


# ============================================================
# §20. EXPORTS (Python equivalent of module.exports)
# ============================================================
__all__ = [
    "predict_unified", "sddgamer263_predict", "record_outcome", "deep_train",
    "DEEP", "MODE_AI", "V12_STATE",
    "default_weights", "update_weights",
    "to_side", "flip", "to_color", "NUMBER_MAP",
]

# ============================================================
# §21. USAGE / SELF-TEST
# ============================================================
if __name__ == "__main__":
    import json
    history = [
        {"issueNumber": "202601011200", "number": 7},
        {"issueNumber": "202601011159", "number": 3},
        {"issueNumber": "202601011158", "number": 8},
        {"issueNumber": "202601011157", "number": 2},
        {"issueNumber": "202601011156", "number": 9},
        {"issueNumber": "202601011155", "number": 5},
        {"issueNumber": "202601011154", "number": 1},
        {"issueNumber": "202601011153", "number": 6},
        {"issueNumber": "202601011152", "number": 0},
        {"issueNumber": "202601011151", "number": 4},
    ]
    out = predict_unified(history)
    print(json.dumps({k: v for k, v in out.items() if k != "diagnostics"}, indent=2))

    # Alias self-test
    out2 = sddgamer263_predict(history)
    assert out2["success"] is True
    print("\n✅ sddgamer263_predict alias works:", out2["prediction"])
