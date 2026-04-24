from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.assistant_service import AssistantService
from bot.api_client import EasyTapApiClient
from bot.keyboards import main_keyboard


def build_router(
  assistant: AssistantService,
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

  @router.message(CommandStart())
  async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user is None:
      return

    link_hint = ""
    if sync_api:
      code = await sync_api.register_telegram_user(
        tg_user_id=user.id,
        username=user.username,
        full_name=user.full_name,
      )
      if code:
        web_line = f"\nОткрой сайт: {web_app_url}" if web_app_url else ""
        link_hint = (
          f"\n\nКод синхронизации: <b>{code}</b>"
          f"\nВведи его в AI-чате на сайте, чтобы связать аккаунты.{web_line}"
        )

    text = (
      "Привет! Я EasyTap AI-бот.\n"
      "Пиши карьерный вопрос, а я отвечу и подберу вакансии с hh.ru."
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
    code = await sync_api.register_telegram_user(
      tg_user_id=user.id,
      username=user.username,
      full_name=user.full_name,
    )
    if not code:
      await message.answer("Не удалось получить код. Попробуй позже.")
      return
    web_line = f"\nСайт: {web_app_url}" if web_app_url else ""
    await message.answer(f"Твой код синхронизации: <b>{code}</b>{web_line}")

  @router.callback_query(F.data == "show_jobs")
  async def show_jobs(callback: CallbackQuery) -> None:
    user = callback.from_user
    jobs: list = []
    if sync_api:
      payload = await sync_api.assistant_chat(
        tg_user_id=user.id,
        message="Покажи актуальные стажировки и junior вакансии",
      )
      if payload:
        jobs = list(payload.get("jobs", []))[:3]
    if not jobs:
      result = await assistant.handle_user_message("Покажи актуальные стажировки и junior вакансии")
      jobs = result.jobs[:3]
    if not jobs:
      await callback.message.answer("Пока нет свежих вакансий с hh.ru. Попробуй другой запрос.")
      await callback.answer()
      return

    await callback.message.answer(format_jobs_message("Твои топ вакансии", jobs))
    await callback.answer()

  @router.message()
  async def handle_message(message: Message) -> None:
    if not message.text:
      await message.answer("Пока поддерживаю только текстовые сообщения.")
      return
    user = message.from_user
    if user is None:
      return

    if sync_api:
      payload = await sync_api.assistant_chat(tg_user_id=user.id, message=message.text)
      if payload:
        reply = str(payload.get("reply") or "Готовлю ответ...")
        jobs = list(payload.get("jobs", []))
        await message.answer(reply, reply_markup=main_keyboard())
        if jobs:
          await message.answer(format_jobs_message("Подобрал вакансии по твоему запросу", jobs[:3]))
        else:
          await message.answer("По этому запросу ничего не нашлось. Уточни роль или город.")
        return

    result = await assistant.handle_user_message(message.text)
    await message.answer(result.answer, reply_markup=main_keyboard())

    if result.jobs:
      await message.answer(format_jobs_message("Подобрал вакансии по твоему запросу", result.jobs[:3]))
    else:
      await message.answer("По этому запросу ничего не нашлось ни на hh.ru, ни на других источниках. Уточни роль или город.")

  return router
