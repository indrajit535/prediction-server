from fastapi import Response, Cookie
from fastapi.responses import JSONResponse
import secrets

# ============================================================
# 🔑 SESSION MANAGEMENT (Cookie-based, no localStorage)
# ============================================================
# Session store: {session_id: {"key": user_key, "created": ts}}
SESSIONS: Dict[str, dict] = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutes


@app.post("/auth/login")
async def auth_login(request: Request, response: Response):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    key = (body.get("key") or "").strip()
    if not key:
        raise HTTPException(400, "Key required")

    srv = get_server_status()
    if not srv["online"]:
        raise HTTPException(503, srv["message"])

    status = check_key_active(key)
    if not status["active"]:
        raise HTTPException(403, status["reason"])

    d = status["data"]

    # Create session
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "key": key,
        "created": time.time(),
        "lastActive": time.time()
    }

    # Set cookie (HttpOnly = JS can't read = secure)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=SESSION_TIMEOUT,
        httponly=True,
        samesite="lax",
        path="/"
    )

    return {
        "success": True,
        "message": "Login successful",
        "key": key,
        "balance": float(d.get("balance", 0)),
        "expiry": d.get("expiry", 0),
        "createdAt": d.get("createdAt", 0)
    }


@app.get("/auth/session")
def auth_session(session_id: Optional[str] = Cookie(default=None)):
    """Check if session is valid (called on page load)."""
    if not session_id or session_id not in SESSIONS:
        return {"loggedIn": False}

    sess = SESSIONS[session_id]
    if time.time() - sess["created"] > SESSION_TIMEOUT:
        del SESSIONS[session_id]
        return {"loggedIn": False}

    # Verify key still valid in Firebase
    status = check_key_active(sess["key"])
    if not status["active"]:
        del SESSIONS[session_id]
        return {"loggedIn": False, "reason": status["reason"]}

    sess["lastActive"] = time.time()
    d = status["data"]
    return {
        "loggedIn": True,
        "key": sess["key"],
        "balance": float(d.get("balance", 0)),
        "expiry": d.get("expiry", 0),
        "createdAt": d.get("createdAt", 0)
    }


@app.post("/auth/logout")
def auth_logout(response: Response, session_id: Optional[str] = Cookie(default=None)):
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    response.delete_cookie("session_id", path="/")
    return {"success": True}


# ============================================================
# 🔑 KEY VALIDATION FROM SESSION (for protected endpoints)
# ============================================================
def get_key_from_session(session_id: Optional[str]) -> str:
    """Session cookie se user key nikalo."""
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(401, "Not logged in")
    sess = SESSIONS[session_id]
    if time.time() - sess["created"] > SESSION_TIMEOUT:
        del SESSIONS[session_id]
        raise HTTPException(401, "Session expired")
    sess["lastActive"] = time.time()
    return sess["key"]
