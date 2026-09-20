def generate_prediction(period: Optional[str] = None,
                        game_id: str = "wingo_1min",
                        use_cache: bool = True):
    if period is None:
        live = fetch_live_period()
        period = live["period"]

    # ✅ Cache check — sirf 55 sec tak valid (period ke andar)
    if use_cache:
        cached = get_cached_prediction(period)
        if cached is not None:
            # Cache age check karo
            age_sec = (time.time() * 1000 - cached.get("timestamp", 0)) / 1000
            if age_sec < 55:
                cached["timestamp"] = int(time.time() * 1000)
                cached["fromCache"] = True
                return cached
            else:
                # Purana cache — delete karo
                PREDICTION_CACHE.pop(period, None)

    history_data = fetch_history()
    history_list = history_data.get("data", {}).get("list", [])

    last_number = 0
    if history_list:
        try:
            last_number = int(history_list[0].get("number", 0)) % 10
        except (ValueError, TypeError):
            last_number = 0

    result = sddgamer263_predict(current_number=last_number, period=period)

    prediction = {
        "period": period,
        "gameId": game_id,
        "mode": "1m",
        "bigSmallResult": result["bigSmall"],
        "numberResult": result["prediction"],
        "numbers": result.get("numbers", [result["prediction"]]),
        "confidence": result["confidence"],
        "patternName": "NAVEEN AI v2026",
        "steps": result.get("steps", []),
        "source": result.get("source", "naveen-ai"),
        "inputNumber": last_number,
        "timestamp": int(time.time() * 1000),
        "fromCache": False
    }

    if use_cache:
        save_prediction_to_cache(period, prediction)

    return prediction
