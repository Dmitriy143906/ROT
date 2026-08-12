# RØT Clan Website v5

Публичный сайт RØT с формой набора.

## Что изменилось

- Админ-панель полностью удалена.
- SQLite и локальное хранение заявок удалены.
- Каждая заявка отправляется напрямую в Discord через webhook.
- Оставлены направления: Комбатер, Индустриал, Академка.
- Если Discord webhook недоступен, сайт не показывает ложный успех — кандидат увидит ошибку и сможет попробовать снова.

## Настройка Discord

1. В Discord открой нужный канал для заявок.
2. Настройки канала → Интеграции → Вебхуки.
3. Создай новый webhook и скопируй его URL.
4. В Render открой свой Web Service → Environment.
5. Добавь переменную:

DISCORD_WEBHOOK_URL = URL_ТВОЕГО_WEBHOOK

Webhook URL нельзя публиковать в GitHub, HTML или JavaScript.

## Render

Build Command:

pip install -r requirements.txt

Start Command:

uvicorn app:app --host 0.0.0.0 --port $PORT

После изменения Environment Variables сделай новый Deploy.
