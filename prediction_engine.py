#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#  NAVEEN AI TOOL 2026 — Python Port
#  Prediction logic: 100% same as JS (routes-Dl9jpyPE.js)
#  Old logic: FULLY REMOVED
# ═══════════════════════════════════════════════════════════════

import time
import requests
import os

# ─── Colors ───
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
WHITE   = "\033[97m"
RESET   = "\033[0m"
BOLD    = "\033[1m"

# ─── Banner font ───
try:
    from cfonts import render
except ImportError:
    os.system('pip install python-cfonts -q')
    from cfonts import render

# ─── API ───
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-100"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hgnice.biz"
}


# ═══════════════════════════════════════════════════════════════
#  CORE PREDICTION LOGIC — JS ka exact port
# ═══════════════════════════════════════════════════════════════

def fnv1a_hash(s: str) -> int:
    """
    JS re() function ka exact port.
    FNV-1a 32-bit hash — deterministic randomness ke liye.
    """
    t = 2166136261
    for ch in s:
        t ^= ord(ch)
        t = (t * 16777619) & 0xFFFFFFFF   # Math.imul 32-bit wrap
    return abs(t)


def next_issue(issue: str) -> str:
    """
    JS ne() function ka exact port.
    Period number ko +1 karta hai, leading zeros preserve karte hue.
    """
    digits = ''.join(c for c in issue if c.isdigit())
    if not digits:
        return issue
    nxt = str(int(digits) + 1).zfill(len(digits))
    return issue.replace(digits, nxt)


def get_big_small(num: int) -> str:
    """Number >= 5 → BIG, warna SMALL."""
    return "BIG" if num >= 5 else "SMALL"


def predict(results, last_issue: str):
    """
    JS te() function ka exact port.

    Input:
        results    = list of dicts [{'period':..., 'number':int, 'size':...}, ...]
                     (latest pehle, matlab results[0] = sabse naya)
        last_issue = latest period number (string)

    Output:
        {
          'issue': next period number,
          'size': 'BIG' / 'SMALL',
          'confidence': 68..97,
          'score': float
        }
    """
    if not results:
        return None

    # ── Step 1: Next period number ──
    n = next_issue(last_issue)

    # ── Step 2: Last 10 results lo ──
    r = results[:10]
    if not r:
        return None

    # ── Step 3: Weighted trend score ──
    i = 0.0
    for idx, item in enumerate(r):
        weight = 1.0 / (idx + 1)                              # 1, 1/2, 1/3 ...
        size_sign = 1 if item['size'] == 'BIG' else -1
        i += size_sign * weight                               # BIG=+, SMALL=-
        i += (item['number'] - 4.5) / 4.5 * weight * 0.6      # number bias

    # ── Step 4: Streak reversal detection ──
    a = 1
    while a < len(r) and r[a]['size'] == r[0]['size']:
        a += 1
    if a >= 3:
        # 3+ same → reverse predict
        i += -1.4 if r[0]['size'] == 'BIG' else 1.4

    # ── Step 5: Deterministic hash noise ──
    o = fnv1a_hash(n) % 1000
    i += (o / 1000.0 - 0.5) * 0.5

    # ── Step 6: Final prediction ──
    size = 'BIG' if i < 0 else 'SMALL'
    confidence = min(97, 68 + round(abs(i) * 9))

    return {
        'issue': n,
        'size': size,
        'confidence': confidence,
        'score': round(i, 4)
    }


# ═══════════════════════════════════════════════════════════════
#  API FETCH
# ═══════════════════════════════════════════════════════════════

def fetch_data():
    """Yaar Win server se last 100 WinGo results laata hai."""
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        data = res.json()

        if 'data' in data and 'list' in data['data']:
            out = []
            for item in data['data']['list']:
                num = int(item['number'])
                out.append({
                    'period': str(item['issueNumber']),
                    'number': num,
                    'size': get_big_small(num)
                })
            return out
    except Exception as e:
        print(f"{RED}Fetch error: {e}{RESET}")
        return []
    return []


# ═══════════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════════

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    output = render('SDD', colors=['yellow', 'green'], align='center', font='block')
    print(output)
    print(f"{CYAN}{'═' * 40}{RESET}")
    print(f"{YELLOW}{BOLD}🔥 1 MINUTE AUTO MODE ACTIVE 🔥{RESET}")
    print(f"{CYAN}{'═' * 40}{RESET}\n")


def print_prediction(period, pred, confidence, score):
    short_period = period[-3:]
    print(f"\n{MAGENTA}{'━' * 40}{RESET}")
    print(f"{CYAN}⏱ PERIOD     ➜ {WHITE}{short_period}{RESET}")
    color = RED if pred == "BIG" else GREEN
    print(f"{CYAN}🎯 PREDICTION ➜ {color}{BOLD}{pred}{RESET}")
    print(f"{CYAN}📈 CONFIDENCE ➜ {WHITE}{confidence}%{RESET}")
    print(f"{CYAN}🧮 SCORE      ➜ {WHITE}{score}{RESET}")
    print(f"{CYAN}📊 RESULT     ➜ {RESET}", end="", flush=True)


def print_result(actual_num, pred_type):
    actual_type = get_big_small(actual_num)
    if actual_type == pred_type:
        print(f"{GREEN}{BOLD}WIN ✅ [{actual_num} {actual_type}]{RESET}")
    else:
        print(f"{RED}{BOLD}LOSS ❌ [{actual_num} {actual_type}]{RESET}")


# ═══════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════

def run():
    banner()

    last_period = None
    active_prediction = None
    predicted_period = None

    while True:
        data = fetch_data()

        if not data or len(data) < 3:
            time.sleep(2)
            continue

        latest = data[0]
        current_period = latest['period']
        current_number = latest['number']

        if current_period != last_period:
            last_period = current_period

            # Pichhli prediction ka result dikhao
            if active_prediction and predicted_period:
                print_result(current_number, active_prediction)

            # Naya prediction
            pred = predict(data, current_period)
            if pred:
                predicted_period = pred['issue']
                active_prediction = pred['size']
                print_prediction(
                    pred['issue'],
                    pred['size'],
                    pred['confidence'],
                    pred['score']
                )

        time.sleep(3)


# ═══════════════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run()
