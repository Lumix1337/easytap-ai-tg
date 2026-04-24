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
      "Привет! Я EasyTap AI-бот.\n"
      "Пиши карьерный вопрос, а я отвечу и подберу вакансии из базы EasyTap."
      f"{link_hint}"
    )
    await message.answer(text, reply_markup=main_keyboard())

  @router.message(Command("link"))
  async def cmd_link(message: Message) -> None:
    user = message.from_user
    if user is None:
      return
    if not sync_api:
      await message.answer("Синхронизация с сайтом отключена в настройках бота.")
      return
    link_info = await sync_api.register_telegram_user(
      tg_user_id=user.id,
      username=user.username,
      full_name=user.full_name,
    )
    if not link_info:
      await message.answer("Не удалось получить код. Попробуй позже.")
      return
    if link_info.get("linked"):
      await message.answer("Этот Telegram уже синхронизирован с аккаунтом на сайте.")
      return
    code = str(link_info.get("link_code") or "")
    if not code:
      await message.answer("Код не получен. Попробуй позже.")
      return
    web_line = f"\nСайт: {web_app_url}" if web_app_url else ""
    await message.answer(f"Твой код синхронизации: <b>{code}</b>{web_line}")

  @router.callback_query(F.data == "show_jobs")
  async def show_jobs(callback: CallbackQuery) -> None:
    user = callback.from_user
    if not sync_api:
      await callback.message.answer("Backend API не настроен. Укажи easytap_api_url в настройках бота.")
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
      await callback.message.answer("Пока нет свежих вакансий в базе. Попробуй другой запрос.")
      await callback.answer()
      return

    await callback.message.answer(format_jobs_message("Твои топ вакансии", jobs), reply_markup=build_job_keyboard(jobs))
    await callback.answer()

  @router.message()
  async def handle_message(message: Message) -> None:
    if not message.text:
      await message.answer("Пока поддерживаю только текстовые сообщения.")
      return
    user = message.from_user
    if user is None:
      return

    if not sync_api:
      await message.answer("Backend API не настроен. Укажи easytap_api_url в настройках бота.")
      return

    payload = await sync_api.assistant_chat(tg_user_id=user.id, message=message.text)
    if not payload:
      await message.answer("Не удалось получить ответ из backend. Проверь API и попробуй снова.")
      return

    reply = str(payload.get("reply") or "Готовлю ответ...")
    jobs = list(payload.get("jobs", []))
    await message.answer(reply, reply_markup=main_keyboard())
    if jobs:
      top_jobs = jobs[:3]
      await message.answer(
        format_jobs_message("Подобрал вакансии по твоему запросу", top_jobs),
        reply_markup=build_job_keyboard(top_jobs),
      )
    else:
      await message.answer("По этому запросу ничего не нашлось в базе. Уточни роль или город.")

  return router
