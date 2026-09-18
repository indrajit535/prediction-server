# Prediction API

FastAPI prediction server — Render.com par free deploy.

## ⚠️ Free Tier Warning

Render Free Service inactivity ke baad **SLEEP** ho jaati hai.
Pehli request **30-60 sec** le sakti hai (cold start).

### Cold Start Avoid Karne Ke Liye:
- **UptimeRobot** (free) se har 5 min ping karo
- Ya **Cron-job.org** (free) se 10 min interval set karo
- URL: `https://your-app.onrender.com/` ping karo

---

## 📡 Endpoints

### Public (No Auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server status check |
| GET | `/server-status` | Server online/offline status |
| GET | `/firebase-config` | Client Firebase config |

### Auth Required (key= param)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with key |
| GET | `/auth/check?key=XXX` | Check key validity |
| GET | `/predict?key=XXX` | Get prediction |
| GET | `/predict-full?key=XXX` | Full prediction + history |
| GET | `/period?key=XXX` | Current period info |
| GET | `/history?key=XXX` | Last 100 results |
| GET | `/withdrawal/balance?key=XXX` | User balance |
| POST | `/withdrawal/request` | Withdrawal request |
| GET | `/withdrawal/history?key=XXX` | Withdrawal history |

### Admin (password= param)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/keys?password=XXX` | List all keys |
| POST | `/admin/keys/create` | Create new key |
| POST | `/admin/keys/delete` | Delete key |
| POST | `/admin/keys/toggle` | Toggle active |
| POST | `/admin/keys/balance` | Update balance |
| POST | `/admin/server/toggle` | Server on/off |
| GET | `/admin/withdrawals?password=XXX` | All withdrawals |
| POST | `/admin/withdrawals/action` | Accept/reject |
| GET | `/admin/stats?password=XXX` | Dashboard stats |

---

## 📥 Example Requests

### 1. Server Status
```bash
curl https://your-app.onrender.com/
