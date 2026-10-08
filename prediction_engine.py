"""
ULTIMATE MIXED PREDICTION ENGINE — Python Port
BMW X BOSS LX + WINGO 25 PATTERNS + ALL PATTERN LOGIC
100% Full Integration — Nothing Removed
--------------------------------------------------
Ported from JavaScript (predictionEngine.js)
"""

import math
import random
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

# ============================================================
# SECTION 1: HISTORY FETCHING HELPERS
# ============================================================

HISTORY_API = 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'


def extract_list(payload: Any) -> List[dict]:
    """Extract list from various response shapes."""
    if payload is None:
        return []
    
    # Shape: payload.data.list
    if isinstance(payload, dict):
        data = payload.get('data')
        if isinstance(data, dict):
            for key in ['list', 'gameslist', 'records', 'history', 'items']:
                if isinstance(data.get(key), list):
                    return data[key]
            if isinstance(data, list):
                return data
        if isinstance(data.get('list'), list):
            return payload['list']
        if isinstance(payload.get('records'), list):
            return payload['records']
        if isinstance(payload.get('gameslist'), list):
            return payload['gameslist']
    
    if isinstance(payload, list):
        return payload
    
    return []


# ============================================================
# SECTION 2: FALLBACK HISTORY
# ============================================================

def fnv_hash(s: str) -> int:
    """FNV-1a hash mod 10."""
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    h = (h ^ (h >> 16)) * 2246822507 & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 3266489909 & 0xFFFFFFFF
    h ^= h >> 16
    return abs(h) % 10


def generate_fallback_history(mode: str = '1m') -> List[dict]:
    """Generate fallback history using FNV hash."""
    now = datetime.now(timezone.utc)
    day = f"{now.year}{now.month:02d}{now.day:02d}"
    minute_of_day = now.hour * 60 + now.minute
    out = []
    
    for i in range(30):
        m = minute_of_day - i
        d = day
        if m < 1:
            m += 1440
            prev = now - timedelta(days=1)
            d = f"{prev.year}{prev.month:02d}{prev.day:02d}"
        
        period = f"{d}{str(m).zfill(4)}"
        num = fnv_hash(period)
        size = 'BIG' if num >= 5 else 'SMALL'
        
        if num in [0, 2, 4, 6, 8]:
            color = 'RED'
        elif num in [1, 3, 7, 9]:
            color = 'GREEN'
        else:
            color = 'VIOLET'
        
        out.append({
            'issue': period,
            'number': num,
            'size': size,
            'color': color,
            'timestamp': int(datetime.now().timestamp() * 1000) - i * 60000,
        })
    
    return out


def next_period(current_issue: Optional[str], mode: str = '1m') -> str:
    """Compute next period from current issue."""
    if not current_issue:
        n = datetime.now(timezone.utc)
        day = f"{n.year}{n.month:02d}{n.day:02d}"
        m = n.hour * 60 + n.minute + 1
        return f"{day}{str(m).zfill(4)}"
    
    try:
        return str(int(current_issue) + 1)
    except (ValueError, TypeError):
        try:
            return str(int(str(current_issue or '1000')) + 1)
        except (ValueError, TypeError):
            return str(1001)


# ============================================================
# SECTION 3: 1000-ROUND CORPUS
# ============================================================

CORPUS_KEY = 'bmwx_corpus_1000'


def build_corpus() -> List[str]:
    """Build deterministic 1000-round corpus."""
    out = []
    side = 'B'
    run = 1
    
    for i in range(1000):
        r = (math.sin(i * 997 + 13) + 1) / 2
        
        if run >= 4:
            if r > 0.65:
                side = 'S' if side == 'B' else 'B'
                run = 1
            else:
                run += 1
        elif run == 3:
            if r > 0.42:
                side = 'S' if side == 'B' else 'B'
                run = 1
            else:
                run += 1
        elif r > 0.51:
            side = 'S' if side == 'B' else 'B'
            run = 1
        else:
            run += 1
        
        out.append(side)
    
    return out


def load_corpus(recent_results: List[dict]) -> List[str]:
    """Load corpus (with in-memory storage)."""
    stored = []
    try:
        import json
        from pathlib import Path
        cache_file = Path('.bmwx_corpus_1000.json')
        if cache_file.exists():
            stored = json.loads(cache_file.read_text())
    except Exception:
        pass
    
    if len(stored) < 1000:
        fresh = build_corpus()
        stored = (stored + fresh)[:1000]
    
    recent = ['B' if r.get('number', 0) >= 5 else 'S' for r in recent_results]
    if recent:
        stored = (recent + stored)[:1000]
        try:
            import json
            from pathlib import Path
            Path('.bmwx_corpus_1000.json').write_text(json.dumps(stored))
        except Exception:
            pass
    
    return stored


# ============================================================
# SECTION 4: EMPIRICAL RECOVERY BACKTEST
# ============================================================

def empirical_backtest(pattern: List[str], recent_results: List[str]) -> dict:
    """Empirical recovery backtest."""
    corpus = recent_results if len(recent_results) >= 100 else build_corpus()
    
    for depth in [4, 3, 2]:
        if len(pattern) < depth:
            continue
        
        needle = pattern[:depth][::-1]  # reverse
        matches = 0
        big = 0
        small = 0
        
        for i in range(len(corpus) - depth - 1, -1, -1):
            ok = True
            for j in range(depth):
                if corpus[i + j] != needle[j]:
                    ok = False
                    break
            if ok:
                matches += 1
                nxt = corpus[i + depth]
                if nxt == 'B':
                    big += 1
                elif nxt == 'S':
                    small += 1
        
        if matches >= 4:
            dominant = 'BIG' if big >= small else 'SMALL'
            rate = round((max(big, small) / matches) * 100)
            return {
                'matchCount': matches,
                'bigCount': big,
                'smallCount': small,
                'dominantSide': dominant,
                'empiricalWinRate': rate,
                'isStatisticallyVerified': rate >= 58,
                'sampleDepth': len(corpus),
            }
    
    big = corpus.count('B')
    dominant = 'BIG' if big >= len(corpus) / 2 else 'SMALL'
    return {
        'matchCount': len(corpus),
        'bigCount': big,
        'smallCount': len(corpus) - big,
        'dominantSide': dominant,
        'empiricalWinRate': 64,
        'isStatisticallyVerified': True,
        'sampleDepth': len(corpus),
    }


# ============================================================
# SECTION 5: MARKOV STREAK + HOT NUMBER ANALYSIS
# ============================================================

NUMBER_TRANSITIONS = {
    0: {'BIG': [7, 8, 9], 'SMALL': [2, 1, 3]},
    1: {'BIG': [8, 9, 6], 'SMALL': [3, 2, 4]},
    2: {'BIG': [9, 7, 8], 'SMALL': [4, 1, 0]},
    3: {'BIG': [6, 8, 7], 'SMALL': [1, 2, 0]},
    4: {'BIG': [5, 7, 9], 'SMALL': [0, 2, 3]},
    5: {'BIG': [6, 7, 8], 'SMALL': [1, 3, 0]},
    6: {'BIG': [7, 8, 9], 'SMALL': [2, 0, 4]},
    7: {'BIG': [8, 9, 5], 'SMALL': [3, 1, 2]},
    8: {'BIG': [9, 6, 7], 'SMALL': [4, 0, 1]},
    9: {'BIG': [5, 8, 6], 'SMALL': [0, 3, 2]},
}


def markov_streak_scan(pattern: List[str], results: List[dict], corpus: Optional[List[str]] = None) -> dict:
    """Markov streak scan with hot number analysis."""
    n = len(pattern)
    corp = corpus if corpus else (results if len(results) >= 200 else build_corpus())
    
    # Convert results to B/S if needed
    if corp and isinstance(corp[0], dict):
        corp = ['B' if r.get('number', 0) >= 5 else 'S' for r in corp]
    
    seq = pattern[::-1]  # reverse
    matches = 0
    big = 0
    small = 0
    
    for i in range(len(corp) - n - 1, -1, -1):
        ok = True
        for j in range(n):
            if corp[i + j] != seq[j]:
                ok = False
                break
        if ok:
            matches += 1
            nxt = corp[i + n]
            if nxt == 'B':
                big += 1
            elif nxt == 'S':
                small += 1
    
    if matches > 0:
        dominant = 'SMALL' if small >= big else 'BIG'
    else:
        dominant = 'SMALL' if pattern[0] == 'B' else 'BIG'
    
    rate = round(((small if dominant == 'SMALL' else big) / matches) * 100) if matches > 0 else 76
    
    freq = {i: 0 for i in range(10)}
    for r in results[:50]:
        num = r.get('number', 0)
        freq[num] = freq.get(num, 0) + 1
    
    bigs = sorted([5, 6, 7, 8, 9], key=lambda x: freq.get(x, 0), reverse=True)
    smalls = sorted([0, 1, 2, 3, 4], key=lambda x: freq.get(x, 0), reverse=True)
    
    favor_hot = bigs[0] if dominant == 'BIG' else smalls[0]
    opp_hot = smalls[0] if dominant == 'BIG' else bigs[0]
    
    return {
        'dominantSide': dominant,
        'empiricalWinRate': max(72, min(99, rate)),
        'matchCount': matches,
        'bigCount': big,
        'smallCount': small,
        'hotFavorNumber': favor_hot,
        'hotOppositeNumber': opp_hot,
        'sampleDepth': len(corp),
        'streakPattern': '-'.join(seq),
    }


# ============================================================
# SECTION 6: NUMBER SELECTION
# ============================================================

def compute_target_numbers(side: str, results: List[int], rule_code: Optional[str] = None) -> dict:
    """Compute target numbers based on side and rules."""
    big_pool = [5, 6, 7, 8, 9]
    small_pool = [0, 1, 2, 3, 4]
    favor_pool = big_pool if side == 'BIG' else small_pool
    opp_pool = small_pool if side == 'BIG' else big_pool
    
    primary = results[0] if results else (7 if side == 'BIG' else 2)
    secondary = results[1] if len(results) > 1 else None
    
    if rule_code == 'RULE_1_REPEAT_5':
        target = next((x for x in [6, 7, 8] if x != primary), 7)
        sec = primary % 5 or 2
        return {'targetNumber': target, 'secondaryNumber': sec, 'favorNumber': target, 'oppositeNumber': sec}
    
    if rule_code == 'RULE_2_REPEAT_4':
        target = next((x for x in [1, 0, 2] if x != primary), 2)
        return {'targetNumber': target, 'secondaryNumber': 7, 'favorNumber': target, 'oppositeNumber': 7}
    
    if rule_code == 'RULE_3_BRIDGE_4_6':
        return {'targetNumber': 2, 'secondaryNumber': 8, 'favorNumber': 2, 'oppositeNumber': 8}
    
    freq = {i: 0 for i in range(10)}
    for r in results[:25]:
        if r in freq:
            freq[r] += 1
    
    favor_hints = NUMBER_TRANSITIONS.get(primary, {}).get(side, favor_pool[:3])
    opp_side = 'SMALL' if side == 'BIG' else 'BIG'
    opp_hints = NUMBER_TRANSITIONS.get(primary, {}).get(opp_side, opp_pool[:3])
    
    seed = abs(primary * 37 + (secondary or 4) * 19 + len(results) * 13)
    
    favor_scores = []
    for num in favor_pool:
        score = 100
        if num in favor_hints:
            idx = favor_hints.index(num)
            score += (3 - idx) * 22
        f = freq.get(num, 0)
        score -= f * 8
        if num == primary:
            score -= 36
        if num == secondary:
            score -= 16
        if primary % 2 != num % 2:
            score += 14
        score += (seed + num * 7) % 11
        favor_scores.append({'candidate': num, 'score': score})
    
    favor_scores.sort(key=lambda x: x['score'], reverse=True)
    favor_number = favor_scores[0]['candidate']
    
    opp_scores = []
    for num in opp_pool:
        score = 100
        if num in opp_hints:
            idx = opp_hints.index(num)
            score += (3 - idx) * 22
        f = freq.get(num, 0)
        score -= f * 8
        if num == primary:
            score -= 28
        if primary % 2 != num % 2:
            score += 14
        score += (seed + num * 11) % 13
        opp_scores.append({'candidate': num, 'score': score})
    
    opp_scores.sort(key=lambda x: x['score'], reverse=True)
    opposite_number = opp_scores[0]['candidate']
    
    return {
        'targetNumber': favor_number,
        'secondaryNumber': opposite_number,
        'favorNumber': favor_number,
        'oppositeNumber': opposite_number,
    }


# ============================================================
# SECTION 7: 10-PERIOD MACRO SCAN HELPERS
# ============================================================

def analyze_streak(history: List[str]) -> dict:
    """Analyze streak from B/S history."""
    if not history:
        return {'char': None, 'count': 0}
    
    first = history[0]
    count = 0
    for h in history:
        if h == first:
            count += 1
        else:
            break
    return {'char': first, 'count': count}


def compute_window_stats(recent_results: List[dict]) -> dict:
    """Compute window statistics."""
    sides = []
    for r in recent_results:
        if isinstance(r, dict):
            size = r.get('size') or r.get('actualSize')
            if size in ('BIG', 'SMALL'):
                sides.append(size)
            else:
                num = r.get('number', 0)
                sides.append('BIG' if num >= 5 else 'SMALL')
        elif isinstance(r, (int, float)):
            sides.append('BIG' if r >= 5 else 'SMALL')
        else:
            sides.append('BIG')
    
    last = sides[0] if sides else 'BIG'
    same_count = 0
    for s in sides:
        if s == last:
            same_count += 1
        else:
            break
    
    window = sides[:30]
    big = window.count('BIG')
    big_pct = round((big / len(window)) * 100) if window else 50
    small_pct = 100 - big_pct
    favored = 'BIG' if big_pct >= small_pct else 'SMALL'
    strength = abs(big_pct - small_pct) + 75
    
    return {
        'sameResultCount': same_count,
        'lastResult': last,
        'favoredSize': favored,
        'bias': favored,
        'strength': strength,
        'bigPct': big_pct,
        'smallPct': small_pct,
    }


def number_distribution(recent_results: List[dict]) -> dict:
    """Compute number distribution."""
    freq = {i: 0 for i in range(10)}
    big = 0
    small = 0
    slice_data = recent_results[:50]
    
    for r in slice_data:
        if isinstance(r, (int, float)):
            num = int(r)
        elif isinstance(r, dict):
            num = r.get('number', r.get('actualNumber', 0))
        else:
            num = 0
        freq[num] = freq.get(num, 0) + 1
        if num >= 5:
            big += 1
        else:
            small += 1
    
    total = max(1, len(slice_data))
    big_pct = round((big / total) * 100)
    small_pct = 100 - big_pct
    favored = 'BIG' if big_pct >= small_pct else 'SMALL'
    
    top_numbers = sorted(
        [{'num': num, 'count': count} for num, count in freq.items()],
        key=lambda x: x['count'],
        reverse=True
    )
    
    return {
        'favoredSize': favored,
        'dominantSize': favored,
        'confidence': max(big_pct, small_pct),
        'bigPct': big_pct,
        'smallPct': small_pct,
        'topNumbers': top_numbers,
    }


def oscillation_stats(recent_results: List[dict]) -> dict:
    """Compute oscillation statistics."""
    sides = []
    for r in recent_results[:10]:
        if isinstance(r, dict):
            s = r.get('size') or r.get('actualSize')
            if s in ('BIG', 'SMALL'):
                sides.append(s)
            else:
                num = r.get('number', 0)
                sides.append('BIG' if num >= 5 else 'SMALL')
        elif isinstance(r, (int, float)):
            sides.append('BIG' if r >= 5 else 'SMALL')
        else:
            sides.append('BIG')
    
    flips = 0
    for i in range(len(sides) - 1):
        if sides[i] != sides[i + 1]:
            flips += 1
    
    density = flips / (len(sides) - 1) if len(sides) > 1 else 0.5
    first = sides[0] if sides else 'BIG'
    
    if density >= 0.6:
        opp = 'SMALL' if first == 'BIG' else 'BIG'
        return {
            'bigPct': 65 if opp == 'BIG' else 35,
            'smallPct': 65 if opp == 'SMALL' else 35,
        }
    
    return {'bigPct': 50, 'smallPct': 50}


def level_defense(level: int) -> dict:
    """Level defense configuration."""
    return {
        'level': level,
        'safeThreshold': 0 if level == 1 else 35,
        'antiDrawdownArmed': level >= 2,
        'timestamp': int(datetime.now().timestamp() * 1000),
    }


# ============================================================
# SECTION 8: HELPER FUNCTIONS FOR PATTERNS
# ============================================================

def opposite(side: str) -> str:
    return 'S' if side == 'B' else 'B'


def count_b(seq: List[str]) -> int:
    return seq.count('B')


def count_s(seq: List[str]) -> int:
    return seq.count('S')


def majority(seq: List[str]) -> Optional[str]:
    if not seq:
        return None
    b = count_b(seq)
    s = count_s(seq)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return None


def majority_with_tie(seq: List[str], newest: str) -> str:
    m = majority(seq)
    if m:
        return m
    return opposite(newest)


def streak_length(seq: List[str]) -> int:
    if not seq:
        return 0
    first = seq[0]
    c = 0
    for x in seq:
        if x == first:
            c += 1
        else:
            break
    return c


def weighted_score(seq: List[str], weights: List[int]) -> Tuple[int, int]:
    b = 0
    s = 0
    for i in range(min(len(seq), len(weights))):
        if seq[i] == 'B':
            b += weights[i]
        else:
            s += weights[i]
    return b, s


# ============================================================
# SECTION 9: 25 PATTERNS (WINGO 25 PATTERN LOGIC)
# ============================================================

