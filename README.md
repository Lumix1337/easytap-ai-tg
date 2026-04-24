# EasyTap Telegram Bot (Python)

Telegram-бот для EasyTap.ai: автономное общение с AI (Groq) и подбор вакансий с hh.ru + remotive.com.

## Что уже есть

- Команды `/start` и `/link`
- Ответы AI через Groq API
- Подбор релевантных вакансий через HH API (`https://api.hh.ru/vacancies`)
- Дополнительный источник вакансий: Remotive API (`https://remotive.com/api/remote-jobs`)
- Умный парсер запроса (роль, город, удаленка, уровень)
- Multi-search pipeline (синонимы + ослабление фильтров)
- Fallback-режим при 0 результатов (более широкий поиск)
- Кликабельные ссылки "Открыть вакансию" в Telegram
- Кнопка показа топ вакансий
- Полностью независим от сайта и backend EasyTap

## Структура

- `main.py` - точка входа (polling)
- `bot/config.py` - конфиг из `.env`
- `bot/groq_client.py` - клиент Groq LLM
- `bot/hh_client.py` - клиент HH API
- `bot/assistant_service.py` - оркестрация AI + поиск вакансий
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
- `GROQ_API_KEY` - ключ Groq API
- `GROQ_MODEL` - модель Groq (по умолчанию `llama-3.3-70b-versatile`)
- `HH_API_URL` - базовый URL HH API
- `REMOTIVE_API_URL` - базовый URL Remotive API
- `HH_RESULTS_LIMIT` - количество вакансий в подборе
- `REQUEST_TIMEOUT` - таймаут внешних запросов в секундах

## Примечания

- Сейчас используется polling (без webhook), чтобы быстрее стартовать локально.
- Для продакшена лучше перейти на webhook + reverse proxy.
