"""
============================================================
  WINGO PREDICTION ENGINE v16.0
  GEMINI AI PREDICTION ENGINE (STABLE)
  
  Fixes:
  - 503 error handling with multiple model fallback
  - JSON parse error fix (higher token limit + repair)
  - Period Lock: ek period pe sirf EK BAAR Gemini call
  - Exponential backoff retry
============================================================
"""

import json
import time
import re
import urllib.request
import urllib.error

# ============================================================
# SECTION 1: CONFIGURATION
# ============================================================
API_URL = "https://sky-predictor-1012593186417.asia-southeast1.run.app/api/wingo-history-1M-500"

GEMINI_API_KEY = "AQ.Ab8RN6IBPunk06vqlt6E3Qv3W9gdoXcKrAcWvhViORe8rMnOwA"

# Multiple models — agar ek fail ho to dusra try karo
GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

CONFIG = {
    "HISTORY_LIMIT": 50,
    "GEMINI_TIMEOUT": 25,
    "MAX_RETRIES_PER_MODEL": 2,
    "BASE_RETRY_DELAY": 3,
    "MAX_OUTPUT_TOKENS": 800,
}


# ============================================================
# SECTION 2: UTILITY FUNCTIONS
# ============================================================
def get_size(num):
    return "BIG" if int(num) >= 5 else "SMALL"


def get_type(num):
    return get_size(num)


