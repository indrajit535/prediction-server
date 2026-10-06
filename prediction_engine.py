"""
CYBER TAMILAN — prediction_engine.py

Prediction engine — HTML logic transplant.

This engine is a 1:1 Python port of the JavaScript `EaglePredictionEngine`
logic found in the EAGLE SERVER standalone prediction engine.

The original Python zig-zag / normal heuristic has been completely removed
and replaced with the JavaScript Eagle Prediction Engine logic.

Ported from JS:
  - HISTORICAL_SEED           -> HISTORICAL_SEED
  - getSize()                 -> get_size()
  - getColorCategory()        -> get_color_category()
  - getNumberInfo()           -> get_number_info()
  - EaglePredictionEngine     -> EaglePredictionEngine
      - updateHistory()       -> update_history()
      - getBSHistory()        -> get_bs_history()
      - rankNumbers()         -> rank_numbers()
      - generatePairs()       -> generate_pairs()
      - checkPriority()       -> check_priority()
      - runBmwEngine()        -> run_bmw_engine()
      - predict()             -> predict()
      - evaluateResult()      -> evaluate_result()
  - createEngine()            -> create_engine()
  - quickPredict()            -> quick_predict()

This is a heuristic only; it cannot guarantee future outcomes.
"""

from __future__ import annotations

import time
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# CONFIGURATION — mirrors the HTML CONFIG block
# ============================================================

CONFIG = {
    "period_seconds": 30,                       # HTML: CONFIG.periodSeconds
    "history_url": (
        "https://draw.ar-lottery01.com/WinGo/WinGo_1M/"
        "GetHistoryIssuePage.json"
    ),
    "cache_ttl": 2,                             # HTML polls every 2000 ms
    "signal_confidence": 0.92,                  # Default confidence
    "engine_name": "EAGLE PREDICTOR",
    "engine_code": "eagle-predictor",
}


# ============================================================
# HISTORICAL SEED DATA — exact copy from JS
# ============================================================

