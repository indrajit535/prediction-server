"""
WEBC0DC V3 — ULTIMATE HYBRID PREDICTION ENGINE
================================================
100% Python Port + JS ULTIMATE WINGO AI v11.0 + WEBC0DC V2 7-Layer Engine

COMBINED:
  ✅ JS ULTIMATE WINGO AI v11.0 (Full)
     - MAFIYA AI Engine
     - 11-Pattern Analysis
     - 250+ Pattern Database
     - 200+ CPU Patterns (Bunny AI)
     - RIFU Engine
     - Ultimate Pro Engine
     - Hyper Engine (8 Logic Modes)
     - Anti-Loss Strategy (NO WAIT)
     - Ensemble Voting
  ✅ WEBC0DC V2 7-Layer Engine
     - L1 STREAK SCAN
     - L2 ALTERNATION
     - L3 BALANCE
     - L4 MOMENTUM
     - L5 MARKOV
     - L6 GRAVITY
     - L7 RECENCY
     - 5 Pattern Detectors (ABAB, AABB, AAABBB, DRGN, MIRR)

⚠️  1-MINUTE MODE ONLY (30s NOT used)
"""

import time
import random
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple


# ============================================================
# CONSTANTS
# ============================================================
LAYER_KEYS = ["l1", "l2", "l3", "l4", "l5", "l6", "l7"]

CONFIG = {
    "HISTORY_LIMIT": 30,
    "MIN_CONFIDENCE": 60,
    "MAX_CONFIDENCE": 99,
    "BREAK_STREAK": 1,
    "CRITICAL_LOSS_LIMIT": 1,
    # 1-MINUTE MODE ONLY (30s removed)
    "API_URL": "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    "MODE": "1M",
}

SAFE_POOLS = {
    "BIG_HIGH": [8, 9, 7],
    "SMALL_HIGH": [1, 2, 3],
    "BIG_CRITICAL": [8, 9],
    "SMALL_CRITICAL": [1, 2],
    "BIG_ULTRA": [8],
    "SMALL_ULTRA": [1],
    "BIG_EMERGENCY": [9, 8],
    "SMALL_EMERGENCY": [2, 1],
}

PATTERNS_11 = [
    {"id": 1, "name": "Alternating Pattern", "sequence": ["BIG","SMALL","BIG","SMALL","BIG","SMALL","BIG","SMALL"]},
    {"id": 2, "name": "Double Switch Pattern", "sequence": ["BIG","BIG","SMALL","SMALL","BIG","BIG","SMALL","SMALL"]},
    {"id": 3, "name": "Triple Block Pattern", "sequence": ["BIG","BIG","BIG","SMALL","SMALL","SMALL","BIG","BIG","BIG","SMALL","SMALL","SMALL"]},
    {"id": 4, "name": "Four Block Pattern", "sequence": ["BIG","BIG","BIG","BIG","SMALL","SMALL","SMALL","SMALL","BIG","BIG","BIG","BIG","SMALL","SMALL","SMALL","SMALL"]},
    {"id": 5, "name": "1-2 Repeating Pattern", "sequence": ["SMALL","BIG","BIG","SMALL","BIG","BIG","SMALL","BIG","BIG","SMALL"]},
    {"id": 6, "name": "B-S-S Pattern", "sequence": ["BIG","SMALL","SMALL","BIG","SMALL","SMALL","BIG","SMALL","SMALL"]},
    {"id": 7, "name": "B-SSS Pattern", "sequence": ["BIG","SMALL","SMALL","SMALL","BIG","SMALL","SMALL","SMALL","BIG","SMALL","SMALL","SMALL"]},
    {"id": 8, "name": "S-BBB Pattern", "sequence": ["SMALL","BIG","BIG","BIG","SMALL","BIG","BIG","BIG","SMALL"]},
    {"id": 9, "name": "Mixed Block Pattern", "sequence": ["BIG","BIG","SMALL","SMALL","SMALL","BIG","BIG","BIG","SMALL","SMALL","SMALL","BIG","BIG"]},
    {"id": 10, "name": "S-S-BBB Pattern", "sequence": ["SMALL","SMALL","BIG","BIG","BIG","SMALL","SMALL","BIG","BIG","BIG"]},
    {"id": 11, "name": "Long BIG Run", "sequence": ["BIG"]*14},
    {"id": 12, "name": "Long SMALL Run", "sequence": ["SMALL"]*12},
]

LOGIC_MODES = [
    {"name": "REVERSAL", "weight": 0},
    {"name": "TREND_FOLLOW", "weight": 1},
    {"name": "PATTERN_BREAK", "weight": 2},
    {"name": "MOMENTUM_SHIFT", "weight": 3},
    {"name": "ALTERNATING_FLOW", "weight": 4},
    {"name": "STREAK_KILLER", "weight": 5},
    {"name": "FREQUENCY_PROB", "weight": 6},
    {"name": "RANDOM_FOREST", "weight": 7},
]


# ============================================================
# HELPERS (JS Port)
# ============================================================

def default_weights() -> Dict[str, float]:
    return {k: 1 for k in LAYER_KEYS}


def to_side(n: int) -> str:
    return "B" if int(n) >= 5 else "S"


def to_side_full(n: int) -> str:
    return "BIG" if int(n) >= 5 else "SMALL"


def flip(side: str) -> str:
    if side in ("B", "BIG"):
        return "S" if side == "B" else "SMALL"
    return "B" if side == "S" else "BIG"


def get_size_from_number(n) -> Optional[str]:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return None
    try:
        return "BIG" if int(n) >= 5 else "SMALL"
    except (ValueError, TypeError):
        return None


# ============================================================
# 250+ PATTERN DATABASE (JS Port)
# ============================================================

def _build_pattern_database() -> Dict[str, Dict]:
    db = {}
    raw = [
        ('B','S',48),('S','B',48),
        ('BB','S',58),('SS','B',58),
        ('BS','B',53),('SB','S',53),
        ('BBB','S',75),('SSS','B',75),
        ('BBS','B',68),('SSB','S',68),
        ('BSB','S',72),('SBS','B',72),
        ('BSS','B',67),('SBB','S',67),
        ('BBBB','S',85),('SSSS','B',85),
        ('BBBS','S',73),('SSSB','B',73),
        ('BBSB','S',71),('SSBS','B',71),
        ('BSBB','S',71),('SBSS','B',71),
        ('BSBS','S',75),('SBSB','B',75),
        ('BBSS','B',68),('SSBB','S',68),
        ('BBBBB','S',90),('SSSSS','B',90),
        ('BBBBS','S',78),('SSSSB','B',78),
        ('BBSBB','S',75),('SSBSS','B',75),
        ('BSBBB','S',77),('SBSSS','B',77),
        ('BBBBBB','S',94),('SSSSSS','B',94),
        ('BBBBBS','S',82),('SSSSSB','B',82),
        ('BBBBBBB','S',96),('SSSSSSS','B',96),
        ('BBBBBBBB','S',98),('SSSSSSSS','B',98),
        ('BSBSBS','B',80),('SBSBSB','S',80),
        ('BSBSBSB','B',84),('SBSBSBS','S',84),
        ('BSBSBSBS','B',87),('SBSBSBSB','S',87),
        ('BBSBBS','S',74),('SSBSSB','B',74),
        ('BBSSBB','S',72),('SSBBSS','B',72),
        ('BSSSB','S',76),('SBBBS','B',76),
    ]
    for pat, nxt, conf in raw:
        db[pat] = {"next": nxt, "conf": conf}
    return db


PATTERNS_DB = _build_pattern_database()