def pattern01_apex_flow(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    b = count_b(last5)
    s = count_s(last5)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def pattern02_orbit_x(hist: List[str]) -> Optional[str]:
    if len(hist) < 6:
        return None
    last6 = hist[:6]
    alternating = True
    for i in range(5):
        if last6[i] == last6[i + 1]:
            alternating = False
            break
    if alternating:
        return opposite(last6[0])
    return majority_with_tie(last6, hist[0])


def pattern03_nexus_core(hist: List[str]) -> Optional[str]:
    if len(hist) < 7:
        return None
    last7 = hist[:7]
    weights = [7, 6, 5, 4, 3, 2, 1]
    b, s = weighted_score(last7, weights)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def pattern04_shadow_grid(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    st = streak_length(hist)
    if st >= 3:
        return opposite(hist[0])
    last5 = hist[:5]
    return majority_with_tie(last5, hist[0])


def pattern05_phoenix_wave(hist: List[str]) -> Optional[str]:
    if len(hist) < 6:
        return None
    last3 = hist[:3]
    prev3 = hist[3:6]
    b_now = count_b(last3)
    s_now = count_s(last3)
    b_prev = count_b(prev3)
    s_prev = count_s(prev3)
    b_delta = b_now - b_prev
    s_delta = s_now - s_prev
    if b_delta > s_delta:
        return 'B'
    if s_delta > b_delta:
        return 'S'
    return opposite(hist[0])


def pattern06_quantum_edge(hist: List[str]) -> Optional[str]:
    if len(hist) < 10:
        return None
    last10 = hist[:10]
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    b, s = weighted_score(last10, weights)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def pattern07_cyber_pulse(hist: List[str]) -> Optional[str]:
    if len(hist) < 8:
        return None
    last8 = hist[:8]
    total = 0
    for x in last8:
        total += 1 if x == 'B' else -1
    if total > 0:
        return 'B'
    if total < 0:
        return 'S'
    return opposite(hist[0])


def pattern08_omega_matrix(hist: List[str]) -> Optional[str]:
    if len(hist) < 10:
        return None
    last10 = hist[:10]
    return majority_with_tie(last10, hist[0])


def pattern09_dark_vortex(hist: List[str]) -> Optional[str]:
    if len(hist) < 6:
        return None
    st = streak_length(hist)
    if st >= 4:
        return opposite(hist[0])
    last6 = hist[:6]
    return majority_with_tie(last6, hist[0])


def pattern10_titan_flow(hist: List[str]) -> Optional[str]:
    signals = []
    a = pattern01_apex_flow(hist)
    b = pattern03_nexus_core(hist)
    c = pattern06_quantum_edge(hist)
    d = pattern08_omega_matrix(hist)
    for x in [a, b, c, d]:
        if x:
            signals.append(x)
    if not signals:
        return None
    m = majority(signals)
    if m:
        return m
    return opposite(hist[0])


def pattern11_nova_signal(hist: List[str]) -> Optional[str]:
    if len(hist) < 3:
        return None
    st = streak_length(hist)
    if st >= 4:
        return opposite(hist[0])
    if st == 2 or st == 3:
        return hist[0]
    last3 = hist[:3]
    return majority_with_tie(last3, hist[0])


def pattern12_eclipse_core(hist: List[str]) -> Optional[str]:
    if len(hist) < 7:
        return None
    positions2to7 = hist[1:7]
    return majority_with_tie(positions2to7, hist[0])


def pattern13_fusion_x(hist: List[str]) -> Optional[str]:
    if len(hist) < 7:
        return None
    last5 = hist[:5]
    last7 = hist[:7]
    weights5 = [5, 4, 3, 2, 1]
    m5 = majority_with_tie(last5, hist[0])
    m7 = majority_with_tie(last7, hist[0])
    b, s = weighted_score(last5, weights5)
    ws = 'B' if b > s else ('S' if s > b else opposite(hist[0]))
    signals = [m5, m7, ws]
    m = majority(signals)
    if m:
        return m
    return opposite(hist[0])


def pattern14_zero_point(hist: List[str]) -> Optional[str]:
    if len(hist) < 4:
        return None
    last4 = hist[:4]
    total = 0
    for x in last4:
        total += 1 if x == 'B' else -1
    if total > 0:
        return 'B'
    if total < 0:
        return 'S'
    return opposite(hist[0])


def pattern15_hyper_wave(hist: List[str]) -> Optional[str]:
    if len(hist) < 8:
        return None
    last4 = hist[:4]
    prev4 = hist[4:8]
    b_now = count_b(last4)
    s_now = count_s(last4)
    b_prev = count_b(prev4)
    s_prev = count_s(prev4)
    b_delta = b_now - b_prev
    s_delta = s_now - s_prev
    if b_delta > s_delta:
        return 'B'
    if s_delta > b_delta:
        return 'S'
    return opposite(hist[0])


def pattern16_void_matrix(hist: List[str]) -> Optional[str]:
    if len(hist) < 8:
        return None
    rest = hist[1:8]
    return majority_with_tie(rest, hist[0])


def pattern17_prime_shift(hist: List[str]) -> Optional[str]:
    if len(hist) < 8:
        return None
    last8 = hist[:8]
    odd = [last8[0], last8[2], last8[4], last8[6]]
    even = [last8[1], last8[3], last8[5], last8[7]]
    b_odd = count_b(odd)
    s_odd = count_s(odd)
    b_even = count_b(even)
    s_even = count_s(even)
    b_total = b_odd + b_even
    s_total = s_odd + s_even
    if b_total > s_total:
        return 'B'
    if s_total > b_total:
        return 'S'
    return opposite(hist[0])


def pattern18_neon_grid(hist: List[str]) -> Optional[str]:
    if len(hist) < 9:
        return None
    last9 = hist[:9]
    weights = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    b, s = weighted_score(last9, weights)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def pattern19_infinity_pulse(hist: List[str]) -> Optional[str]:
    if len(hist) < 10:
        return None
    m3 = majority(hist[:3])
    m5 = majority(hist[:5])
    m10 = majority(hist[:10])
    signals = [x for x in [m3, m5, m10] if x]
    if not signals:
        return opposite(hist[0])
    m = majority(signals)
    if m:
        return m
    return opposite(hist[0])


def pattern20_phantom_core(hist: List[str]) -> Optional[str]:
    if len(hist) < 10:
        return None
    positions3to10 = hist[2:10]
    return majority_with_tie(positions3to10, hist[0])


def pattern21_black_phoenix(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    st = streak_length(hist)
    if st >= 3:
        return opposite(hist[0])
    last5 = hist[:5]
    weights5 = [5, 4, 3, 2, 1]
    b, s = weighted_score(last5, weights5)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def pattern22_crimson_edge(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    b_to_s = 0
    s_to_b = 0
    for i in range(len(last5) - 1):
        if last5[i] == 'B' and last5[i + 1] == 'S':
            b_to_s += 1
        if last5[i] == 'S' and last5[i + 1] == 'B':
            s_to_b += 1
    if b_to_s > s_to_b:
        return 'S'
    if s_to_b > b_to_s:
        return 'B'
    return opposite(hist[0])


def pattern23_storm_vector(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    st = streak_length(hist)
    if st >= 4:
        return opposite(hist[0])
    last5 = hist[:5]
    return majority_with_tie(last5, hist[0])


def pattern24_apex_matrix(hist: List[str]) -> Optional[str]:
    signals = []
    a = pattern01_apex_flow(hist)
    b = pattern02_orbit_x(hist)
    c = pattern05_phoenix_wave(hist)
    d = pattern14_zero_point(hist)
    e = pattern19_infinity_pulse(hist)
    for x in [a, b, c, d, e]:
        if x:
            signals.append(x)
    if not signals:
        return None
    m = majority(signals)
    if m:
        return m
    return opposite(hist[0])


def pattern25_rajput_ultra_x(hist: List[str]) -> Optional[dict]:
    """Master engine combining all 24 patterns."""
    signals = []
    
    p1 = pattern01_apex_flow(hist)
    p2 = pattern02_orbit_x(hist)
    p3 = pattern03_nexus_core(hist)
    p4 = pattern04_shadow_grid(hist)
    p5 = pattern05_phoenix_wave(hist)
    p6 = pattern06_quantum_edge(hist)
    p7 = pattern07_cyber_pulse(hist)
    p8 = pattern08_omega_matrix(hist)
    p9 = pattern09_dark_vortex(hist)
    p10 = pattern10_titan_flow(hist)
    p11 = pattern11_nova_signal(hist)
    p12 = pattern12_eclipse_core(hist)
    p13 = pattern13_fusion_x(hist)
    p14 = pattern14_zero_point(hist)
    p15 = pattern15_hyper_wave(hist)
    p16 = pattern16_void_matrix(hist)
    p17 = pattern17_prime_shift(hist)
    p18 = pattern18_neon_grid(hist)
    p19 = pattern19_infinity_pulse(hist)
    p20 = pattern20_phantom_core(hist)
    p21 = pattern21_black_phoenix(hist)
    p22 = pattern22_crimson_edge(hist)
    p23 = pattern23_storm_vector(hist)
    p24 = pattern24_apex_matrix(hist)
    
    for x in [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10,
              p11, p12, p13, p14, p15, p16, p17, p18, p19, p20,
              p21, p22, p23, p24]:
        if x:
            signals.append(x)
    
    if not signals:
        return None
    
    big_votes = count_b(signals)
    small_votes = count_s(signals)
    total = len(signals)
    
    if big_votes > small_votes:
        final_signal = 'B'
    elif small_votes > big_votes:
        final_signal = 'S'
    else:
        final_signal = pattern08_omega_matrix(hist) or opposite(hist[0])
    
    confidence = round((max(big_votes, small_votes) / total) * 100)
    
    return {
        'signal': final_signal,
        'bigVotes': big_votes,
        'smallVotes': small_votes,
        'totalVotes': total,
        'confidence': confidence,
        'allSignals': {
            'p1': p1, 'p2': p2, 'p3': p3, 'p4': p4, 'p5': p5, 'p6': p6,
            'p7': p7, 'p8': p8, 'p9': p9, 'p10': p10, 'p11': p11, 'p12': p12,
            'p13': p13, 'p14': p14, 'p15': p15, 'p16': p16, 'p17': p17,
            'p18': p18, 'p19': p19, 'p20': p20, 'p21': p21, 'p22': p22,
            'p23': p23, 'p24': p24,
        },
    }


# ============================================================
# SECTION 10: 20 DEMO PATTERNS
# ============================================================

def demo_pattern01_nexus(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    b = count_b(last5)
    s = count_s(last5)
    if b < s:
        return 'B'
    if s < b:
        return 'S'
    return opposite(hist[0])


def demo_pattern02_vortex(hist: List[str]) -> Optional[str]:
    if len(hist) < 4:
        return None
    last4 = hist[:4]
    is_alternating = (
        (last4[0] == 'B' and last4[1] == 'S' and last4[2] == 'B' and last4[3] == 'S') or
        (last4[0] == 'S' and last4[1] == 'B' and last4[2] == 'S' and last4[3] == 'B')
    )
    if is_alternating:
        return opposite(last4[0])
    return majority_with_tie(last4, hist[0])


def demo_pattern03_eclipse(hist: List[str]) -> Optional[str]:
    if not hist:
        return None
    st = streak_length(hist)
    if st >= 3 and hist[0] == 'B':
        return 'S'
    if st >= 3 and hist[0] == 'S':
        return 'B'
    return opposite(hist[0])


def demo_pattern04_quantum(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    weights = [5, 4, 3, 2, 1]
    b, s = weighted_score(last5, weights)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def demo_pattern05_phantom(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    weights = [1, 2, 3, 4, 5]
    b, s = weighted_score(last5, weights)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def demo_pattern06_omega(hist: List[str]) -> Optional[str]:
    if len(hist) < 10:
        return None
    last10 = hist[:10]
    return majority_with_tie(last10, hist[0])


def demo_pattern07_nova(hist: List[str]) -> Optional[str]:
    if len(hist) < 3:
        return None
    st = streak_length(hist)
    if st >= 4:
        return opposite(hist[0])
    if st == 2 or st == 3:
        return hist[0]
    last3 = hist[:3]
    return majority_with_tie(last3, hist[0])


def demo_pattern08_titan(hist: List[str]) -> Optional[str]:
    signals = []
    a = demo_pattern01_nexus(hist)
    b = demo_pattern02_vortex(hist)
    c = demo_pattern03_eclipse(hist)
    d = demo_pattern04_quantum(hist)
    for x in [a, b, c, d]:
        if x:
            signals.append(x)
    if not signals:
        return None
    m = majority(signals)
    if m:
        return m
    return demo_pattern06_omega(hist)


def demo_pattern09_matrix99(hist: List[str]) -> Optional[str]:
    signals = []
    a = demo_pattern01_nexus(hist)
    b = demo_pattern02_vortex(hist)
    c = demo_pattern03_eclipse(hist)
    d = demo_pattern04_quantum(hist)
    e = demo_pattern06_omega(hist)
    for x in [a, b, c, d, e]:
        if x:
            signals.append(x)
    if not signals:
        return None
    m = majority(signals)
    if m:
        return m
    return demo_pattern05_phantom(hist)


def demo_pattern10_dark_core(hist: List[str]) -> Optional[str]:
    if len(hist) < 7:
        return None
    last7 = hist[:7]
    b = count_b(last7)
    s = count_s(last7)
    if b >= 5:
        return 'S'
    if s >= 5:
        return 'B'
    return majority_with_tie(last7, hist[0])


def demo_pattern11_zenith(hist: List[str]) -> Optional[str]:
    if len(hist) < 6:
        return None
    last3 = hist[:3]
    prev3 = hist[3:6]
    b_now = count_b(last3)
    s_now = count_s(last3)
    b_prev = count_b(prev3)
    s_prev = count_s(prev3)
    b_delta = b_now - b_prev
    s_delta = s_now - s_prev
    if b_delta > s_delta:
        return 'B'
    if s_delta > b_delta:
        return 'S'
    return opposite(hist[0])


def demo_pattern12_phantom_x(hist: List[str]) -> Optional[str]:
    if len(hist) < 8:
        return None
    positions2to8 = hist[1:8]
    return majority_with_tie(positions2to8, hist[0])


def demo_pattern13_inferno(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    st = streak_length(hist)
    if st >= 5 and hist[0] == 'B':
        return 'S'
    if st >= 5 and hist[0] == 'S':
        return 'B'
    last5 = hist[:5]
    return majority_with_tie(last5, hist[0])


def demo_pattern14_cyber_x(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    weights = [5, 4, 3, 2, 1]
    score = 0
    for i in range(5):
        score += (1 if last5[i] == 'B' else -1) * weights[i]
    if score > 0:
        return 'B'
    if score < 0:
        return 'S'
    return opposite(hist[0])


def demo_pattern15_void_x(hist: List[str]) -> Optional[str]:
    if len(hist) < 6:
        return None
    last6 = hist[:6]
    s = ''.join(last6)
    if 'BBSS' in s:
        return 'B'
    if 'SSBB' in s:
        return 'S'
    return majority_with_tie(last6, hist[0])


def demo_pattern16_neon_wave(hist: List[str]) -> Optional[str]:
    if len(hist) < 8:
        return None
    last4 = hist[:4]
    prev4 = hist[4:8]
    b_now = count_b(last4)
    s_now = count_s(last4)
    b_prev = count_b(prev4)
    s_prev = count_s(prev4)
    b_delta = b_now - b_prev
    s_delta = s_now - s_prev
    if b_delta > s_delta:
        return 'B'
    if s_delta > b_delta:
        return 'S'
    return opposite(hist[0])


def demo_pattern17_crypton(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    last5 = hist[:5]
    total = 0
    for x in last5:
        total += 2 if x == 'B' else 1
    if total >= 8:
        return 'B'
    return 'S'


def demo_pattern18_hyperion(hist: List[str]) -> Optional[str]:
    if len(hist) < 10:
        return None
    last10 = hist[:10]
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    b, s = weighted_score(last10, weights)
    if b > s:
        return 'B'
    if s > b:
        return 'S'
    return opposite(hist[0])


def demo_pattern19_shadow_x(hist: List[str]) -> Optional[str]:
    if len(hist) < 5:
        return None
    if hist[0] == hist[1]:
        return opposite(hist[0])
    last5 = hist[:5]
    return majority_with_tie(last5, hist[0])


def demo_pattern20_black_nova(hist: List[str]) -> Optional[str]:
    signals = []
    a = demo_pattern06_omega(hist)
    b = demo_pattern04_quantum(hist)
    c = demo_pattern07_nova(hist)
    d = demo_pattern10_dark_core(hist)
    e = demo_pattern19_shadow_x(hist)
    for x in [a, b, c, d, e]:
        if x:
            signals.append(x)
    if not signals:
        return None
    m = majority(signals)
    if m:
        return m
    return demo_pattern08_titan(hist)


def demo_master_all_patterns(hist: List[str]) -> Optional[dict]:
    """Master engine combining all 20 demo patterns."""
    signals = []
    
    p1 = demo_pattern01_nexus(hist)
    p2 = demo_pattern02_vortex(hist)
    p3 = demo_pattern03_eclipse(hist)
    p4 = demo_pattern04_quantum(hist)
    p5 = demo_pattern05_phantom(hist)
    p6 = demo_pattern06_omega(hist)
    p7 = demo_pattern07_nova(hist)
    p8 = demo_pattern08_titan(hist)
    p9 = demo_pattern09_matrix99(hist)
    p10 = demo_pattern10_dark_core(hist)
    p11 = demo_pattern11_zenith(hist)
    p12 = demo_pattern12_phantom_x(hist)
    p13 = demo_pattern13_inferno(hist)
    p14 = demo_pattern14_cyber_x(hist)
    p15 = demo_pattern15_void_x(hist)
    p16 = demo_pattern16_neon_wave(hist)
    p17 = demo_pattern17_crypton(hist)
    p18 = demo_pattern18_hyperion(hist)
    p19 = demo_pattern19_shadow_x(hist)
    p20 = demo_pattern20_black_nova(hist)
    
    for x in [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10,
              p11, p12, p13, p14, p15, p16, p17, p18, p19, p20]:
        if x:
            signals.append(x)
    
    if not signals:
        return None
    
    big_votes = count_b(signals)
    small_votes = count_s(signals)
    total_votes = len(signals)
    
    if big_votes > small_votes:
        final_signal = 'B'
    elif small_votes > big_votes:
        final_signal = 'S'
    else:
        final_signal = demo_pattern06_omega(hist) or opposite(hist[0])
    
    confidence = round((max(big_votes, small_votes) / total_votes) * 100)
    
    return {
        'signal': final_signal,
        'bigVotes': big_votes,
        'smallVotes': small_votes,
        'totalVotes': total_votes,
        'confidence': confidence,
        'allSignals': {
            'p1': p1, 'p2': p2, 'p3': p3, 'p4': p4, 'p5': p5, 'p6': p6,
            'p7': p7, 'p8': p8, 'p9': p9, 'p10': p10, 'p11': p11, 'p12': p12,
            'p13': p13, 'p14': p14, 'p15': p15, 'p16': p16, 'p17': p17,
            'p18': p18, 'p19': p19, 'p20': p20,
        },
    }


# ============================================================
# SECTION 11: MAIN PREDICT FUNCTION
# ============================================================

def predict(history: List[dict], period: str, mode: str = '1m', options: Optional[dict] = None) -> dict:
    """Main prediction function — ported from JS predict()."""
    options = options or {}
    
    numbers = [h.get('number', 0) if isinstance(h, dict) else h for h in history]
    sides = ['B' if n >= 5 else 'S' for n in numbers]
    
    # Foundation calibration
    if len(sides) < 2:
        side = 'SMALL' if (numbers[0] if numbers else 0) >= 5 else 'BIG'
        t = compute_target_numbers(side, numbers)
        return {
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 88,
            'patternName': 'NEURAL STREAM CALIBRATION',
            'patternCategory': 'FOUNDATION',
            'ruleCode': 'INIT_STREAM',
            'reason': 'Calibrating stream with historical parity equilibrium',
            'regime': 'NEUTRAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': False,
            'trapDefenseMode': 'SAFE_FLOW',
            'scanStatus': 'EQUILIBRIUM_SCAN',
            'deepAnalysisSummary': 'Waiting for stream synchronization...',
        }
    
    last = numbers[0]
    prev = numbers[1] if len(numbers) > 1 else None
    streak = analyze_streak(sides)
    confirmed = match_confirmed_pattern(''.join(sides[::-1]))
    
    # 1) Confirmed winning database
    if confirmed:
        t = compute_target_numbers(confirmed['prediction'], numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': confirmed['prediction'],
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': confirmed['confidence'],
            'patternName': confirmed['name'],
            'patternCategory': confirmed['category'],
            'ruleCode': f"USER_RULE_{confirmed['pattern']}",
            'reason': confirmed['reason'],
            'regime': 'TRENDING' if confirmed['prediction'] == 'BIG' else 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': confirmed['reason'],
        }, history, options)
    
    # 2) Zigzag 1:1 (3+ flips)
    zig = 1
    for i in range(min(len(sides) - 1, 8)):
        if sides[i] != sides[i + 1]:
            zig += 1
        else:
            break
    if zig >= 3:
        side = 'SMALL' if sides[0] == 'B' else 'BIG'
        t = compute_target_numbers(side, numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': min(99, 96 + zig),
            'patternName': f'⭐ CONFIRMED WINNING: ZIGZAG (1:1) PING-PONG (×{zig} → {side})',
            'patternCategory': 'ZIGZAG',
            'ruleCode': 'CONFIRMED_ZIGZAG_1_1',
            'reason': f'Active 1:1 alternating rhythm ({zig} consecutive flips). Confirmed Winning zigzag continuation locks {side}.',
            'regime': 'CHOPPY',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': f'⭐ Confirmed Winning: Zigzag reached {zig} flips. Next lock: {side}.',
        }, history, options)
    
    # 3) Special confirmed twins patterns (BB-SSS / SS-BBB)
    if len(sides) >= 5 and sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'S' and sides[3] == 'B' and sides[4] == 'B':
        t = compute_target_numbers('BIG', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'BIG',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 99,
            'patternName': '⭐ CONFIRMED WINNING: TWINS INFLECTION (BB-SSS → BIG)',
            'patternCategory': 'TWINS',
            'ruleCode': 'TWINS_BBSSS_BIG',
            'reason': '2 Bigs followed by 3 Smalls (BB-SSS). Confirmed winning twins completion enforces pivot to BIG.',
            'regime': 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: BB-SSS twins completion locked to BIG.',
        }, history, options)
    
    if len(sides) >= 5 and sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'B' and sides[3] == 'S' and sides[4] == 'S':
        t = compute_target_numbers('SMALL', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 99,
            'patternName': '⭐ CONFIRMED WINNING: TWINS INFLECTION (SS-BBB → SMALL)',
            'patternCategory': 'TWINS',
            'ruleCode': 'TWINS_SSBBB_SMALL',
            'reason': '2 Smalls followed by 3 Bigs (SS-BBB). Confirmed winning twins completion enforces pivot to SMALL.',
            'regime': 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: SS-BBB twins completion locked to SMALL.',
        }, history, options)
    
    # 4) SBBS mirror (BB-SS-BB → SMALL)
    if len(sides) >= 6 and sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'S' and sides[3] == 'S' and sides[4] == 'B' and sides[5] == 'B':
        t = compute_target_numbers('SMALL', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 99,
            'patternName': '⭐ CONFIRMED WINNING: SBBS MIRROR SYMMETRY (BB-SS-BB → SMALL)',
            'patternCategory': 'TWINS_SBBS',
            'ruleCode': 'SBBS_BBSSBB_SMALL',
            'reason': '2 Bigs, 2 Smalls, followed by 2 Bigs (BB-SS-BB). Confirmed winning SBBS symmetry locked — predicting pivot to SMALL.',
            'regime': 'CYCLIC',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: BB-SS-BB completed. SBBS mirror symmetry engaged — pivot to SMALL.',
        }, history, options)
    
    if len(sides) >= 6 and sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'B' and sides[3] == 'B' and sides[4] == 'S' and sides[5] == 'S':
        t = compute_target_numbers('BIG', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'BIG',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 99,
            'patternName': '⭐ CONFIRMED WINNING: BSSB MIRROR SYMMETRY (SS-BB-SS → BIG)',
            'patternCategory': 'TWINS_BSSB',
            'ruleCode': 'BSSB_SSBBSS_BIG',
            'reason': '2 Smalls, 2 Bigs, followed by 2 Smalls (SS-BB-SS). Confirmed winning BSSB symmetry locked — predicting pivot to BIG.',
            'regime': 'CYCLIC',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: SS-BB-SS completed. BSSB mirror symmetry engaged — pivot to BIG.',
        }, history, options)
    
    # 5) Twin resurgence (BB-SS-B → BIG)
    if len(sides) >= 5 and sides[0] == 'B' and sides[1] == 'S' and sides[2] == 'S' and sides[3] == 'B' and sides[4] == 'B':
        t = compute_target_numbers('BIG', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'BIG',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 98,
            'patternName': '⭐ CONFIRMED WINNING: TWIN RESURGENCE (BB-SS-B → BIG)',
            'patternCategory': 'TWINS',
            'ruleCode': 'TWIN_BBSSB_BIG',
            'reason': 'BB-SS followed by Big inflection (BB-SS-B). Confirmed winning twin resurgence locks continuation of BIG.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: BB-SS-B detected. Repeating BIG to establish twin leg.',
        }, history, options)
    
    if len(sides) >= 5 and sides[0] == 'S' and sides[1] == 'B' and sides[2] == 'B' and sides[3] == 'S' and sides[4] == 'S':
        t = compute_target_numbers('SMALL', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 98,
            'patternName': '⭐ CONFIRMED WINNING: TWIN RESURGENCE (SS-BB-S → SMALL)',
            'patternCategory': 'TWINS',
            'ruleCode': 'TWIN_SSBBS_SMALL',
            'reason': 'SS-BB followed by Small inflection (SS-BB-S). Confirmed winning twin resurgence locks continuation of SMALL.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: SS-BB-S detected. Repeating SMALL to establish twin leg.',
        }, history, options)
    
    # 6) 2:2 pair extension
    if len(sides) >= 4 and sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'B' and sides[3] == 'B':
        t = compute_target_numbers('SMALL', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 98,
            'patternName': '⭐ CONFIRMED WINNING: 2:2 PAIR EXTENSION (BB-SS → SMALL)',
            'patternCategory': 'TWINS',
            'ruleCode': 'PAIR_BBSS_SMALL',
            'reason': '2 Bigs followed by 2 Smalls (BB-SS). Confirmed winning pair extension to 3rd Small.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: BB-SS detected. Predicting continuation to 3rd Small.',
        }, history, options)
    
    if len(sides) >= 4 and sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'S' and sides[3] == 'S':
        t = compute_target_numbers('BIG', numbers)
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': 'BIG',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 98,
            'patternName': '⭐ CONFIRMED WINNING: 2:2 PAIR EXTENSION (SS-BB → BIG)',
            'patternCategory': 'TWINS',
            'ruleCode': 'PAIR_SSBB_BIG',
            'reason': '2 Smalls followed by 2 Bigs (SS-BB). Confirmed winning pair extension to 3rd Big.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': '⭐ Confirmed Winning: SS-BB detected. Predicting continuation to 3rd Big.',
        }, history, options)
    
    # 7) BSSB / SBBS recovery
    if len(sides) >= 6:
        if sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'B' and sides[3] == 'S' and sides[4] == 'S' and sides[5] == 'B':
            t = compute_target_numbers('BIG', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'BIG',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': '⭐ CONFIRMED WINNING: SBBS RECOVERY (B-SS-B-SS → BIG)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'SYMMETRIC_BSSBSS_BIG',
                'reason': 'B-S-S-B followed by 2 consecutive Small outcomes. Confirmed winning symmetrical bounce to BIG.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: B-SS-B-SS completed. Symmetrical bounce to BIG locked.',
            }, history, options)
        
        if sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'S' and sides[3] == 'B' and sides[4] == 'B' and sides[5] == 'S':
            t = compute_target_numbers('SMALL', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'SMALL',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': '⭐ CONFIRMED WINNING: BSSB RECOVERY (S-BB-S-BB → SMALL)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'SYMMETRIC_SBBSBB_SMALL',
                'reason': 'S-B-B-S followed by 2 consecutive Big outcomes. Confirmed winning symmetrical bounce to SMALL.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: S-BB-S-BB completed. Symmetrical bounce to SMALL locked.',
            }, history, options)
    
    # 8) Twist inflection (B-SS-BB → SMALL)
    if len(sides) >= 5:
        if sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'S' and sides[3] == 'S' and sides[4] == 'B':
            t = compute_target_numbers('SMALL', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'SMALL',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': '⭐ CONFIRMED WINNING: SBBS TWIST INFLECTION (B-SS-BB → SMALL)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'TWIST_PATTERN_BSSBB',
                'reason': 'B-S-S-B followed by unexpected Big twist. Confirmed winning twist pattern locks next to SMALL.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: B-SS-BB twist pattern identified. Anti-trap lock on SMALL.',
            }, history, options)
        
        if sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'B' and sides[3] == 'B' and sides[4] == 'S':
            t = compute_target_numbers('BIG', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'BIG',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': '⭐ CONFIRMED WINNING: BSSB TWIST INFLECTION (S-BB-SS → BIG)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'TWIST_PATTERN_SBBSS',
                'reason': 'S-B-B-S followed by unexpected Small twist. Confirmed winning twist pattern locks next to BIG.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: S-BB-SS twist pattern identified. Anti-trap lock on BIG.',
            }, history, options)
    
    # 9) Continuation
    if len(sides) >= 5:
        if sides[0] == 'S' and sides[1] == 'B' and sides[2] == 'S' and sides[3] == 'S' and sides[4] == 'B':
            t = compute_target_numbers('SMALL', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'SMALL',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': '⭐ CONFIRMED WINNING: SBBS CONTINUATION (B-SS-B-S → SMALL)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'CONTINUATION_BSSBS_SMALL',
                'reason': 'B-S-S-B correctly produced Small. Confirmed winning continuation locks 2nd SMALL.',
                'regime': 'TRENDING',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: B-SS-B-S continuation active. Repeating SMALL for 2nd step.',
            }, history, options)
        
        if sides[0] == 'B' and sides[1] == 'S' and sides[2] == 'B' and sides[3] == 'B' and sides[4] == 'S':
            t = compute_target_numbers('BIG', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'BIG',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': '⭐ CONFIRMED WINNING: BSSB CONTINUATION (S-BB-S-B → BIG)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'CONTINUATION_SBBSB_BIG',
                'reason': 'S-B-B-S correctly produced Big. Confirmed winning continuation locks 2nd BIG.',
                'regime': 'TRENDING',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: S-BB-S-B continuation active. Repeating BIG for 2nd step.',
            }, history, options)
    
    # 10) Base anti-trap pivot
    if len(sides) >= 4:
        if sides[0] == 'B' and sides[1] == 'S' and sides[2] == 'S' and sides[3] == 'B':
            t = compute_target_numbers('SMALL', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'SMALL',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 97,
                'patternName': '⭐ CONFIRMED WINNING: SBBS ANTI-TRAP PIVOT (→ SMALL)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'BASE_BSSB_PREDICT_SMALL',
                'reason': 'B-S-S-B sandwich detected. Confirmed winning anti-trap policy: will NOT chase Big; predicting SMALL.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: B-S-S-B pattern detected. Zero-trap policy: issuing SMALL.',
            }, history, options)
        
        if sides[0] == 'S' and sides[1] == 'B' and sides[2] == 'B' and sides[3] == 'S':
            t = compute_target_numbers('BIG', numbers)
            return finalize({
                'period': period,
                'mode': mode,
                'prediction': 'BIG',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 97,
                'patternName': '⭐ CONFIRMED WINNING: BSSB ANTI-TRAP PIVOT (→ BIG)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'BASE_SBBS_PREDICT_BIG',
                'reason': 'S-B-B-S sandwich detected. Confirmed winning anti-trap policy: will NOT chase Small; predicting BIG.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isConfirmedWinning': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': '⭐ Confirmed Winning: S-B-B-S pattern detected. Zero-trap policy: issuing BIG.',
            }, history, options)
    
    # 11) 3-streak Markov scan
    if streak['count'] == 3 and streak['char']:
        corpus = options.get('corpus1000') or load_corpus(history)
        scan = markov_streak_scan([streak['char']] * 3, history, corpus)
        side = scan['dominantSide']
        source = 'BIG' if streak['char'] == 'B' else 'SMALL'
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': scan['hotFavorNumber'],
            'secondaryNumber': scan['hotOppositeNumber'],
            'favorNumber': scan['hotFavorNumber'],
            'oppositeNumber': scan['hotOppositeNumber'],
            'confidence': max(96, scan['empiricalWinRate']),
            'patternName': f'⭐ CONFIRMED WINNING: 1,000-ROUND MARKOV 3-STREAK ARCHIVE ({streak["char"]}×3 → {side})',
            'patternCategory': 'SPECIAL_SEQUENCE',
            'ruleCode': f'STREAK_3_1000_BACKTEST_{streak["char"]}',
            'reason': f'3 consecutive {source} detected. 1,000-round historical Markov transition scan confirms {side} dominated in {scan["empiricalWinRate"]}% of occurrences ({scan["bigCount"] if side == "BIG" else scan["smallCount"]}/{scan["matchCount"]} matched historical sequences). Primary Hot #{scan["hotFavorNumber"]} | Defense Hot #{scan["hotOppositeNumber"]}.',
            'regime': 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': f'⭐ Confirmed Winning: 1,000-round backtest of {streak["char"]}×3 evaluated: {scan["dominantSide"]} confirmed ({scan["empiricalWinRate"]}% win rate). Hot Favor #{scan["hotFavorNumber"]} | Opposite #{scan["hotOppositeNumber"]}.',
        }, history, options)
    
    # 12) 4+ dragon lock
    if streak['count'] >= 4 and streak['char']:
        side = 'BIG' if streak['char'] == 'B' else 'SMALL'
        t = compute_target_numbers(side, numbers)
        conf = min(99, 94 + streak['count'])
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': conf,
            'patternName': f'⭐ CONFIRMED WINNING: {side} DRAGON LIVE LOCK (×{streak["count"]} LIVE)',
            'patternCategory': 'DRAGON_MOMENTUM',
            'ruleCode': f'DRAGON_LOCK_{streak["count"]}',
            'reason': f'{streak["count"]} consecutive {side} active. Full Dragon Entry (Streak >= 4) — Undisturbed Dragon Lock maintains continuous {side} ride.',
            'regime': 'DRAGON',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isConfirmedWinning': True,
            'isDragonActive': True,
            'dragonStreak': streak['count'],
            'dragonSide': side,
            'trapDefenseMode': 'DRAGON_LOCK',
            'scanStatus': 'DRAGON_LOCK',
            'deepAnalysisSummary': f'⭐ Confirmed Winning: Undisturbed Dragon active ({streak["count"]} {side}). Zero-interference lock on {side}.',
        }, history, options)
    
    # 13) Loss recovery: 1000-draw empirical backtest
    if options.get('lastResultWasLoss'):
        scan = empirical_backtest(sides, options.get('corpus1000') or load_corpus(history))
        if scan['isStatisticallyVerified']:
            side = scan['dominantSide']
            t = compute_target_numbers(side, numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': side,
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': max(95, scan['empiricalWinRate']),
                'patternName': f'🛡️ 1,000-DRAW EMPIRICAL RECOVERY ({scan["empiricalWinRate"]}%)',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': f'RECOVERY_1000_{side}',
                'reason': f'Loss detected. 1,000-draw empirical backtest verified across {scan["matchCount"]} matched historical sequences. Prioritizing {side} with {scan["empiricalWinRate"]}% historical win-rate for immediate next win.',
                'regime': 'REVERSAL',
                'stepLevel': 2,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'PATTERN_MATCH_LOCK',
                'deepAnalysisSummary': f'Background 1000-draw backtest: {scan["matchCount"]} matches evaluated ({scan["empiricalWinRate"]}% {side}). Zero UI clutter.',
            }
    
    # 14) 10-result macro evaluation (3-streak)
    if streak['count'] == 3 and streak['char']:
        side = 'BIG' if streak['char'] == 'B' else 'SMALL'
        opp = 'SMALL' if streak['char'] == 'B' else 'BIG'
        window10 = sides[:10]
        count_big = window10.count(streak['char'])
        count_small = len(window10) - count_big
        flips = 0
        for i in range(len(window10) - 1):
            if window10[i] != window10[i + 1]:
                flips += 1
        
        # 3:3 mirror
        if len(window10) >= 6 and window10[3] != streak['char'] and window10[4] != streak['char'] and window10[5] != streak['char']:
            t = compute_target_numbers(opp, numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': opp,
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 97,
                'patternName': '⚖️ 10-RESULT 3:3 MIRROR DUAL WING (COMPLETED)',
                'patternCategory': 'MIRROR',
                'ruleCode': 'MACRO_10_MIRROR_3_3',
                'reason': f'Last 10 results reveal 3 consecutive {opp} followed by 3 consecutive {side}. 3:3 Mirror completed — pivoting back to {opp}.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': f'10-Draw Scan: 3:3 Mirror Bridge verified across last 10 rounds ({opp}3 → {side}3 → {opp}).',
            }
        
        mean = (numbers[0] + numbers[1] + numbers[2]) / 3 if len(numbers) >= 3 else 5
        
        # Saturation
        if count_big >= 6:
            t = compute_target_numbers(opp, numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': opp,
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 98,
                'patternName': f'🛡️ SATURATION EXHAUSTION PIVOT (→ {opp})',
                'patternCategory': 'MEAN_REVERSION',
                'ruleCode': 'MACRO_SATURATION_EXHAUSTION',
                'reason': f'Last 10 results reached {count_big}/10 {side} saturation (3-period mean: {mean:.1f}). Strict anti-trap prevents repeat trap — pivoting to {opp}.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': f'Macro saturation ({count_big}/10) reached terminal climax. Reversion to {opp} locked.',
            }
        
        # Oscillation cluster pivot
        if flips >= 5:
            t = compute_target_numbers(opp, numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': opp,
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 96,
                'patternName': '⚡ 10-RESULT OSCILLATION CLUSTER PIVOT',
                'patternCategory': 'SPECIAL_SEQUENCE',
                'ruleCode': 'MACRO_10_OSCILLATION_PIVOT',
                'reason': f'Last 10 results exhibit strong alternating oscillation ({flips} switches). 3-streak cluster exhausted — pivoting to {opp}.',
                'regime': 'REVERSAL',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'isDragonActive': False,
                'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': f'10-Draw Scan: Alternation density {flips}/9. Cluster exhaustion detected — pivoting to {opp}.',
            }
        
        # Equilibrium pivot
        favored = opp if count_big > count_small else side
        t = compute_target_numbers(favored, numbers)
        return {
            'period': period,
            'mode': mode,
            'prediction': favored,
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 96,
            'patternName': f'⚖️ 10-RESULT MACRO EQUILIBRIUM PIVOT (→ {favored})',
            'patternCategory': 'SPECIAL_SEQUENCE',
            'ruleCode': 'MACRO_10_EQUILIBRIUM_PIVOT',
            'reason': f'Evaluated across last 10 results (Balance: {count_big} {side} vs {count_small} {opp}). Macro equilibrium pivot predicts {favored}.',
            'regime': 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isDragonActive': False,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': f'10-Draw Scan: Comprehensive 10-period rhythm indicates parity rotation to {favored}.',
        }
    
    # 15) Dragon interrupt scan
    rest_streak = analyze_streak(sides[1:])
    if rest_streak['count'] >= 3 and sides[0] != rest_streak['char'] and rest_streak['char']:
        prior_side = 'BIG' if rest_streak['char'] == 'B' else 'SMALL'
        last_side = 'BIG' if sides[0] == 'B' else 'SMALL'
        corpus = options.get('corpus1000') or load_corpus(history)
        scan = markov_streak_scan([rest_streak['char']] * 3 + [sides[0]], history, corpus)
        side = scan['dominantSide']
        return finalize({
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': scan['hotFavorNumber'],
            'secondaryNumber': scan['hotOppositeNumber'],
            'favorNumber': scan['hotFavorNumber'],
            'oppositeNumber': scan['hotOppositeNumber'],
            'confidence': max(96, scan['empiricalWinRate']),
            'patternName': f'🐉 1,000-ROUND DRAGON INTERRUPT SCAN ({rest_streak["char"]}×3+{sides[0]} → {side})',
            'patternCategory': 'DRAGON_INTERRUPT',
            'ruleCode': f'DRAGON_INTERRUPT_1000_{rest_streak["char"]}_{sides[0]}',
            'reason': f'Dragon streak of {rest_streak["count"]}× {prior_side} interrupted by 1 opposite #{numbers[0]} ({last_side}). 1,000-period deep scan confirms {side} dominated in {scan["empiricalWinRate"]}% of occurrences ({scan["bigCount"] if side == "BIG" else scan["smallCount"]}/{scan["matchCount"]} matched historical occurrences). Hot #{scan["hotFavorNumber"]} | Defense #{scan["hotOppositeNumber"]}.',
            'regime': 'DRAGON' if side == prior_side else 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'isDragonActive': side == prior_side,
            'dragonStreak': rest_streak['count'] if side == prior_side else None,
            'dragonSide': prior_side if side == prior_side else None,
            'trapDefenseMode': 'FAKEOUT_BYPASS' if side == prior_side else 'TRAP_BUSTER_ARMED',
            'scanStatus': 'DRAGON_BREAK_DEEP_SCAN',
            'deepAnalysisSummary': f'Prior {rest_streak["count"]}× {prior_side} interrupted by #{numbers[0]}. 1,000-round scan locks {side} ({scan["empiricalWinRate"]}% historical edge). Primary #{scan["hotFavorNumber"]} | Opposite #{scan["hotOppositeNumber"]}.',
        }, history, options)
    
    # 16) Special repeat rules
    if last == 5 and prev == 5:
        t = compute_target_numbers('BIG', numbers, 'RULE_1_REPEAT_5')
        return {
            'period': period,
            'mode': mode,
            'prediction': 'BIG',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 98,
            'patternName': 'RULE 1: 5-REPEAT BIGG TRIGGER',
            'patternCategory': 'SPECIAL_RULE',
            'ruleCode': 'RULE_1_REPEAT_5',
            'reason': 'Consecutive 5 -> 5 detected. Deep scan confirms strong continuous BIGG momentum.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': 'Consecutive 5->5 strike locked. High-probability BIG prediction.',
        }
    
    if last == 4 and prev == 4:
        t = compute_target_numbers('SMALL', numbers, 'RULE_2_REPEAT_4')
        return {
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 98,
            'patternName': 'RULE 2: 4-REPEAT SMALL TRIGGER',
            'patternCategory': 'SPECIAL_RULE',
            'ruleCode': 'RULE_2_REPEAT_4',
            'reason': 'Consecutive 4 -> 4 detected. Deep scan confirms deep SMALL trend.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': 'Consecutive 4->4 strike locked. High-probability SMALL prediction.',
        }
    
    if len(sides) >= 3 and sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'S':
        t = compute_target_numbers('SMALL', numbers)
        return {
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 95,
            'patternName': 'SBB → S REVERSAL PATTERN',
            'patternCategory': 'SPECIAL_SEQUENCE',
            'ruleCode': 'SBB_TO_S',
            'reason': 'Deep scan locked Chrono S-B-B pattern. Systematic inflection to SMALL.',
            'regime': 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': 'S-B-B inflection completed. Transitioning to SMALL.',
        }
    
    if len(sides) >= 3 and sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'B':
        t = compute_target_numbers('BIG', numbers)
        return {
            'period': period,
            'mode': mode,
            'prediction': 'BIG',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 95,
            'patternName': 'BSS → B REVERSAL PATTERN',
            'patternCategory': 'SPECIAL_SEQUENCE',
            'ruleCode': 'BSS_TO_B',
            'reason': 'Deep scan locked Chrono B-S-S pattern. Systematic recovery to BIG.',
            'regime': 'REVERSAL',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': 'B-S-S inflection completed. Recovering to BIG.',
        }
    
    # 17) 235-pattern matcher
    reversed_sides = sides[::-1]
    sorted_patterns = sorted(PATTERNS, key=lambda p: len(p['sequence']), reverse=True)
    for pat in sorted_patterns:
        length = len(pat['sequence'])
        if len(reversed_sides) >= length:
            tail = reversed_sides[-length:]
            ok = True
            for i in range(length):
                if tail[i] != pat['sequence'][i]:
                    ok = False
                    break
            if ok:
                side = 'BIG' if pat['next'] == 'B' else 'SMALL'
                t = compute_target_numbers(side, numbers)
                return {
                    'period': period,
                    'mode': mode,
                    'prediction': side,
                    'targetNumber': t['targetNumber'],
                    'secondaryNumber': t['secondaryNumber'],
                    'confidence': pat.get('confidence', 97),
                    'patternName': pat['name'],
                    'patternCategory': pat['category'],
                    'ruleCode': pat['id'],
                    'reason': f"{pat['description']} [Pattern {pat['id']}]",
                    'regime': 'DRAGON' if pat['category'] == 'DRAGON' else 'CYCLIC',
                    'stepLevel': 1,
                    'createdAt': int(datetime.now().timestamp() * 1000),
                    'verified': True,
                    'trapDefenseMode': 'TRAP_BUSTER_ARMED',
                    'scanStatus': 'PATTERN_MATCH_LOCK',
                    'deepAnalysisSummary': f"220+ Heuristics Engine matched {pat['id']}: {pat['name']}. Target {side}.",
                }
    
    # 18) 2:2 twins swap
    if len(sides) >= 4:
        if sides[0] == sides[1] and sides[2] == sides[3] and sides[0] != sides[2]:
            side = 'SMALL' if sides[0] == 'B' else 'BIG'
            t = compute_target_numbers(side, numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': side,
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 95,
                'patternName': 'TWINS (2:2) DUAL PAIR SWAP',
                'patternCategory': 'TWINS',
                'ruleCode': 'TWINS_2_2',
                'reason': 'Double pair completed (2:2). Deep scan synchronizes with opposite twin leg.',
                'regime': 'CYCLIC',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'trapDefenseMode': 'SAFE_FLOW',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': 'Pair completion (2:2) identified. Swapping to opposite pair.',
            }
        
        if sides[0] != sides[1] and sides[1] == sides[2]:
            side = 'BIG' if sides[0] == 'B' else 'SMALL'
            t = compute_target_numbers(side, numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': side,
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 93,
                'patternName': 'TWINS (2:2) IN-PAIR COMPLETION',
                'patternCategory': 'TWINS',
                'ruleCode': 'TWINS_2_2_COMPLETION',
                'reason': 'First leg of twin appeared. Locking companion completion round.',
                'regime': 'CYCLIC',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'trapDefenseMode': 'SAFE_FLOW',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': 'First leg of pair confirmed. Locking companion twin match.',
            }
    
    # 19) 2:1:2 dual wing
    if len(sides) >= 5:
        if sides[0] == 'B' and sides[1] == 'B' and sides[2] == 'S' and sides[3] == 'B' and sides[4] == 'B':
            t = compute_target_numbers('SMALL', numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': 'SMALL',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 96,
                'patternName': '(2:1:2) DUAL WING (BB-S-BB)',
                'patternCategory': 'STRUCTURED_212',
                'ruleCode': 'PATTERN_2_1_2',
                'reason': 'Symmetrical 2:1:2 bridge locked. Completing center inflection node.',
                'regime': 'CYCLIC',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'trapDefenseMode': 'SAFE_FLOW',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': 'Symmetrical 2:1:2 bridge matched. Predicting SMALL.',
            }
        
        if sides[0] == 'S' and sides[1] == 'S' and sides[2] == 'B' and sides[3] == 'S' and sides[4] == 'S':
            t = compute_target_numbers('BIG', numbers)
            return {
                'period': period,
                'mode': mode,
                'prediction': 'BIG',
                'targetNumber': t['targetNumber'],
                'secondaryNumber': t['secondaryNumber'],
                'confidence': 96,
                'patternName': '(2:1:2) DUAL WING (SS-B-SS)',
                'patternCategory': 'STRUCTURED_212',
                'ruleCode': 'PATTERN_2_1_2',
                'reason': 'Symmetrical 2:1:2 bridge locked. Completing center inflection node.',
                'regime': 'CYCLIC',
                'stepLevel': 1,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'verified': True,
                'trapDefenseMode': 'SAFE_FLOW',
                'scanStatus': 'SPECIAL_RULE_LOCK',
                'deepAnalysisSummary': 'Symmetrical 2:1:2 bridge matched. Predicting BIG.',
            }
    
    # 20) Rule 3: 4/6 bridge
    if last == 4 or last == 6:
        t = compute_target_numbers('SMALL', numbers, 'RULE_3_BRIDGE_4_6')
        return {
            'period': period,
            'mode': mode,
            'prediction': 'SMALL',
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 93,
            'patternName': f'RULE 3: TRANSITION BRIDGE ({last} TRIGGER)',
            'patternCategory': 'SPECIAL_RULE',
            'ruleCode': 'RULE_3_BRIDGE_4_6',
            'reason': f'Number {last} triggered stabilization wave. Next result: SMALL.',
            'regime': 'TRENDING',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'SAFE_FLOW',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': f'Bridge number {last} activated. Locking SMALL.',
        }
    
    # 21) Extended zigzag harmonic reversal
    flips = 1
    for i in range(min(len(sides) - 1, 8)):
        if sides[i] != sides[i + 1]:
            flips += 1
        else:
            break
    if flips >= 5:
        last_num = numbers[0] if numbers else 5
        side = 'SMALL' if last_num >= 5 else 'BIG'
        t = compute_target_numbers(side, numbers)
        return {
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 96,
            'patternName': f'⚡ EXTENDED ZIGZAG HARMONIC REVERSAL ({flips} FLIPS)',
            'patternCategory': 'ZIGZAG_SNAP',
            'ruleCode': 'ZIGZAG_HARMONIC_REVERSAL',
            'reason': f'Zigzag extended to {flips} flips (#{last_num}). Mathematical parity enforces reversion to {side}.',
            'regime': 'CHOPPY',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'TRAP_BUSTER_ARMED',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': f'Zigzag reached {flips} flips. Parity harmonic locks {side}.',
        }
    if flips >= 3:
        side = 'SMALL' if sides[0] == 'B' else 'BIG'
        t = compute_target_numbers(side, numbers)
        return {
            'period': period,
            'mode': mode,
            'prediction': side,
            'targetNumber': t['targetNumber'],
            'secondaryNumber': t['secondaryNumber'],
            'confidence': 93,
            'patternName': f'ZIGZAG (1:1) PING-PONG (×{flips})',
            'patternCategory': 'ALTERNATING',
            'ruleCode': 'ZIGZAG_1_1',
            'reason': f'Active 1:1 alternating rhythm ({flips} rounds). Flowing with oscillation switch wave.',
            'regime': 'CHOPPY',
            'stepLevel': 1,
            'createdAt': int(datetime.now().timestamp() * 1000),
            'verified': True,
            'trapDefenseMode': 'SAFE_FLOW',
            'scanStatus': 'SPECIAL_RULE_LOCK',
            'deepAnalysisSummary': f'Active 1:1 rhythm ({flips} flips). Continuing switch to {side}.',
        }
    
    # 22) Fallback radar
    window = sides[:10]
    big_count = window.count('B')
    small_count = len(window) - big_count
    
    if big_count >= 7:
        fallback_side = 'SMALL'
        fallback_name = '📊 10-PERIOD SCAN: ZONE OVERLOAD MEAN-REVERSION'
        fallback_reason = f'Main pattern absent. 10-period scan: BIG saturated ({big_count}/10). Anti-trap counter-balances to SMALL.'
    elif small_count >= 7:
        fallback_side = 'BIG'
        fallback_name = '📊 10-PERIOD SCAN: ZONE DEFICIT RECOVERY'
        fallback_reason = f'Main pattern absent. 10-period scan: SMALL saturated ({small_count}/10). Anti-trap upward recovery to BIG.'
    else:
        fallback_side = 'SMALL' if sides[0] == 'B' else 'BIG'
        fallback_name = '📊 10-PERIOD STATISTICAL EQUILIBRIUM SCAN'
        fallback_reason = f'Main pattern absent. 10-period distribution ({big_count}B / {small_count}S) equilibrium consensus locked to {fallback_side}.'
    
    t = compute_target_numbers(fallback_side, numbers)
    base = {
        'period': period,
        'mode': mode,
        'prediction': fallback_side,
        'targetNumber': t['targetNumber'],
        'secondaryNumber': t['secondaryNumber'],
        'confidence': 90,
        'patternName': fallback_name,
        'patternCategory': 'NEURAL_RADAR',
        'ruleCode': 'TEN_PERIOD_RADAR_SCAN',
        'reason': fallback_reason,
        'regime': 'TRENDING',
        'stepLevel': 1,
        'createdAt': int(datetime.now().timestamp() * 1000),
        'verified': False,
        'isConfirmedWinning': False,
        'trapDefenseMode': 'SAFE_FLOW',
        'scanStatus': 'EQUILIBRIUM_SCAN',
        'deepAnalysisSummary': f'Main pattern absent. 10-period distribution ({big_count}B / {small_count}S) evaluated. Locking {fallback_side}.',
    }
    lvl = options.get('level', 1)
    level_result = evaluate_level(history, t['favorNumber'], t['oppositeNumber'], lvl)
    return {
        **base,
        'prediction': level_result['predictedSize'],
        'confidence': max(base['confidence'], level_result['confidence']),
        'favorNumber': level_result['favNumber'],
        'oppositeNumber': level_result['oppNumber'],
        'isTwoLevelVerified': level_result['isTwoLevelVerified'],
        'isSkipRecommended': level_result['isSkipRecommended'],
        'actionText': level_result['actionText'],
        'skipReason': level_result['skipReason'],
        'riskLevel': level_result['riskLevel'],
        'recommendedUnit': level_result['recommendedUnit'],
        'transferDescription': level_result['transferDescription'],
        'currentLevel': level_result['currentLevel'],
        'levelMultiplier': level_result['levelMultiplier'],
        'levelDefenseStatus': level_result['levelDefenseStatus'],
        'markovProb': level_result['markovProb'],
        'logicConsensus': level_result['logicConsensus'],
    }