HISTORICAL_SEED = [
    3, 8, 1, 1, 7, 1, 5, 0, 2, 2, 1, 7, 3, 3, 4, 7, 1, 5, 4, 0, 7,
    9, 7, 3, 9, 0, 5, 0, 4, 7, 7, 6, 5, 2, 1, 3, 3, 9, 4, 3, 4, 5,
    9, 9, 6, 9, 4, 4, 2, 9, 4, 5, 6, 4, 5, 1, 2, 1, 0, 8, 4, 6, 5,
    7, 4, 3, 9, 5, 9, 4, 7, 4, 6, 6, 4, 8, 8, 7, 1, 2, 0, 4, 9, 4,
    8, 6, 4, 6, 3, 5, 7, 2, 5, 3, 8, 2, 0, 8, 9, 8, 8, 6, 3, 8, 7,
    1, 5, 5, 9, 5, 1, 6, 4, 3, 7, 3, 2, 6, 6, 5, 5, 5, 9, 5, 0, 7,
    2, 3, 0, 4, 5, 7, 2, 6, 6, 7, 4, 7, 0, 2, 8, 2, 1, 9, 8, 6, 7,
    4, 2, 9, 3, 9, 8, 2, 5, 9, 4, 0, 1, 3, 2, 3, 4, 8, 9, 0, 8, 9,
    2, 3, 7, 6, 6, 1, 5, 5, 2, 9, 9, 5, 5, 3, 2, 5, 8, 9, 2, 1, 5,
    6, 5, 5, 1, 1, 9, 9, 6, 0, 5, 2, 2, 2, 6, 2, 4, 9, 4, 0, 0, 6,
    7, 4, 4, 8, 6, 4, 6, 5, 5, 8, 3, 3, 0, 2, 1, 0, 2, 3, 7, 1, 4,
    5, 2, 5, 9, 3, 5, 5, 4, 9, 2, 4, 9, 1, 9, 6, 7, 0, 3, 7, 7, 5,
    3, 8, 4, 7, 0, 0, 0, 4, 7, 4, 5, 9, 4, 6, 8, 0, 7, 3, 0, 2, 4,
    4, 2, 3, 3, 6, 8, 4, 3, 1, 5, 3, 2, 0, 3, 7, 6, 9, 7, 5, 8, 2,
    5, 3, 5, 5, 7, 8, 6, 7, 9, 4, 6, 5, 9, 8, 7, 2, 8, 1, 1, 4, 6,
    1, 3, 1, 3, 9, 0, 7, 4, 6, 7, 2, 6, 6, 1, 7, 3, 1, 4, 9, 9, 9,
    9, 6, 3, 9, 4, 9, 8, 8, 1, 0, 2, 0, 5, 4, 8, 6, 0, 4, 8, 2, 0,
    4, 0, 8, 8, 4, 9, 6, 4, 1, 4, 1, 2, 0, 7, 2, 1, 7, 5, 2, 2, 4,
    2, 1, 0, 3, 4, 5, 4, 7, 2, 5, 7, 1, 6, 3, 6, 1, 5, 5, 3, 7, 4,
    8, 1, 7, 3, 3, 0, 8, 9, 4, 7, 0, 4, 5, 2, 3, 0, 7, 3, 0, 9, 1,
    3, 5, 1, 0, 3, 2, 0, 8, 2, 8, 5, 8, 8, 7, 0, 8, 2, 6, 8, 0, 3,
    1, 8, 9, 8, 3, 8, 8, 9, 7, 2, 4, 6, 3, 4, 7, 2, 6, 8, 0, 8, 2,
    0, 8, 8, 9, 2, 2, 3, 6, 4, 4, 7, 5, 2, 4, 1, 9, 7, 9, 6, 7, 5,
    3, 1, 2, 9, 3, 8, 1, 0, 9, 6, 2, 7, 8, 9, 9, 5, 3, 0, 7, 7, 4,
    3, 6, 4, 7, 9, 5, 5, 6, 3, 3, 2, 5, 6, 5, 3, 2, 7, 0, 9, 3, 0,
    6, 4, 8, 5, 2, 8, 2, 0, 9, 0, 7, 4, 2, 9, 7, 9, 9, 7, 7, 2, 3,
    3, 2, 7, 1, 4, 2, 5, 9, 0, 0, 1, 4, 4, 8, 5, 5, 5, 0, 5, 3, 7,
    7, 3, 6, 0, 3, 1, 6, 9, 6, 8, 4, 6, 0, 5, 9, 9, 4, 7, 3, 9, 9,
    9, 5, 5, 1, 2, 9, 9, 1, 6, 9, 4, 8, 5, 4, 7, 7, 0, 7, 1, 2, 0,
    7, 9, 8, 2, 5, 6, 5, 1, 3, 7, 2, 3, 9, 2, 7, 6, 7, 9, 2, 4, 4,
    6, 2, 3, 4, 6, 2, 0, 7, 7, 7, 6, 6, 5, 3, 2, 5, 1, 8, 2, 1, 8,
    2, 0, 2, 0, 0, 9, 0, 8, 9, 7, 1, 2, 6, 8, 2, 3, 9, 3, 6, 4, 8,
    0, 3, 4, 2, 2, 5, 4, 5, 3, 2, 7, 0, 3, 1, 5, 6, 0, 0, 9, 7, 1,
    4, 6, 6, 0, 1, 0, 0, 1, 4, 6, 4, 5, 8, 9, 8, 8, 7, 6, 6, 7, 9,
    8, 1, 1, 4, 9, 2, 9, 0, 1, 7, 6, 6, 6, 6, 9, 4, 3, 7, 5, 0, 6,
    7, 8, 4, 5, 6, 9, 1, 1, 8, 2, 9, 3, 6, 8, 4, 0, 8, 7, 9, 0, 3,
    3, 5, 7, 7, 3, 8, 0, 2, 9, 3, 3, 3, 1, 1, 5, 1, 4, 2, 2, 7, 0,
    5, 9, 8, 1, 3, 6, 4, 5, 4, 8, 0, 3, 3, 6, 8, 5, 8, 4, 4, 7, 4,
    3, 1, 0, 3, 5, 0, 2, 1, 8, 7, 8, 7, 2, 6, 6, 6, 8, 8, 5, 6, 2,
    2, 4, 6, 1, 1, 1, 9, 4, 0, 5, 9, 3, 3, 1, 6, 3, 5, 1, 4, 3, 1,
    7, 5, 7, 0, 0, 2, 3, 8, 0, 8, 5, 3, 0, 9, 3, 7, 0, 5, 6, 1, 8,
    8, 2, 0, 9, 3, 4, 2, 0, 0, 0, 0, 2, 5, 3, 4, 4, 3, 4, 0, 6, 5,
    4, 4, 7, 0, 6, 5, 4, 5, 1, 8, 5, 9, 2, 7, 6, 8, 3, 2, 6, 2, 4,
    3, 2, 5, 3, 3, 6, 7, 4, 6, 2, 2, 1, 8, 7, 8, 0, 6, 3, 7, 2, 9,
    2, 9, 0, 3, 2, 3, 8, 7, 7, 5, 3, 1, 6, 8, 0, 4, 6, 0, 2, 0, 2,
    5, 6, 1, 0, 0, 6, 8, 2, 2, 2, 5, 4, 5, 8, 2, 9, 9, 1, 0, 7, 7,
    7, 5, 1, 4, 7, 5, 5, 1, 0, 1, 8, 9, 5, 9, 9, 9, 2, 0, 4, 2, 4,
    7, 9, 4, 7, 6, 5, 9, 6, 2, 7, 9, 6, 2, 0, 2, 5, 6, 1, 0, 0, 6,
    8, 2, 2, 2, 5, 4, 5, 8, 2, 9, 9, 1, 0, 7, 7, 7, 5, 1, 4, 7, 5,
    5, 1, 0, 1, 8, 9, 5, 9, 9, 9, 2, 0, 4, 2, 4, 7, 9, 4, 7, 6, 5,
    9, 6, 2, 7, 9, 6, 2, 0, 2, 5, 6, 1, 0, 0, 6, 8, 2, 2, 2, 5, 4,
    5, 8, 2, 9, 9, 1, 0, 7, 7, 7, 5, 1, 4, 7, 5, 5, 1, 0, 1, 8, 9,
    5, 9, 9, 9, 2, 0, 4, 2, 4, 7, 9, 4, 7, 6, 5, 9, 6, 2, 7, 9, 6,
    2, 0, 2, 5, 6, 1, 0, 0, 6, 8, 2, 2, 2, 5, 4, 5, 8, 2, 9, 9, 1,
    0, 7, 7, 7, 5, 1, 4, 7, 5, 5, 1, 0, 1, 8, 9, 5, 9, 9, 9, 2, 0,
    4, 2, 4, 7, 9, 4, 7, 6, 5, 9, 6, 2, 7, 9, 6, 2, 0, 2, 5, 6, 1,
    0, 0, 6, 8, 2, 2, 2, 5, 4, 5, 8, 2, 9, 9, 1, 0, 7, 7, 7, 5, 1,
    4, 7, 5, 5, 1, 0, 1, 8, 9, 5, 9, 9, 9, 2, 0, 4, 2, 4, 7, 9, 4,
    7, 6, 5, 9, 6, 2, 7, 9, 6, 2, 0, 2, 5, 6, 1, 0, 0, 6, 8, 2, 2,
    2, 5, 4, 5, 8, 2, 9, 9, 1, 0, 7, 7, 7, 5, 1, 4, 7, 5, 5, 1, 0,
    1, 8, 9, 5, 9, 9, 9, 2, 0, 4, 2, 4, 7, 9, 4, 7, 6, 5, 9, 6, 2,
    7, 9, 6
]