# ============================================================
# SECTION 3: FETCH HISTORY
# ============================================================
def fetch_history_from_api():
    try:
        req = urllib.request.Request(
            API_URL + f"?ts={int(time.time() * 1000)}",
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
# SECTION 4: JSON REPAIR HELPER
# ============================================================
def safe_json_parse(text):
    """
    Gemini response se JSON nikalne ki koshish karo.
    Agar truncated ho to repair karo.
    """
    if not text:
        return None

    # Markdown cleanup
    text = text.strip()
    if text.startswith("```"):
        # Remove ```json ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Direct parse try
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Regex se JSON object extract karo
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Truncated JSON repair — missing closing brace add karo
    if "{" in text:
        start = text.find("{")
        candidate = text[start:]
        # Count braces
        open_c = candidate.count("{")
        close_c = candidate.count("}")
        if open_c > close_c:
            candidate += "}" * (open_c - close_c)
        # Agar string adhoori hai to band karo
        if candidate.count('"') % 2 != 0:
            candidate = candidate.rstrip()
            if not candidate.endswith('"'):
                candidate += '"'
            candidate += "}"
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# SECTION 5: GEMINI API PREDICTION (STABLE)
# ============================================================
def call_gemini_api(history_data):
    """
    Gemini API ko call karo with multiple model fallback.
    Returns: dict or None
    """
    if not history_data:
        return None

    history_str = "\n".join([
        f"{h['issue']} -> {h['number']} ({h['size']})"
        for h in history_data[:30]
    ])

    prompt = f"""Analyze WinGo 1M lottery history and predict next result.

HISTORY (recent first):
{history_str}

Respond ONLY with valid JSON in this exact format:
{{"prediction_number": 7, "big_small": "BIG", "confidence": 75, "reason": "short reason"}}

Rules:
- prediction_number: integer 0 to 9
- big_small: "BIG" if number >= 5, else "SMALL"
- confidence: integer 0 to 100
- reason: max 10 words
- NO markdown, NO extra text, ONLY the JSON object"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": CONFIG["MAX_OUTPUT_TOKENS"],
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    }

    # Har model try karo
    for model in GEMINI_MODELS:
        url = GEMINI_BASE.format(model=model)

        for attempt in range(CONFIG["MAX_RETRIES_PER_MODEL"]):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "X-goog-api-key": GEMINI_API_KEY,
                    },
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=CONFIG["GEMINI_TIMEOUT"]) as r:
                    response = json.loads(r.read().decode())

                # Check candidates
                candidates = response.get("candidates", [])
                if not candidates:
                    print(f"[!] {model}: no candidates in response")
                    break

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    finish = candidates[0].get("finishReason", "UNKNOWN")
                    print(f"[!] {model}: no parts (finish={finish})")
                    break

                text = parts[0].get("text", "").strip()
                if not text:
                    print(f"[!] {model}: empty text")
                    break

                # Parse JSON
                result = safe_json_parse(text)
                if result is None:
                    print(f"[!] {model}: JSON parse failed. Raw: {text[:150]}")
                    break

                # Validate fields
                if "prediction_number" not in result:
                    print(f"[!] {model}: missing prediction_number")
                    break

                pred_num = int(result["prediction_number"])
                pred_num = max(0, min(9, pred_num))

                confidence = int(result.get("confidence", 70))
                confidence = max(0, min(100, confidence))

                print(f"[✓] Gemini OK via {model}: {pred_num} ({get_size(pred_num)}) conf={confidence}")

                return {
                    "number": pred_num,
                    "side": get_size(pred_num),
                    "confidence": confidence,
                    "reason": str(result.get("reason", "AI analysis"))[:100],
                    "model": model,
                }

            except urllib.error.HTTPError as e:
                code = e.code
                try:
                    err_body = e.read().decode()[:200]
                except Exception:
                    err_body = ""

                if code == 503:
                    print(f"[!] {model} 503 (high demand) attempt {attempt+1}")
                elif code == 429:
                    print(f"[!] {model} 429 (rate limit) attempt {attempt+1}")
                elif code == 404:
                    print(f"[!] {model} 404 (not found) — skipping model")
                    break  # next model
                elif code == 400:
                    print(f"[!] {model} 400 (bad request): {err_body}")
                    break  # next model
                else:
                    print(f"[!] {model} HTTP {code}: {err_body}")

                # Exponential backoff
                if attempt < CONFIG["MAX_RETRIES_PER_MODEL"] - 1:
                    delay = CONFIG["BASE_RETRY_DELAY"] * (2 ** attempt)
                    time.sleep(delay)

            except json.JSONDecodeError as e:
                print(f"[!] {model} response not JSON: {e}")
                break

            except Exception as e:
                print(f"[!] {model} error: {e}")
                if attempt < CONFIG["MAX_RETRIES_PER_MODEL"] - 1:
                    time.sleep(CONFIG["BASE_RETRY_DELAY"])

    return None


# ============================================================
# SECTION 6: MAIN PREDICTOR CLASS
# ============================================================
class PredictionEngine:
    def __init__(self):
        self.stats = {"wins": 0, "losses": 0, "total": 0}
        self.prediction_log = []

        # Period lock — ek period pe sirf EK BAAR predict
        self.locked_period = None          # jis period ka prediction already ban chuka
        self.locked_prediction = None      # us period ka prediction data

        # Pending — jiska result aana hai
        self.pending_prediction = None

        # Completed periods — duplicate validation rokne ke liye
        self.completed_periods = set()

    # --------------------------------------------------------
    # VALIDATE PENDING
    # --------------------------------------------------------
    def _try_validate_pending(self, history_data):
        if not self.pending_prediction:
            return None

        target_period = str(self.pending_prediction["period"])

        # Already validate ho chuka?
        if target_period in self.completed_periods:
            self.pending_prediction = None
            return None

        actual = None
        for item in history_data:
            if str(item["issue"]) == target_period:
                actual = item
                break

        if actual is None:
            return None  # result abhi nahi aaya

        actual_num = actual["number"]
        actual_side = actual["size"]
        pred_num = self.pending_prediction["number"]
        pred_side = self.pending_prediction["side"]

        is_win = (pred_side == actual_side)
        is_jackpot = (pred_num == actual_num)

        self.stats["total"] += 1
        if is_win:
            self.stats["wins"] += 1
        else:
            self.stats["losses"] += 1

        if is_jackpot:
            status = "JACKPOT"
        elif is_win:
            status = "WIN"
        else:
            status = "LOSS"

        log_entry = {
            "period": target_period[-6:],
            "predicted_side": pred_side,
            "predicted_number": pred_num,
            "actual_side": actual_side,
            "actual_number": actual_num,
            "result": status,
            "confidence": self.pending_prediction.get("confidence", 0),
            "reason": self.pending_prediction.get("reason", ""),
        }
        self.prediction_log.insert(0, log_entry)
        self.prediction_log = self.prediction_log[:50]

        completed = dict(self.pending_prediction)
        completed["result_status"] = status
        completed["actual_number"] = actual_num
        completed["actual_side"] = actual_side

        self.completed_periods.add(target_period)
        self.pending_prediction = None

        return completed

    # --------------------------------------------------------
    # MAIN PREDICT
    # --------------------------------------------------------
    def predict(self, list_data):
        latest = list_data[0]
        latest_issue = str(latest["issue"])
        next_period = str(int(latest_issue) + 1)

        # Pehle pending validate karo
        completed = self._try_validate_pending(list_data)

        # ----------------------------------------------------
        # PERIOD LOCK: agar is period ka prediction already hai
        # to naya Gemini call BILKUL mat karo
        # ----------------------------------------------------
        if self.locked_period == next_period and self.locked_prediction:
            return {
                "period": next_period,
                "side": self.locked_prediction["side"],
                "number": self.locked_prediction["number"],
                "confidence": self.locked_prediction["confidence"],
                "reason": self.locked_prediction["reason"],
                "model": self.locked_prediction.get("model", "cached"),
                "source": "GEMINI_AI",
                "cached": True,
                "just_completed": completed,
                "stats": dict(self.stats),
                "prediction_log": self.prediction_log[:10],
            }

        # ----------------------------------------------------
        # NAYA PREDICTION — Gemini call (SIRF EK BAAR per period)
        # ----------------------------------------------------
        print(f"\n[→] New period detected: {next_period} — calling Gemini...")

        gemini_result = call_gemini_api(list_data)

        if gemini_result is None:
            # Fallback — but still lock karo taaki baar baar Gemini na call ho
            last_num = latest["number"]
            # Simple heuristic: last 3 numbers ka pattern dekh kar opposite side
            fallback_num = (last_num + 5) % 10
            gemini_result = {
                "number": fallback_num,
                "side": get_size(fallback_num),
                "confidence": 35,
                "reason": "Fallback (Gemini unavailable)",
                "model": "fallback",
            }
            print(f"[!] Using fallback: {fallback_num} ({gemini_result['side']})")

        prediction = {
            "period": next_period,
            "side": gemini_result["side"],
            "number": gemini_result["number"],
            "confidence": gemini_result["confidence"],
            "reason": gemini_result["reason"],
            "model": gemini_result.get("model", "unknown"),
        }

        # Lock this period
        self.locked_period = next_period
        self.locked_prediction = prediction

        # Set pending for validation
        self.pending_prediction = prediction

        return {
            "period": next_period,
            "side": prediction["side"],
            "number": prediction["number"],
            "confidence": prediction["confidence"],
            "reason": prediction["reason"],
            "model": prediction["model"],
            "source": "GEMINI_AI",
            "cached": False,
            "just_completed": completed,
            "stats": dict(self.stats),
            "prediction_log": self.prediction_log[:10],
        }

    def run_once(self):
        data = fetch_history_from_api()
        if not data or len(data) < 4:
            return None
        return self.predict(data)


# ============================================================
# SECTION 7: PUBLIC WRAPPER for FastAPI
# ============================================================
_shared_engine = None


def _get_engine():
    global _shared_engine
    if _shared_engine is None:
        _shared_engine = PredictionEngine()
    return _shared_engine


def sddgamer263_predict(current_number: int, period: str) -> dict:
    engine = _get_engine()
    data = fetch_history_from_api()

    if data and len(data) >= 4:
        result = engine.predict(data)
        if result:
            return {
                "bigSmall": result["side"],
                "prediction": result["number"],
                "numbers": [result["number"]],
                "confidence": result["confidence"],
                "reason": result.get("reason", ""),
                "model": result.get("model", ""),
                "source": "GEMINI_AI",
                "period": result["period"],
                "cached": result.get("cached", False),
                "stats": result.get("stats", {}),
                "recent_log": result.get("prediction_log", [])[:5],
                "steps": [
                    f"Period: {result['period']}",
                    f"Predicted: {result['side']} ({result['number']})",
                    f"Confidence: {result['confidence']}%",
                    f"Model: {result.get('model', '')}",
                    f"Reason: {result.get('reason', '')}",
                ]
            }

    fallback_num = (current_number + 5) % 10
    return {
        "bigSmall": get_size(fallback_num),
        "prediction": fallback_num,
        "numbers": [fallback_num],
        "confidence": 35,
        "reason": "Fallback (no API data)",
        "source": "FALLBACK",
        "steps": ["Fallback: no API data"],
    }


# ============================================================
# SECTION 8: ENTRY POINT
# ============================================================
if __name__ == "__main__":
    engine = PredictionEngine()
    print("=" * 60)
    print("  WINGO PREDICTION ENGINE v16.0")
    print("  GEMINI AI (STABLE)")
    print("=" * 60)
    print("  - Multi-model fallback (503 fix)")
    print("  - JSON repair (parse error fix)")
    print("  - Period Lock (duplicate fix)")
    print("=" * 60)

    last_shown_period = None

    while True:
        try:
            r = engine.run_once()
            if r:
                # Sirf tab print karo jab naya period ho ya result complete hua ho
                show = (r["period"] != last_shown_period) or r.get("just_completed")

                if show:
                    print(f"\n{'─' * 60}")
                    print(f"  PERIOD: {r['period']}")
                    print(f"  🎯 PREDICTION: {r['side']}")
                    print(f"  🔢 NUMBER: {r['number']}")
                    print(f"  📊 CONFIDENCE: {r['confidence']}%")
                    print(f"  🤖 MODEL: {r.get('model', 'N/A')}")
                    print(f"  💡 REASON: {r['reason']}")
                    print(f"  📈 Stats → W:{r['stats']['wins']} L:{r['stats']['losses']} "
                          f"Total:{r['stats']['total']}")
                    if r.get("cached"):
                        print(f"  🔒 (locked — same period, no new API call)")

                    if r.get("just_completed"):
                        jc = r["just_completed"]
                        print(f"  ✅ RESULT [{jc['period'][-6:]}]: "
                              f"Pred {jc['predicted_side']}({jc['predicted_number']}) → "
                              f"Actual {jc['actual_side']}({jc['actual_number']}) | "
                              f"{jc['result_status']}")

                    if r.get("prediction_log"):
                        print(f"  📋 Recent:")
                        for p in r["prediction_log"][:3]:
                            print(f"     [{p['period']}] "
                                  f"{p['predicted_side']}({p['predicted_number']}) → "
                                  f"{p['actual_side']}({p['actual_number']}) | "
                                  f"{p['result']}")

                    last_shown_period = r["period"]

        except KeyboardInterrupt:
            print("\n[!] Stopped.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")
        time.sleep(5)