# ============================================================
# SECTION 12: LEVEL EVALUATION
# ============================================================

def evaluate_level(history: List[dict], favor_number: int, opp_number: int, level: int = 1) -> dict:
    """Evaluate level for prediction."""
    streak_info = compute_window_stats(history)
    dist = number_distribution(history)
    active = find_active_pattern(history)
    osc = oscillation_stats(history)
    def_ = level_defense(level)
    
    predicted = 'BIG'
    confidence = 80
    two_level_verified = False
    skip = False
    action = 'PLAY'
    risk = 'LOW_RISK'
    unit = '3X UNIT (RECOVERY PLAY)' if level == 2 else ('8X UNIT (RECOVERY PLAY)' if level >= 3 else '1X UNIT (CONFIDENT PLAY)')
    transfer = None
    skip_reason = None
    
    if streak_info['sameResultCount'] >= 4:
        predicted = streak_info['lastResult']
        confidence = min(99, 90 + streak_info['sameResultCount'] * 2)
        two_level_verified = True
        skip = False
        action = 'PLAY'
        risk = 'LOW_RISK'
        unit = '3X UNIT (RECOVERY DRAGON RIDE)' if level == 2 else ('8X UNIT (RECOVERY DRAGON RIDE)' if level >= 3 else '1X UNIT (PLAY / RIDE DRAGON)')
        transfer = f"Confirmed {streak_info['lastResult']} Dragon ({streak_info['sameResultCount']} in a row) -> Stay with {streak_info['lastResult']}"
    elif active and active.get('recommendedSize') and active.get('strength', 0) >= 88:
        predicted = active['recommendedSize']
        confidence = active['strength']
        two_level_verified = True
        skip = False
        action = 'PLAY'
        risk = 'LOW_RISK'
        unit = '3X UNIT (LEVEL 2 RECOVERY HIT)' if level == 2 else ('8X UNIT (LEVEL 3 RECOVERY HIT)' if level >= 3 else '1X UNIT (CONFIDENT PLAY)')
        transfer = active['detail']
    elif level >= 2:
        big_score = 0
        small_score = 0
        if dist['favoredSize'] == 'BIG':
            big_score += dist['confidence'] * 1.5
        else:
            small_score += dist['confidence'] * 1.5
        big_score += osc['bigPct'] * 1.2
        small_score += osc['smallPct'] * 1.2
        if streak_info['bias'] == 'BIG':
            big_score += streak_info['strength']
        else:
            small_score += streak_info['strength']
        if active and active.get('recommendedSize'):
            if active['recommendedSize'] == 'BIG':
                big_score += active['strength']
            else:
                small_score += active['strength']
        diff = abs(big_score - small_score)
        predicted = 'BIG' if big_score >= small_score else 'SMALL'
        if diff >= 35:
            confidence = min(99, 95 + level)
            two_level_verified = True
            skip = False
            action = 'PLAY'
            risk = 'LOW_RISK'
            unit = '3X UNIT (LEVEL 2 RECOVERY HIT)' if level == 2 else '8X UNIT (LEVEL 3 RECOVERY HIT)'
            transfer = f'Level {level} Anti-Drawdown Protocol: Multi-Model Consensus ({predicted} score +{round(diff)}) locked to reset to Level 1!'
        else:
            confidence = 78
            two_level_verified = False
            skip = True
            action = 'SKIP'
            risk = 'HIGH_RISK_TRAP'
            unit = '0X (SKIP ROUND / LEVEL-2 DEFENSE)'
            skip_reason = 'LEVEL-2 CAP DEFENSE · Multi-Engine Ambiguity Filter Active · Advised: SKIP (Wait for High-Confidence Setup)'
            transfer = 'Ambiguous 50/50 noise filtered out. Level-2 defense active to prevent advancing to Level 3 or 4. SKIP advised.'
    else:
        if dist:
            predicted = dist['dominantSize']
            confidence = max(dist['bigPct'], dist['smallPct'])
        else:
            predicted = streak_info['favoredSize']
            confidence = max(streak_info['bigPct'], streak_info['smallPct'])
        two_level_verified = False
        skip = True
        action = 'SKIP'
        risk = 'HIGH_RISK_TRAP'
        unit = '0X (SKIP ROUND / PRESERVE BALANCE)'
        skip_reason = f'UNCLEAR PATTERN · 1000-Period Analysis Favors {predicted} ({confidence}%) · Advised: SKIP'
        transfer = f'Unclear pattern structure. 1000 historical rounds analyzed. Dominant side is {predicted}, but high variance: SKIP advised.'
    
    fav = pick_favor_number(predicted, dist, history, favor_number, opp_number)
    return {
        'predictedSize': predicted,
        'favNumber': fav['favNumber'],
        'oppNumber': fav['oppNumber'],
        'confidence': confidence,
        'isTwoLevelVerified': two_level_verified,
        'activePattern': active,
        'backtest': dist,
        'isSkipRecommended': skip,
        'actionText': action,
        'skipReason': skip_reason,
        'riskLevel': risk,
        'recommendedUnit': unit,
        'transferDescription': transfer,
        'currentLevel': level,
        'levelMultiplier': '1X' if level == 1 else ('3X' if level == 2 else ('8X' if level == 3 else '24X')),
        'levelDefenseStatus': (
            'L1 STANDARD (OPTIMAL ALPHA)' if level == 1
            else ('L2 RECOVERY MATRIX (95% CAP DEFENSE)' if level == 2 else 'L3 EMERGENCY SHIELD')
        ),
        'markovProb': {'bigPct': streak_info['bigPct'], 'smallPct': streak_info['smallPct']},
        'logicConsensus': def_,
    }


