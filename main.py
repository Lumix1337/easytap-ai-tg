import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.assistant_service import AssistantService
from bot.api_client import EasyTapApiClient
from bot.config import settings
from bot.groq_client import GroqClient
from bot.handlers import build_router
from bot.hh_client import HhClient
from bot.remotive_client import RemotiveClient


async def run() -> None:
  logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

  bot = Bot(token=settings.tg_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
  dp = Dispatcher()

  groq = GroqClient(settings.groq_api_key, settings.groq_model, settings.request_timeout)
  hh = HhClient(settings.hh_api_url, settings.request_timeout)
  remotive = RemotiveClient(settings.remotive_api_url, settings.request_timeout)
  assistant = AssistantService(groq, hh, remotive, jobs_limit=settings.hh_results_limit)
  sync_api = EasyTapApiClient(settings.easytap_api_url, settings.request_timeout) if settings.easytap_api_url else None
  dp.include_router(build_router(assistant, sync_api, settings.easytap_web_app_url))

  try:
    await dp.start_polling(bot)
  finally:
    await assistant.close()
    if sync_api:
      await sync_api.close()
    await bot.session.close()


if __name__ == "__main__":
  asyncio.run(run())