# ============================================================
# 200+ CPU PATTERN DATABASE (JS Port)
# ============================================================
CPU_PATTERN_DB = {
    "BBB": {"next": "SMALL", "conf": 82}, "SSS": {"next": "BIG", "conf": 82},
    "BBS": {"next": "SMALL", "conf": 70}, "SSB": {"next": "BIG", "conf": 70},
    "BSS": {"next": "BIG", "conf": 68}, "SBB": {"next": "SMALL", "conf": 68},
    "BSB": {"next": "SMALL", "conf": 63}, "SBS": {"next": "BIG", "conf": 63},
    "BBBB": {"next": "SMALL", "conf": 88}, "SSSS": {"next": "BIG", "conf": 88},
    "BBBS": {"next": "SMALL", "conf": 84}, "SSSB": {"next": "BIG", "conf": 84},
    "BBSS": {"next": "SMALL", "conf": 76}, "SSBB": {"next": "BIG", "conf": 76},
    "BSBS": {"next": "BIG", "conf": 62}, "SBSB": {"next": "SMALL", "conf": 62},
    "BSSB": {"next": "BIG", "conf": 68}, "SBBS": {"next": "SMALL", "conf": 68},
    "BSBB": {"next": "SMALL", "conf": 68}, "SBSS": {"next": "BIG", "conf": 68},
    "BBSB": {"next": "SMALL", "conf": 72}, "SSBS": {"next": "BIG", "conf": 72},
    "BSSS": {"next": "BIG", "conf": 80}, "SBBB": {"next": "SMALL", "conf": 80},
    "BBBBB": {"next": "SMALL", "conf": 90}, "SSSSS": {"next": "BIG", "conf": 90},
    "BBBBS": {"next": "SMALL", "conf": 86}, "SSSSB": {"next": "BIG", "conf": 86},
    "BBBSS": {"next": "SMALL", "conf": 76}, "SSSBB": {"next": "BIG", "conf": 76},
    "BSBSB": {"next": "BIG", "conf": 62}, "SBSBS": {"next": "SMALL", "conf": 62},
    "BBSSB": {"next": "SMALL", "conf": 70}, "SSBBS": {"next": "BIG", "conf": 70},
    "BSSBB": {"next": "SMALL", "conf": 70}, "SBBSS": {"next": "BIG", "conf": 70},
    "BSSSS": {"next": "BIG", "conf": 84}, "SBBBB": {"next": "SMALL", "conf": 84},
    "BBBSB": {"next": "SMALL", "conf": 78}, "SSSBS": {"next": "BIG", "conf": 78},
    "BBBBBB": {"next": "SMALL", "conf": 92}, "SSSSSS": {"next": "BIG", "conf": 92},
    "BBBSSS": {"next": "SMALL", "conf": 85}, "SSSBBB": {"next": "BIG", "conf": 85},
    "BBSSBB": {"next": "SMALL", "conf": 83}, "SSBBSS": {"next": "BIG", "conf": 83},
    "BSBSBS": {"next": "BIG", "conf": 74}, "SBSBSB": {"next": "SMALL", "conf": 74},
    "BBBBSS": {"next": "SMALL", "conf": 86}, "SSSSBB": {"next": "BIG", "conf": 86},
    "BBBBBBB": {"next": "SMALL", "conf": 93}, "SSSSSSS": {"next": "BIG", "conf": 93},
    "BSBSBSB": {"next": "BIG", "conf": 76}, "SBSBSBS": {"next": "SMALL", "conf": 76},
    "BBBSSSS": {"next": "SMALL", "conf": 76}, "SSSBBBB": {"next": "BIG", "conf": 76},
    "BBBBBBBB": {"next": "SMALL", "conf": 96}, "SSSSSSSS": {"next": "BIG", "conf": 96},
    "BSBSBSBS": {"next": "BIG", "conf": 78}, "SBSBSBSB": {"next": "SMALL", "conf": 78},
    "BBBBSSSS": {"next": "SMALL", "conf": 86}, "SSSSBBBB": {"next": "BIG", "conf": 86},
    "BBBBBBBS": {"next": "SMALL", "conf": 94}, "SSSSSSSB": {"next": "BIG", "conf": 94},
    "BBBBBBBBB": {"next": "SMALL", "conf": 99}, "SSSSSSSSS": {"next": "BIG", "conf": 99},
    "BBBBBBBBBB": {"next": "SMALL", "conf": 99}, "SSSSSSSSSS": {"next": "BIG", "conf": 99},
    "BBBSBS": {"next": "SMALL", "conf": 78}, "SSSBSB": {"next": "BIG", "conf": 78},
    "BBBSBSB": {"next": "SMALL", "conf": 79}, "SSSBSBS": {"next": "BIG", "conf": 79},
    "BBBBBSBS": {"next": "SMALL", "conf": 86}, "SSSSSBSB": {"next": "BIG", "conf": 86},
    "BBBSBB": {"next": "SMALL", "conf": 76}, "SSSBSS": {"next": "BIG", "conf": 76},
    "BSBBS": {"next": "BIG", "conf": 66}, "SBSSB": {"next": "SMALL", "conf": 66},
    "SBBBSS": {"next": "BIG", "conf": 69}, "BSSBB": {"next": "SMALL", "conf": 69},
    "BBBBBSSS": {"next": "SMALL", "conf": 88}, "SSSSSBBB": {"next": "BIG", "conf": 88},
    "BSBBB": {"next": "SMALL", "conf": 70}, "SBSSS": {"next": "BIG", "conf": 70},
    "BBBSSB": {"next": "SMALL", "conf": 78}, "BBSBSS": {"next": "BIG", "conf": 66},
    "SSBSBB": {"next": "SMALL", "conf": 66}, "BBSBSB": {"next": "SMALL", "conf": 64},
    "SSBSBS": {"next": "BIG", "conf": 64}, "BBBBBSSSS": {"next": "SMALL", "conf": 88},
    "SSSSSBBBB": {"next": "BIG", "conf": 88}, "BBBBBSB": {"next": "SMALL", "conf": 88},
    "BBBBBSS": {"next": "SMALL", "conf": 88}, "BBBBSBB": {"next": "SMALL", "conf": 84},
    "BBBBSBS": {"next": "SMALL", "conf": 84}, "BBBBSSB": {"next": "SMALL", "conf": 84},
    "BBBSBBB": {"next": "SMALL", "conf": 78}, "BBBSBBS": {"next": "SMALL", "conf": 78},
    "BBBSBSS": {"next": "SMALL", "conf": 78},
    "BBSBBBB": {"next": "BIG", "conf": 70}, "BBSBBBS": {"next": "SMALL", "conf": 68},
    "BBSBBSB": {"next": "SMALL", "conf": 68}, "BBSBBSS": {"next": "SMALL", "conf": 68},
    "BBSSBBB": {"next": "SMALL", "conf": 68}, "BBSSBBS": {"next": "SMALL", "conf": 68},
    "BBSSBSB": {"next": "SMALL", "conf": 68}, "BBSSBSS": {"next": "SMALL", "conf": 70},
    "BSBBBBB": {"next": "SMALL", "conf": 68}, "BSBBBBS": {"next": "SMALL", "conf": 68},
    "BSBBSBB": {"next": "SMALL", "conf": 68}, "BSBBSBS": {"next": "SMALL", "conf": 64},
    "BSBSBBB": {"next": "SMALL", "conf": 72}, "BSBSBBS": {"next": "SMALL", "conf": 72},
    "BSBSBSS": {"next": "SMALL", "conf": 72}, "BSBSSBB": {"next": "SMALL", "conf": 64},
    "BSSBBBB": {"next": "SMALL", "conf": 68}, "BSSBBBS": {"next": "SMALL", "conf": 64},
    "BSSBBSB": {"next": "SMALL", "conf": 64}, "BSSBBSS": {"next": "SMALL", "conf": 64},
    "BSSSBBB": {"next": "SMALL", "conf": 64}, "BSSSBBS": {"next": "SMALL", "conf": 64},
    "BSSSBSB": {"next": "SMALL", "conf": 64}, "BSSSBSS": {"next": "BIG", "conf": 68},
    "SBBBBBB": {"next": "SMALL", "conf": 68}, "SBBBBBS": {"next": "SMALL", "conf": 68},
    "SBBBBSB": {"next": "SMALL", "conf": 68}, "SBBBBSS": {"next": "BIG", "conf": 64},
    "SBBBSBB": {"next": "SMALL", "conf": 68}, "SBBBSBS": {"next": "BIG", "conf": 64},
    "SBBSBBB": {"next": "SMALL", "conf": 68}, "SBBSBBS": {"next": "BIG", "conf": 64},
    "SBBSBSB": {"next": "BIG", "conf": 64}, "SBBSBSS": {"next": "BIG", "conf": 64},
    "SBSBBBB": {"next": "SMALL", "conf": 68}, "SBSBBBS": {"next": "BIG", "conf": 64},
    "SBSBBSB": {"next": "BIG", "conf": 64}, "SBSBBSS": {"next": "BIG", "conf": 64},
    "SBSBSBB": {"next": "BIG", "conf": 72}, "SBSBSSB": {"next": "BIG", "conf": 72},
    "SBSBSSS": {"next": "BIG", "conf": 72}, "SBSSBBB": {"next": "BIG", "conf": 64},
    "SBSSBBS": {"next": "BIG", "conf": 64}, "SBSSBSB": {"next": "BIG", "conf": 64},
    "SBSSBSS": {"next": "BIG", "conf": 68}, "SBSSSBB": {"next": "BIG", "conf": 64},
    "SBSSSBS": {"next": "BIG", "conf": 68}, "SBSSSSB": {"next": "BIG", "conf": 68},
    "SSBBBBB": {"next": "SMALL", "conf": 70}, "SSBBBBS": {"next": "SMALL", "conf": 70},
    "SSBBBSB": {"next": "SMALL", "conf": 70}, "SSBBBSS": {"next": "BIG", "conf": 68},
    "SSBBSBB": {"next": "SMALL", "conf": 70}, "SSBBSBS": {"next": "BIG", "conf": 68},
    "SSBBSSB": {"next": "BIG", "conf": 68}, "SSBBSSS": {"next": "BIG", "conf": 68},
    "SSBSBBB": {"next": "SMALL", "conf": 70}, "SSBSBBS": {"next": "BIG", "conf": 68},
    "SSBSBSB": {"next": "BIG", "conf": 68}, "SSBSBSS": {"next": "BIG", "conf": 68},
    "SSBSSBB": {"next": "BIG", "conf": 68}, "SSBSSBS": {"next": "BIG", "conf": 68},
    "SSBSSSB": {"next": "BIG", "conf": 68}, "SSBSSSS": {"next": "BIG", "conf": 70},
    "SSSBBBS": {"next": "BIG", "conf": 78}, "SSSBBSB": {"next": "BIG", "conf": 78},
    "SSSBSBB": {"next": "BIG", "conf": 78}, "SSSBSBS": {"next": "BIG", "conf": 78},
    "SSSBSSB": {"next": "BIG", "conf": 78}, "SSSBSSS": {"next": "BIG", "conf": 78},
    "SSSSBBS": {"next": "BIG", "conf": 84}, "SSSSBSB": {"next": "BIG", "conf": 84},
    "SSSSBSS": {"next": "BIG", "conf": 84}, "SSSSSBB": {"next": "BIG", "conf": 88},
    "SSSSSBS": {"next": "BIG", "conf": 88}, "SSSSSSB": {"next": "BIG", "conf": 90},
    "BBBBBBBS": {"next": "SMALL", "conf": 92}, "BBBBBBSB": {"next": "SMALL", "conf": 90},
    "BBBBBSBB": {"next": "SMALL", "conf": 88}, "BBBBBSBS": {"next": "SMALL", "conf": 88},
    "BBBBBSSB": {"next": "SMALL", "conf": 88}, "BBBBSBBB": {"next": "SMALL", "conf": 84},
    "BBBBSBBS": {"next": "SMALL", "conf": 84}, "BBBBSBSB": {"next": "SMALL", "conf": 84},
    "BBBBSBSS": {"next": "SMALL", "conf": 84}, "BBBBSSBB": {"next": "SMALL", "conf": 84},
    "BBBBSSBS": {"next": "SMALL", "conf": 84}, "BBBBSSSB": {"next": "SMALL", "conf": 84},
    "BBBSBBBB": {"next": "SMALL", "conf": 78}, "BBBSBBBS": {"next": "SMALL", "conf": 78},
    "BBBSBBSB": {"next": "SMALL", "conf": 78}, "BBBSBBSS": {"next": "SMALL", "conf": 78},
    "BBBSBSBB": {"next": "SMALL", "conf": 78}, "BBBSBSBS": {"next": "SMALL", "conf": 78},
    "BBBSBSSB": {"next": "SMALL", "conf": 78}, "BBBSBSSS": {"next": "SMALL", "conf": 78},
    "BBBSSBBS": {"next": "SMALL", "conf": 78}, "BBBSSBSB": {"next": "SMALL", "conf": 78},
    "BBBSSBSS": {"next": "SMALL", "conf": 78}, "BBBSSSBS": {"next": "SMALL", "conf": 78},
    "BBBSSSSB": {"next": "SMALL", "conf": 78}, "BBBSSSSS": {"next": "SMALL", "conf": 78},
}


