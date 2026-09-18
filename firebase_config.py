"""
Firebase Configuration & Helper Functions
------------------------------------------
- Firebase Admin SDK initialize
- Realtime Database se key check
- Server status check
- Withdrawal requests
"""

import firebase_admin
from firebase_admin import credentials
import os
import json
import time
import urllib.request
import urllib.error


# ============================================================
# 🔥 FIREBASE CONFIG (Web Config)
# ============================================================
FIREBASE_WEB_CONFIG = {
    "apiKey": "AIzaSyBcneJ6KGeF3nSyYQJFQcPag88b3Jsbtas",
    "authDomain": "maxmod-d825c.firebaseapp.com",
    "databaseURL": "https://maxmod-d825c-default-rtdb.firebaseio.com",
    "projectId": "maxmod-d825c",
    "storageBucket": "maxmod-d825c.firebasestorage.app",
    "messagingSenderId": "65122374",
    "appId": "1:65122374:web:fd8fb265821b1242169a47",
    "measurementId": "G-63BFTWW8HP"
}

DATABASE_URL = FIREBASE_WEB_CONFIG["databaseURL"]


# ============================================================
# 🔥 FIREBASE ADMIN SDK INIT
# ============================================================
_firebase_initialized = False


def init_firebase():
    """Firebase Admin SDK initialize karo."""
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        service_account_path = os.path.join(
            os.path.dirname(__file__), "serviceAccountKey.json"
        )
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
            _firebase_initialized = True
            print("✅ Firebase Admin SDK initialized")
            return True
        else:
            print("⚠️ serviceAccountKey.json nahi mila — REST API fallback use hoga")
            return False
    except Exception as e:
        print(f"❌ Firebase init error: {e}")
        return False


# ============================================================
# 🌐 REST API
# ============================================================
def _rest_get(path: str):
    url = f"{DATABASE_URL}/{path}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw and raw != "null" else None
    except urllib.error.HTTPError as e:
        print(f"REST GET HTTP error [{path}]: {e.code}")
        return None
    except Exception as e:
        print(f"REST GET error [{path}]: {e}")
        return None


def _rest_put(path: str, data):
    url = f"{DATABASE_URL}/{path}.json"
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="PUT",
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else data
    except Exception as e:
        print(f"REST PUT error [{path}]: {e}")
        return None


def _rest_patch(path: str, data):
    url = f"{DATABASE_URL}/{path}.json"
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="PATCH",
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else data
    except Exception as e:
        print(f"REST PATCH error [{path}]: {e}")
        return None


# ============================================================
# 🔑 KEY VALIDATION
# ============================================================
def check_key_active(key: str) -> dict:
    if not key or not isinstance(key, str):
        return {"active": False, "reason": "Key empty", "data": None}

    key = key.strip()
    data = _rest_get(f"keys/{key}")
    if data is None:
        return {"active": False, "reason": "Key not found", "data": None}

    if data.get("deleted") is True:
        return {"active": False, "reason": "Key deleted by admin", "data": data}

    if data.get("active") is not True:
        return {"active": False, "reason": "Key inactive", "data": data}

    expiry = data.get("expiry", 0)
    if expiry and expiry > 0 and int(time.time() * 1000) > expiry:
        return {"active": False, "reason": "Key expired", "data": data}

    return {"active": True, "reason": "OK", "data": data}


# ============================================================
# 🖥️ SERVER STATUS
# ============================================================
def get_server_status() -> dict:
    data = _rest_get("server_status")
    if data is None:
        return {"online": True, "message": "Server is running"}

    return {
        "online": bool(data.get("online", True)),
        "message": data.get("message", "Server is running")
    }


# ============================================================
# 💰 WITHDRAWAL SYSTEM
# ============================================================
def create_withdrawal_request(key: str, amount: float, method: str, account: str) -> dict:
    req_id = f"WD{int(time.time() * 1000)}"
    data = {
        "id": req_id,
        "key": key,
        "amount": float(amount),
        "method": method,
        "account": account,
        "status": "pending",
        "createdAt": int(time.time() * 1000)
    }
    result = _rest_put(f"withdrawals/{req_id}", data)
    if result:
        return {"success": True, "requestId": req_id, "data": data}
    return {"success": False, "error": "Failed to create request"}


def get_user_withdrawals(key: str) -> list:
    data = _rest_get("withdrawals")
    if not data or not isinstance(data, dict):
        return []
    user_wds = [v for v in data.values() if isinstance(v, dict) and v.get("key") == key]
    user_wds.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return user_wds


def get_user_balance(key: str) -> float:
    data = _rest_get(f"keys/{key}")
    if data and isinstance(data, dict):
        try:
            return float(data.get("balance", 0))
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def update_user_balance(key: str, new_balance: float) -> bool:
    result = _rest_patch(f"keys/{key}", {"balance": float(new_balance)})
    return result is not None
