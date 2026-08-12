# RØT Clan Website — FINAL

Эта версия подготовлена так, чтобы фон работал без папки assets.

## Структура для GitHub

В корне репозитория:

- app.py
- requirements.txt
- .env.example
- README.md
- static/

Внутри static:

- index.html
- app.js
- styles.css
- rot-banner.png
- rot-logo.jpg

## Render

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn app:app --host 0.0.0.0 --port $PORT

Для заявок в Discord добавь в Render → Environment:

DISCORD_WEBHOOK_URL=твой_webhook

Не загружай .env в публичный GitHub.