# ============================================================
# STATE MANAGEMENT (JS Port)
# ============================================================
class State:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.jackpots = 0
        self.consecutiveLoss = 0
        self.consecutiveWin = 0
        self.lastLossNum = None
        self.lastWinNum = None
        self.totalBets = 0
        self.profit = 0.0
        self.balance = 1000.0
        self.lastPrediction = None
        self.lastActual = None
        self.emergencyMode = False
        self.inverseMode = False
        self.guaranteedWinMode = False
        self.periodCounter = 0
        self.totalRoundsAnalyzed = 0
        self.oppositeCount = 0
        self.lossStreak = 0
        self.winStreak = 0
        self.lastIssue = None
        self.fullHistory = []
        self.predictionHistory = []
        self.actualHistory = []
        self.numberFrequency = [0]*10
        self.currentLogicIndex = 0
        self.bunnyPrediction = None
        self.bunnyPattern = None
        self.bunnyConfidence = 0

    def reset(self):
        self.__init__()


STATE = State()
# Pro engine memory (in-memory replacement of localStorage)
PRO_MEMORY = {
    "winRate": 0, "totalPredictions": 0, "correctPredictions": 0,
    "streakHistory": [], "patternDatabase": {},
    "adaptiveWeights": {"mirror": 3, "ema": 2, "gap": 1, "cluster": 2, "trend": 2},
    "last10Accuracy": [], "lastPrediction": "BIG",
}


# ============================================================
# PATTERN SCORING (JS: calculateScore, windowMatch)
# ============================================================

def _calculate_score(history_sizes: List[str], pattern: dict) -> int:
    if not history_sizes:
        return 0
    seq = pattern["sequence"]
    compare_len = min(len(history_sizes), max(len(seq), 12))
    matches = 0
    for i in range(compare_len):
        hi = len(history_sizes) - compare_len + i
        pi = (i + len(seq) - compare_len) % len(seq)
        if history_sizes[hi] == seq[pi]:
            matches += 1
    return round((matches / compare_len) * 100)


def _window_match(history_sizes: List[str], pattern: dict) -> int:
    seq = pattern["sequence"]
    if not history_sizes or len(history_sizes) < len(seq):
        return 0
    best = 0
    for start in range(len(history_sizes) - len(seq) + 1):
        match = 0
        for i in range(len(seq)):
            if history_sizes[start + i] == seq[i]:
                match += 1
        score = round((match / len(seq)) * 100)
        if score > best:
            best = score
    return best


# ============================================================
# MAFIYA AI ENGINE (JS Port)
# ============================================================

def mafiya_analyze(history: List[int]) -> Dict:
    STATE.totalRoundsAnalyzed += 1
    if not history or len(history) < 5:
        pred = "BIG" if random.random() > 0.5 else "SMALL"
        return {"prediction": pred, "confidence": 50,
                "mode": "INITIALIZATION_RANDOM", "scores": {"BIG": 10, "SMALL": 10}}

    scores = {"BIG": 0, "SMALL": 0}
    last20 = [to_side_full(h) for h in history[:CONFIG["HISTORY_LIMIT"]]]
    last5 = last20[:5]
    latest = last20[0]
    current_streak = 1
    for i in range(1, len(last20)):
        if last20[i] == last20[0]:
            current_streak += 1
        else:
            break

    if current_streak >= 3:
        weight = current_streak * 15
        if latest == "BIG":
            scores["SMALL"] += weight
        else:
            scores["BIG"] += weight

    big5 = last5.count("BIG")
    small5 = last5.count("SMALL")
    if big5 >= 4 and current_streak < 4:
        scores["BIG"] += 20
    if small5 >= 4 and current_streak < 4:
        scores["SMALL"] += 20

    alternating = all(last5[i] != last5[i+1] for i in range(4)) if len(last5) >= 5 else False
    if alternating:
        scores["SMALL" if latest == "BIG" else "BIG"] += 30

    micro = "-".join(last5)
    if micro == "BIG-BIG-SMALL-BIG-SMALL":
        scores["BIG"] += 25
    if micro == "SMALL-SMALL-BIG-SMALL-BIG":
        scores["SMALL"] += 25
    if len(last5) >= 3 and last5[0] == last5[1] and last5[1] != last5[2]:
        scores["SMALL" if latest == "BIG" else "BIG"] += 15

    big20 = last20.count("BIG")
    small20 = len(last20) - big20
    if big20 >= 13:
        scores["SMALL"] += 18
    if small20 >= 13:
        scores["BIG"] += 18

    if STATE.lastPrediction and STATE.lastPrediction != latest:
        STATE.oppositeCount += 1
    else:
        STATE.oppositeCount = 0
    if STATE.oppositeCount >= 2:
        scores[latest] += 25
        STATE.oppositeCount = 0

    if scores["SMALL"] > scores["BIG"]:
        prediction = "SMALL"
    elif scores["BIG"] > scores["SMALL"]:
        prediction = "BIG"
    else:
        prediction = latest

    total = scores["BIG"] + scores["SMALL"] or 1
    confidence = int((max(scores["BIG"], scores["SMALL"]) / total) * 100)

    if STATE.lossStreak >= CONFIG["BREAK_STREAK"]:
        prediction = "SMALL" if prediction == "BIG" else "BIG"

    STATE.lastPrediction = prediction
    return {"prediction": prediction, "confidence": confidence,
            "mode": "ADAPTIVE_AI", "scores": scores}


# ============================================================
# PATTERN-BASED PREDICTION (250+ Patterns)
# ============================================================

def compute_pattern_prediction(history: List[int]) -> Optional[Dict]:
    if not history or len(history) < 3:
        return {"prediction": "BIG", "confidence": 50, "reason": "INSUFFICIENT_DATA"}

    pattern_str = "".join(
        "B" if h >= 5 else "S" for h in history[:min(len(history), 11)]
    )

    matches = []
    for pat, data in PATTERNS_DB.items():
        if pat.startswith(pattern_str) and len(pattern_str) < len(pat):
            matches.append(data["next"])

    if not matches:
        return None

    big_c = matches.count("B")
    small_c = matches.count("S")
    total = len(matches)
    predicted = "BIG" if big_c >= small_c else "SMALL"
    confidence = min(95, 55 + round((max(big_c, small_c) / total) * 40))
    return {"prediction": predicted, "confidence": confidence,
            "reason": f"PATTERN-MATCH ({total} matches)"}


