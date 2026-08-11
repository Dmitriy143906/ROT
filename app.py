import os
import sqlite3
import json
import urllib.request
import hmac
import hashlib
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "applications.db"
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
SESSION_COOKIE = "rot_admin_session"
SESSION_TTL = 60 * 60 * 24 * 7  # 7 days

if not SESSION_SECRET:
    # Safe enough for local development, but production should set SESSION_SECRET in .env.
    SESSION_SECRET = secrets.token_urlsafe(32)

app = FastAPI(title="RØT Clan", version="2.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class Application(BaseModel):
    discord: str = Field(min_length=2, max_length=64)
    age: int = Field(ge=13, le=99)
    rust_hours: int = Field(ge=0, le=100000)
    role: str = Field(min_length=2, max_length=64)
    timezone: str = Field(min_length=2, max_length=64)
    online: str = Field(min_length=2, max_length=120)
    steam: str = Field(min_length=3, max_length=300)
    about: str = Field(min_length=10, max_length=2000)


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class StatusPayload(BaseModel):
    status: str


ALLOWED_STATUSES = {"new", "accepted", "rejected"}


def db_connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                discord TEXT NOT NULL,
                age INTEGER NOT NULL,
                rust_hours INTEGER NOT NULL,
                role TEXT NOT NULL,
                timezone TEXT NOT NULL,
                online TEXT NOT NULL,
                steam TEXT NOT NULL,
                about TEXT NOT NULL
            )
            """
        )
        columns = {row["name"] for row in con.execute("PRAGMA table_info(applications)")}
        if "status" not in columns:
            con.execute("ALTER TABLE applications ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
        if "updated_at" not in columns:
            con.execute("ALTER TABLE applications ADD COLUMN updated_at TEXT")
        con.commit()


def send_discord_webhook(data: dict):
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        return

    payload = {
        "username": "RØT Recruitment",
        "embeds": [
            {
                "title": "☣️ Новая заявка в RØT",
                "color": 11206656,
                "fields": [
                    {"name": "Discord", "value": data["discord"], "inline": True},
                    {"name": "Возраст", "value": str(data["age"]), "inline": True},
                    {"name": "Часы Rust", "value": str(data["rust_hours"]), "inline": True},
                    {"name": "Роль", "value": data["role"], "inline": True},
                    {"name": "Часовой пояс", "value": data["timezone"], "inline": True},
                    {"name": "Онлайн", "value": data["online"], "inline": False},
                    {"name": "Steam", "value": data["steam"], "inline": False},
                    {"name": "О себе", "value": data["about"][:1000], "inline": False},
                ],
                "footer": {"text": "RØT • We don't survive. We spread."},
            }
        ],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            response.read()
    except Exception:
        pass


def _sign(value: str) -> str:
    return hmac.new(
        SESSION_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_session_token(username: str) -> str:
    expires = int(time.time()) + SESSION_TTL
    nonce = secrets.token_hex(12)
    payload = f"{username}|{expires}|{nonce}"
    return f"{payload}|{_sign(payload)}"


def verify_session_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        username, expires_raw, nonce, signature = token.split("|", 3)
        payload = f"{username}|{expires_raw}|{nonce}"
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        if int(expires_raw) < int(time.time()):
            return None
        if username != ADMIN_USERNAME:
            return None
        return username
    except (ValueError, TypeError):
        return None


def require_admin(request: Request) -> str:
    username = verify_session_token(request.cookies.get(SESSION_COOKIE))
    if not username:
        raise HTTPException(status_code=401, detail="Требуется вход администратора")
    return username


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")


@app.post("/api/applications")
def create_application(application: Application):
    data = application.model_dump()
    created_at = datetime.now(timezone.utc).isoformat()

    with db_connect() as con:
        cursor = con.execute(
            """
            INSERT INTO applications
            (created_at, discord, age, rust_hours, role, timezone, online, steam, about, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
            """,
            (
                created_at,
                data["discord"],
                data["age"],
                data["rust_hours"],
                data["role"],
                data["timezone"],
                data["online"],
                data["steam"],
                data["about"],
            ),
        )
        con.commit()
        application_id = cursor.lastrowid

    send_discord_webhook(data)
    return {"ok": True, "id": application_id, "message": "Заявка отправлена в RØT."}


@app.post("/api/admin/login")
def admin_login(payload: LoginPayload, response: Response):
    valid_user = hmac.compare_digest(payload.username, ADMIN_USERNAME)
    valid_password = hmac.compare_digest(payload.password, ADMIN_PASSWORD)
    if not (valid_user and valid_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_session_token(payload.username)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_TTL,
        httponly=True,
        samesite="strict",
        secure=os.getenv("COOKIE_SECURE", "0") == "1",
        path="/",
    )
    return {"ok": True, "username": payload.username}


@app.post("/api/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/admin/me")
def admin_me(username: str = Depends(require_admin)):
    return {"ok": True, "username": username}


@app.get("/api/admin/applications")
def admin_applications(
    status: str = "all",
    q: str = "",
    username: str = Depends(require_admin),
):
    del username
    clauses = []
    params: list[object] = []

    if status != "all":
        if status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail="Неизвестный статус")
        clauses.append("status = ?")
        params.append(status)

    q = q.strip()
    if q:
        clauses.append("(discord LIKE ? OR role LIKE ? OR steam LIKE ? OR about LIKE ?)")
        needle = f"%{q}%"
        params.extend([needle, needle, needle, needle])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with db_connect() as con:
        rows = con.execute(
            f"""
            SELECT id, created_at, updated_at, discord, age, rust_hours,
                   role, timezone, online, steam, about, status
            FROM applications
            {where}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()

    return {"items": [dict(row) for row in rows]}


@app.get("/api/admin/stats")
def admin_stats(username: str = Depends(require_admin)):
    del username
    with db_connect() as con:
        total = con.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        new = con.execute("SELECT COUNT(*) FROM applications WHERE status='new'").fetchone()[0]
        accepted = con.execute("SELECT COUNT(*) FROM applications WHERE status='accepted'").fetchone()[0]
        rejected = con.execute("SELECT COUNT(*) FROM applications WHERE status='rejected'").fetchone()[0]
    return {
        "total": total,
        "new": new,
        "accepted": accepted,
        "rejected": rejected,
    }


@app.patch("/api/admin/applications/{application_id}/status")
def admin_change_status(
    application_id: int,
    payload: StatusPayload,
    username: str = Depends(require_admin),
):
    del username
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Неизвестный статус")

    updated_at = datetime.now(timezone.utc).isoformat()
    with db_connect() as con:
        cursor = con.execute(
            "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
            (payload.status, updated_at, application_id),
        )
        con.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

    return {"ok": True, "status": payload.status}


@app.delete("/api/admin/applications/{application_id}")
def admin_delete_application(
    application_id: int,
    username: str = Depends(require_admin),
):
    del username
    with db_connect() as con:
        cursor = con.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        con.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
    return {"ok": True}
