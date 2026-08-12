import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="RØT Clan", version="5.0.0")
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

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed_roles = {"Комбатер", "Индустриал", "Академка"}
        if value not in allowed_roles:
            raise ValueError("Недопустимое направление")
        return value


def send_discord_application(data: dict) -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        raise HTTPException(
            status_code=503,
            detail="Discord для заявок ещё не настроен. Сообщите администрации RØT.",
        )

    role_icons = {
        "Комбатер": "⚔️",
        "Индустриал": "⚙️",
        "Академка": "☣️",
    }

    submitted_at = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    payload = {
        "username": "RØT Recruitment",
        "allowed_mentions": {"parse": []},
        "embeds": [
            {
                "title": "☣️ НОВАЯ ЗАЯВКА В RØT",
                "description": (
                    f"**Направление:** {role_icons.get(data['role'], '☣️')} "
                    f"**{data['role']}**"
                ),
                "color": 11141120,
                "fields": [
                    {
                        "name": "👤 Discord",
                        "value": data["discord"],
                        "inline": True,
                    },
                    {
                        "name": "🎂 Возраст",
                        "value": str(data["age"]),
                        "inline": True,
                    },
                    {
                        "name": "⏱ Часы в Rust",
                        "value": f"{data['rust_hours']:,}".replace(",", " "),
                        "inline": True,
                    },
                    {
                        "name": "🌍 Часовой пояс",
                        "value": data["timezone"],
                        "inline": True,
                    },
                    {
                        "name": "🕒 Онлайн",
                        "value": data["online"],
                        "inline": True,
                    },
                    {
                        "name": "🔗 Steam",
                        "value": data["steam"],
                        "inline": False,
                    },
                    {
                        "name": "📝 О кандидате",
                        "value": data["about"][:1000],
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": f"RØT Recruitment • {submitted_at} • WE DON'T SURVIVE. WE SPREAD."
                },
            }
        ],
    }

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ROT-Clan-Website/5.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
            if response.status not in (200, 204):
                raise HTTPException(
                    status_code=502,
                    detail="Discord не принял заявку. Попробуйте ещё раз.",
                )
    except urllib.error.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Discord не принял заявку (код {exc.code}).",
        ) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Не удалось связаться с Discord. Попробуйте ещё раз позже.",
        ) from exc


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/applications")
def create_application(application: Application):
    data = application.model_dump()
    send_discord_application(data)
    return {
        "ok": True,
        "message": "Заявка отправлена напрямую в Discord RØT.",
    }


@app.get("/health")
def health():
    return {"ok": True}