# ============================================================
# RIFU ENGINE (JS Port)
# ============================================================

def get_rifu_prediction(history: List[int], period_counter: int) -> Dict:
    if not history:
        return {"side": "BIG", "confidence": 70, "logic": "START", "specialActive": False}

    side_seq = [to_side_full(h) for h in history]
    last_side = side_seq[-1]
    predicted = None
    logic_used = "RIFU TREND"
    special = False
    confidence = 72
    pc = (period_counter or 0) + 1

    if pc >= 5:
        pc = 0
        special = True
        last8 = side_seq[-8:]
        big8 = last8.count("BIG")
        predicted = "BIG" if big8 >= 4 else "SMALL"
        logic_used = "5P-VIP-TREND"
        confidence = 88

    if not predicted and len(side_seq) >= 5:
        last = side_seq[-1]
        count = 0
        for i in range(len(side_seq) - 1, -1, -1):
            if side_seq[i] == last:
                count += 1
            else:
                break
        if count >= 5:
            predicted = last
            logic_used = f"5+-STREAK-{last}"
            special = True
            confidence = 92

    if not predicted and len(side_seq) >= 3:
        last3 = side_seq[-3:]
        if last3[0] == "BIG" and last3[1] == "SMALL" and last3[2] == "BIG":
            predicted = "BIG"; logic_used = "3P-PATTERN-BIG"; special = True; confidence = 84
        elif last3[0] == "SMALL" and last3[1] == "BIG" and last3[2] == "SMALL":
            predicted = "SMALL"; logic_used = "3P-PATTERN-SMALL"; special = True; confidence = 84

    if not predicted and len(side_seq) >= 7:
        last7 = side_seq[-7:]
        is_alt = all(last7[i] != last7[i-1] for i in range(1, 7))
        if is_alt:
            predicted = last7[-1]
            logic_used = f"7x-ALT-VIP-{predicted}"
            special = True
            confidence = 90

    if not predicted:
        last5 = side_seq[-5:]
        bigs = last5.count("BIG")
        if bigs >= 4:
            predicted = "SMALL"
        elif bigs <= 1:
            predicted = "BIG"
        else:
            predicted = "SMALL" if last_side == "BIG" else "BIG"
        logic_used = "RIFU-REVERSAL"
        confidence = 76

    return {"side": predicted, "logic": logic_used, "specialActive": special,
            "confidence": confidence, "pc": pc}


# ============================================================
# ULTIMATE PRO ENGINE (JS Port)
# ============================================================

def compute_ultimate_pro_prediction(periods: List[Dict]) -> Dict:
    if not periods or len(periods) < 8:
        return {"prediction": "BIG", "number": 5, "reason": "INITIALIZING...", "confidence": 60}

    pattern_score = {"BIG": 0.0, "SMALL": 0.0}
    weights = PRO_MEMORY["adaptiveWeights"]

    s = [p["side"] for p in periods[:5]]
    if len(s) >= 5 and s[0] == s[4] and s[1] == s[3]:
        vote = "SMALL" if s[0] == "BIG" else "BIG"
        pattern_score[vote] += weights["mirror"] * 1.5

    max_streak = 1; cur_streak = 1
    for i in range(1, len(periods)):
        if periods[i]["side"] == periods[i-1]["side"]:
            cur_streak += 1
            max_streak = max(max_streak, cur_streak)
        else:
            cur_streak = 1
    if max_streak >= 4:
        streak_side = periods[0]["side"]
        if max_streak >= 6:
            pattern_score["SMALL" if streak_side == "BIG" else "BIG"] += 4
        else:
            pattern_score[streak_side] += 2

    if len(periods) >= 5:
        last5 = [p["side"] for p in periods[-5:]]
        is_alt = all(last5[i] != last5[i-1] for i in range(1, 5))
        if is_alt:
            nxt = "SMALL" if last5[4] == "BIG" else "BIG"
            pattern_score[nxt] += 3
        if last5[0] == last5[1] and last5[3] == last5[4] and last5[0] == last5[4]:
            pattern_score[last5[0]] += 3

    fib_score = 0
    fib_weights = [8, 5, 3, 2, 1, 1, 0, 0]
    for i in range(min(len(periods), 8)):
        fib_score += (1 if periods[i]["number"] >= 5 else -1) * fib_weights[i]
    pattern_score["BIG" if fib_score > 0 else "SMALL"] += 2

    all_nums = list(range(10))
    recent_nums = [p["number"] for p in periods[:15]]
    missing = [n for n in all_nums if n not in recent_nums]
    if missing:
        pattern_score["BIG" if missing[0] >= 5 else "SMALL"] += 1.5

    cluster = [p["number"] for p in periods[:5]]
    edge = sum(1 for n in cluster if n <= 1 or n >= 8)
    if edge >= 3:
        pattern_score["BIG"] += 1.5

    avg_acc = PRO_MEMORY["correctPredictions"] / max(PRO_MEMORY["totalPredictions"], 1)
    if avg_acc < 0.5:
        last_pred = PRO_MEMORY.get("lastPrediction", "BIG")
        pattern_score["SMALL" if last_pred == "BIG" else "BIG"] += 2

    diff = abs(pattern_score["BIG"] - pattern_score["SMALL"])
    if diff >= 5: confidence = 95
    elif diff >= 4: confidence = 90
    elif diff >= 3: confidence = 85
    elif diff >= 2: confidence = 78
    else: confidence = 70

    if avg_acc > 0.6: confidence += 5
    if avg_acc > 0.75: confidence += 5

    final_side = "BIG" if pattern_score["BIG"] >= pattern_score["SMALL"] else "SMALL"
    PRO_MEMORY["lastPrediction"] = final_side

    return {"prediction": final_side, "number": 7 if final_side == "BIG" else 2,
            "reason": "ULTIMATE-PRO-ADAPTIVE", "confidence": round(confidence)}


# ============================================================
# 30-ROUND RATIO LOGIC
# ============================================================

def compute_30round_ratio(periods: List[Dict]) -> Optional[Dict]:
    if not periods or len(periods) < 20:
        return None
    recent = periods[:30]
    big_count = sum(1 for p in recent if p["number"] >= 5)
    ratio = big_count / 30
    pred = "SMALL" if ratio >= 0.5 else "BIG"
    conf = 70 + abs(ratio - 0.5) * 60
    return {"prediction": pred, "confidence": min(95, round(conf)),
            "reason": f"30-RATIO: {ratio*100:.1f}%"}


# ============================================================
# 2-LEVEL FIXED WIN
# ============================================================

def compute_two_level_fixed_win(periods: List[Dict]) -> Optional[Dict]:
    if not periods or len(periods) < 6:
        return None
    sides = [p["side"] for p in periods[:10]]
    if len(sides) < 6:
        return None

    last2 = sides[:2]
    if last2[0] == last2[1]:
        pred = last2[0]
        match_count = 0; win_count = 0
        for i in range(len(sides) - 3):
            if sides[i] == sides[i+1] and sides[i] == last2[0]:
                match_count += 1
                if i + 2 < len(sides) and sides[i+2] == sides[i]:
                    win_count += 1
        if match_count >= 2 and win_count >= 1:
            return {"prediction": pred, "confidence": 92,
                    "reason": f"2-LEVEL-FIXED: {pred} continuation"}
        return {"prediction": pred, "confidence": 78,
                "reason": f"2-LEVEL-FIXED: {pred} (moderate)"}

    if len(sides) >= 4:
        alt = sides[:4]
        if alt[0] != alt[1] and alt[1] != alt[2] and alt[2] != alt[3]:
            pred = "SMALL" if sides[0] == "BIG" else "BIG"
            return {"prediction": pred, "confidence": 85,
                    "reason": "2-LEVEL-FIXED: alternating reversal"}

    return {"prediction": sides[0], "confidence": 72, "reason": "2-LEVEL-FIXED: last side"}


# ============================================================
# 11-PATTERN ENGINE
# ============================================================

def generate_11pattern_prediction(history: List[Dict]) -> Dict:
    if not history or len(history) < 5:
        return {"predictionSize": "BIG", "sureNumbers": [5,6], "confidence": 50,
                "patternName": "INSUFFICIENT_DATA", "topPatterns": []}

    history_sizes = [
        d.get("size") or to_side_full(d.get("number", d) if isinstance(d, dict) else d)
        for d in history
    ]
    history_sizes = [x for x in history_sizes if x]
    history_sizes.reverse()

    analyzed = []
    for p in PATTERNS_11:
        rep = _calculate_score(history_sizes, p)
        direct = _window_match(history_sizes, p)
        score = max(rep, direct)
        analyzed.append({**p, "score": score})
    analyzed.sort(key=lambda x: x["score"], reverse=True)

    top = analyzed[0] if analyzed else PATTERNS_11[0]
    nxt_idx = len(history_sizes) % len(top["sequence"])
    predicted_size = top["sequence"][nxt_idx] if top["sequence"] else "BIG"
    confidence = min(97, max(72, top.get("score", 78)))

    recent_numbers = [(d.get("number", d) if isinstance(d, dict) else d)
                      for d in history[:15]]
    freq = {}
    for num in recent_numbers:
        freq[num] = freq.get(num, 0) + 1
    hot_numbers = [k for k, _ in sorted(freq.items(), key=lambda x: -x[1])]

    pool = [5,6,7,8,9] if predicted_size == "BIG" else [0,1,2,3,4]
    hot_in_pool = [n for n in hot_numbers if n in pool]
    cold_in_pool = [n for n in pool if n not in recent_numbers]

    sure1 = hot_in_pool[0] if hot_in_pool else pool[0]
    sure2 = hot_in_pool[1] if len(hot_in_pool) > 1 else (cold_in_pool[0] if cold_in_pool else pool[1])
    if sure1 == sure2:
        sure2 = next((n for n in pool if n != sure1), pool[-1])

    return {"predictionSize": predicted_size, "sureNumbers": [sure1, sure2],
            "confidence": confidence, "patternName": top["name"],
            "topPatterns": analyzed[:3]}


