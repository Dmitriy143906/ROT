# RØT Clan Website v2

Мрачный сайт Rust-клана RØT с формой набора и закрытым кабинетом администрации.

## Возможности

- Публичная главная страница RØT.
- Ссылки YouTube / Twitch / TikTok / Discord.
- Форма заявки на вступление.
- SQLite-хранилище заявок.
- Необязательная отправка новых заявок в Discord webhook.
- Админ-панель `/admin`.
- Статистика: все / новые / принятые / отклонённые.
- Поиск по заявкам.
- Просмотр полной анкеты.
- Кнопки «Принять», «Отклонить», «Вернуть в новые».
- Удаление заявки.
- Авторизация администратора через HttpOnly cookie.

## 1. Установка

PowerShell в папке проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Создай `.env`

```powershell
Copy-Item .env.example .env
```

Открой `.env` и ОБЯЗАТЕЛЬНО поменяй:

```env
ADMIN_USERNAME=rotadmin
ADMIN_PASSWORD=придумай_сильный_пароль
SESSION_SECRET=длинная_случайная_строка
```

Сгенерировать секрет можно так:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Не публикуй `.env` и не загружай его в GitHub.

## 3. Запуск

```powershell
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Сайт:

```text
http://127.0.0.1:8000
```

Админ-панель:

```text
http://127.0.0.1:8000/admin
```

## 4. Discord webhook (необязательно)

Вставь URL webhook в `.env`:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Новые заявки останутся в SQLite даже если Discord webhook временно недоступен.

## 5. Публикация в интернете

При размещении сайта за HTTPS поставь:

```env
COOKIE_SECURE=1
```

Для реального публичного проекта также рекомендуется поставить сайт за HTTPS/reverse proxy и сделать резервное копирование `data/applications.db`.

## 6. Соцсети

Ссылки на YouTube, Twitch, TikTok и Discord находятся в `static/index.html`. Замени заглушки на реальные URL.


## Социальные ссылки

В этой версии уже подключены:

- YouTube: https://www.youtube.com/@weareROT
- Twitch: https://www.twitch.tv/rotrusttv
- Discord: https://discord.gg/8aDauz4qF

TikTok пока оставлен как заглушка, потому что ссылка не была указана.
