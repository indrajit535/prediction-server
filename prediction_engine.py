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
# =====
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
        "        if actual is None:
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
            "
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