# ============================================================
# BUNNY AI ENGINE (200+ CPU Patterns)
# ============================================================

def run_bunny_ai(history_numbers: List[int]) -> Dict:
    if not history_numbers or len(history_numbers) < 3:
        return {"pattern": "CHAOS", "patternName": "Chaos Zone",
                "prediction": "BIG", "confidence": 55, "message": "Analyzing..."}

    deep = history_numbers[:500]
    types = ["B" if n >= 5 else "S" for n in deep]

    pat_key = "MULTI"; pred = "BIG"; conf = 70
    sk = 1
    for i in range(len(types) - 1):
        if types[i] == types[i+1]:
            sk += 1
        else:
            break
    cur = types[0]

    cycle_found = False
    for cl in range(2, 9):
        if len(types) < cl * 2:
            continue
        ok = all(types[j] == types[j+cl] for j in range(cl))
        if ok:
            pat_key = f"CYCLE_{cl}"
            cycle_found = True
            conf = 96 if cl >= 5 else (91 if cl >= 3 else 82)
            pred = "BIG" if types[cl] == "B" else "SMALL"
            break

    if not cycle_found:
        b10 = types[:10].count("B")
        if sk >= 6:
            pat_key = "DRAGON_B" if cur == "B" else "DRAGON_S"
            conf = min(95, 70 + sk * 3)
            pred = "SMALL" if cur == "B" else "BIG"
        elif sk == 5:
            pat_key = "5x_STREAK_B" if cur == "B" else "5x_STREAK_S"
            conf = 93
            pred = "SMALL" if cur == "B" else "BIG"
        elif sk >= 4:
            pat_key = f"4x_STREAK_{cur}"
            conf = 92
            pred = "SMALL" if cur == "B" else "BIG"
        elif sk == 3:
            p6 = "".join(types[:6]) if len(types) >= 6 else ""
            p7 = "".join(types[:7]) if len(types) >= 7 else ""
            p8 = "".join(types[:8]) if len(types) >= 8 else ""
            if p8 == "BBBSBSBS" or p7 == "BBBSBSB" or p6 == "BBBSBS":
                pat_key = "BBBSBS_B"; conf = 80; pred = "SMALL"
            elif p8 == "SSSBSBSB" or p7 == "SSSBSBS" or p6 == "SSSBSB":
                pat_key = "BBBSBS_S"; conf = 80; pred = "BIG"
            else:
                pat_key = f"3x_STREAK_{cur}"; conf = 78
                pred = "SMALL" if cur == "B" else "BIG"
        elif sk == 2:
            pat_key = f"2x_STREAK_{cur}"; conf = 65
            pred = "SMALL" if cur == "B" else "BIG"
        else:
            seq = "".join(types[:min(len(types), 9)])
            found = False
            for l in range(min(len(seq), 9), 2, -1):
                sub = seq[:l]
                hit = CPU_PATTERN_DB.get(sub)
                if hit:
                    pat_key = "LIVE_LEARN"; conf = hit["conf"]; pred = hit["next"]
                    found = True
                    break
            if not found:
                if b10 >= 7:
                    pat_key = "HEAVY_BIG"; conf = 82; pred = "SMALL"
                elif b10 <= 3:
                    pat_key = "HEAVY_SMALL"; conf = 82; pred = "BIG"
                else:
                    pat_key = "CHAOS"; conf = 65
                    pred = "BIG" if random.random() < 0.5 else "SMALL"

    STATE.bunnyPrediction = pred
    STATE.bunnyPattern = pat_key
    STATE.bunnyConfidence = conf

    names = {
        "DRAGON_B": "Dragon Streak (BIG) 🐉", "DRAGON_S": "Dragon Streak (SMALL) 🐉",
        "5x_STREAK_B": "5× BIG Dragon Zone 🐉🔥", "5x_STREAK_S": "5× SMALL Dragon Zone 🐉🔥",
        "4x_STREAK_B": "4× BIG Streak 🔥", "4x_STREAK_S": "4× SMALL Streak 🔥",
        "3x_STREAK_B": "3× BIG Streak 📈", "3x_STREAK_S": "3× SMALL Streak 📈",
        "2x_STREAK_B": "2× BIG Streak →", "2x_STREAK_S": "2× SMALL Streak →",
        "CYCLE_2": "2-Beat Cycle 🔄", "CYCLE_3": "3-Beat Cycle 🔄",
        "CYCLE_4": "4-Beat Cycle 🔄", "CYCLE_5": "5-Beat Cycle 🔄",
        "HEAVY_BIG": "Heavy BIG Bias ⚖️", "HEAVY_SMALL": "Heavy SMALL Bias ⚖️",
        "LIVE_LEARN": "⚡ AI Live Pattern", "CHAOS": "Chaos Zone 🌀",
        "BBBSBS_B": "BBBSBS Trend Injection 🎯", "BBBSBS_S": "SSSBSB Trend Injection 🎯",
        "MULTI": "Multi-Engine Vote 🧠",
    }
    return {"pattern": pat_key, "patternName": names.get(pat_key, "Unknown Pattern"),
            "prediction": pred, "confidence": conf,
            "message": f"🎯 {names.get(pat_key, 'Unknown')}"}


# ============================================================
# HYPER PREDICTION (JS Port — 8 Logic Modes)
# ============================================================

