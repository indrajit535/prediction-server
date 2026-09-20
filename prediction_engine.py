"""
Prediction Engine — Gemini AI Powered
--------------------------------------
Ye file purane SDDGAMER263 algorithm ki jagah Gemini API use karti hai.
Same function name rakha hai: sddgamer263_predict()
Taki app.py mein kuch change na karna pade.
"""

import urllib.request
import json
import time
from typing import List, Dict, Optional

# ============================================================
# 🔑 GEMINI API CONFIG
# ============================================================
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
GEMINI_API_KEY = "AQ.Ab8RN6IBPunk06vqlt6E3Qv3W9gdoXcKrAcWvhViORe8rMnOwA"

# History fetch API (app.py wali)
HISTORY_API = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-1000"

# ============================================================
# 🗄️ CACHE — same period → same prediction
# ============================================================
_GEMINI_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 55  # seconds


# ============================================================
# 🧠 HELPERS
# ============================================================
def _is_big(number: int) -> bool:
    return number >= 5


def _fetch_history() -> List[dict]:
    """Live history fetch karo."""
    try:
        req = urllib.request.Request(HISTORY_API, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"[History Fetch Error] {e}")
        return []


def _format_history(history: List[dict], limit: int = 50) -> str:
    """History ko readable string me convert karo."""
    lines = []
    for i, item in enumerate(history[:limit]):
        try:
            issue = str(item.get("issueNumber", "?"))
            num = int(item.get("number", 0)) % 10
            color = item.get("color", "?")
            size = "BIG" if _is_big(num) else "SMALL"
            lines.append(f"{i+1}. Period={issue} | Number={num} | Size={size} | Color={color}")
        except Exception:
            continue
    return "\n".join(lines)


def _build_prompt(history: List[dict], next_period: str) -> str:
    """Gemini ke liye analysis prompt."""
    history_text = _format_history(history, limit=50)

    return f"""You are an expert Wingo 1-Minute lottery pattern analyzer. Analyze recent game history and predict the NEXT result.

RECENT HISTORY (latest first):
{history_text}

TARGET PERIOD: {next_period}

Analysis rules:
- Numbers 0-4 = SMALL, Numbers 5-9 = BIG
- Look for patterns: streaks, alternations, frequency, gap analysis, hot/cold numbers
- Consider colors (Green: 1,3,7,9 | Red: 2,4,6,8 | Violet: 0,5)
- Analyze last 5, 10, 20 draws for trends
- Weight recent draws more heavily

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "prediction": <number 0-9>,
  "bigSmall": "BIG" or "SMALL",
  "confidence": <integer 50-95>,
  "reasoning": "<short 1-line analysis>",
  "alternateNumbers": [<num1>, <num2>]
}}"""


def _call_gemini(prompt: str) -> Optional[dict]:
    """Gemini API call."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 512,
        }
    }

    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[Gemini API Error] {e}")
        return None


def _parse_response(api_response: dict) -> Optional[dict]:
    """Gemini response se JSON nikalo."""
    try:
        candidates = api_response.get("candidates", [])
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return None

        text = parts[0].get("text", "").strip()

        # ```json ... ``` hatao
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return None

        return json.loads(text[start:end])
    except Exception as e:
        print(f"[Gemini Parse Error] {e}")
        return None


# ============================================================
# 🎯 MAIN FUNCTION — app.py isi ko call karta hai
# ============================================================
def sddgamer263_predict(current_number: int, period: str) -> dict:
    """
    Main prediction function — Gemini AI use karta hai.
    
    Args:
        current_number: Last draw ka number (0-9)
        period: Target period jiske liye predict karna hai
    
    Returns:
        dict with keys: prediction, bigSmall, confidence, reasoning, numbers, steps
    """

    # ✅ Cache check — same period → same prediction
    cached = _GEMINI_CACHE.get(period)
    if cached and (time.time() - cached["_cachedAt"]) < _CACHE_TTL:
        return {
            "prediction": cached["prediction"],
            "bigSmall": cached["bigSmall"],
            "confidence": cached["confidence"],
            "reasoning": cached["reasoning"],
            "numbers": cached["numbers"],
            "steps": cached["steps"],
            "source": "gemini-cache"
        }

    # Live history fetch
    history = _fetch_history()

    if not history:
        # Fallback — agar history nahi mili
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": "BIG" if fallback_num >= 5 else "SMALL",
            "confidence": 55,
            "reasoning": "History unavailable — fallback used",
            "numbers": [fallback_num],
            "steps": [],
            "source": "fallback"
        }

    # Gemini API call
    prompt = _build_prompt(history, period)
    api_response = _call_gemini(prompt)

    if not api_response:
        # Fallback
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": "BIG" if fallback_num >= 5 else "SMALL",
            "confidence": 55,
            "reasoning": "Gemini API failed — fallback used",
            "numbers": [fallback_num],
            "steps": [],
            "source": "fallback"
        }

    parsed = _parse_response(api_response)

    if not parsed:
        fallback_num = (current_number + 5) % 10
        return {
            "prediction": fallback_num,
            "bigSmall": "BIG" if fallback_num >= 5 else "SMALL",
            "confidence": 55,
            "reasoning": "Gemini parse failed — fallback used",
            "numbers": [fallback_num],
            "steps": [],
            "source": "fallback"
        }

    # ✅ Normalize & validate
    pred_num = int(parsed.get("prediction", 5)) % 10
    big_small = str(parsed.get("bigSmall", "BIG")).upper()
    if big_small not in ("BIG", "SMALL"):
        big_small = "BIG" if pred_num >= 5 else "SMALL"

    confidence = int(parsed.get("confidence", 70))
    confidence = max(50, min(95, confidence))

    alternates = parsed.get("alternateNumbers", [])
    if not isinstance(alternates, list):
        alternates = []
    alternates = [int(x) % 10 for x in alternates][:3]

    numbers_list = [pred_num] + alternates

    result = {
        "prediction": pred_num,
        "bigSmall": big_small,
        "confidence": confidence,
        "reasoning": str(parsed.get("reasoning", ""))[:200],
        "numbers": numbers_list,
        "steps": [
            f"History analyzed: {len(history[:50])} draws",
            f"AI Confidence: {confidence}%",
            f"Reasoning: {str(parsed.get('reasoning', ''))[:100]}"
        ],
        "source": "gemini"
    }

    # Cache me save
    result["_cachedAt"] = time.time()
    _GEMINI_CACHE[period] = result

    # Cache cleanup
    if len(_GEMINI_CACHE) > 200:
        old_keys = sorted(_GEMINI_CACHE.keys())[:50]
        for k in old_keys:
            _GEMINI_CACHE.pop(k, None)

    return result


def clear_engine_cache():
    """Cache clear karne ke liye helper."""
    _GEMINI_CACHE.clear()
