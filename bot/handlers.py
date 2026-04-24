from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery, Message

from bot.api_client import EasyTapApiClient
from bot.keyboards import main_keyboard


def build_router(
  sync_api: EasyTapApiClient | None = None,
  web_app_url: str = "",
) -> Router:
  router = Router(name="main")

  def get_job_field(job, field: str, default: str = "") -> str:
    if isinstance(job, dict):
      value = job.get(field, default)
      return str(value) if value is not None else default
    value = getattr(job, field, default)
    return str(value) if value is not None else default

  def format_jobs_message(title: str, jobs: list) -> str:
    lines = [f"<b>{escape(title)}</b>"]
    for idx, job in enumerate(jobs, start=1):
      salary_raw = get_job_field(job, "salary")
      salary = f" · {escape(salary_raw)}" if salary_raw else ""
      source = escape(get_job_field(job, "source", "source"))
      role = escape(get_job_field(job, "title", get_job_field(job, "role", "Без названия")))
      company = escape(get_job_field(job, "company", "Компания"))
      area = escape(get_job_field(job, "area", get_job_field(job, "location", "Не указано")))
      link = escape(get_job_field(job, "url", ""))
      lines.append(
        f"{idx}. <b>{role}</b> — {company} ({area}){salary}\n"
        f"Источник: {source}\n"
        f"<a href=\"{link}\">Открыть вакансию</a>"
      )
    return "\n\n".join(lines)

  def build_job_keyboard(jobs: list) -> InlineKeyboardMarkup | None:
    if not web_app_url:
      return None
    buttons: list[list[InlineKeyboardButton]] = []
    for idx, job in enumerate(jobs[:3], start=1):
      vacancy_id = get_job_field(job, "id")
      if not vacancy_id:
        continue
      url = f"{web_app_url.rstrip('/')}/jobs/{escape(vacancy_id)}"
      buttons.append([InlineKeyboardButton(text=f"Открыть #{idx} на сайте", url=url)])
    if not buttons:
      return None
    return InlineKeyboardMarkup(inline_keyboard=buttons)

  @router.message(CommandStart())
  async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user is None:
      return

    link_hint = ""
    if sync_api:
      link_info = await sync_api.register_telegram_user(
        tg_user_id=user.id,
        username=user.username,
        full_name=user.full_name,
      )
      if link_info and link_info.get("linked"):
        link_hint = "\n\nАккаунт уже синхронизирован с сайтом."
      elif link_info and link_info.get("link_code"):
        code = str(link_info.get("link_code"))
        web_line = f"\nОткрой сайт: {web_app_url}" if web_app_url else ""
        link_hint = (
          f"\n\nКод синхронизации: <b>{code}</b>"
          f"\nВведи его в AI-чате на сайте, чтобы связать аккаунты.{web_line}"
        )

    text = (
      "Привет! Я EasyTap AI-бот и рад помочь тебе с карьерой.\n"
      "Напиши вопрос о стажировке, резюме или собеседовании, а я подскажу шаги и подберу вакансии."
      f"{link_hint}\n\n"
      "Если у тебя уже есть аккаунт EasyTap на сайте, нажми кнопку «Связать Telegram с аккаунтом»."
    )
    await message.answer(text, reply_markup=main_keyboard(web_app_url))

  @router.message(Command("link"))
  async def cmd_link(message: Message) -> None:
    user = message.from_user
    if user is None:
      return
    if not sync_api:
      await message.answer("Синхронизация с сайтом сейчас недоступна. Попробуй чуть позже.")
      return
    link_info = await sync_api.register_telegram_user(
      tg_user_id=user.id,
      username=user.username,
      full_name=user.full_name,
    )
    if not link_info:
      await message.answer("Не смог получить код привязки. Давай попробуем ещё раз чуть позже.")
      return
    if link_info.get("linked"):
      await message.answer("Готово! Этот Telegram уже связан с твоим аккаунтом на сайте.")
      return
    code = str(link_info.get("link_code") or "")
    if not code:
      await message.answer("Код пока не получен. Попробуй ещё раз через минуту.")
      return
    web_line = f"\nСайт: {web_app_url}" if web_app_url else ""
    await message.answer(
      "Чтобы войти в свой аккаунт EasyTap через Telegram:\n"
      f"1) Открой сайт и войди в существующий аккаунт.{web_line}\n"
      "2) В AI-чате на сайте отправь этот код.\n"
      f"3) Код: <b>{code}</b>\n\n"
      "После этого бот будет узнавать твой профиль автоматически."
    )

  @router.message(Command("login"))
  async def cmd_login(message: Message) -> None:
    if not web_app_url:
      await message.answer("Ссылка на сайт пока не настроена. Обратись к администратору сервиса.")
      return
    site = web_app_url.rstrip("/")
    await message.answer(
      "Открой вход на сайте по кнопке ниже и авторизуйся в своём аккаунте.",
      reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
          [InlineKeyboardButton(text="Войти на сайте", url=f"{site}/auth?mode=login&redirect=%2Fassistant")]
        ]
      ),
    )

  @router.message(Command("signup"))
  async def cmd_signup(message: Message) -> None:
    if not web_app_url:
      await message.answer("Ссылка на сайт пока не настроена. Обратись к администратору сервиса.")
      return
    site = web_app_url.rstrip("/")
    await message.answer(
      "Создай аккаунт на сайте по кнопке ниже, после чего вернись сюда и используй /link.",
      reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
          [InlineKeyboardButton(text="Регистрация на сайте", url=f"{site}/auth?mode=signup&redirect=%2Fassistant")]
        ]
      ),
    )

  @router.callback_query(F.data == "show_link_help")
  async def show_link_help(callback: CallbackQuery) -> None:
    if not callback.message:
      await callback.answer()
      return

    site_line = f"\nСайт: {web_app_url}" if web_app_url else ""
    text = (
      "Давай быстро свяжем Telegram с аккаунтом EasyTap.\n"
      "Если аккаунт на сайте уже есть — это займёт меньше минуты:\n"
      "1) Нажми /link и получи код.\n"
      "2) Войди на сайт в свой аккаунт.\n"
      "3) Вставь код в AI-чате на сайте.\n\n"
      "После привязки ты сможешь писать боту в Telegram, и он продолжит работу с твоим профилем."
      f"{site_line}"
    )
    await callback.message.answer(text)
    await callback.answer()

  @router.callback_query(F.data == "show_jobs")
  async def show_jobs(callback: CallbackQuery) -> None:
    user = callback.from_user
    if not sync_api:
      await callback.message.answer("Сервис вакансий временно недоступен. Попробуй немного позже.")
      await callback.answer()
      return

    jobs: list = []
    payload = await sync_api.assistant_chat(
      tg_user_id=user.id,
      message="Покажи актуальные стажировки и junior вакансии",
    )
    if payload:
      jobs = list(payload.get("jobs", []))[:3]

    if not jobs:
      await callback.message.answer("Сейчас не нашёл свежих вакансий по этому запросу. Давай попробуем другой вариант.")
      await callback.answer()
      return

    await callback.message.answer(format_jobs_message("Твои топ вакансии", jobs), reply_markup=build_job_keyboard(jobs))
    await callback.answer()

  @router.message()
  async def handle_message(message: Message) -> None:
    if not message.text:
      await message.answer("Пока я умею работать с текстом. Напиши сообщение словами, и я сразу помогу.")
      return
    user = message.from_user
    if user is None:
      return

    if not sync_api:
      await message.answer("Сервис сейчас недоступен. Я уже жду, когда всё заработает, попробуй ещё раз чуть позже.")
      return

    payload = await sync_api.assistant_chat(tg_user_id=user.id, message=message.text)
    if not payload:
      await message.answer("Не получилось получить ответ сервиса. Попробуй снова через пару секунд.")
      return

    reply = str(payload.get("reply") or "Готовлю ответ...")
    jobs = list(payload.get("jobs", []))
    await message.answer(reply, reply_markup=main_keyboard(web_app_url))
    if jobs:
      top_jobs = jobs[:3]
      await message.answer(
        format_jobs_message("Подобрал вакансии по твоему запросу", top_jobs),
        reply_markup=build_job_keyboard(top_jobs),
      )
    else:
      await message.answer("По этому запросу пока нет результатов. Уточни роль, стек или город — и я подберу лучше.")

  return router