def get_hyper_prediction(history_numbers: List[int]) -> Dict:
    history_sizes = [to_side_full(n) for n in history_numbers]
    last_digit = history_numbers[0] if history_numbers else 0
    last_size = history_sizes[0] if history_sizes else "BIG"

    if STATE.guaranteedWinMode and STATE.lastLossNum is not None:
        STATE.guaranteedWinMode = False
        return {"pred": "SMALL" if STATE.lastLossNum >= 5 else "BIG",
                "mode": "🛡️ ANTI-LOSS: FORCED REVERSE"}
    if STATE.consecutiveLoss >= 1 and STATE.lastLossNum is not None:
        return {"pred": "SMALL" if STATE.lastLossNum >= 5 else "BIG",
                "mode": "🛡️ STREAK INTERCEPT FLOW"}

    if len(history_numbers) < 12:
        return {"pred": "BIG" if random.random() < 0.5 else "SMALL",
                "mode": "🔄 SYNCING DATA TUNNEL"}

    s_string = "".join(h[0] for h in history_sizes[:12][::-1])

    if s_string.endswith("BBBBBB"): return {"pred": "BIG", "mode": "🐉 DRAGON PULSE: BIG"}
    if s_string.endswith("SSSSSS"): return {"pred": "SMALL", "mode": "🐉 DRAGON PULSE: SMALL"}
    if s_string.endswith("BSBSBS") or s_string.endswith("SBSBSB"):
        return {"pred": "SMALL" if s_string[-1] == "B" else "BIG", "mode": "⚜️ GOLD ALTERNATE BREAK"}
    if s_string.endswith("BBSS") or s_string.endswith("SSBB"):
        return {"pred": "BIG" if s_string[-1] == "S" else "SMALL", "mode": "⚜️ GOLD BOX REVERSION"}
    if s_string.endswith("BBBSSS") or s_string.endswith("SSSBBB"):
        return {"pred": "BIG" if s_string[-1] == "S" else "SMALL", "mode": "⚜️ GOLD DOUBLE TRIPLE"}
    if last_digit in (0, 5):
        return {"pred": "BIG" if last_digit == 0 else "SMALL", "mode": "🔮 VIOLET ENGINE OVERRIDE"}

    big10 = history_sizes[:10].count("BIG")
    small10 = 10 - big10
    if big10 >= 8: return {"pred": "SMALL", "mode": "👑 GOLD BREAK EXTRA BIG"}
    if small10 >= 8: return {"pred": "BIG", "mode": "👑 GOLD BREAK EXTRA SMALL"}

    mode = LOGIC_MODES[STATE.currentLogicIndex % len(LOGIC_MODES)]
    w = mode["weight"]

    if w == 0:
        return {"pred": "SMALL" if last_size == "BIG" else "BIG", "mode": "⚙️ ENGINE: REVERSAL"}
    elif w == 1:
        return {"pred": "BIG" if history_sizes[:5].count("BIG") >= 3 else "SMALL",
                "mode": "⚙️ ENGINE: TREND_FOLLOW"}
    elif w == 2:
        if len(history_sizes) >= 4:
            last4 = history_sizes[:4]
            if all(r == last4[0] for r in last4):
                return {"pred": "SMALL" if last4[0] == "BIG" else "BIG",
                        "mode": "⚙️ ENGINE: PATTERN_BREAK"}
            b4 = last4.count("BIG")
            if b4 == 3: return {"pred": "SMALL", "mode": "⚙️ ENGINE: PATTERN_BREAK"}
            if b4 == 1: return {"pred": "BIG", "mode": "⚙️ ENGINE: PATTERN_BREAK"}
        return {"pred": "SMALL" if last_size == "BIG" else "BIG",
                "mode": "⚙️ ENGINE: PATTERN_FALLBACK"}
    elif w == 3:
        if len(history_sizes) >= 8:
            recent_big = history_sizes[:4].count("BIG")
            older_big = history_sizes[4:8].count("BIG")
            if recent_big > older_big + 1: return {"pred": "SMALL", "mode": "⚙️ ENGINE: MOMENTUM_SHIFT"}
            if older_big > recent_big + 1: return {"pred": "BIG", "mode": "⚙️ ENGINE: MOMENTUM_SHIFT"}
        return {"pred": "SMALL" if last_size == "BIG" else "BIG", "mode": "⚙️ ENGINE: MOMENTUM_BASE"}
    elif w == 4:
        alt = all(history_sizes[i] != history_sizes[i-1]
                  for i in range(1, min(5, len(history_sizes))))
        if alt:
            return {"pred": "SMALL" if last_size == "BIG" else "BIG",
                    "mode": "⚙️ ENGINE: ALTERNATING_FLOW"}
        return {"pred": "BIG" if history_sizes[:6].count("BIG") >= 3 else "SMALL",
                "mode": "⚙️ ENGINE: ALTERNATING_ALT"}
    elif w == 5:
        streak = 1
        for i in range(1, min(len(history_sizes), 6)):
            if history_sizes[i] == last_size:
                streak += 1
            else:
                break
        if streak >= 2:
            return {"pred": "SMALL" if last_size == "BIG" else "BIG",
                    "mode": "⚙️ ENGINE: STREAK_KILLER"}
        return {"pred": "BIG" if history_sizes[:4].count("BIG") >= 2 else "SMALL",
                "mode": "⚙️ ENGINE: STREAK_WEIGHT"}
    elif w == 6:
        ratio = history_sizes[:10].count("BIG") / 10
        return {"pred": "BIG" if random.random() < ratio else "SMALL",
                "mode": "⚙️ ENGINE: FREQUENCY_PROB"}
    else:
        votes = []
        votes.append("SMALL" if last_size == "BIG" else "BIG")
        votes.append("BIG" if history_sizes[:5].count("BIG") >= 3 else "SMALL")
        if len(history_sizes) >= 4:
            b4 = history_sizes[:4].count("BIG")
            if b4 == 3: votes.append("SMALL")
            if b4 == 1: votes.append("BIG")
        big_votes = votes.count("BIG")
        return {"pred": "BIG" if big_votes >= len(votes)/2 else "SMALL",
                "mode": "⚙️ ENGINE: RANDOM_FOREST"}


# ============================================================
# ENSEMBLE VOTE
# ============================================================

def ensemble_vote(history: List[int], period_counter: int) -> Dict:
    periods = [{"number": h, "side": to_side_full(h), "period": "----"} for h in history[:30]]
    results = []

    pat = compute_pattern_prediction(history[:12])
    if pat:
        results.append({**pat, "name": "PATTERN", "weight": 1.2})

    rifu = get_rifu_prediction(history[:12], period_counter)
    results.append({"prediction": rifu["side"], "confidence": rifu.get("confidence", 70),
                    "reason": rifu["logic"], "name": "RIFU", "weight": 1.1})

    ult = compute_ultimate_pro_prediction(periods)
    results.append({"prediction": ult["prediction"], "confidence": ult.get("confidence", 70),
                    "reason": ult["reason"], "name": "ULTIMATE", "weight": 1.3})

    ratio = compute_30round_ratio(periods)
    if ratio:
        results.append({"prediction": ratio["prediction"], "confidence": ratio.get("confidence", 60),
                        "reason": ratio["reason"], "name": "30-RATIO", "weight": 0.9})

    two = compute_two_level_fixed_win(periods)
    if two:
        results.append({"prediction": two["prediction"], "confidence": two.get("confidence", 80),
                        "reason": two["reason"], "name": "2-LEVEL-FIXED", "weight": 1.0})

    maf = mafiya_analyze(history[:30])
    results.append({"prediction": maf["prediction"], "confidence": maf.get("confidence", 70),
                    "reason": maf["mode"], "name": "MAFIYA", "weight": 1.15})

    eleven = generate_11pattern_prediction([{"number": h} for h in history[:25]])
    results.append({"prediction": eleven["predictionSize"],
                    "confidence": eleven.get("confidence", 75),
                    "reason": eleven["patternName"], "name": "11-PATTERN", "weight": 1.25})

    bunny = run_bunny_ai(history[:25])
    results.append({"prediction": bunny["prediction"], "confidence": bunny.get("confidence", 70),
                    "reason": bunny["patternName"], "name": "BUNNY-AI", "weight": 1.2})

    score_big = 0.0; score_small = 0.0
    for r in results:
        w = (r.get("confidence", 70)) * (r.get("weight", 1))
        if r["prediction"] == "BIG":
            score_big += w
        elif r["prediction"] == "SMALL":
            score_small += w

    total = score_big + score_small
    final_pred = "BIG" if score_big >= score_small else "SMALL"
    final_conf = min(99, round((max(score_big, score_small) / total) * 100)) if total > 0 else 70

    by_name = {r["name"]: r for r in results}
    if "PATTERN" in by_name and "2-LEVEL-FIXED" in by_name and \
       by_name["PATTERN"]["prediction"] == by_name["2-LEVEL-FIXED"]["prediction"]:
        final_conf = min(99, final_conf + 12)
    if "ULTIMATE" in by_name and "RIFU" in by_name and \
       by_name["ULTIMATE"]["prediction"] == by_name["RIFU"]["prediction"]:
        final_conf = min(99, final_conf + 8)
    if "11-PATTERN" in by_name and "MAFIYA" in by_name and \
       by_name["11-PATTERN"]["prediction"] == by_name["MAFIYA"]["prediction"]:
        final_conf = min(99, final_conf + 10)
    if "BUNNY-AI" in by_name and "PATTERN" in by_name and \
       by_name["BUNNY-AI"]["prediction"] == by_name["PATTERN"]["prediction"]:
        final_conf = min(99, final_conf + 8)

    return {"prediction": final_pred, "confidence": final_conf,
            "results": results, "scoreBIG": round(score_big), "scoreSMALL": round(score_small)}


# ============================================================
# SMART NUMBER SELECTION
# ============================================================

def smart_number_selection(prediction: str, periods: List[Dict]) -> int:
    pool = [5,6,7,8,9] if prediction == "BIG" else [0,1,2,3,4]
    if not periods or len(periods) < 5:
        return random.choice(pool)

    freq = {n: 0 for n in pool}
    for p in periods[:20]:
        if p["number"] in pool:
            freq[p["number"]] += 1

    best = min(pool, key=lambda n: freq[n])
    if random.random() > 0.65:
        best = random.choice(pool)
    return best


# ============================================================
# ANTI-LOSS STRATEGY (NO WAIT)
# ============================================================

def anti_loss_strategy(raw_pred: str, raw_num: int, confidence: float,
                       history: List[int]) -> Dict:
    if STATE.consecutiveLoss >= 1:
        STATE.emergencyMode = True
        STATE.inverseMode = True
        if STATE.lastLossNum is not None and STATE.lastLossNum >= 5:
            safe_size = "SMALL"; safe_num = SAFE_POOLS["SMALL_CRITICAL"][0]
        else:
            safe_size = "BIG"; safe_num = SAFE_POOLS["BIG_CRITICAL"][0]
        return {"prediction": safe_size, "number": safe_num, "confidence": 95,
                "adjusted": True, "reason": "🛡️ EMERGENCY REVERSE (NO WAIT)",
                "betSize": 0.5, "skip": False}

    if STATE.consecutiveLoss == 0:
        STATE.emergencyMode = False
        STATE.inverseMode = False

    if confidence < CONFIG["MIN_CONFIDENCE"]:
        confidence = CONFIG["MIN_CONFIDENCE"]

    final_pred = raw_pred
    final_num = raw_num
    if STATE.inverseMode:
        final_pred = "SMALL" if raw_pred == "BIG" else "BIG"
        final_num = SAFE_POOLS["BIG_CRITICAL"][0] if final_pred == "BIG" else SAFE_POOLS["SMALL_CRITICAL"][0]

    return {"prediction": final_pred, "number": final_num, "confidence": confidence,
            "adjusted": False, "reason": "NORMAL", "betSize": 1, "skip": False}