# ============================================================
# HELPERS — exact port from JS
# ============================================================

def get_size(num: Any) -> str:
    """
    Convert number (0-9) to BIG/SMALL
    BIG: 5-9, SMALL: 0-4
    """
    try:
        return 'BIG' if int(num) >= 5 else 'SMALL'
    except (TypeError, ValueError):
        return 'SMALL'


def get_color_category(num: Any) -> str:
    """Get color category for a number"""
    try:
        n = int(num)
    except (TypeError, ValueError):
        return 'VIOLET'
    if n in (1, 3, 7, 9):
        return 'GREEN'
    if n in (2, 4, 6, 8):
        return 'RED'
    return 'VIOLET'  # 0, 5


def get_number_info(raw_num: Any) -> Dict[str, Any]:
    """Get detailed color info (used for UI, kept for compatibility)"""
    try:
        t = abs(int(raw_num)) % 10
    except (TypeError, ValueError):
        t = 0

    size = get_size(t)

    if t == 0:
        return {
            'number': t, 'size': size, 'colorName': 'RED_VIOLET',
            'bgGradient': 'linear-gradient(135deg, #ef4444 50%, #a855f7 50%)',
            'glowColor': 'rgba(239, 68, 68, 0.6)'
        }
    if t == 5:
        return {
            'number': t, 'size': size, 'colorName': 'GREEN_VIOLET',
            'bgGradient': 'linear-gradient(135deg, #10b981 50%, #a855f7 50%)',
            'glowColor': 'rgba(16, 185, 129, 0.6)'
        }
    if t in (1, 3, 7, 9):
        return {
            'number': t, 'size': size, 'colorName': 'GREEN',
            'bgGradient': 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
            'glowColor': 'rgba(16, 185, 129, 0.7)'
        }
    return {
        'number': t, 'size': size, 'colorName': 'RED',
        'bgGradient': 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
        'glowColor': 'rgba(239, 68, 68, 0.7)'
    }


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# CORE PREDICTION ENGINE — 1:1 port of JS EaglePredictionEngine
# ============================================================

