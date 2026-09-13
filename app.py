"""
FastAPI Prediction Server
Render.com par deploy karne ke liye ready.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

app = FastAPI(
    title="Prediction API",
    description="Simple FastAPI prediction server",
    version="1.0.0"
)

# CORS enable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 🔥 YAHAN APNA ACTUAL PREDICTION ALGORITHM PASTE KARO
# ============================================================
def run_prediction(period: Optional[int] = None) -> str:
    # -------- DUMMY LOGIC (ise apne algorithm se replace karo) --------
    if period is None:
        return "BIG"
    if period % 2 == 0:
        return "BIG"
    else:
        return "SMALL"
    # -------- END DUMMY --------


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"status": "online"}


@app.get("/predict")
def predict(period: Optional[int] = Query(default=None)):
    try:
        if period is not None and period < 0:
            raise HTTPException(status_code=400, detail="period must be >= 0")
        result = run_prediction(period=period)
        return {"prediction": result}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Prediction failed", "detail": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)