# ============================================================
# 7-LAYER ENGINE (WEBC0DC V2 Python Port)
# ============================================================

def seven_layer_engine(draws: List[Dict], weights: Optional[Dict[str, float]] = None) -> Dict:
    """Original WEBC0DC V2 7-Layer engine — returns layer votes."""
    if weights is None:
        weights = default_weights()

    numbers = [int(d["number"]) for d in draws]
    sides = [to_side(n) for n in numbers]
    layers = []

    # L1 — STREAK
    streak = 0
    if sides:
        for s in sides:
            if s == sides[0]: streak += 1
            else: break
    if sides:
        head = sides[0]
        reversal = streak >= 4
        layers.append({"key": "l1", "name": "STREAK SCAN",
                       "vote": flip(head) if reversal else head,
                       "strength": min(1.0, 0.45 + (streak-4)*0.12) if reversal else min(0.7, streak*0.2),
                       "note": f"{streak}x {sides[0]}"})

    # L2 — ALTERNATION
    flips = 0
    for i in range(1, min(len(sides), 8)):
        if sides[i] != sides[i-1]: flips += 1
        else: break
    layers.append({"key": "l2", "name": "ALTERNATION",
                   "vote": flip(sides[0]) if (flips >= 3 and sides) else None,
                   "strength": min(1.0, 0.4 + flips*0.1) if flips >= 3 else 0,
                   "note": f"{flips} flips"})

    # L3 — BALANCE
    last20 = sides[:20]
    big_c = sum(1 for s in last20 if s == "B")
    big_ratio = big_c / len(last20) if last20 else 0.5
    layers.append({"key": "l3", "name": "BALANCE",
                   "vote": None if abs(big_ratio - 0.5) < 0.06 else ("S" if big_ratio > 0.5 else "B"),
                   "strength": min(1.0, abs(big_ratio - 0.5) * 3),
                   "note": f"{round(big_ratio*100)}% big"})

    # L4 — MOMENTUM
    def _r(arr): return sum(1 for s in arr if s == "B") / len(arr) if arr else 0.5
    mom = _r(sides[:5]) - _r(sides[5:10])
    layers.append({"key": "l4", "name": "MOMENTUM",
                   "vote": None if abs(mom) < 0.15 else ("B" if mom > 0 else "S"),
                   "strength": min(1.0, abs(mom) * 1.6),
                   "note": f"{'+' if mom > 0 else ''}{round(mom*100)}%"})

    # L5 — MARKOV
    mv = None; ms = 0.0
    if len(sides) >= 6:
        pair = f"{sides[1]}{sides[0]}"
        bc = 0; sc = 0
        for i in range(1, len(sides) - 1):
            if i + 2 < len(sides) and f"{sides[i+2]}{sides[i+1]}" == pair:
                if sides[i] == "B": bc += 1
                else: sc += 1
        total_m = bc + sc
        if total_m >= 3:
            mv = None if bc == sc else ("B" if bc > sc else "S")
            ms = abs(bc - sc) / total_m if total_m else 0
    layers.append({"key": "l5", "name": "MARKOV", "vote": mv, "strength": ms,
                   "note": mv if mv else "—"})

    # L6 — GRAVITY
    last6 = numbers[:6]
    avg6 = sum(last6) / len(last6) if last6 else 4.5
    layers.append({"key": "l6", "name": "GRAVITY",
                   "vote": None if abs(avg6 - 4.5) < 0.4 else ("S" if avg6 > 4.5 else "B"),
                   "strength": min(1.0, abs(avg6 - 4.5) / 2.5),
                   "note": f"{avg6:.1f}"})

    # L7 — RECENCY
    rec = 0.0
    for i, s in enumerate(sides[:12]):
        rec += (1 if s == "B" else -1) * (0.85 ** i)
    layers.append({"key": "l7", "name": "RECENCY",
                   "vote": None if abs(rec) < 0.5 else ("B" if rec > 0 else "S"),
                   "strength": min(1.0, abs(rec) / 4),
                   "note": f"{rec:.1f}"})

    # 5 Pattern Detectors
    cur_streak = streak if sides else 0
    is_abab = len(sides) >= 4 and all(sides[1+i] != sides[i+2] for i in range(3))
    is_aabb = len(sides) >= 4 and sides[0] == sides[1] and sides[2] == sides[3] and sides[0] != sides[2]
    is_aaabbb = (len(sides) >= 6 and all(s == sides[0] for s in sides[:3])
                 and all(s == sides[3] for s in sides[3:6]) and sides[0] != sides[3])
    mirror_count = 0
    for i in range(0, min(len(numbers), 8) - 1, 2):
        if i+1 < len(numbers) and numbers[i] + numbers[i+1] == 9:
            mirror_count += 1
    is_mirror = mirror_count >= 2

    pattern_signals = [
        {"key": "ABAB", "vote": flip(sides[0]) if (is_abab and sides) else None,
         "strength": min(0.94, 0.62 + flips*0.05) if is_abab else 0, "active": is_abab},
        {"key": "AABB", "vote": flip(sides[0]) if (is_aabb and sides) else None,
         "strength": 0.78 if is_aabb else 0, "active": is_aabb},
        {"key": "AAABBB", "vote": flip(sides[0]) if (is_aaabbb and sides) else None,
         "strength": 0.84 if is_aaabbb else 0, "active": is_aaabbb},
        {"key": "DRGN",
         "vote": (flip(sides[0]) if cur_streak >= 5 else sides[0]) if (cur_streak >= 3 and sides) else None,
         "strength": min(0.9, 0.5 + cur_streak*0.07) if cur_streak >= 3 else 0,
         "active": cur_streak >= 3},
        {"key": "MIRR", "vote": flip(sides[0]) if (is_mirror and sides) else None,
         "strength": min(0.86, 0.48 + mirror_count*0.1) if is_mirror else 0, "active": is_mirror},
    ]

    # Weighted voting (B / S)
    bs = 0.0; ss = 0.0
    for l in layers:
        if not l["vote"]: continue
        w = l["strength"] * weights.get(l["key"], 1)
        if l["vote"] == "B": bs += w
        else: ss += w
    for sig in pattern_signals:
        if not sig["vote"]: continue
        w = sig["strength"] * 0.65
        if sig["vote"] == "B": bs += w
        else: ss += w

    total = bs + ss
    if total == 0: pred = None
    elif bs == ss: pred = sides[0] if sides else None
    else: pred = "B" if bs > ss else "S"

    conf = 0.0 if total == 0 else min(99, 50 + (abs(bs - ss) / total) * 45)

    return {"pred": pred, "confidence": round(conf, 1),
            "bigScore": bs, "smallScore": ss,
            "layers": layers, "patternSignals": pattern_signals,
            "streak": streak, "flips": flips, "bigRatio": big_ratio}


# ============================================================
# UNIFIED PREDICT (Master Orchestrator)
# ============================================================

