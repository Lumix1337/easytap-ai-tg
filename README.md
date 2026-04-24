# EasyTap Telegram Bot (Python)

Telegram-бот EasyTap.ai с синхронизацией аккаунта между сайтом и Telegram.

## Что реализовано

- Команды `/start`, `/link`, `/login`, `/signup`
- Кнопки в Telegram: вход, регистрация, привязка Telegram к сайту, топ вакансий
- Вход через сайт с возвратом в единый AI-аккаунт
- Если пользователь уже зарегистрирован на сайте, он связывает Telegram кодом и продолжает работу в том же аккаунте
- Ответы AI и подбор вакансий через backend EasyTap (`/api/assistant/channel-chat/`)
- Дружелюбные тексты и сценарии помощи в боте

## Как работает синхронизация

1. Пользователь в Telegram отправляет `/link`.
2. Бот получает одноразовый код через backend (`/api/tg/link/start/`).
3. Пользователь входит на сайт и вставляет код в разделе "Синхронизация с Telegram".
4. Backend подтверждает код (`/api/tg/link/confirm/`) и связывает Telegram с web-аккаунтом.
5. После привязки сообщения из Telegram идут в тот же профиль пользователя.

## Структура

- `main.py` - точка входа (polling)
- `bot/config.py` - конфиг из `.env`
- `bot/api_client.py` - клиент API backend EasyTap
- `bot/handlers.py` - хендлеры команд и сообщений
- `bot/keyboards.py` - inline-кнопки

## Быстрый старт

1. Создай виртуальное окружение:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
2. Установи зависимости:
   - `pip install -r requirements.txt`
3. Создай `.env` на основе `.env.example`
4. Запусти бота:
   - `python main.py`

## Переменные окружения

- `TG_BOT_TOKEN` - токен Telegram-бота
- `EASYTAP_API_URL` - URL backend API, например `http://localhost:8000/api`
- `EASYTAP_WEB_APP_URL` - URL сайта, например `http://localhost:5173`
- `REQUEST_TIMEOUT` - таймаут HTTP-запросов
- `GROQ_API_KEY`, `GROQ_MODEL`, `HH_API_URL`, `REMOTIVE_API_URL`, `HH_RESULTS_LIMIT` - резервные настройки

## Команды бота

- `/start` - приветствие и быстрые кнопки
- `/link` - получить код привязки Telegram к сайту
- `/login` - открыть страницу входа на сайт
- `/signup` - открыть страницу регистрации на сайт

## Примечания

- Используется polling (без webhook) для локальной разработки.
- Для продакшена рекомендуется webhook + reverse proxy.
