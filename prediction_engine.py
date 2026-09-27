"""
Prediction Engine — NAVEEN AI TOOL 2026
----------------------------------------
SUJAL NUMBER HACK 2.0 — 20-Module Master Predictive Ensemble
HTML logic 100% ported to Python.
Purana prediction logic 100% REMOVED.
"""

import requests
import time
import random
import math
from typing import Dict, List, Optional


# ============================================================
# 🔑 API CONFIG (Same as HTML)
# ============================================================
API_PRIMARY  = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1m-1000"
API_FALLBACK = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hgnice.biz"
}

# ============================================================
# 🗄️ INTERNAL CACHE — 50 sec TTL
# ============================================================
_ENGINE_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 50

# ============================================================
# 🧠 GLOBAL STATE (Same as HTML)
# ============================================================
_consecutive_losses = 0
_last_failed_predicted_size: Optional[str] = None
_last_observed_period: Optional[str] = None
_current_prediction: Optional[dict] = None
_jackpots_count = 0


# ============================================================
# 📚 CONSTANTS (HTML 100% EXACT)
# ============================================================
B_POOL = [5, 6, 7, 8, 9]   # BIG numbers
S_POOL = [0, 1, 2, 3, 4]   # SMALL numbers

PATTERN_RULES = {
    'BBBSBB': 'SMALL', 'SSBS': 'BIG', 'BSBSBS': 'SMALL',
    'BBBSSS': 'BIG', 'SSSBBSS': 'BIG', 'BBBSSBB': 'SMALL',
    'SSBBS': 'BIG', 'BSSBB': 'BIG', 'SBBSS': 'SMALL',
    'BBSSB': 'BIG', 'SSS': 'BIG', 'SBB': 'BIG',
    'BSSBSS': 'SMALL', 'BBB': 'SMALL', 'BSBB': 'BIG',
    'BSBS': 'SMALL', 'SBSB': 'BIG', 'BBSS': 'BIG',
    'SSBB': 'SMALL', 'BSBSB': 'SMALL', 'SBSBS': 'BIG'
}

FIBONACCI_SERIES = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]


# ============================================================
# 🛠️ MATH HELPERS (HTML 100% EXACT)
# ============================================================
def sizeOf(n: int) -> str:
    """HTML: parseInt(n, 10) >= 5 ? 'BIG' : 'SMALL'"""
    return 'BIG' if int(n) >= 5 else 'SMALL'


def mean(arr: List[float]) -> float:
    return sum(arr) / len(arr) if arr else 0.0


def stdDev(arr: List[float]) -> float:
    if not arr:
        return 1.0
    m = mean(arr)
    variance = mean([(x - m) ** 2 for x in arr])
    sd = math.sqrt(variance)
    return sd if sd > 0 else 1.0


def calcEMA(arr: List[float], period: int) -> float:
    """HTML calcEMA exact port"""
    if not arr:
        return 0.0
    k = 2 / (period + 1)
    val = arr[0]
    for i in range(1, len(arr)):
        val = arr[i] * k + val * (1 - k)
    return val


# ============================================================
# 🧮 MARKOV TRANSITION TENSOR (HTML 100% EXACT)
# ============================================================
def calc_markov_score(chronological_rows: List[dict], target_digit: int, order: int) -> float:
    """HTML calcMarkovScore exact port"""
    if len(chronological_rows) <= order:
        return 0.0

    n = len(chronological_rows)
    key = '|'.join(str(r['number']) for r in chronological_rows[n - order:])

    count = 0
    support = 0
    for i in range(order, n):
        prev_key = '|'.join(str(r['number']) for r in chronological_rows[i - order:i])
        if prev_key == key:
            support += 1
            if chronological_rows[i]['number'] == target_digit:
                count += 1

    return (count / support) if support else 0.0


