# Prediction API

FastAPI prediction server — Render.com par free deploy.

## ⚠️ Free Tier Warning
Render Free Service inactivity ke baad SLEEP ho jaati hai.
Pehli request 30-60 sec le sakti hai (cold start).

## Endpoints
- GET / → {"status":"online"}
- GET /predict → {"prediction":"BIG"}
- GET /predict?period=12345 → prediction with input

## Start Command
uvicorn app:app --host 0.0.0.0 --port $PORT