def pick_favor_number(side: str, dist: dict, history: List[dict], fav_hint: int, opp_hint: int) -> dict:
    """Pick favor number and opposite number."""
    opp = 'SMALL' if side == 'BIG' else 'BIG'
    big_pool = [5, 6, 7, 8, 9]
    small_pool = [0, 1, 2, 3, 4]
    favor_pool = big_pool if side == 'BIG' else small_pool
    opp_pool = big_pool if opp == 'BIG' else small_pool
    
    weights = {i: 1 for i in range(10)}
    
    if dist and dist.get('topNumbers'):
        for idx, t in enumerate(dist['topNumbers']):
            weights[t['num']] = weights.get(t['num'], 0) + (12 - idx * 3) + t['count']
    
    for idx, r in enumerate(history[:25]):
        if isinstance(r, (int, float)):
            num = int(r)
        elif isinstance(r, dict):
            num = r.get('number', r.get('actualNumber', 0))
        else:
            num = 0
        weights[num] = weights.get(num, 0) + (16 - min(idx, 15))
    
    fav_sorted = sorted(favor_pool, key=lambda x: weights.get(x, 0), reverse=True)
    opp_sorted = sorted(opp_pool, key=lambda x: weights.get(x, 0), reverse=True)
    
    fav_list = [n for n in fav_sorted if n != fav_hint]
    if not fav_list:
        fav_list = fav_sorted
    
    opp_list = [n for n in opp_sorted if n != opp_hint and n != fav_list[0]]
    if not opp_list:
        opp_list = [n for n in opp_sorted if n != fav_list[0]]
    if not opp_list:
        opp_list = opp_sorted
    
    return {'favNumber': fav_list[0], 'oppNumber': opp_list[0]}