class EaglePredictionEngine:
    """
    1:1 Python port of the JavaScript EaglePredictionEngine class.
    """

    def __init__(self):
        self.last100_nums: List[int] = []
        self.trans_matrix: List[List[int]] = [[0] * 10 for _ in range(10)]
        self.freq_map: List[int] = [0] * 10

    def update_history(self, numbers_array: List[int]) -> None:
        """
        Update history with new draw numbers (newest first)
        """
        self.last100_nums = list(numbers_array[:100])
        self.trans_matrix = [[0] * 10 for _ in range(10)]
        self.freq_map = [0] * 10

        for i in range(len(self.last100_nums)):
            curr = self.last100_nums[i]
            if 0 <= curr <= 9:
                self.freq_map[curr] += 1
                if i > 0:
                    prev = self.last100_nums[i - 1]
                    if 0 <= prev <= 9:
                        self.trans_matrix[prev][curr] += 1

    def get_bs_history(self) -> List[str]:
        """Get BIG/SMALL history array"""
        return [get_size(n) for n in self.last100_nums]

    def rank_numbers(self, numbers: List[int], target_size: Optional[str] = None) -> List[int]:
        """Rank numbers by weighted score"""
        weights = []
        n_len = len(self.last100_nums) if self.last100_nums else 1

        for num in numbers:
            w = 1.0

            # Frequency weight
            w += (self.freq_map[num] / n_len) * 22

            # Recency weight
            try:
                idx = self.last100_nums.index(num)
            except ValueError:
                idx = -1

            if idx == -1:
                w += 25
            elif idx > 12:
                w += (idx - 12) * 1.2

            # Markov transition weight
            if self.last100_nums:
                last = self.last100_nums[0]
                row = self.trans_matrix[last] if last < 10 else []
                s = sum(row) if row else 0
                if s > 0:
                    w += (row[num] / s) * 35

            # Target size bias
            if target_size:
                recent15 = [get_size(n) for n in self.last100_nums[:15]]
                nums15 = self.last100_nums[:15]
                bonus = 0
                for i, n in enumerate(nums15):
                    if recent15[i] == target_size and n == num:
                        bonus += 2
                w += bonus * 1.5

            weights.append(max(0.01, w))

        # Sort by weight descending
        ranked = sorted(
            zip(numbers, weights),
            key=lambda x: x[1],
            reverse=True
        )
        return [n for n, _ in ranked]

    def generate_pairs(self, size: str) -> Dict[str, int]:
        """Generate favor + opposite pair for a target size"""
        target_pool = [5, 6, 7, 8, 9] if size == 'BIG' else [0, 1, 2, 3, 4]
        opposite_pool = [0, 1, 2, 3, 4] if size == 'BIG' else [5, 6, 7, 8, 9]

        ranked_target = self.rank_numbers(target_pool, size)
        ranked_opp = self.rank_numbers(opposite_pool, size)

        default_favor = 7 if size == 'BIG' else 2
        default_opp = 2 if size == 'BIG' else 7

        return {
            'favor': ranked_target[0] if ranked_target else default_favor,
            'opp': ranked_opp[0] if ranked_opp else default_opp
        }

    def check_priority(self) -> Dict[str, Any]:
        """
        PRIORITY PATTERN DETECTION
        Detects high-confidence patterns: streaks, palindromes, symmetry, color deficit
        """
        h = self.get_bs_history()
        if len(h) < 3:
            return {'active': False}

        # === 1. STREAK DETECTION ===
        streak = 1
        for i in range(1, len(h)):
            if h[i] == h[0]:
                streak += 1
            else:
                break

        if streak >= 4:
            if streak >= 7:
                return {
                    'active': True,
                    'size': 'SMALL' if h[0] == 'BIG' else 'BIG',
                    'pattern': 'STREAK-BREAK-7+',
                    'detail': f'{h[0]} ×{streak} → 1-BET REVERSAL',
                    'confidence': 91,
                    'lock': 'BREAK'
                }
            return {
                'active': True,
                'size': h[0],
                'pattern': f'STREAK-FOLLOW-{streak}',
                'detail': f'{h[0]} ×{streak} → CONTINUATION',
                'confidence': min(97, 83 + streak * 2.5),
                'lock': 'STREAK'
            }

        # === 2. 6-PATTERN SYMMETRY (BBSSBB) ===
        if len(h) >= 6:
            p = h[:6]
            if (p[0] == p[1] and p[2] == p[3] and p[4] == p[5] and
                    p[0] != p[2] and p[2] != p[4]):
                return {
                    'active': True,
                    'size': p[4],
                    'pattern': 'BBSS-6+ SYMMETRY',
                    'detail': f'BB-SS-BB Pattern → {p[4]} Complete',
                    'confidence': 89,
                    'lock': 'BBSS'
                }

        # === 3. ABAB PING-PONG ===
        if len(h) >= 4:
            alt = 1
            for i in range(1, len(h)):
                if h[i] != h[i - 1]:
                    alt += 1
                else:
                    break
            if alt >= 3:
                next_sz = 'SMALL' if h[0] == 'BIG' else 'BIG'
                return {
                    'active': True,
                    'size': next_sz,
                    'pattern': f'ABAB-PINGPONG-{alt}',
                    'detail': f'Alternating ×{alt} → Next {next_sz}',
                    'confidence': min(95, 84 + alt * 2),
                    'lock': 'ABAB'
                }

        # === 4. COLOR MODE (color deficit detection) ===
        if len(h) >= 8:
            flips = 0
            n = min(len(h) - 1, 8)
            for i in range(n):
                if h[i] != h[i + 1]:
                    flips += 1
            flip_ratio = flips / n if n > 0 else 0
            big_count = sum(1 for x in h[:10] if x == 'BIG')

            if flip_ratio >= 0.7 and not (big_count >= 7 or big_count <= 3):
                colors = [get_color_category(x) for x in self.last100_nums[:12]]
                counts = {'GREEN': 0, 'RED': 0, 'VIOLET': 0}
                for c in colors:
                    counts[c] = counts.get(c, 0) + 1

                expected = {'GREEN': 4.8, 'RED': 4.8, 'VIOLET': 2.4}
                deficits = {}
                for k in counts:
                    deficits[k] = (expected[k] - counts[k]) * 2

                top_color = max(deficits.items(), key=lambda x: x[1])[0]
                candidates = [n for n in range(10) if get_color_category(n) == top_color]

                if candidates:
                    pick = self.rank_numbers(candidates)[0]
                    return {
                        'active': True,
                        'size': get_size(pick),
                        'pattern': 'COLOR-MODE',
                        'detail': f'COLOR DEFICIT: {top_color} → FAVOR #{pick}',
                        'confidence': 82,
                        'lock': 'COLOR',
                        'isColor': True
                    }

        return {'active': False}

    def run_bmw_engine(self) -> Dict[str, Any]:
        """
        BMW ENGINE — Main Markov + pattern engine
        """
        h = self.get_bs_history()

        # Base probability from Markov transition matrix
        big_prob = 0.5
        small_prob = 0.5

        if self.last100_nums:
            row = self.trans_matrix[self.last100_nums[0]] if self.last100_nums[0] < 10 else []
            s = sum(row) if row else 0
            if s > 0:
                big_trans = sum(row[i] for i in range(10) if get_size(i) == 'BIG')
                big_prob = big_trans / s
                small_prob = 1 - big_prob

        dom_name = 'MARKOV-CORE'
        dom_detail = 'Markov transition matrix bias'
        bonus = 0.05
        lock_name = None

        # === MR-10 FAST (mean reversion on last 10) ===
        big_in_10 = sum(1 for x in h[:10] if x == 'BIG')
        if big_in_10 >= 8:
            small_prob += 0.22
            big_prob -= 0.22
            dom_name = 'MR-10 FAST'
            dom_detail = '10-period BIG overload → Reverting SMALL'
            bonus = 0.22
        elif big_in_10 <= 2:
            big_prob += 0.22
            small_prob -= 0.22
            dom_name = 'MR-10 FAST'
            dom_detail = '10-period SMALL overload → Reverting BIG'
            bonus = 0.22

        # === 3-CYCLE HARMONIC ===
        if len(h) >= 6 and h[0] == h[3] and h[1] == h[4] and h[2] == h[5] and h[0] != h[2]:
            if h[2] == 'BIG':
                big_prob += 0.25
            else:
                small_prob += 0.25
            lock_name = 'CYCLE-LOCK'
            dom_name = '3-CYCLE HARMONIC'
            dom_detail = f'Harmonic cycle completion → {h[2]}'
            bonus = 0.25

        # === PALINDROME-4 (ABBA) ===
        if len(h) >= 4 and h[0] == h[3] and h[1] == h[2] and h[0] != h[1]:
            next_sz = 'SMALL' if h[0] == 'BIG' else 'BIG'
            if next_sz == 'BIG':
                big_prob += 0.28
            else:
                small_prob += 0.28
            lock_name = 'PALIN-LOCK'
            dom_name = 'PALINDROME-4'
            dom_detail = f'Mirror symmetry (1:2:1) → {next_sz}'
            bonus = 0.28

        # === TWIN / TRIPLET PATTERN ANALYSIS ===
        runs = []
        for i in range(min(len(h), 16)):
            if runs and runs[-1]['s'] == h[i]:
                runs[-1]['n'] += 1
            else:
                runs.append({'s': h[i], 'n': 1})

        # Twin 2-2 symmetry
        if len(runs) >= 4 and sum(1 for r in runs[:4] if r['n'] == 2) >= 3:
            first = runs[0]
            is_complete = first['n'] == 1
            if is_complete:
                next_sz = first['s']
            else:
                next_sz = 'SMALL' if first['s'] == 'BIG' else 'BIG'
            if next_sz == 'BIG':
                big_prob += 0.24
            else:
                small_prob += 0.24
            dom_name = 'TWIN 2-2 SYMMETRY'
            dom_detail = f"BB-SS Twin chain ({'Complete' if is_complete else 'New pair'}) → {next_sz}"
            bonus = 0.24
            if is_complete:
                lock_name = 'TWIN-LOCK'

        # Triplet 3-3
        if len(runs) >= 3:
            top3 = runs[:3]
            if sum(1 for r in top3 if r['n'] == 3) >= 2 and top3[0]['n'] <= 3:
                if top3[0]['n'] == 3:
                    next_sz = 'SMALL' if top3[0]['s'] == 'BIG' else 'BIG'
                    if next_sz == 'BIG':
                        big_prob += 0.26
                    else:
                        small_prob += 0.26
                    lock_name = 'TRIPLET-LOCK'
                    dom_name = 'TRIPLET 3-3'
                    dom_detail = f'Triplet street complete → Flip {next_sz}'
                    bonus = 0.26
                else:
                    if top3[0]['s'] == 'BIG':
                        big_prob += 0.26
                    else:
                        small_prob += 0.26
                    dom_name = 'TRIPLET 3-3'
                    dom_detail = f"Building triplet → Sustain {top3[0]['s']}"
                    bonus = 0.26

        # === ORACLE 1000 (historical seed correlation) ===
        if len(h) >= 4:
            last3 = list(reversed(h[:3]))
            seed_bs = [get_size(x) for x in HISTORICAL_SEED]
            big_after = 0
            small_after = 0
            for i in range(len(seed_bs) - 3):
                if (seed_bs[i] == last3[0] and
                        seed_bs[i + 1] == last3[1] and
                        seed_bs[i + 2] == last3[2]):
                    if seed_bs[i + 3] == 'BIG':
                        big_after += 1
                    else:
                        small_after += 1
            total = big_after + small_after
            if total >= 10:
                ratio = max(big_after, small_after) / total
                if ratio >= 0.58:
                    next_sz = 'BIG' if big_after >= small_after else 'SMALL'
                    if next_sz == 'BIG':
                        big_prob += 0.25
                    else:
                        small_prob += 0.25
                    if bonus < 0.25:
                        dom_name = 'ORACLE 1000'
                        dom_detail = f'Historical seed correlation: {round(ratio * 100)}% ({total}×) → {next_sz}'
                        bonus = 0.25
                        lock_name = 'ORACLE-LOCK'

        # Normalize
        total = max(0.01, big_prob + small_prob)
        big_prob /= total
        small_prob = 1 - big_prob

        size = 'BIG' if big_prob >= small_prob else 'SMALL'
        gap = abs(big_prob - small_prob)
        conf = min(97, max(76, round(75 + gap * 45 + (6 if bonus > 0.2 else 2))))

        return {
            'size': size,
            'conf': conf,
            'domName': dom_name,
            'domDetail': dom_detail,
            'lockName': lock_name
        }

    def predict(self) -> Dict[str, Any]:
        """
        MAIN PREDICT METHOD
        Returns full prediction object
        """
        # Priority pattern check first
        priority = self.check_priority()

        if priority.get('active') and priority.get('size'):
            pairs = self.generate_pairs(priority['size'])
            is_color = priority.get('isColor', False)
            return {
                'size': priority['size'],
                'confidence': priority.get('confidence', 88),
                'nums': [pairs['favor'], pairs['opp']],
                'favNum': pairs['favor'],
                'oppNum': pairs['opp'],
                'patternName': priority.get('pattern', 'PRIORITY-SIG'),
                'patternDetail': priority.get('detail', 'High confidence pattern match'),
                'engine': 'COLOR' if is_color else 'PRIORITY',
                'lockName': priority.get('lock')
            }

        # Fallback to BMW engine
        bmw = self.run_bmw_engine()
        pairs = self.generate_pairs(bmw['size'])

        return {
            'size': bmw['size'],
            'confidence': bmw['conf'],
            'nums': [pairs['favor'], pairs['opp']],
            'favNum': pairs['favor'],
            'oppNum': pairs['opp'],
            'patternName': bmw['domName'],
            'patternDetail': bmw['domDetail'],
            'engine': 'BMW',
            'lockName': bmw['lockName']
        }

    def evaluate_result(self, prediction: Dict[str, Any], actual_num: int) -> str:
        """
        Evaluate an actual result against a prediction
        Returns: 'JACKPOT' | 'WIN' | 'LOSS'
        """
        actual_size = get_size(actual_num)
        is_jackpot = (actual_num == prediction['favNum'] or actual_num == prediction['oppNum'])
        if is_jackpot:
            return 'JACKPOT'
        if actual_size == prediction['size']:
            return 'WIN'
        return 'LOSS'