# ============================================================
# 🔮 20-MODULE MASTER PREDICTIVE ENSEMBLE (HTML 100% EXACT)
# ============================================================
def execute_deep_causal_pipeline(raw_list: List[dict]) -> dict:
    """
    HTML executeDeepCausalPipeline() ka 100% EXACT port.
    raw_list: newest first (same as HTML API response order)
    """
    global _consecutive_losses, _last_failed_predicted_size

    if not raw_list or len(raw_list) < 10:
        return {
            'size': 'BIG',
            'primary': 7,
            'opposite': 2,
            'conf': '98.5',
            'level': 1,
            'reason': 'Syncing Model Kernel'
        }

    # Chronological order: index 0 = oldest, index len-1 = latest
    chronological = list(reversed(raw_list))
    n = len(chronological)
    latest = chronological[n - 1]
    prev = chronological[n - 2] if n >= 2 else latest
    old = chronological[n - 4] if n >= 4 else prev

    nums = [r['number'] for r in chronological]
    sizes = [r['size'] for r in chronological]
    recent_sizes_desc = list(reversed(sizes))  # index 0 = newest

    big_score = 0.0
    sml_score = 0.0
    digit_scores = [0.0] * 10
    reasons = []

    def vote(side: str, weight: float, label: str):
        nonlocal big_score, sml_score
        if side == 'BIG':
            big_score += weight
        else:
            sml_score += weight
        reasons.append(label)

    # ---- M01: Raw Modulo & Parity Momentum ----
    vote('BIG' if latest['number'] >= 5 else 'SMALL', 10, 'Parity Momentum')

    # ---- M02: Dual Delta Dynamics ----
    d1 = latest['number'] - prev['number']
    d2 = latest['number'] - old['number']
    if d1 != 0:
        vote('BIG' if d1 > 0 else 'SMALL', 12, 'Dual Delta')

    # ---- M03: Extended Fibonacci Modulo ----
    fib_val = FIBONACCI_SERIES[n % len(FIBONACCI_SERIES)] % 10
    vote('BIG' if fib_val >= 5 else 'SMALL', 10, 'Fibonacci Resonance')

    # ---- M04: Triple EMA Crossover (EMA-3 vs EMA-20) ----
    ema3 = calcEMA(nums, 3)
    ema20 = calcEMA(nums, 20)
    vote('BIG' if ema3 >= ema20 else 'SMALL', 14, 'EMA Crossover')

    # ---- M05: Dragon Streak & Follow-Through Guard ----
    streak = 1
    for i in range(1, len(recent_sizes_desc)):
        if recent_sizes_desc[i] == recent_sizes_desc[0]:
            streak += 1
        else:
            break

    if streak >= 5:
        vote(recent_sizes_desc[0], 26, f'Dragon Follow {streak}x')
    elif streak >= 3:
        vote(recent_sizes_desc[0], 15, f'Streak Momentum {streak}x')
    else:
        vote('SMALL' if recent_sizes_desc[0] == 'BIG' else 'BIG', 12, 'Alternation Shift')

    # ---- M06: Markov Transition Tensor (1st, 2nd, 3rd Order) ----
    best_markov_digit = 7
    max_markov_score = -1.0
    for d in range(10):
        m1 = calc_markov_score(chronological, d, 1)
        m2 = calc_markov_score(chronological, d, 2)
        m3 = calc_markov_score(chronological, d, 3)
        combined = m1 * 0.5 + m2 * 0.3 + m3 * 0.2
        digit_scores[d] += combined * 25
        if combined > max_markov_score:
            max_markov_score = combined
            best_markov_digit = d

    vote('BIG' if best_markov_digit >= 5 else 'SMALL', 18, f'Markov Tensor (#{best_markov_digit})')

    # ---- M07: Fourier Spectral Harmonic Phase ----
    fourier_phase = math.atan2(d1, max(1, abs(d2)))
    vote('BIG' if fourier_phase >= 0 else 'SMALL', 12, 'Fourier Harmonic')

    # ---- M08: RSI-14 Multi-Scale Momentum ----
    gains = []
    losses = []
    for i in range(1, min(15, len(nums))):
        diff = nums[len(nums) - i] - nums[len(nums) - i - 1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = mean(gains)
    avg_loss = mean(losses) if losses else 1.0
    rsi14 = 100 - (100 / (1 + (avg_gain / avg_loss)))
    if rsi14 >= 68:
        vote('SMALL', 15, 'RSI Overbought')
    elif rsi14 <= 32:
        vote('BIG', 15, 'RSI Oversold')

    # ---- M09: Bayesian Prior Estimation ----
    recent50_mean = mean(nums[-50:])
    vote('BIG' if recent50_mean < 4.5 else 'SMALL', 12, 'Bayesian Equilibrium')

    # ---- M10: Monte Carlo Drift (2,500 Iterations) ----
    sigma = stdDev(nums[-30:])
    above_count = 0
    trials = 2500
    for _ in range(trials):
        simulated = latest['number'] + ((random.random() - 0.5) * sigma * 1.6)
        if simulated >= 4.5:
            above_count += 1

    vote('BIG' if (above_count / trials) >= 0.5 else 'SMALL', 14, 'Monte Carlo Drift')

    # ---- M11: Pattern DNA Matcher ----
    pattern_key = ''.join('B' if x == 'BIG' else 'S' for x in recent_sizes_desc[:8])
    for plen in range(8, 2, -1):
        sub = pattern_key[:plen]
        if sub in PATTERN_RULES:
            vote(PATTERN_RULES[sub], 22, f'Pattern Rule [{sub}]')
            break

    # ---- M12: Cold Number Gap Recovery ----
    gaps = [len(chronological)] * 10
    for i in range(len(chronological) - 1, -1, -1):
        num = chronological[i]['number']
        if gaps[num] == len(chronological):
            gaps[num] = len(chronological) - 1 - i

    for d in range(10):
        digit_scores[d] += (gaps[d] / max(1, len(chronological))) * 14

    # ---- M13: Mirror & Delta Projection ----
    mirror_digit = 9 - latest['number']
    digit_scores[mirror_digit] += 10

    delta_target = max(0, min(9, round(latest['number'] + d1)))
    digit_scores[delta_target] += 12

    # ---- M14: Special Violet Parity Pivot (0 & 5) ----
    if latest['number'] == 0:
        vote('BIG', 12, 'Violet 0 -> Big Pivot')
    if latest['number'] == 5:
        vote('SMALL', 12, 'Violet 5 -> Small Pivot')

    # ---- M15-M20: Level-2 Zero-Loss Inversion Shield ----
    active_level = 1
    if _consecutive_losses == 1 and _last_failed_predicted_size:
        active_level = 2
        inverted_side = 'SMALL' if _last_failed_predicted_size == 'BIG' else 'BIG'
        vote(inverted_side, 250, 'L2 ZERO-LOSS SHIELD ACTIVE')
    elif _consecutive_losses >= 2 and _last_failed_predicted_size:
        active_level = 2
        inverted_side = 'SMALL' if _last_failed_predicted_size == 'BIG' else 'BIG'
        vote(inverted_side, 500, 'L2 EMERGENCY RECOVERY OVERRIDE')

    consensus_size = 'BIG' if big_score >= sml_score else 'SMALL'

    # Rank candidate digits matching consensus size
    matching_digits = sorted(
        [{'digit': d, 'score': digit_scores[d]} for d in range(10) if sizeOf(d) == consensus_size],
        key=lambda x: x['score'],
        reverse=True
    )

    primary_candidate = matching_digits[0]['digit'] if matching_digits else (7 if consensus_size == 'BIG' else 2)

    # Opposite harmonic candidate
    opposite_pool = [0, 1, 2, 3, 4] if consensus_size == 'BIG' else [5, 6, 7, 8, 9]
    harmonic_candidate = (primary_candidate + 5) % 10
    secondary_candidate = harmonic_candidate if harmonic_candidate in opposite_pool else opposite_pool[0]

    total_votes = (big_score + sml_score) or 1
    confidence = min(99.8, max(88.5, 50 + (abs(big_score - sml_score) / total_votes) * 50))

    return {
        'size': consensus_size,
        'primary': primary_candidate,
        'opposite': secondary_candidate,
        'conf': f"{confidence:.1f}",
        'level': active_level,
        'reason': ' · '.join(reasons[-4:])
    }


# ============================================================
# 🌐 FETCH DATA (HTML 100% EXACT — Primary + Fallback)
# ============================================================
def fetch_data() -> List[dict]:
    """
    HTML pollLiveData() ka 100% port.
    Returns newest-first list.
    """
    raw_list = []

    # Try primary
    try:
        r = requests.get(API_PRIMARY, headers=HEADERS, timeout=10)
        if r.ok:
            j = r.json()
            raw_list = (j.get('data', {}) or {}).get('list') or j.get('list') or []
    except Exception as e:
        print(f"[API_PRIMARY] error: {e}")

    # Try fallback
    if not raw_list:
        try:
            r = requests.get(API_FALLBACK, headers=HEADERS, timeout=10)
            if r.ok:
                j = r.json()
                raw_list = (j.get('data', {}) or {}).get('list') or j.get('list') or []
        except Exception as e:
            print(f"[API_FALLBACK] error: {e}")

    if not isinstance(raw_list, list) or not raw_list:
        return []

    normalized = []
    for item in raw_list:
        try:
            raw_num = item.get('number', item.get('result', 0))
            num = int(raw_num)
        except (ValueError, TypeError):
            num = 0

        period = str(item.get('period') or item.get('issueNumber') or '')
        if not period:
            continue

        size_raw = item.get('size')
        size = size_raw.upper() if size_raw else ('BIG' if num >= 5 else 'SMALL')

        normalized.append({
            'period': period,
            'number': num,
            'size': size
        })

    return normalized


# ============================================================
# 🎯 RESOLUTION TRACKER (HTML handleResolution exact port)
# ============================================================
def _handle_resolution(latest_draw: dict):
    """HTML handleResolution() ka 100% port."""
    global _current_prediction, _consecutive_losses, _last_failed_predicted_size, _jackpots_count

    if not _current_prediction:
        return
    if _current_prediction.get('period') != latest_draw.get('period'):
        return

    drawn_num = latest_draw['number']
    drawn_size = latest_draw['size']

    is_jackpot = (drawn_num == _current_prediction['primary'] or
                  drawn_num == _current_prediction['opposite'])
    is_size_win = (drawn_size == _current_prediction['size'])
    is_win = is_jackpot or is_size_win

    if is_jackpot:
        _jackpots_count += 1

    if is_win:
        _consecutive_losses = 0
        _last_failed_predicted_size = None
    else:
        _consecutive_losses += 1
        _last_failed_predicted_size = _current_prediction['size']


# ============================================================
# 🔌 WRAPPER — app.py compatible
# ============================================================
def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    app.py compatible wrapper.
    SUJAL NUMBER HACK 2.0 — 20-Module Ensemble (HTML 100% port).
    """
    global _current_prediction, _last_observed_period

    # Cache check
    cached = _ENGINE_CACHE.get(period)
    if cached and (time.time() - cached.get('_ts', 0)) < _CACHE_TTL:
        return {
            'prediction': cached['prediction'],
            'bigSmall': cached['bigSmall'],
            'confidence': cached['confidence'],
            'numbers': cached['numbers'],
            'opposites': cached['opposites'],
            'steps': cached['steps'],
            'source': 'engine-cache'
        }

    # Live history
    history = fetch_data()

    if not history:
        # Fallback (same HTML pattern)
        fallback_size = 'BIG' if random.random() > 0.5 else 'SMALL'
        pool = S_POOL if fallback_size == 'BIG' else B_POOL
        pool_copy = pool[:]
        random.shuffle(pool_copy)
        fallback_opps = pool_copy[:2]
        fallback_num = fallback_opps[0] if fallback_opps else current_number

        return {
            'prediction': fallback_num,
            'bigSmall': fallback_size,
            'confidence': 55,
            'numbers': [fallback_num],
            'opposites': fallback_opps,
            'steps': ['Fallback mode (no history)'],
            'source': 'fallback'
        }

    # === Step 1: Resolve previous prediction (if period advanced) ===
    latest_draw = history[0]
    if _last_observed_period and latest_draw['period'] != _last_observed_period:
        _handle_resolution(latest_draw)

    # === Step 2: Run 20-Module Deep Causal Pipeline ===
    pred = execute_deep_causal_pipeline(history)

    # === Step 3: Compute next period ===
    try:
        next_period = str(int(latest_draw['period']) + 1)
    except (ValueError, TypeError):
        next_period = latest_draw['period']

    # === Step 4: Store current prediction for next resolution ===
    _last_observed_period = latest_draw['period']
    _current_prediction = {
        'period': next_period,
        'size': pred['size'],
        'primary': pred['primary'],
        'opposite': pred['opposite'],
        'conf': pred['conf'],
        'level': pred['level'],
        'reason': pred['reason']
    }

    final_result = {
        'prediction': pred['primary'],
        'bigSmall': pred['size'],
        'confidence': float(pred['conf']),
        'numbers': [pred['primary'], pred['opposite']],
        'opposites': [pred['opposite']],
        'level': pred['level'],
        'steps': [
            f"Period: {period}",
            f"Next Issue: {next_period}",
            f"Level: {pred['level']}",
            f"Signal: {pred['size']} ({pred['conf']}%)",
            f"Primary: #{pred['primary']}",
            f"Opposite: #{pred['opposite']}",
            f"Reason: {pred['reason']}"
        ],
        'source': 'sujal-number-hack-2.0'
    }

    # Cache save
    final_result['_ts'] = time.time()
    _ENGINE_CACHE[period] = final_result

    # Cleanup
    if len(_ENGINE_CACHE) > 100:
        sorted_keys = sorted(
            _ENGINE_CACHE.keys(),
            key=lambda k: _ENGINE_CACHE[k].get('_ts', 0),
            reverse=True
        )
        for k in sorted_keys[50:]:
            _ENGINE_CACHE.pop(k, None)

    return final_result


def clear_engine_cache():
    """Reset cache + global state"""
    global _consecutive_losses, _last_failed_predicted_size
    global _last_observed_period, _current_prediction, _jackpots_count

    _ENGINE_CACHE.clear()
    _consecutive_losses = 0
    _last_failed_predicted_size = None
    _last_observed_period = None
    _current_prediction = None
    _jackpots_count = 0