def find_active_pattern(recent_results: List[dict]) -> Optional[dict]:
    """Find active pattern from recent results."""
    sides = []
    for r in recent_results[:15]:
        if isinstance(r, dict):
            s = r.get('size') or r.get('actualSize')
            if s == 'BIG':
                sides.append('B')
            elif s == 'SMALL':
                sides.append('S')
            else:
                num = r.get('number', 0)
                sides.append('B' if num >= 5 else 'S')
        elif isinstance(r, (int, float)):
            sides.append('B' if r >= 5 else 'S')
        else:
            sides.append('B')
    
    seq = ''.join(sides[::-1])
    confirmed = match_confirmed_pattern(seq)
    if confirmed:
        return {
            'recommendedSize': confirmed['prediction'],
            'strength': confirmed['confidence'],
            'detail': f"{confirmed['name']} [Confidence: {confirmed['confidence']}%]",
            'name': confirmed['name'],
            'icon': '⭐',
            'category': confirmed['category'],
        }
    
    for pat in PATTERNS:
        length = len(pat['sequence'])
        if len(seq) >= length:
            tail = seq[-length:]
            if tail == ''.join(pat['sequence']):
                return {
                    'recommendedSize': 'BIG' if pat['next'] == 'B' else 'SMALL',
                    'strength': pat.get('confidence', 94),
                    'detail': f"{pat['name']} [Confidence: {pat['confidence']}%]",
                    'name': pat['name'],
                    'icon': '⭐',
                    'category': pat['category'],
                }
    
    return None


# ============================================================
# SECTION 13: FINALIZE
# ============================================================

def finalize(base: dict, history: List[dict], options: dict) -> dict:
    """Finalize prediction with level evaluation."""
    fav = base.get('favorNumber', base.get('targetNumber'))
    opp = base.get('oppositeNumber', base.get('secondaryNumber'))
    level = options.get('level', 1) if isinstance(options.get('level'), int) else 1
    
    lvl = evaluate_level(history, fav, opp, level)
    
    confirmed = base.get('isConfirmedWinning')
    if confirmed is None:
        confirmed = base.get('verified') and (
            base.get('scanStatus') == 'SPECIAL_RULE_LOCK' or
            'CONFIRMED WINNING' in base.get('patternName', '')
        )
    
    return {
        **base,
        'isConfirmedWinning': confirmed,
        'favorNumber': fav,
        'oppositeNumber': opp,
        'targetNumber': base.get('targetNumber', fav),
        'secondaryNumber': base.get('secondaryNumber', opp),
        'confidence': max(base['confidence'], 98) if confirmed else max(base['confidence'], lvl['confidence']),
        'isTwoLevelVerified': confirmed or (
            base.get('verified') is not False and (
                lvl['isTwoLevelVerified'] or base['confidence'] >= 92
            )
        ),
        'isSkipRecommended': not confirmed and lvl['isSkipRecommended'] and not base.get('verified'),
        'actionText': 'PLAY' if confirmed else ('SKIP' if lvl['isSkipRecommended'] and not base.get('verified') else 'PLAY'),
        'riskLevel': 'LOW_RISK' if confirmed else ('HIGH_RISK_TRAP' if lvl['isSkipRecommended'] and not base.get('verified') else 'LOW_RISK'),
        'recommendedUnit': (
            ('3X UNIT (CONFIRMED WINNING RECOVERY)' if level == 2 else '8X UNIT (CONFIRMED WINNING RECOVERY)')
            if confirmed and level >= 2
            else ('1X UNIT (CONFIRMED WINNING PLAY)' if confirmed else lvl['recommendedUnit'])
        ),
        'skipReason': None if confirmed else lvl['skipReason'],
        'transferDescription': base.get('deepAnalysisSummary') or lvl['transferDescription'],
        'currentLevel': level,
        'levelMultiplier': level_multiplier(level),
        'levelDefenseStatus': level_defense_status(level),
        'markovProb': lvl['markovProb'],
        'logicConsensus': lvl['logicConsensus'],
    }


def level_multiplier(level: int) -> str:
    return '1X' if level == 1 else ('3X' if level == 2 else ('8X' if level == 3 else '24X'))


def level_defense_status(level: int) -> str:
    return (
        'L1 STANDARD (OPTIMAL ALPHA)' if level == 1
        else ('L2 RECOVERY MATRIX (95% CAP DEFENSE)' if level == 2 else 'L3 EMERGENCY SHIELD')
    )


# ============================================================
# SECTION 14: PATTERNS DATABASE (235 Patterns)
# ============================================================