# ============================================================
# CONVENIENCE API (factory-style usage)
# ============================================================

def create_engine() -> EaglePredictionEngine:
    """Create a new engine instance"""
    return EaglePredictionEngine()


def quick_predict(history_array: Optional[List[int]] = None) -> Dict[str, Any]:
    """One-shot prediction with default seed history"""
    engine = EaglePredictionEngine()
    engine.update_history(history_array if history_array else HISTORICAL_SEED)
    return engine.predict()


# ============================================================
# PROXY CHAIN — exact same four entries as the HTML PROXIES array
# ============================================================

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


# ============================================================
# INTERNAL MUTABLE STATE
# ============================================================

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


# ============================================================
# HTTP FETCH
# ============================================================

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
    Fetch the latest issue list from the WinGo history endpoint
    with the same 4-proxy fallback chain.
    """
    global _last_fetch_ts, _last_fetch_list

    now = time.time()
    if _last_fetch_list and (now - _last_fetch_ts) < CONFIG["cache_ttl"]:
        return _last_fetch_list

    direct_url = f"{CONFIG['history_url']}?ts={int(now * 1000)}"

    for proxy in PROXIES:
        url = proxy(direct_url)
        body = _http_get(url)
        if not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue

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


# ============================================================
# ENGINE PRO — main prediction tick using EaglePredictionEngine
# ============================================================

def _grade_previous(issue: str, latest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Grade the previous prediction against the actual result.
    Returns a popup payload when the previous prediction wins (or jackpots).
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
    Main engine tick using the EaglePredictionEngine logic.

    Fetches history, grades previous prediction, and runs the
    EaglePredictionEngine to generate the next signal.
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

    # ---- Run the EaglePredictionEngine on live history ----
    # Extract numbers from the fetched history (newest first)
    numbers = []
    for item in list_[:100]:
        n = _to_int(item.get("number") or item.get("openCode") or item.get("winNumber"))
        numbers.append(n)

    # If we have enough live numbers, use them; otherwise fall back to seed
    if len(numbers) >= 10:
        engine = EaglePredictionEngine()
        engine.update_history(numbers)
        prediction = engine.predict()
    else:
        # Not enough live data — use HISTORICAL_SEED
        prediction = quick_predict(HISTORICAL_SEED)

    # Extract the prediction values
    trend = prediction["size"]
    n1 = prediction["nums"][0] if prediction["nums"] else 7
    n2 = prediction["nums"][1] if len(prediction["nums"]) > 1 else 2

    _current_active = {
        "period": next_period,
        "size": trend,
        "n1": n1,
        "n2": n2,
        "confidence": prediction["confidence"],
        "patternName": prediction["patternName"],
        "patternDetail": prediction["patternDetail"],
        "engine": prediction["engine"],
        "lockName": prediction.get("lockName"),
    }
    _pred_state["step"] = _pred_state["lossCount"] + 1

    _last_processed = issue

    result["active"] = dict(_current_active)
    result["confidence"] = prediction["confidence"] / 100.0
    result["engine"] = {
        "name": CONFIG["engine_name"],
        "code": CONFIG["engine_code"],
    }
    return result


# ============================================================
# TIMER — port of the HTML countdown / ring logic
# ============================================================

def update_timer() -> Dict[str, Any]:
    """
    Returns the remaining seconds and the ring fraction for drawing.
    """
    now = int(time.time())
    rem = CONFIG["period_seconds"] - (now % CONFIG["period_seconds"])
    return {
        "secondsLeft": rem,
        "periodSeconds": CONFIG["period_seconds"],
        "ringFraction": rem / CONFIG["period_seconds"],
    }


# ============================================================
# STATS
# ============================================================

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


# ============================================================
# PUBLIC API
# ============================================================

def sddgamer263_predict() -> Dict[str, Any]:
    """
    Run one engine tick and return the full state dict.

    This is the main entry point. Callers typically invoke it once per
    second (or once per period boundary) to obtain:

        {
          "ok":            bool,
          "issue":         str,
          "nextPeriod":    str,
          "active":        {"period", "size", "n1", "n2", ...} | None,
          "popup":         win/jackpot payload | None,
          "confidence":    float,
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


# ============================================================
# CLI / SELF-TEST
# ============================================================

if __name__ == "__main__":
    reset()
    print("Testing prediction_engine.py (EAGLE Predictor port) ...\n")

    # ---- Test the core engine standalone ----
    print("=== Core Engine Test (using HISTORICAL_SEED) ===")
    engine = create_engine()
    engine.update_history(HISTORICAL_SEED)
    result = engine.predict()
    print(f"Prediction: size={result['size']} nums={result['nums']} "
          f"conf={result['confidence']}% pattern={result['patternName']}")
    print(f"Detail: {result['patternDetail']}")
    print(f"Engine: {result['engine']}  Lock: {result.get('lockName')}")

    # Simulate a result
    actual = 7
    verdict = engine.evaluate_result(result, actual)
    print(f"Test actual={actual} → {verdict}\n")

    # ---- Test the live engine ----
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
                    f"tick {i}: issue={out['issue']} "
                    f"next={out['nextPeriod']} "
                    f"signal={active['size']} "
                    f"[{active['n1']} & {active['n2']}] "
                    f"conf={int(out['confidence']*100)}% "
                    f"pattern={active.get('patternName', 'N/A')} "
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