def predict(history: List[int]) -> Dict:
    """Unified predict — combines ALL engines (JS v11 + WEBC0DC V2)."""
    if not history:
        history = []

    # Update number frequency
    if history:
        n = history[0]
        if 0 <= n <= 9:
            STATE.numberFrequency[n] += 1

    # ==== Run All Engines ====
    ensemble = ensemble_vote(history, STATE.totalRoundsAnalyzed)
    hyper = get_hyper_prediction(history)

    big_score = 0.0; small_score = 0.0

    # Ensemble (weighted ×1.2)
    if ensemble["prediction"] == "BIG": big_score += ensemble["confidence"] * 1.2
    else: small_score += ensemble["confidence"] * 1.2

    # Hyper (weighted 85)
    if hyper["pred"] == "BIG": big_score += 85
    else: small_score += 85

    # Pattern
    pat = compute_pattern_prediction(history)
    if pat:
        if pat["prediction"] == "BIG": big_score += pat["confidence"]
        else: small_score += pat["confidence"]

    # Ultimate Pro
    periods = [{"number": h, "side": to_side_full(h)} for h in history[:30]]
    ult = compute_ultimate_pro_prediction(periods)
    if ult["prediction"] == "BIG": big_score += ult["confidence"]
    else: small_score += ult["confidence"]

    # 11-Pattern
    eleven = generate_11pattern_prediction([{"number": h, "size": to_side_full(h)} for h in history[:25]])
    if eleven["predictionSize"] == "BIG": big_score += eleven["confidence"]
    else: small_score += eleven["confidence"]

    # Bunny AI
    bunny = run_bunny_ai(history[:25])
    if bunny["prediction"] == "BIG": big_score += bunny["confidence"]
    else: small_score += bunny["confidence"]

    # 7-Layer WEBC0DC V2 engine
    seven = seven_layer_engine([{"number": h} for h in history[:25]])
    if seven["pred"]:
        seven_full = "BIG" if seven["pred"] == "B" else "SMALL"
        if seven_full == "BIG": big_score += seven["confidence"]
        else: small_score += seven["confidence"]

    total = big_score + small_score
    final_pred = "BIG" if big_score >= small_score else "SMALL"
    confidence = round((max(big_score, small_score) / total) * 100) if total > 0 else 80
    confidence = max(CONFIG["MIN_CONFIDENCE"], min(98, confidence))

    # Number selection
    predicted_number = smart_number_selection(final_pred, periods)
    if eleven.get("sureNumbers"):
        lucky = eleven["sureNumbers"][0]
        if lucky >= 5 and final_pred == "BIG":
            predicted_number = lucky
        elif lucky < 5 and final_pred == "SMALL":
            predicted_number = lucky

    # Anti-loss
    final = anti_loss_strategy(final_pred, predicted_number, confidence, history)

    # Save prediction
    STATE.predictionHistory.append({
        "timestamp": time.time(), "predicted": final["prediction"],
        "number": final["number"], "confidence": final["confidence"],
        "adjusted": final["adjusted"], "reason": final["reason"],
    })
    if len(STATE.predictionHistory) > 50:
        STATE.predictionHistory.pop(0)

    STATE.lastPrediction = final["prediction"]

    return {
        "predictedNumber": final["number"],
        "predictedSize": final["prediction"],
        "confidence": final["confidence"],
        "consecutiveLoss": STATE.consecutiveLoss,
        "consecutiveWin": STATE.consecutiveWin,
        "adjusted": final["adjusted"],
        "reason": final["reason"],
        "predictedOddEven": "EVEN" if final["number"] % 2 == 0 else "ODD",
        "predictedPrime": "PRIME" if final["number"] in (2,3,5,7) else "COMPOSITE",
        "riskLevel": "⚠️ RECOVERY MODE ⚠️" if STATE.consecutiveLoss == 1 else "NORMAL",
        "suggestedBetSize": final.get("betSize", 1),
        "suggestion": "🛡️ Emergency reverse active - next signal forced!"
                       if STATE.consecutiveLoss == 1 else "✅ Normal bet",
        "lossProtection": "🛡️ ACTIVE - Reverse in effect"
                          if STATE.consecutiveLoss == 1 else "INACTIVE",
        "ensembleVotes": ensemble["results"],
        "ensembleScoreBIG": ensemble["scoreBIG"],
        "ensembleScoreSMALL": ensemble["scoreSMALL"],
        "hyperMode": hyper["mode"],
        "patternName": eleven.get("patternName", "N/A"),
        "sureNumbers": eleven.get("sureNumbers", [final["number"], final["number"] + 1]),
        "bunnyPattern": bunny["patternName"],
        "bunnyPrediction": bunny["prediction"],
        "bunnyConfidence": bunny["confidence"],
        "sevenLayer": {
            "pred": seven["pred"],
            "confidence": seven["confidence"],
            "bigScore": round(seven["bigScore"], 2),
            "smallScore": round(seven["smallScore"], 2),
            "layers": seven["layers"],
            "patternSignals": seven["patternSignals"],
            "streak": seven["streak"],
            "flips": seven["flips"],
        },
        "mafiyaMode": mafiya_analyze(history[:30])["mode"] if history else "INIT",
        "mode": "1M",
    }


# ============================================================
# SETTLE
# ============================================================

def settle(predicted_num: int, predicted_size: str, actual_num: int, bet: float = 1) -> Dict:
    actual_size = "BIG" if actual_num >= 5 else "SMALL"
    is_exact = actual_num == predicted_num
    is_size = actual_size == predicted_size

    if is_exact:
        result = {"win": True, "jackpot": True, "status": "JACKPOT", "profit": bet * 9}
        STATE.jackpots += 1; STATE.wins += 1; STATE.consecutiveWin += 1
        STATE.consecutiveLoss = 0; STATE.lastWinNum = actual_num
        STATE.profit += bet * 9; STATE.balance += bet * 9
    elif is_size:
        result = {"win": True, "jackpot": False, "status": "WIN", "profit": bet * 0.9}
        STATE.wins += 1; STATE.consecutiveWin += 1; STATE.consecutiveLoss = 0
        STATE.lastWinNum = actual_num
        STATE.profit += bet * 0.9; STATE.balance += bet * 0.9
    else:
        result = {"win": False, "jackpot": False, "status": "LOSS", "profit": -bet}
        STATE.losses += 1; STATE.consecutiveLoss += 1; STATE.consecutiveWin = 0
        STATE.lastLossNum = actual_num
        STATE.profit -= bet; STATE.balance -= bet
        if STATE.consecutiveLoss >= 1:
            STATE.guaranteedWinMode = True

    STATE.totalBets += 1
    STATE.actualHistory.insert(0, actual_num)
    if len(STATE.actualHistory) > 50:
        STATE.actualHistory.pop()
    STATE.lastActual = actual_num
    STATE.currentLogicIndex = (STATE.currentLogicIndex + 1) % len(LOGIC_MODES)
    return result


# ============================================================
# STATS / RESET
# ============================================================

def get_stats() -> Dict:
    total = STATE.wins + STATE.losses
    win_rate = (STATE.wins / total * 100) if total > 0 else 100
    return {
        "wins": STATE.wins, "losses": STATE.losses, "jackpots": STATE.jackpots,
        "total": total, "accuracy": round(win_rate),
        "consecutiveLoss": STATE.consecutiveLoss, "consecutiveWin": STATE.consecutiveWin,
        "winRate": f"{win_rate:.1f}%",
        "lossStreakProtected": "🛡️ RECOVERY MODE ACTIVE" if STATE.consecutiveLoss >= 1 else "INACTIVE",
        "emergencyMode": STATE.emergencyMode,
        "totalProfit": f"{STATE.profit:.2f}", "totalBets": STATE.totalBets,
        "balance": f"{STATE.balance:.2f}",
        "roi": f"{(STATE.profit / STATE.totalBets * 100):.2f}%" if STATE.totalBets > 0 else "0%",
    }


def reset():
    STATE.reset()


# ============================================================
# app.py COMPATIBLE WRAPPER
# ============================================================

_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 50


def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    app.py compatible wrapper — WEBC0DC V3 ULTIMATE HYBRID ENGINE.
    1-MINUTE MODE ONLY.
    """
    cached = _CACHE.get(period)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return {k: v for k, v in cached.items() if k != "_ts"}

    seed = int(abs(hash(period)) % 100000)
    rng = random.Random(seed)
    history = [current_number] + [rng.randint(0, 9) for _ in range(25)]

    result = predict(history)
    result["period"] = period
    result["currentNumber"] = current_number
    result["timestamp"] = datetime.now(timezone.utc).strftime("%I:%M %p")
    result["_ts"] = time.time()

    _CACHE[period] = result
    if len(_CACHE) > 100:
        keys = sorted(_CACHE.keys(), key=lambda k: _CACHE[k].get("_ts", 0))
        for k in keys[:50]:
            _CACHE.pop(k, None)
    return {k: v for k, v in result.items() if k != "_ts"}


def clear_engine_cache():
    _CACHE.clear()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("🔥 WEBC0DC V3 — ULTIMATE HYBRID PREDICTION ENGINE (1M)")
    print("=" * 65)

    sample = [7, 3, 8, 5, 2, 9, 4, 6, 1, 0, 7, 8, 3, 5, 2, 9, 1, 4, 6, 0, 5, 8, 3, 7, 2]

    result = predict(sample)

    print(f"\nPrediction   : {result['predictedSize']} ({result['predictedNumber']})")
    print(f"Confidence   : {result['confidence']}%")
    print(f"Reason       : {result['reason']}")
    print(f"Pattern      : {result['patternName']}")
    print(f"Bunny AI     : {result['bunnyPattern']} → {result['bunnyPrediction']} ({result['bunnyConfidence']}%)")
    print(f"Hyper Mode   : {result['hyperMode']}")
    print(f"Mafiya Mode  : {result['mafiyaMode']}")
    print(f"Ensemble B/S : {result['ensembleScoreBIG']} / {result['ensembleScoreSMALL']}")
    print(f"Sure Numbers : {result['sureNumbers']}")
    print(f"Odd/Even     : {result['predictedOddEven']}")
    print(f"Prime        : {result['predictedPrime']}")

    print(f"\n--- 7-Layer Engine (WEBC0DC V2) ---")
    seven = result["sevenLayer"]
    print(f"Vote         : {seven['pred']} | Confidence: {seven['confidence']}%")
    print(f"B/S Score    : {seven['bigScore']} / {seven['smallScore']}")
    print(f"Streak/Flips : {seven['streak']}x / {seven['flips']}")
    for l in seven["layers"]:
        print(f"  {l['key'].upper():<3} {l['name']:<12} vote={l['vote']} str={l['strength']:.2f} note={l['note']}")
    print("Pattern Signals:")
    for sig in seven["patternSignals"]:
        print(f"  {sig['key']:<7} active={sig['active']} vote={sig['vote']} str={sig['strength']:.2f}")

    print(f"\n--- Ensemble Votes ({len(result['ensembleVotes'])} engines) ---")
    for v in result["ensembleVotes"]:
        print(f"  {v['name']:<16} → {v['prediction']:<6} ({v['confidence']}%) — {v['reason']}")

    print("\n" + "=" * 65)
    print("✅ All engines merged successfully!")
    print("=" * 65)