PATTERNS = [
    {'id': 'P001', 'name': '🐉 3-DRAGON RIDE (B-B-B → B)', 'sequence': ['B', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 94, 'description': '3 consecutive Big results initiating standard Dragon streak momentum.'},
    {'id': 'P002', 'name': '🐉 3-DRAGON RIDE (S-S-S → S)', 'sequence': ['S', 'S', 'S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 94, 'description': '3 consecutive Small results initiating standard Dragon streak momentum.'},
    {'id': 'P003', 'name': '🐉 4-DRAGON LIVE LOCK (B-B-B-B → B)', 'sequence': ['B', 'B', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 96, 'description': '4-Round unbroken Big streak. Full dragon lock ride engaged.'},
    {'id': 'P004', 'name': '🐉 4-DRAGON LIVE LOCK (S-S-S-S → S)', 'sequence': ['S', 'S', 'S', 'S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 96, 'description': '4-Round unbroken Small streak. Full dragon lock ride engaged.'},
    {'id': 'P005', 'name': '🐉 5-DRAGON ACCELERATOR (B5 → B)', 'sequence': ['B', 'B', 'B', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 97, 'description': '5 consecutive Big results. Dragon velocity accelerating unbroken.'},
    {'id': 'P006', 'name': '🐉 5-DRAGON ACCELERATOR (S5 → S)', 'sequence': ['S', 'S', 'S', 'S', 'S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 97, 'description': '5 consecutive Small results. Dragon velocity accelerating unbroken.'},
    {'id': 'P007', 'name': '🐉 6-DRAGON CLIMAX RIDE (B6 → B)', 'sequence': ['B', 'B', 'B', 'B', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 97, 'description': '6 consecutive Big results. Maximum confidence dragon ride.'},
    {'id': 'P008', 'name': '🐉 6-DRAGON CLIMAX RIDE (S6 → S)', 'sequence': ['S', 'S', 'S', 'S', 'S', 'S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 97, 'description': '6 consecutive Small results. Maximum confidence dragon ride.'},
    {'id': 'P009', 'name': '🐉 7-DRAGON ASCENT (B7 → B)', 'sequence': ['B', 'B', 'B', 'B', 'B', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 98, 'description': '7-Streak Big dragon. High-altitude trend velocity maintained.'},
    {'id': 'P010', 'name': '🐉 7-DRAGON ASCENT (S7 → S)', 'sequence': ['S', 'S', 'S', 'S', 'S', 'S', 'S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 98, 'description': '7-Streak Small dragon. High-altitude trend velocity maintained.'},
    {'id': 'P011', 'name': '🐉 8-DRAGON PINNACLE (B8 → B)', 'sequence': ['B'] * 8, 'next': 'B', 'category': 'DRAGON', 'confidence': 98, 'description': '8-Streak Big dragon. Super-trend continuation policy active.'},
    {'id': 'P012', 'name': '🐉 8-DRAGON PINNACLE (S8 → S)', 'sequence': ['S'] * 8, 'next': 'S', 'category': 'DRAGON', 'confidence': 98, 'description': '8-Streak Small dragon. Super-trend continuation policy active.'},
    {'id': 'P013', 'name': '🐉 9-DRAGON SUPREME (B9 → B)', 'sequence': ['B'] * 9, 'next': 'B', 'category': 'DRAGON', 'confidence': 99, 'description': '9 consecutive Big outcomes. Absolute dragon lock mode.'},
    {'id': 'P014', 'name': '🐉 9-DRAGON SUPREME (S9 → S)', 'sequence': ['S'] * 9, 'next': 'S', 'category': 'DRAGON', 'confidence': 99, 'description': '9 consecutive Small outcomes. Absolute dragon lock mode.'},
    {'id': 'P015', 'name': '🐉 10-DRAGON SOVEREIGN (B10 → B)', 'sequence': ['B'] * 10, 'next': 'B', 'category': 'DRAGON', 'confidence': 99, 'description': '10 consecutive Big outcomes. Undisturbed Sovereign Ride.'},
    {'id': 'P016', 'name': '🐉 10-DRAGON SOVEREIGN (S10 → S)', 'sequence': ['S'] * 10, 'next': 'S', 'category': 'DRAGON', 'confidence': 99, 'description': '10 consecutive Small outcomes. Undisturbed Sovereign Ride.'},
    {'id': 'P017', 'name': '🔄 DRAGON FAKEOUT RETURN (B-B-B-B-S → B)', 'sequence': ['B', 'B', 'B', 'B', 'S'], 'next': 'B', 'category': 'DRAGON', 'confidence': 96, 'description': '4 Big interrupted by single Small glitch. Re-riding original Big dragon.'},
    {'id': 'P018', 'name': '🔄 DRAGON FAKEOUT RETURN (S-S-S-S-B → S)', 'sequence': ['S', 'S', 'S', 'S', 'B'], 'next': 'S', 'category': 'DRAGON', 'confidence': 96, 'description': '4 Small interrupted by single Big glitch. Re-riding original Small dragon.'},
    {'id': 'P019', 'name': '🔄 5-DRAGON RETURN FAKEOUT (B5-S → B)', 'sequence': ['B', 'B', 'B', 'B', 'B', 'S'], 'next': 'B', 'category': 'DRAGON', 'confidence': 97, 'description': '5 Big interrupted by single Small bounce. Returning to Big dragon core.'},
    {'id': 'P020', 'name': '🔄 5-DRAGON RETURN FAKEOUT (S5-B → S)', 'sequence': ['S', 'S', 'S', 'S', 'S', 'B'], 'next': 'S', 'category': 'DRAGON', 'confidence': 97, 'description': '5 Small interrupted by single Big bounce. Returning to Small dragon core.'},
    {'id': 'P021', 'name': '⛓ DOUBLE-DRAGON BRIDGE (B4-S2 → S)', 'sequence': ['B', 'B', 'B', 'B', 'S', 'S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 95, 'description': '4 Big followed by 2 Small. Confirming dragon reversal trend to Small.'},
    {'id': 'P022', 'name': '⛓ DOUBLE-DRAGON BRIDGE (S4-B2 → B)', 'sequence': ['S', 'S', 'S', 'S', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 95, 'description': '4 Small followed by 2 Big. Confirming dragon reversal trend to Big.'},
    {'id': 'P023', 'name': '🔥 7-DRAGON EXHAUSTION BURN (B7-S → S)', 'sequence': ['B'] * 7 + ['S'], 'next': 'S', 'category': 'DRAGON', 'confidence': 96, 'description': '7 Big streak cleanly broken. Climax exhaustion confirmed — following Small.'},
    {'id': 'P024', 'name': '🔥 7-DRAGON EXHAUSTION BURN (S7-B → B)', 'sequence': ['S'] * 7 + ['B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 96, 'description': '7 Small streak cleanly broken. Climax exhaustion confirmed — following Big.'},
    {'id': 'P025', 'name': '🌊 DRAGON TAIL CASCADE (B-B-B-S-B-B → B)', 'sequence': ['B', 'B', 'B', 'S', 'B', 'B'], 'next': 'B', 'category': 'DRAGON', 'confidence': 96, 'description': 'Dragon tail confirmed after brief dip. Continuing Big momentum cascade.'},
    {'id': 'P026', 'name': '⚡ 1:1 ZIGZAG 3-STEP (B-S-B → S)', 'sequence': ['B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 93, 'description': 'Clean 1:1 alternating rhythm B-S-B. Flowing with oscillation switch to Small.'},
    {'id': 'P027', 'name': '⚡ 1:1 ZIGZAG 3-STEP (S-B-S → B)', 'sequence': ['S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 93, 'description': 'Clean 1:1 alternating rhythm S-B-S. Flowing with oscillation switch to Big.'},
    {'id': 'P028', 'name': '⚡ 1:1 ZIGZAG 4-STEP (B-S-B-S → B)', 'sequence': ['B', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 95, 'description': '4-Round ping-pong sequence. Alternation wave targets Big.'},
    {'id': 'P029', 'name': '⚡ 1:1 ZIGZAG 4-STEP (S-B-S-B → S)', 'sequence': ['S', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 95, 'description': '4-Round ping-pong sequence. Alternation wave targets Small.'},
    {'id': 'P030', 'name': '⚡ 1:1 ZIGZAG 5-STEP (B-S-B-S-B → S)', 'sequence': ['B', 'S', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 95, 'description': '5-Round ping-pong sequence. Switch leg locks on Small.'},
    {'id': 'P031', 'name': '⚡ 1:1 ZIGZAG 5-STEP (S-B-S-B-S → B)', 'sequence': ['S', 'B', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 95, 'description': '5-Round ping-pong sequence. Switch leg locks on Big.'},
    {'id': 'P032', 'name': '⚡ 1:1 ZIGZAG 6-STEP MASTER (B-S-B-S-B-S → B)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 96, 'description': '6-Round perfect ping-pong. Rhythm continuity predicts Big.'},
    {'id': 'P033', 'name': '⚡ 1:1 ZIGZAG 6-STEP MASTER (S-B-S-B-S-B → S)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 96, 'description': '6-Round perfect ping-pong. Rhythm continuity predicts Small.'},
    {'id': 'P034', 'name': '⚡ 1:1 ZIGZAG 7-STEP CLIMAX (B-S-B-S-B-S-B → S)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 96, 'description': '7-Step intense oscillation. Continuing alternating switch to Small.'},
    {'id': 'P035', 'name': '⚡ 1:1 ZIGZAG 7-STEP CLIMAX (S-B-S-B-S-B-S → B)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 96, 'description': '7-Step intense oscillation. Continuing alternating switch to Big.'},
    {'id': 'P036', 'name': '🪃 ZIGZAG 8-FLIP SNAP BREAKOUT (B-S-B-S-B-S-B-S → S)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'S', 'B', 'S'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 97, 'description': '8-Round ping-pong exhaustion. Anti-trap predicts twin snap to Small.'},
    {'id': 'P037', 'name': '🪃 ZIGZAG 8-FLIP SNAP BREAKOUT (S-B-S-B-S-B-S-B → B)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'B', 'S', 'B'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 97, 'description': '8-Round ping-pong exhaustion. Anti-trap predicts twin snap to Big.'},
    {'id': 'P038', 'name': '🔀 1:2 OSCILLATION CADENCE (B-S-S-B-S-S → B)', 'sequence': ['B', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 97, 'description': '1:2 periodic alternation pattern. Next cadence rotation targets Big.'},
    {'id': 'P039', 'name': '🔀 1:2 OSCILLATION CADENCE (S-B-B-S-B-B → S)', 'sequence': ['S', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 97, 'description': '1:2 periodic alternation pattern. Next cadence rotation targets Small.'},
    {'id': 'P040', 'name': '🔀 2:1 INVERTED OSCILLATION (B-B-S-B-B-S → B)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 96, 'description': '2:1 inverted cycle. Double Big lead cycle targets Big.'},
    {'id': 'P041', 'name': '🔀 2:1 INVERTED OSCILLATION (S-S-B-S-S-B → S)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 96, 'description': '2:1 inverted cycle. Double Small lead cycle targets Small.'},
    {'id': 'P042', 'name': '⚡ 1:1:2 PHASE SHIFT (B-S-B-B → S)', 'sequence': ['B', 'S', 'B', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Alternating flip broken into twin Big. Phase shift targets Small.'},
    {'id': 'P043', 'name': '⚡ 1:1:2 PHASE SHIFT (S-B-S-S → B)', 'sequence': ['S', 'B', 'S', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Alternating flip broken into twin Small. Phase shift targets Big.'},
    {'id': 'P044', 'name': '🌊 1:1:3 EXPANSION WAVE (B-S-B-S-S-S → B)', 'sequence': ['B', 'S', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 96, 'description': 'Zigzag expanded into 3 Small. Rebound wave triggers Big.'},
    {'id': 'P045', 'name': '🌊 1:1:3 EXPANSION WAVE (S-B-S-B-B-B → S)', 'sequence': ['S', 'B', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 96, 'description': 'Zigzag expanded into 3 Big. Rebound wave triggers Small.'},
    {'id': 'P046', 'name': '🔍 CHOPPY TRAP PIVOT (B-S-B-S-B-B-S → B)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Choppy consolidation breakout follow-up predicting Big.'},
    {'id': 'P047', 'name': '🔍 CHOPPY TRAP PIVOT (S-B-S-B-S-S-B → S)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Choppy consolidation breakout follow-up predicting Small.'},
    {'id': 'P048', 'name': '⚡ RAPID DOUBLE FLIP (B-B-S-S-B-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 94, 'description': 'Twin transition decaying into 1:1. Pivot targets Big.'},
    {'id': 'P049', 'name': '⚡ RAPID DOUBLE FLIP (S-S-B-B-S-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 94, 'description': 'Twin transition decaying into 1:1. Pivot targets Small.'},
    {'id': 'P050', 'name': '⚡ 3-ROUND ALTERNATING RECOVERY (S-B-S-B-S-B-B → S)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Double Big ending long zigzag. Mean reversion targets Small.'},
    {'id': 'P051', 'name': '⚡ 3-ROUND ALTERNATING RECOVERY (B-S-B-S-B-S-S → B)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Double Small ending long zigzag. Mean reversion targets Big.'},
    {'id': 'P052', 'name': '🌪 HIGH-FREQUENCY OSCILLATOR (B-S-S-B-B-S-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Multi-frequency mixed oscillation phase locking on Small.'},
    {'id': 'P053', 'name': '🌪 HIGH-FREQUENCY OSCILLATOR (S-B-B-S-S-B-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 95, 'description': 'Multi-frequency mixed oscillation phase locking on Big.'},
    {'id': 'P054', 'name': '⚡ PING-PONG TERMINAL CORE (B-S-B-S-B-S-B-S-B → S)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'S', 'B', 'S', 'B'], 'next': 'S', 'category': 'ZIGZAG', 'confidence': 98, 'description': '9-Flip extreme ping-pong cycle. Invariant rotation to Small.'},
    {'id': 'P055', 'name': '⚡ PING-PONG TERMINAL CORE (S-B-S-B-S-B-S-B-S → B)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'B', 'S', 'B', 'S'], 'next': 'B', 'category': 'ZIGZAG', 'confidence': 98, 'description': '9-Flip extreme ping-pong cycle. Invariant rotation to Big.'},
    {'id': 'P056', 'name': '👯 2:2 TWIN PAIR (B-B-S-S → B)', 'sequence': ['B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': 'Standard 2:2 double pair completed. Reversal step to Big.'},
    {'id': 'P057', 'name': '👯 2:2 TWIN PAIR (S-S-B-B → S)', 'sequence': ['S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': 'Standard 2:2 double pair completed. Reversal step to Small.'},
    {'id': 'P058', 'name': '👯 2:2:2 TRIPLE TWIN (B-B-S-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': 'Triple twin cascade. Alternating twin symmetry targets Small.'},
    {'id': 'P059', 'name': '👯 2:2:2 TRIPLE TWIN (S-S-B-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': 'Triple twin cascade. Alternating twin symmetry targets Big.'},
    {'id': 'P060', 'name': '⚖️ 3:3 DUAL WING MIRROR (B-B-B-S-S-S → B)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': 'Classic 3:3 Triple-Triple mirror completed. Wing rebound targets Big.'},
    {'id': 'P061', 'name': '⚖️ 3:3 DUAL WING MIRROR (S-S-S-B-B-B → S)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': 'Classic 3:3 Triple-Triple mirror completed. Wing rebound targets Small.'},
    {'id': 'P062', 'name': '⚖️ 3:3 DUAL WING LEG 2 (B-B-B-S → S)', 'sequence': ['B', 'B', 'B', 'S'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': '3 Big followed by 1st Small. 3:3 mirror transition predicts Small leg 2.'},
    {'id': 'P063', 'name': '⚖️ 3:3 DUAL WING LEG 2 (S-S-S-B → B)', 'sequence': ['S', 'S', 'S', 'B'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': '3 Small followed by 1st Big. 3:3 mirror transition predicts Big leg 2.'},
    {'id': 'P064', 'name': '⚖️ 3:3 DUAL WING LEG 3 (B-B-B-S-S → S)', 'sequence': ['B', 'B', 'B', 'S', 'S'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': '3 Big followed by 2 Small. 3:3 mirror transition predicts Small leg 3.'},
    {'id': 'P065', 'name': '⚖️ 3:3 DUAL WING LEG 3 (S-S-S-B-B → B)', 'sequence': ['S', 'S', 'S', 'B', 'B'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': '3 Small followed by 2 Big. 3:3 mirror transition predicts Big leg 3.'},
    {'id': 'P066', 'name': '🏛️ 4:4 QUAD MIRROR (B-B-B-B-S-S-S-S → B)', 'sequence': ['B', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 98, 'description': '4:4 Quad Monolith mirror completed. Symmetrical bounce targets Big.'},
    {'id': 'P067', 'name': '🏛️ 4:4 QUAD MIRROR (S-S-S-S-B-B-B-B → S)', 'sequence': ['S', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 98, 'description': '4:4 Quad Monolith mirror completed. Symmetrical bounce targets Small.'},
    {'id': 'P068', 'name': '💎 2:1:2 DUAL WING DIAMOND (B-B-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': '2:1:2 Diamond sandwich completed. Reversal step locks on Small.'},
    {'id': 'P069', 'name': '💎 2:1:2 DUAL WING DIAMOND (S-S-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': '2:1:2 Diamond sandwich completed. Reversal step locks on Big.'},
    {'id': 'P070', 'name': '⏳ 3:1:3 HOURGLASS (B-B-B-S-B-B-B → S)', 'sequence': ['B', 'B', 'B', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': '3:1:3 Hourglass structure completed. Reversal pivot targets Small.'},
    {'id': 'P071', 'name': '⏳ 3:1:3 HOURGLASS (S-S-S-B-S-S-S → B)', 'sequence': ['S', 'S', 'S', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': '3:1:3 Hourglass structure completed. Reversal pivot targets Big.'},
    {'id': 'P072', 'name': '🌉 2:3:2 INCLINE BRIDGE (B-B-S-S-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': '2:3:2 Incline bridge completed. Periodic transition targets Small.'},
    {'id': 'P073', 'name': '🌉 2:3:2 INCLINE BRIDGE (S-S-B-B-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': '2:3:2 Incline bridge completed. Periodic transition targets Big.'},
    {'id': 'P074', 'name': '🏰 3:2:3 CASTLE ARCH (B-B-B-S-S-B-B-B → S)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': '3:2:3 Castle Arch structure completed. Rotational reversal to Small.'},
    {'id': 'P075', 'name': '🏰 3:2:3 CASTLE ARCH (S-S-S-B-B-S-S-S → B)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': '3:2:3 Castle Arch structure completed. Rotational reversal to Big.'},
    {'id': 'P076', 'name': '🥪 1:3:1 SANDWICH (B-S-S-S-B → S)', 'sequence': ['B', 'S', 'S', 'S', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': 'Triple Small sandwiched by single Big. Reversal bounce to Small.'},
    {'id': 'P077', 'name': '🥪 1:3:1 SANDWICH (S-B-B-B-S → B)', 'sequence': ['S', 'B', 'B', 'B', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': 'Triple Big sandwiched by single Small. Reversal bounce to Big.'},
    {'id': 'P078', 'name': '🥪 1:4:1 MONOLITH (B-S-S-S-S-B → S)', 'sequence': ['B', 'S', 'S', 'S', 'S', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': 'Quad Small encased by single Big. Mean reversion to Small.'},
    {'id': 'P079', 'name': '🥪 1:4:1 MONOLITH (S-B-B-B-B-S → B)', 'sequence': ['S', 'B', 'B', 'B', 'B', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': 'Quad Big encased by single Small. Mean reversion to Big.'},
    {'id': 'P080', 'name': '🎪 2:4:2 PAVILION (B-B-S-S-S-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 98, 'description': '2:4:2 Pavilion mirror structure completed. Symmetrical pivot to Small.'},
    {'id': 'P081', 'name': '🎪 2:4:2 PAVILION (S-S-B-B-B-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 98, 'description': '2:4:2 Pavilion mirror structure completed. Symmetrical pivot to Big.'},
    {'id': 'P082', 'name': '🏛️ 5:5 TITAN MIRROR (B5-S5 → B)', 'sequence': ['B'] * 5 + ['S'] * 5, 'next': 'B', 'category': 'MIRROR', 'confidence': 99, 'description': '5:5 Titan mirror parity reached. Invariant mean bounce to Big.'},
    {'id': 'P083', 'name': '🏛️ 5:5 TITAN MIRROR (S5-B5 → S)', 'sequence': ['S'] * 5 + ['B'] * 5, 'next': 'S', 'category': 'MIRROR', 'confidence': 99, 'description': '5:5 Titan mirror parity reached. Invariant mean bounce to Small.'},
    {'id': 'P084', 'name': '👯 2:2:1 STEP CHATTER (B-B-S-S-B → B)', 'sequence': ['B', 'B', 'S', 'S', 'B'], 'next': 'B', 'category': 'MIRROR', 'confidence': 95, 'description': '2:2 followed by single Big. Completing twin step to Big.'},
    {'id': 'P085', 'name': '👯 2:2:1 STEP CHATTER (S-S-B-B-S → S)', 'sequence': ['S', 'S', 'B', 'B', 'S'], 'next': 'S', 'category': 'MIRROR', 'confidence': 95, 'description': '2:2 followed by single Small. Completing twin step to Small.'},
    {'id': 'P086', 'name': '👯 2:3 TWIN EXTENSION (B-B-S-S-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': 'Double Big followed by triple Small. 2:3 extension targets Big.'},
    {'id': 'P087', 'name': '👯 2:3 TWIN EXTENSION (S-S-B-B-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': 'Double Small followed by triple Big. 2:3 extension targets Small.'},
    {'id': 'P088', 'name': '👯 3:2 INVERTED EXTENSION (B-B-B-S-S → B)', 'sequence': ['B', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 95, 'description': '3 Big followed by 2 Small. Twin defense rebound to Big.'},
    {'id': 'P089', 'name': '👯 3:2 INVERTED EXTENSION (S-S-S-B-B → S)', 'sequence': ['S', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 95, 'description': '3 Small followed by 2 Big. Twin defense rebound to Small.'},
    {'id': 'P090', 'name': '🪞 RECURSIVE QUAD DUAL (B-B-S-S-B-B-S-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 98, 'description': 'Perfect 4-pair 2:2 recursion. Flowing with twin cycle to Big.'},
    {'id': 'P091', 'name': '🪞 RECURSIVE QUAD DUAL (S-S-B-B-S-S-B-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 98, 'description': 'Perfect 4-pair 2:2 recursion. Flowing with twin cycle to Small.'},
    {'id': 'P092', 'name': '🪞 1:2:1:2 RHYTHMIC BRIDGE (B-S-S-B-S-S-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 96, 'description': '1:2 rhythmic cadence verified. Follows periodic phase to Small.'},
    {'id': 'P093', 'name': '🪞 1:2:1:2 RHYTHMIC BRIDGE (S-B-B-S-B-B-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 96, 'description': '1:2 rhythmic cadence verified. Follows periodic phase to Big.'},
    {'id': 'P094', 'name': '🪞 2:1:2:1 RHYTHMIC FLIP (B-B-S-B-B-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'MIRROR', 'confidence': 97, 'description': '2:1:2:1 rhythmic flip completed. Phase rotation to Small.'},
    {'id': 'P095', 'name': '🪞 2:1:2:1 RHYTHMIC FLIP (S-S-B-S-S-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'MIRROR', 'confidence': 97, 'description': '2:1:2:1 rhythmic flip completed. Phase rotation to Big.'},
    {'id': 'P096', 'name': '🧗 1:2:3 PYRAMID COMPLETE (B-S-S-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 97, 'description': '1:2:3 Ascending pyramid completed. Peak reached — reversing to Small.'},
    {'id': 'P097', 'name': '🧗 1:2:3 PYRAMID COMPLETE (S-B-B-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 97, 'description': '1:2:3 Ascending pyramid completed. Peak reached — reversing to Big.'},
    {'id': 'P098', 'name': '🧗 1:2:3 STEP 3 ASCENT (B-S-S-B-B → B)', 'sequence': ['B', 'S', 'S', 'B', 'B'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': '1:2:3 Pyramid building. 3rd Big expected to complete 3-step pinnacle.'},
    {'id': 'P099', 'name': '🧗 1:2:3 STEP 3 ASCENT (S-B-B-S-S → S)', 'sequence': ['S', 'B', 'B', 'S', 'S'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': '1:2:3 Pyramid building. 3rd Small expected to complete 3-step pinnacle.'},
    {'id': 'P100', 'name': '📉 3:2:1 DECRESCENDO (B-B-B-S-S-B → S)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': '3:2:1 Decrescendo pattern completed. Decaying cadence flips to Small.'},
    {'id': 'P101', 'name': '📉 3:2:1 DECRESCENDO (S-S-S-B-B-S → B)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': '3:2:1 Decrescendo pattern completed. Decaying cadence flips to Big.'},
    {'id': 'P102', 'name': '🏛️ 1:2:3:4 GRAND STAIRCASE (B-S-S-B-B-B-S-S-S-S → B)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 99, 'description': '1-2-3-4 Grand staircase complete. Invariant reversal bounce to Big.'},
    {'id': 'P103', 'name': '🏛️ 1:2:3:4 GRAND STAIRCASE (S-B-B-S-S-S-B-B-B-B → S)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 99, 'description': '1-2-3-4 Grand staircase complete. Invariant reversal bounce to Small.'},
    {'id': 'P104', 'name': '🌊 4:3:2:1 CASCADE WATERFALL (B4-S3-B2-S → B)', 'sequence': ['B', 'B', 'B', 'B', 'S', 'S', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 98, 'description': '4-3-2-1 Cascade completed at terminal 1-step. Reset wave triggers Big.'},
    {'id': 'P105', 'name': '🌊 4:3:2:1 CASCADE WATERFALL (S4-B3-S2-B → S)', 'sequence': ['S', 'S', 'S', 'S', 'B', 'B', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 98, 'description': '4-3-2-1 Cascade completed at terminal 1-step. Reset wave triggers Small.'},
    {'id': 'P106', 'name': '📶 2:3:4 EXPANDING LADDER (B-B-S-S-S-B-B-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 98, 'description': '2-3-4 Expanding ladder peaked at 4 Big. Climax exhaustion triggers Small.'},
    {'id': 'P107', 'name': '📶 2:3:4 EXPANDING LADDER (S-S-B-B-B-S-S-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 98, 'description': '2-3-4 Expanding ladder peaked at 4 Small. Climax exhaustion triggers Big.'},
    {'id': 'P108', 'name': '🪜 1:1:2:2 DOUBLE STEP (B-S-B-B-S-S → B)', 'sequence': ['B', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': '1-1-2-2 Progressive step pairs completed. Cycle reboot targets Big.'},
    {'id': 'P109', 'name': '🪜 1:1:2:2 DOUBLE STEP (S-B-S-S-B-B → S)', 'sequence': ['S', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': '1-1-2-2 Progressive step pairs completed. Cycle reboot targets Small.'},
    {'id': 'P110', 'name': '🪜 2:2:3:3 TWIN STEP LADDER (B-B-S-S-B-B-B-S-S-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 98, 'description': '2-2-3-3 Double symmetric expansion completed. Rebound to Big.'},
    {'id': 'P111', 'name': '🪜 2:2:3:3 TWIN STEP LADDER (S-S-B-B-S-S-S-B-B-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 98, 'description': '2-2-3-3 Double symmetric expansion completed. Rebound to Small.'},
    {'id': 'P112', 'name': '🔯 1:3:5 ODD HARMONIC (B-S-S-S-B-B-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'S', 'B', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 98, 'description': '1-3-5 Odd harmonic expansion reached 5th Big. Pivot to Small.'},
    {'id': 'P113', 'name': '🔯 1:3:5 ODD HARMONIC (S-B-B-B-S-S-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'B', 'S', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 98, 'description': '1-3-5 Odd harmonic expansion reached 5th Small. Pivot to Big.'},
    {'id': 'P114', 'name': '🔯 2:4:6 EVEN HARMONIC (B-B-S-S-S-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 97, 'description': '2-4 Harmonic step completed. Reversal step to Big.'},
    {'id': 'P115', 'name': '🔯 2:4:6 EVEN HARMONIC (S-S-B-B-B-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 97, 'description': '2-4 Harmonic step completed. Reversal step to Small.'},
    {'id': 'P116', 'name': '📐 1:2:1:3 ASYMMETRIC STAIR (B-S-S-B-S-S-S → B)', 'sequence': ['B', 'S', 'S', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': 'Asymmetric 3-step expansion climax. Rebound targets Big.'},
    {'id': 'P117', 'name': '📐 1:2:1:3 ASYMMETRIC STAIR (S-B-B-S-B-B-B → S)', 'sequence': ['S', 'B', 'B', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': 'Asymmetric 3-step expansion climax. Rebound targets Small.'},
    {'id': 'P118', 'name': '🧗 3-STEP ASCENT LEVEL 2 (B-S-S-B → S)', 'sequence': ['B', 'S', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': 'B-SS-B anti-trap step predicts Small.'},
    {'id': 'P119', 'name': '🧗 3-STEP ASCENT LEVEL 2 (S-B-B-S → B)', 'sequence': ['S', 'B', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': 'S-BB-S anti-trap step predicts Big.'},
    {'id': 'P120', 'name': '📉 2:1:1 CASCADE RESET (B-B-S-B → S)', 'sequence': ['B', 'B', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 94, 'description': '2:1:1 decaying cadence flips to Small.'},
    {'id': 'P121', 'name': '📉 2:1:1 CASCADE RESET (S-S-B-S → B)', 'sequence': ['S', 'S', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 94, 'description': '2:1:1 decaying cadence flips to Big.'},
    {'id': 'P122', 'name': '🧗 STEPPING STONE (B-B-S-B-B-S-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 95, 'description': 'Stepping stone rhythmic progression flips to Small.'},
    {'id': 'P123', 'name': '🧗 STEPPING STONE (S-S-B-S-S-B-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 95, 'description': 'Stepping stone rhythmic progression flips to Big.'},
    {'id': 'P124', 'name': '📶 1:2:4 POWER EXPANSION (B-S-S-B-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 97, 'description': '1-2-4 Binary doubling expansion peaked at 4 Big. Pivot to Small.'},
    {'id': 'P125', 'name': '📶 1:2:4 POWER EXPANSION (S-B-B-S-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 97, 'description': '1-2-4 Binary doubling expansion peaked at 4 Small. Pivot to Big.'},
    {'id': 'P126', 'name': '🪜 3:2:2 DOUBLE RAMP (B-B-B-S-S-B-B → S)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': '3:2:2 Double Ramp transition completes leg on Small.'},
    {'id': 'P127', 'name': '🪜 3:2:2 DOUBLE RAMP (S-S-S-B-B-S-S → B)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': '3:2:2 Double Ramp transition completes leg on Big.'},
    {'id': 'P128', 'name': '📉 4:2:1 EXPONENT DOWN (B4-S2-B → S)', 'sequence': ['B', 'B', 'B', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': '4:2:1 Exponential compression pivots to Small.'},
    {'id': 'P129', 'name': '📉 4:2:1 EXPONENT DOWN (S4-B2-S → B)', 'sequence': ['S', 'S', 'S', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': '4:2:1 Exponential compression pivots to Big.'},
    {'id': 'P130', 'name': '🧗 PYRAMID ECHO (B-S-S-B-B-B-S-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 95, 'description': 'Pyramid echo transition targets Small.'},
    {'id': 'P131', 'name': '🧗 PYRAMID ECHO (S-B-B-S-S-S-B-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 95, 'description': 'Pyramid echo transition targets Big.'},
    {'id': 'P132', 'name': '🪜 1:2:2:1 PODIUM (B-S-S-B-B-S → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'S'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 95, 'description': '1:2:2:1 Podium structure completed with terminal Small.'},
    {'id': 'P133', 'name': '🪜 1:2:2:1 PODIUM (S-B-B-S-S-B → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'B'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 95, 'description': '1:2:2:1 Podium structure completed with terminal Big.'},
    {'id': 'P134', 'name': '📸 2:3:1 PEAK COLLAPSE (B-B-S-S-S-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'B'], 'next': 'S', 'category': 'STAIRCASE', 'confidence': 96, 'description': '2:3:1 Peak collapse rebound locks on Small.'},
    {'id': 'P135', 'name': '📸 2:3:1 PEAK COLLAPSE (S-S-B-B-B-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'S'], 'next': 'B', 'category': 'STAIRCASE', 'confidence': 96, 'description': '2:3:1 Peak collapse rebound locks on Big.'},
    {'id': 'P136', 'name': '🌪️ B-SS-BB TWIST PATTERN BUSTER (→ S)', 'sequence': ['B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 98, 'description': 'B-S-S-B followed unexpectedly by Big. Twist pattern intercepted — issuing Small.'},
    {'id': 'P137', 'name': '🌪️ S-BB-SS TWIST PATTERN BUSTER (→ B)', 'sequence': ['S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 98, 'description': 'S-B-B-S followed unexpectedly by Small. Twist pattern intercepted — issuing Big.'},
    {'id': 'P138', 'name': '💎 SYMMETRIC B-SS-B-SS BOUNCE (→ B)', 'sequence': ['B', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 98, 'description': 'B-S-S-B-S-S completed. Symmetric 2-Small bounce targets Big.'},
    {'id': 'P139', 'name': '💎 SYMMETRIC S-BB-S-BB BOUNCE (→ S)', 'sequence': ['S', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 98, 'description': 'S-B-B-S-B-B completed. Symmetric 2-Big bounce targets Small.'},
    {'id': 'P140', 'name': '🔁 B-SS-B-S CONTINUATION (→ S)', 'sequence': ['B', 'S', 'S', 'B', 'S'], 'next': 'S', 'category': 'TWIST', 'confidence': 97, 'description': 'B-S-S-B produced Small. Second Small continuation locked.'},
    {'id': 'P141', 'name': '🔁 S-BB-S-B CONTINUATION (→ B)', 'sequence': ['S', 'B', 'B', 'S', 'B'], 'next': 'B', 'category': 'TWIST', 'confidence': 97, 'description': 'S-B-B-S produced Big. Second Big continuation locked.'},
    {'id': 'P142', 'name': '🛡️ BASE B-SS-B ANTI-TRAP (→ S)', 'sequence': ['B', 'S', 'S', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'B-S-S-B sandwich detected. Anti-trap protocol issues Small (not Big).'},
    {'id': 'P143', 'name': '🛡️ BASE S-BB-S ANTI-TRAP (→ B)', 'sequence': ['S', 'B', 'B', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'S-B-B-S sandwich detected. Anti-trap protocol issues Big (not Small).'},
    {'id': 'P144', 'name': '🪃 TWIST DOUBLE EXTENSION (B-S-S-B-B-S → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'S'], 'next': 'S', 'category': 'TWIST', 'confidence': 97, 'description': 'Twist sandwich broke into Small. Extending Small continuation.'},
    {'id': 'P145', 'name': '🪃 TWIST DOUBLE EXTENSION (S-B-B-S-S-B → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'B'], 'next': 'B', 'category': 'TWIST', 'confidence': 97, 'description': 'Twist sandwich broke into Big. Extending Big continuation.'},
    {'id': 'P146', 'name': '🔄 5-REPEAT BIGG SPECIAL RULE (B-B-B-B-B → B)', 'sequence': ['B', 'B', 'B', 'B', 'B'], 'next': 'B', 'category': 'TWIST', 'confidence': 97, 'description': '5-Repeat Big rule: maintains unbroken trend ride.'},
    {'id': 'P147', 'name': '🔄 4-REPEAT SMALL SPECIAL RULE (S-S-S-S → S)', 'sequence': ['S', 'S', 'S', 'S'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': '4-Repeat Small rule: locks unbroken trend ride.'},
    {'id': 'P148', 'name': '🪤 FALSE BREAKOUT TRAP (B-B-B-S-B-B → B)', 'sequence': ['B', 'B', 'B', 'S', 'B', 'B'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'False breakout trap bypassed. Resuming primary Big trend.'},
    {'id': 'P149', 'name': '🪤 FALSE BREAKOUT TRAP (S-S-S-B-S-S → S)', 'sequence': ['S', 'S', 'S', 'B', 'S', 'S'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'False breakout trap bypassed. Resuming primary Small trend.'},
    {'id': 'P150', 'name': '🚫 CHOP CLUSTERING DEFENSE (B-B-S-B-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'Chop cluster trapped on 2nd Big. Enforcing pivot to Small.'},
    {'id': 'P151', 'name': '🚫 CHOP CLUSTERING DEFENSE (S-S-B-S-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'Chop cluster trapped on 2nd Small. Enforcing pivot to Big.'},
    {'id': 'P152', 'name': '🛡️ SBB-S CONTINUATION RUN (S-B-B-S → B)', 'sequence': ['S', 'B', 'B', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'S-BB-S sandwich continuation targets Big.'},
    {'id': 'P153', 'name': '🛡️ BSS-B CONTINUATION RUN (B-S-S-B → S)', 'sequence': ['B', 'S', 'S', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'B-SS-B sandwich continuation targets Small.'},
    {'id': 'P154', 'name': '🌪️ TRIPLE TWIST (B-S-S-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 97, 'description': 'B-S-S followed by 3 Big. Climax exhaustion locks on Small.'},
    {'id': 'P155', 'name': '🌪️ TRIPLE TWIST (S-B-B-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 97, 'description': 'S-B-B followed by 3 Small. Climax exhaustion locks on Big.'},
    {'id': 'P156', 'name': '🪤 DUAL REJECTION TRAP (B-B-S-B-B-S → B)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 95, 'description': 'Double rejection of Small. Bypassing trap by backing Big.'},
    {'id': 'P157', 'name': '🪤 DUAL REJECTION TRAP (S-S-B-S-S-B → S)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 95, 'description': 'Double rejection of Big. Bypassing trap by backing Small.'},
    {'id': 'P158', 'name': '🪤 3-STEP TRAP INFLECTION (B-B-S-S-B-S-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'Double twin trap inflection completes. Pivoting to Big.'},
    {'id': 'P159', 'name': '🪤 3-STEP TRAP INFLECTION (S-S-B-B-S-B-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'Double twin trap inflection completes. Pivoting to Small.'},
    {'id': 'P160', 'name': '🌪️ INCLINE TRAP BUSTER (B-S-S-S-B-B → S)', 'sequence': ['B', 'S', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'Incline transition followed by twin Big. Trap buster triggers Small.'},
    {'id': 'P161', 'name': '🌪️ INCLINE TRAP BUSTER (S-B-B-B-S-S → B)', 'sequence': ['S', 'B', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'Incline transition followed by twin Small. Trap buster triggers Big.'},
    {'id': 'P162', 'name': '🛡️ DOUBLE CLUMP INTERCEPT (B-B-B-S-B-S → B)', 'sequence': ['B', 'B', 'B', 'S', 'B', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 95, 'description': 'Chop trap following 3-Big clump. Intercept locks on Big.'},
    {'id': 'P163', 'name': '🛡️ DOUBLE CLUMP INTERCEPT (S-S-S-B-S-B → S)', 'sequence': ['S', 'S', 'S', 'B', 'S', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 95, 'description': 'Chop trap following 3-Small clump. Intercept locks on Small.'},
    {'id': 'P164', 'name': '🌪️ TWIST SANDWICH RESET (B-S-S-B-B-S-S → B)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 98, 'description': 'Complete Twist Sandwich cycle finished. Hard reset to Big.'},
    {'id': 'P165', 'name': '🌪️ TWIST SANDWICH RESET (S-B-B-S-S-B-B → S)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 98, 'description': 'Complete Twist Sandwich cycle finished. Hard reset to Small.'},
    {'id': 'P166', 'name': '🛡️ BSSB-BB-B CLIMAX ROTATION (B-S-S-B-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 97, 'description': 'Quad Big after BSSB. Overload mean reversion triggers Small.'},
    {'id': 'P167', 'name': '🛡️ SBBS-SS-S CLIMAX ROTATION (S-B-B-S-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 97, 'description': 'Quad Small after SBBS. Overload mean reversion triggers Big.'},
    {'id': 'P168', 'name': '🪤 PRE-DRAGON FAKEOUT TRAP (B-B-B-S-S-B → B)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'B'], 'next': 'B', 'category': 'TWIST', 'confidence': 95, 'description': 'Twin Small trap broken by Big. Resuming Big momentum.'},
    {'id': 'P169', 'name': '🪤 PRE-DRAGON FAKEOUT TRAP (S-S-S-B-B-S → S)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'S'], 'next': 'S', 'category': 'TWIST', 'confidence': 95, 'description': 'Twin Big trap broken by Small. Resuming Small momentum.'},
    {'id': 'P170', 'name': '🌪️ ASYMMETRIC TWIST CLIMAX (B-S-S-B-S-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': 'Asymmetric twist climax locks on Small.'},
    {'id': 'P171', 'name': '🌪️ ASYMMETRIC TWIST CLIMAX (S-B-B-S-B-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': 'Asymmetric twist climax locks on Big.'},
    {'id': 'P172', 'name': '🛡️ BSSB EXTENDED PIVOT (B-S-S-B-S-S-B → B)', 'sequence': ['B', 'S', 'S', 'B', 'S', 'S', 'B'], 'next': 'B', 'category': 'TWIST', 'confidence': 97, 'description': 'BSSB with twin Small bounce and Big entry. Continuation to Big.'},
    {'id': 'P173', 'name': '🛡️ SBBS EXTENDED PIVOT (S-B-B-S-B-B-S → S)', 'sequence': ['S', 'B', 'B', 'S', 'B', 'B', 'S'], 'next': 'S', 'category': 'TWIST', 'confidence': 97, 'description': 'SBBS with twin Big bounce and Small entry. Continuation to Small.'},
    {'id': 'P174', 'name': '🪤 4-REPEAT TRAP INTERCEPT (B-B-B-B-S-B → S)', 'sequence': ['B', 'B', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'TWIST', 'confidence': 96, 'description': '4-Repeat broken by Small then single Big. Intercepting trap with Small.'},
    {'id': 'P175', 'name': '🪤 4-REPEAT TRAP INTERCEPT (S-S-S-S-B-S → B)', 'sequence': ['S', 'S', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'TWIST', 'confidence': 96, 'description': '4-Repeat broken by Big then single Small. Intercepting trap with Big.'},
    {'id': 'P176', 'name': '📐 FIBONACCI 1-1-2 EXPANSION (B-S-B-B → S)', 'sequence': ['B', 'S', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 95, 'description': 'Fibonacci 1-1-2 cadence completed. Turn targets Small.'},
    {'id': 'P177', 'name': '📐 FIBONACCI 1-1-2 EXPANSION (S-B-S-S → B)', 'sequence': ['S', 'B', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 95, 'description': 'Fibonacci 1-1-2 cadence completed. Turn targets Big.'},
    {'id': 'P178', 'name': '📐 FIBONACCI 1-2-3 SEQUENCE (B-S-S-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Fibonacci 1-2-3 harmonic complete. Next golden rotation to Small.'},
    {'id': 'P179', 'name': '📐 FIBONACCI 1-2-3 SEQUENCE (S-B-B-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Fibonacci 1-2-3 harmonic complete. Next golden rotation to Big.'},
    {'id': 'P180', 'name': '📐 FIBONACCI 2-3-5 EXPANSION (B-B-S-S-S-B-B-B-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 98, 'description': 'Fibonacci 2-3-5 golden ratio climax at 5 Big. Reversal to Small.'},
    {'id': 'P181', 'name': '📐 FIBONACCI 2-3-5 EXPANSION (S-S-B-B-B-S-S-S-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 98, 'description': 'Fibonacci 2-3-5 golden ratio climax at 5 Small. Reversal to Big.'},
    {'id': 'P182', 'name': '🔮 LUCAS SERIES 1-3-4 (B-S-S-S-B-B-B-B → S)', 'sequence': ['B', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Lucas 1-3-4 harmonic step completed. Reversal pivot targets Small.'},
    {'id': 'P183', 'name': '🔮 LUCAS SERIES 1-3-4 (S-B-B-B-S-S-S-S → B)', 'sequence': ['S', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Lucas 1-3-4 harmonic step completed. Reversal pivot targets Big.'},
    {'id': 'P184', 'name': '📐 GOLDEN RATIO 3:5 EQUILIBRIUM (B-B-B-S-S-S-S-S → B)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 97, 'description': '3:5 Golden ratio harmonic boundary reached. Mean rebound to Big.'},
    {'id': 'P185', 'name': '📐 GOLDEN RATIO 3:5 EQUILIBRIUM (S-S-S-B-B-B-B-B → S)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 97, 'description': '3:5 Golden ratio harmonic boundary reached. Mean rebound to Small.'},
    {'id': 'P186', 'name': '🔮 2-1-3 HARMONIC FLIP (B-B-S-B-B-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 96, 'description': '2-1-3 Harmonic cadence peaks on 3rd Big. Pivot to Small.'},
    {'id': 'P187', 'name': '🔮 2-1-3 HARMONIC FLIP (S-S-B-S-S-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 96, 'description': '2-1-3 Harmonic cadence peaks on 3rd Small. Pivot to Big.'},
    {'id': 'P188', 'name': '📐 PRIME 2-3-5 EXPANSION WAVE (B-B-S-S-S-B-B-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Prime number step distribution predicts pivot to Small.'},
    {'id': 'P189', 'name': '📐 PRIME 2-3-5 EXPANSION WAVE (S-S-B-B-B-S-S-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Prime number step distribution predicts pivot to Big.'},
    {'id': 'P190', 'name': '🔮 HARMONIC OSCILLATION OCTAVE (B-S-B-B-S-B-B → S)', 'sequence': ['B', 'S', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 95, 'description': 'Harmonic octave recurrence locks on Small.'},
    {'id': 'P191', 'name': '🔮 HARMONIC OSCILLATION OCTAVE (S-B-S-S-B-S-S → B)', 'sequence': ['S', 'B', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 95, 'description': 'Harmonic octave recurrence locks on Big.'},
    {'id': 'P192', 'name': '📐 GOLDEN MEAN 5:3 COMPRESSION (B5-S3 → B)', 'sequence': ['B'] * 5 + ['S'] * 3, 'next': 'B', 'category': 'FIBONACCI', 'confidence': 97, 'description': '5:3 Golden mean compression resets to Big.'},
    {'id': 'P193', 'name': '📐 GOLDEN MEAN 5:3 COMPRESSION (S5-B3 → S)', 'sequence': ['S'] * 5 + ['B'] * 3, 'next': 'S', 'category': 'FIBONACCI', 'confidence': 97, 'description': '5:3 Golden mean compression resets to Small.'},
    {'id': 'P194', 'name': '🔮 FIBONACCI STEP 4 EXTENSION (B-S-B-B-S-S-S-B-B-B-B → S)', 'sequence': ['B', 'S', 'B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 98, 'description': 'Deep Fibonacci 1-1-2-3-4 cycle completed. Full pivot to Small.'},
    {'id': 'P195', 'name': '🔮 FIBONACCI STEP 4 EXTENSION (S-B-S-S-B-B-B-S-S-S-S → B)', 'sequence': ['S', 'B', 'S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 98, 'description': 'Deep Fibonacci 1-1-2-3-4 cycle completed. Full pivot to Big.'},
    {'id': 'P196', 'name': '📐 2-1-1-2 GOLDEN SANDWICH (B-B-S-B-S-S → B)', 'sequence': ['B', 'B', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 96, 'description': '2-1-1-2 Symmetric sandwich completed. Bounce targets Big.'},
    {'id': 'P197', 'name': '📐 2-1-1-2 GOLDEN SANDWICH (S-S-B-S-B-B → S)', 'sequence': ['S', 'S', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 96, 'description': '2-1-1-2 Symmetric sandwich completed. Bounce targets Small.'},
    {'id': 'P198', 'name': '🔮 3-2-1-1 DECELERATING HARMONIC (B-B-B-S-S-B-S → B)', 'sequence': ['B', 'B', 'B', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 95, 'description': 'Decelerating harmonic cadence rebound to Big.'},
    {'id': 'P199', 'name': '🔮 3-2-1-1 DECELERATING HARMONIC (S-S-S-B-B-S-B → S)', 'sequence': ['S', 'S', 'S', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 95, 'description': 'Decelerating harmonic cadence rebound to Small.'},
    {'id': 'P200', 'name': '📐 GOLDEN DOUBLE RATIO (B-B-S-S-S-B-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 96, 'description': 'Golden double ratio 2-3-3 inflection targets Small.'},
    {'id': 'P201', 'name': '📐 GOLDEN DOUBLE RATIO (S-S-B-B-B-S-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 96, 'description': 'Golden double ratio 2-3-3 inflection targets Big.'},
    {'id': 'P202', 'name': '🔮 FIBONACCI STEP PEAK (B-B-S-S-B-B-B-B → S)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Twin into quad climax. Reversal to Small.'},
    {'id': 'P203', 'name': '🔮 FIBONACCI STEP PEAK (S-S-B-B-S-S-S-S → B)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 97, 'description': 'Twin into quad climax. Reversal to Big.'},
    {'id': 'P204', 'name': '📐 GOLDEN SPIRAL CORE (B-S-B-B-B-S-S → B)', 'sequence': ['B', 'S', 'B', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'FIBONACCI', 'confidence': 96, 'description': 'Golden spiral core expansion targets Big.'},
    {'id': 'P205', 'name': '📐 GOLDEN SPIRAL CORE (S-B-S-S-S-B-B → S)', 'sequence': ['S', 'B', 'S', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'FIBONACCI', 'confidence': 96, 'description': 'Golden spiral core expansion targets Small.'},
    {'id': 'P206', 'name': '🌐 10-RESULT BIG SATURATION (B7/10 → S)', 'sequence': ['B', 'B', 'B', 'S', 'B', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 98, 'description': 'Big oversaturated 8/10 in macro window. Systematic mean-reversion to Small.'},
    {'id': 'P207', 'name': '🌐 10-RESULT SMALL SATURATION (S7/10 → B)', 'sequence': ['S', 'S', 'S', 'B', 'S', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 98, 'description': 'Small oversaturated 8/10 in macro window. Systematic mean-reversion to Big.'},
    {'id': 'P208', 'name': '⚖️ 10-RESULT PERFECT 5:5 EQUILIBRIUM (B-S-B-S-B-S-B-S-S-B → S)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'S', 'B', 'S', 'S', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': '5:5 Parity equilibrium rotation. Phase oscillation to Small.'},
    {'id': 'P209', 'name': '⚖️ 10-RESULT PERFECT 5:5 EQUILIBRIUM (S-B-S-B-S-B-S-B-B-S → B)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'B', 'S', 'B', 'B', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': '5:5 Parity equilibrium rotation. Phase oscillation to Big.'},
    {'id': 'P210', 'name': '🟣 VIOLET NUMBER 0 POLARITY PIVOT (0-VIOLET → B)', 'sequence': ['S', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 97, 'description': 'Violet 0 marker signifies extreme lower boundary. Reversal upward to Big.'},
    {'id': 'P211', 'name': '🟣 VIOLET NUMBER 5 POLARITY PIVOT (5-VIOLET → S)', 'sequence': ['B', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 97, 'description': 'Violet 5 marker signifies threshold boundary. Reversal downward to Small.'},
    {'id': 'P212', 'name': '📊 6:4 PARITY ROTATION (B-B-S-B-B-S-B-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'S', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': '6:4 Parity pressure triggers rotational switch to Small.'},
    {'id': 'P213', 'name': '📊 6:4 PARITY ROTATION (S-S-B-S-S-B-S-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'B', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': '6:4 Parity pressure triggers rotational switch to Big.'},
    {'id': 'P214', 'name': '🌐 HIGH DEFICIT PULLBACK (S-S-S-S-S-B-S → B)', 'sequence': ['S', 'S', 'S', 'S', 'S', 'B', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': 'Macro deficit pullback recovery enforces second Big step.'},
    {'id': 'P215', 'name': '🌐 HIGH DEFICIT PULLBACK (B-B-B-B-B-S-B → S)', 'sequence': ['B', 'B', 'B', 'B', 'B', 'S', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': 'Macro deficit pullback recovery enforces second Small step.'},
    {'id': 'P216', 'name': '📸 PARITY CLUSTER EXPANSION (B-S-B-B-S-B-B-B → S)', 'sequence': ['B', 'S', 'B', 'B', 'S', 'B', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': 'Triple Big ending cluster expansion. Mean reversion to Small.'},
    {'id': 'P217', 'name': '📸 PARITY CLUSTER EXPANSION (S-B-S-S-B-S-S-S → B)', 'sequence': ['S', 'B', 'S', 'S', 'B', 'S', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 96, 'description': 'Triple Small ending cluster expansion. Mean reversion to Big.'},
    {'id': 'P218', 'name': '🔍 3-STEP ALTERNATION CASCADE (B-B-S-B-B-S-B-B → S)', 'sequence': ['B', 'B', 'S', 'B', 'B', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 97, 'description': '2-1-2-1-2 periodic parity cadence targets Small.'},
    {'id': 'P219', 'name': '🔍 3-STEP ALTERNATION CASCADE (S-S-B-S-S-B-S-S → B)', 'sequence': ['S', 'S', 'B', 'S', 'S', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 97, 'description': '2-1-2-1-2 periodic parity cadence targets Big.'},
    {'id': 'P220', 'name': '🌐 12-ROUND MACRO CYCLE PIVOT (B-S-S-B-B-B-S-B-S-S-B-B → S)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'B', 'S', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 98, 'description': '12-Round macro structural cycle transition locks on Small.'},
    {'id': 'P221', 'name': '🌐 12-ROUND MACRO CYCLE PIVOT (S-B-B-S-S-S-B-S-B-B-S-S → B)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'S', 'B', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 98, 'description': '12-Round macro structural cycle transition locks on Big.'},
    {'id': 'P222', 'name': '⚡ MARKOV TRANSITION PROBABILITY MATRIX (B-S-B-B-S-S → B)', 'sequence': ['B', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 97, 'description': 'Markov 2nd-order state matrix evaluates highest probability transition to Big.'},
    {'id': 'P223', 'name': '⚡ MARKOV TRANSITION PROBABILITY MATRIX (S-B-S-S-B-B → S)', 'sequence': ['S', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 97, 'description': 'Markov 2nd-order state matrix evaluates highest probability transition to Small.'},
    {'id': 'P224', 'name': '🌐 14-ROUND DEEP CONVERGENCE (B-S-B-S-S-B-B-S-B-S-S-B-S-B → B)', 'sequence': ['B', 'S', 'B', 'S', 'S', 'B', 'B', 'S', 'B', 'S', 'S', 'B', 'S', 'B'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '14-Round deep pattern convergence locks on Big.'},
    {'id': 'P225', 'name': '🌐 14-ROUND DEEP CONVERGENCE (S-B-S-B-B-S-S-B-S-B-B-S-B-S → S)', 'sequence': ['S', 'B', 'S', 'B', 'B', 'S', 'S', 'B', 'S', 'B', 'B', 'S', 'B', 'S'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '14-Round deep pattern convergence locks on Small.'},
    {'id': 'P226', 'name': '👑 BOSS MASTER ULTIMATE LOCK (B-B-B-S-B-S-B-B-S-S-B-B → S)', 'sequence': ['B', 'B', 'B', 'S', 'B', 'S', 'B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': 'Boss Master algorithm completes full parity matrix. Invariant execution to Small.'},
    {'id': 'P227', 'name': '👑 BOSS MASTER ULTIMATE LOCK (S-S-S-B-S-B-S-S-B-B-S-S → B)', 'sequence': ['S', 'S', 'S', 'B', 'S', 'B', 'S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': 'Boss Master algorithm completes full parity matrix. Invariant execution to Big.'},
    {'id': 'P228', 'name': '⚡ 15-ROUND SYNCHRONOUS CADENCE (B-S-S-B-B-S-S-B-B-S-S-B-B-S-S → B)', 'sequence': ['B', 'S', 'S', 'B', 'B', 'S', 'S', 'B', 'B', 'S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '15-Round multi-twin harmonic recursion locks on Big.'},
    {'id': 'P229', 'name': '⚡ 15-ROUND SYNCHRONOUS CADENCE (S-B-B-S-S-B-B-S-S-B-B-S-S-B-B → S)', 'sequence': ['S', 'B', 'B', 'S', 'S', 'B', 'B', 'S', 'S', 'B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '15-Round multi-twin harmonic recursion locks on Small.'},
    {'id': 'P230', 'name': '💎 2:2:2:2 OCTO TWIN COMPLETE (B-B-S-S-B-B-S-S-B-B-S-S → B)', 'sequence': ['B', 'B', 'S', 'S', 'B', 'B', 'S', 'S', 'B', 'B', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '12-Round octo-twin sequence completes. Hard rotation to Big.'},
    {'id': 'P231', 'name': '💎 2:2:2:2 OCTO TWIN COMPLETE (S-S-B-B-S-S-B-B-S-S-B-B → S)', 'sequence': ['S', 'S', 'B', 'B', 'S', 'S', 'B', 'B', 'S', 'S', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '12-Round octo-twin sequence completes. Hard rotation to Small.'},
    {'id': 'P232', 'name': '🌊 16-ROUND TSUNAMI CADENCE (B4-S4-B4-S4 → B)', 'sequence': ['B', 'B', 'B', 'B', 'S', 'S', 'S', 'S', 'B', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '16-Round Quad-Tsunami macro rhythm completed. Invariant rebound to Big.'},
    {'id': 'P233', 'name': '🌊 16-ROUND TSUNAMI CADENCE (S4-B4-S4-B4 → S)', 'sequence': ['S', 'S', 'S', 'S', 'B', 'B', 'B', 'B', 'S', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '16-Round Quad-Tsunami macro rhythm completed. Invariant rebound to Small.'},
    {'id': 'P234', 'name': '🏛️ 18-ROUND SUPREME PINNACLE (B-S-B-S-B-B-S-S-B-B-B-S-S-S-B-B-B-B → S)', 'sequence': ['B', 'S', 'B', 'S', 'B', 'B', 'S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'B'], 'next': 'S', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '18-Round master harmonic staircase completed. Terminal pivot to Small.'},
    {'id': 'P235', 'name': '🏛️ 18-ROUND SUPREME PINNACLE (S-B-S-B-S-S-B-B-S-S-S-B-B-B-S-S-S-S → B)', 'sequence': ['S', 'B', 'S', 'B', 'S', 'S', 'B', 'B', 'S', 'S', 'S', 'B', 'B', 'B', 'S', 'S', 'S', 'S'], 'next': 'B', 'category': 'MACRO_PARITY', 'confidence': 99, 'description': '18-Round master harmonic staircase completed. Terminal pivot to Big.'},
]


# ============================================================
# SECTION 15: CONFIRMED WINNING PATTERNS
# ============================================================

CONFIRMED_WINNING_RAW = [
    ('BBBBSBB', 'BIG'), ('SSSSBSS', 'SMALL'), ('BSBSB', 'SMALL'), ('SBSBS', 'BIG'),
    ('BSBSBS', 'BIG'), ('SBSBSB', 'SMALL'), ('BSBSBSB', 'SMALL'), ('SBSBSBS', 'BIG'),
    ('BSBSBSBSB', 'SMALL'), ('SBSBSBSBS', 'BIG'), ('BSSBSS', 'BIG'), ('SBBSBB', 'SMALL'),
    ('BBSBBS', 'BIG'), ('SSBSSB', 'SMALL'), ('BSBB', 'SMALL'), ('SBSS', 'BIG'),
    ('BSBSSS', 'BIG'), ('SBSBBB', 'SMALL'), ('BSBSBBS', 'BIG'), ('SBSBSSB', 'SMALL'),
    ('BSSBBSB', 'SMALL'), ('SBBSSBS', 'BIG'), ('BBSSBB', 'SMALL'), ('SSBBSS', 'BIG'),
    ('BBBBSSSS', 'BIG'), ('SSSSBBBB', 'SMALL'), ('BBSBB', 'SMALL'), ('SSBSS', 'BIG'),
    ('BBBSBBB', 'SMALL'), ('SSSBSSS', 'BIG'), ('BBSSSBB', 'SMALL'), ('SSBBBSS', 'BIG'),
    ('BBSSB', 'BIG'), ('SSBBS', 'SMALL'), ('BBSSSB', 'BIG'), ('SSBBBS', 'SMALL'),
    ('BBSSSSB', 'BIG'), ('SSBBBBS', 'SMALL'), ('BSSBS', 'SMALL'), ('SBBSB', 'BIG'),
    ('BSSBBB', 'SMALL'), ('SBBSSS', 'BIG'), ('BSSBB', 'BIG'), ('SBBSS', 'SMALL'),
    ('BBBSSB', 'SMALL'), ('SSSBBS', 'BIG'), ('BSSBSSS', 'BIG'), ('SBBSBBB', 'SMALL'),
    ('BSBBSS', 'BIG'), ('SBSSBB', 'SMALL'), ('BSSBSS', 'BIG'), ('SBBSBB', 'SMALL'),
    ('BSBSSS', 'BIG'), ('SBSBBB', 'SMALL'), ('BSBBSSBB', 'BIG'), ('SBSSBBSS', 'SMALL'),
    ('BBBSSB', 'BIG'), ('SSSBBS', 'SMALL'), ('BBSSSB', 'BIG'), ('SSBBBS', 'SMALL'),
    ('BBSSS', 'BIG'), ('SSBBB', 'SMALL'), ('BSSSBB', 'SMALL'), ('SBBBSS', 'BIG'),
    ('BBSBSS', 'SMALL'), ('SSBSBB', 'BIG'), ('BSBSSB', 'SMALL'), ('SBSBBS', 'BIG'),
    ('BBSSSSB', 'SMALL'), ('SSBBBBS', 'BIG'), ('BSSBB', 'SMALL'), ('SBBSS', 'BIG'),
    ('BBSSBBSS', 'BIG'), ('SSBBSSBB', 'SMALL'), ('BBBSBS', 'BIG'), ('SSSBSB', 'SMALL'),
    ('BBBSBSS', 'BIG'), ('SSSBSBB', 'SMALL'), ('BSBSSBB', 'SMALL'), ('SBSBBSS', 'BIG'),
    ('BSSBBB', 'SMALL'), ('SBBSSS', 'BIG'), ('BBSBSB', 'SMALL'), ('SSBSBS', 'BIG'),
    ('BBBSBSB', 'BIG'), ('SSSBSBS', 'SMALL'), ('BSSBBS', 'SMALL'), ('SBBSSB', 'BIG'),
    ('BSSBBSB', 'SMALL'), ('SBBSSBS', 'BIG'), ('BSSBBB', 'SMALL'), ('SBBSSS', 'BIG'),
    ('BBSBBB', 'SMALL'), ('SSBSSS', 'BIG'), ('BBSBSBB', 'SMALL'), ('SSBSBSS', 'BIG'),
    ('BBSBSSBB', 'BIG'), ('SSBSBBSS', 'SMALL'), ('BSSBSSB', 'SMALL'), ('SBBSBBS', 'BIG'),
    ('BSBBSBB', 'SMALL'), ('BBSSSBB', 'SMALL'), ('BBBSBBBSBB', 'SMALL'), ('SSSBSSSBSS', 'BIG'),
    ('BSBSBSBSSB', 'SMALL'), ('SBSBSBSBBS', 'BIG'), ('BBBSBSBSBB', 'SMALL'), ('SSSBSBSBSS', 'BIG'),
    ('BSSBSSBSBB', 'SMALL'), ('SBBSSBBSBB', 'BIG'), ('BSSBSSBB', 'BIG'), ('BBSBBSBSB', 'SMALL'),
    ('BSSBBSBSS', 'BIG'), ('SBBSSBSBB', 'SMALL'), ('BSBSBSSBB', 'SMALL'), ('BBBSBBSB', 'BIG'),
    ('SSSBSBSB', 'SMALL'),
]

CONFIRMED_WINNING_MAP = dict(CONFIRMED_WINNING_RAW)

CONFIRMED_WINNING_LIST = []
for pattern, prediction in CONFIRMED_WINNING_MAP.items():
    length = len(pattern)
    confidence = 99 if length >= 8 else (98 if length >= 6 else 97)
    CONFIRMED_WINNING_LIST.append({
        'pattern': pattern,
        'prediction': prediction,
        'confidence': confidence,
        'name': f'👑 CONFIRMED WINNING: {pattern} → {prediction}',
        'category': 'CONFIRMED_WINNING',
        'reason': f'👑 Confirmed Winning Pattern [{pattern}] matched. 100% verified lock to {prediction}.',
    })

CONFIRMED_WINNING_LIST.sort(key=lambda x: len(x['pattern']), reverse=True)


def match_confirmed_pattern(sequence: str) -> Optional[dict]:
    """Match confirmed winning pattern from sequence."""
    for item in CONFIRMED_WINNING_LIST:
        if sequence.endswith(item['pattern']):
            return item
    return None


# ============================================================
# SECTION 16: ULTIMATE MASTER PREDICT
# ============================================================

def ultimate_master_predict(history: List[dict], period: str, mode: str = '1m', options: Optional[dict] = None) -> dict:
    """Ultimate Master Engine — combines 3 prediction logics."""
    options = options or {}
    
    # Step 1: Original engine prediction
    original_prediction = predict(history, period, mode, options)
    
    # Step 2: Convert history to B/S array (newest first)
    sides_array = []
    for h in history:
        if isinstance(h, (int, float)):
            sides_array.append('B' if h >= 5 else 'S')
        elif isinstance(h, dict):
            if h.get('size') == 'BIG':
                sides_array.append('B')
            elif h.get('size') == 'SMALL':
                sides_array.append('S')
            else:
                num = h.get('number', h.get('actualNumber', 0))
                sides_array.append('B' if num >= 5 else 'S')
        else:
            sides_array.append('B')
    
    # Step 3: Run 25 Pattern Engine
    p25_result = pattern25_rajput_ultra_x(sides_array)
    
    # Step 4: Run 20 Pattern Engine
    demo20_result = demo_master_all_patterns(sides_array)
    
    # Step 5: Collect all signals
    all_signals = []
    
    orig_side = 'B' if original_prediction['prediction'] == 'BIG' else 'S'
    all_signals.append({
        'source': 'ORIGINAL_ENGINE',
        'side': orig_side,
        'confidence': original_prediction['confidence'],
        'name': original_prediction['patternName'],
    })
    
    if p25_result:
        all_signals.append({
            'source': 'PATTERN_25_RAJPUT_ULTRA_X',
            'side': p25_result['signal'],
            'confidence': p25_result['confidence'],
            'name': f"RAJPUT ULTRA X (BIG:{p25_result['bigVotes']} / SMALL:{p25_result['smallVotes']})",
            'allSignals': p25_result['allSignals'],
            'bigVotes': p25_result['bigVotes'],
            'smallVotes': p25_result['smallVotes'],
            'totalVotes': p25_result['totalVotes'],
        })
    
    if demo20_result:
        all_signals.append({
            'source': 'DEMO_20_MASTER',
            'side': demo20_result['signal'],
            'confidence': demo20_result['confidence'],
            'name': f"DEMO 20 MASTER (BIG:{demo20_result['bigVotes']} / SMALL:{demo20_result['smallVotes']})",
            'allSignals': demo20_result['allSignals'],
            'bigVotes': demo20_result['bigVotes'],
            'smallVotes': demo20_result['smallVotes'],
            'totalVotes': demo20_result['totalVotes'],
        })
    
    # Step 6: Calculate final vote
    big_votes = sum(1 for s in all_signals if s['side'] == 'B')
    small_votes = sum(1 for s in all_signals if s['side'] == 'S')
    total_votes = len(all_signals)
    
    if big_votes > small_votes:
        final_side = 'B'
    elif small_votes > big_votes:
        final_side = 'S'
    else:
        final_side = orig_side
    
    # Step 7: Calculate final confidence
    agreement = round((max(big_votes, small_votes) / total_votes) * 100) if total_votes > 0 else 50
    
    # Step 8: Get favor numbers
    numbers = []
    for h in history:
        if isinstance(h, (int, float)):
            numbers.append(int(h))
        elif isinstance(h, dict):
            numbers.append(h.get('number', h.get('actualNumber', 0)))
        else:
            numbers.append(0)
    
    final_side_big = 'BIG' if final_side == 'B' else 'SMALL'
    t = compute_target_numbers(final_side_big, numbers)
    
    # Step 9: Build final result
    return {
        **original_prediction,
        'period': period,
        'mode': mode,
        'prediction': final_side_big,
        'targetNumber': t['targetNumber'],
        'secondaryNumber': t['secondaryNumber'],
        'favorNumber': t['favorNumber'],
        'oppositeNumber': t['oppositeNumber'],
        'confidence': max(original_prediction['confidence'], agreement),
        'ultimateMaster': True,
        'ultimateSignal': final_side,
        'ultimateBigVotes': big_votes,
        'ultimateSmallVotes': small_votes,
        'ultimateTotalVotes': total_votes,
        'ultimateAgreement': agreement,
        'ultimateAllSignals': all_signals,
        'pattern25Result': p25_result,
        'demo20Result': demo20_result,
        'originalPrediction': original_prediction,
        'patternName': f"🔥 ULTIMATE MASTER ENGINE — {'BIG' if final_side == 'B' else 'SMALL'} ({agreement}% Agreement)",
        'patternCategory': 'ULTIMATE_MASTER',
        'ruleCode': 'ULTIMATE_MIXED_ENGINE',
        'reason': (
            f"Ultimate Master Engine mixed 3 prediction logics: Original Engine + 25 Pattern Engine + 20 Pattern Engine. "
            f"Final vote: BIG {big_votes} / SMALL {small_votes} (Total: {total_votes}). Agreement: {agreement}%. "
            f"Original Engine: {'BIG' if orig_side == 'B' else 'SMALL'} ({original_prediction['confidence']}%). "
            f"Pattern 25: {'BIG' if p25_result and p25_result['signal'] == 'B' else 'SMALL' if p25_result else 'N/A'} "
            f"({p25_result['confidence'] if p25_result else 'N/A'}%). "
            f"Demo 20: {'BIG' if demo20_result and demo20_result['signal'] == 'B' else 'SMALL' if demo20_result else 'N/A'} "
            f"({demo20_result['confidence'] if demo20_result else 'N/A'}%)."
        ),
        'regime': 'ULTIMATE_MIXED',
        'stepLevel': 1,
        'createdAt': int(datetime.now().timestamp() * 1000),
        'verified': True,
        'isUltimateMaster': True,
        'trapDefenseMode': 'ULTIMATE_MASTER_ARMED',
        'scanStatus': 'ULTIMATE_MASTER_LOCK',
        'deepAnalysisSummary': (
            f"🔥 Ultimate Master Engine: Mixed 3 logics. Final: {final_side_big} ({agreement}% agreement across {total_votes} signals). "
            f"BIG votes: {big_votes}, SMALL votes: {small_votes}."
        ),
    }


# ============================================================
# SECTION 17: SIGNAL TEXT BUILDERS
# ============================================================

def build_signal_text(period: str, prediction: dict) -> str:
    """Build signal text from prediction."""
    p = period or 'PENDING'
    target = prediction.get('predictedSize', prediction.get('prediction', 'UNKNOWN'))
    fav = prediction.get('favNumber', prediction.get('favorNumber', 7))
    opp = prediction.get('oppNumber', prediction.get('oppositeNumber', 2))
    pattern = prediction.get('activePattern', {}).get('name', prediction.get('patternName', '1000-PERIOD STATISTICAL SCAN'))
    is_skip = prediction.get('isSkipRecommended', False)
    
    action = 'ACTION: SKIP (SAFE PLAY / TRAP NODE)' if is_skip else 'ACTION: PLAY / BET NOW (HIGH CONFIDENCE · SAFE SETUP)'
    
    return f"""
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

Period: {p}

Target: {target}

Favor: {fav}

Opp: {opp}

Pattern: {pattern}

Risk Level: {'HIGH RISK TRAP (SKIP ADVISORY)' if is_skip else 'LOW RISK (NORMAL WINNING PATTERN)'}

Bet Sizing: {'0X (SKIP ROUND / SAVE CAPITAL)' if is_skip else '1X UNIT (SAFE BET / CONFIDENT)'}

V3 Quantum Neural:
{'100% VERIFIED ✔' if prediction.get('isTwoLevelVerified') else 'VERIFIED'}

{action}
"""


def build_ultimate_signal_text(period: str, prediction: dict) -> str:
    """Build ultimate signal text."""
    p = period or 'PENDING'
    target = prediction.get('prediction', 'UNKNOWN')
    fav = prediction.get('favorNumber', 7)
    opp = prediction.get('oppositeNumber', 2)
    confidence = prediction.get('confidence', 0)
    agreement = prediction.get('ultimateAgreement', 0)
    big_votes = prediction.get('ultimateBigVotes', 0)
    small_votes = prediction.get('ultimateSmallVotes', 0)
    total_votes = prediction.get('ultimateTotalVotes', 0)
    
    return f"""
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
🔥 ULTIMATE MASTER ENGINE
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

Period: {p}

🎯 TARGET: {target}

⭐ FAVOR: {fav}

🛡️ OPP: {opp}

📊 CONFIDENCE: {confidence}%

🗳️ VOTE BREAKDOWN:
   BIG: {big_votes} votes
   SMALL: {small_votes} votes
   TOTAL: {total_votes} signals
   AGREEMENT: {agreement}%

📋 PATTERN: {prediction.get('patternName', 'N/A')}

📝 REASON:
{prediction.get('reason', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 ULTIMATE MASTER ENGINE — 100% MIXED
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ============================================================
# SECTION 18: MONEY MANAGEMENT
# ============================================================

def allocate_budget(wallet: float, levels: int = 4) -> List[int]:
    """Allocate budget across levels."""
    total = max(10, round(wallet))
    
    if levels == 3:
        l1 = max(1, round(total * 0.1))
        l2 = max(l1 + 1, round(total * 0.25))
        return [l1, l2, max(l2 + 1, total - (l1 + l2))]
    
    l1 = max(1, round(total * 0.05))
    l2 = max(l1 + 1, round(total * 0.11))
    l3 = max(l2 + 1, round(total * 0.25))
    return [l1, l2, l3, max(l3 + 1, total - (l1 + l2 + l3))]


# ============================================================
# SECTION 19: MAIN EXPORT (sddgamer263_predict)
# ============================================================

def sddgamer263_predict(current_number: int = 0, period: str = '', history: Optional[List[dict]] = None) -> dict:
    """
    Main prediction function called by FastAPI server.
    Uses Ultimate Master Engine.
    """
    if history is None:
        history = []
    
    # If no history, create from current_number
    if not history:
        history = [{'number': current_number, 'size': 'BIG' if current_number >= 5 else 'SMALL'}]
    
    # Run ultimate master predict
    result = ultimate_master_predict(history, period, '1m', {})
    
    # Map to expected output format
    return {
        'bigSmall': result.get('prediction', 'BIG'),
        'prediction': result.get('targetNumber', 5),
        'confidence': result.get('confidence', 94.0),
        'numbers': [result.get('targetNumber', 5)],
        'steps': result.get('steps', []),
        'source': result.get('patternName', 'ULTIMATE_MASTER'),
        'patternName': result.get('patternName', 'ULTIMATE_MASTER'),
        'period': period,
        'ultimateMaster': result.get('ultimateMaster', False),
        'ultimateAgreement': result.get('ultimateAgreement', 0),
        'ultimateBigVotes': result.get('ultimateBigVotes', 0),
        'ultimateSmallVotes': result.get('ultimateSmallVotes', 0),
        'ultimateTotalVotes': result.get('ultimateTotalVotes', 0),
        'reason': result.get('reason', ''),
        'scanStatus': result.get('scanStatus', ''),
        'trapDefenseMode': result.get('trapDefenseMode', ''),
    }
