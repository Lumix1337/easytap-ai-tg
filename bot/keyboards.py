from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import urlparse


def _is_telegram_safe_url(url: str) -> bool:
  parsed = urlparse(url)
  if parsed.scheme not in {"http", "https"}:
    return False
  host = (parsed.hostname or "").lower()
  if not host:
    return False
  if host in {"localhost", "127.0.0.1", "::1"}:
    return False
  return True


def main_keyboard(web_app_url: str = "") -> InlineKeyboardMarkup:
  buttons: list[list[InlineKeyboardButton]] = [
    [InlineKeyboardButton(text="Показать топ вакансий", callback_data="show_jobs")],
    [InlineKeyboardButton(text="Связать Telegram с аккаунтом", callback_data="show_link_help")],
  ]

  base_url = web_app_url.rstrip("/")
  if base_url and _is_telegram_safe_url(base_url):
    buttons.extend(
      [
        [InlineKeyboardButton(text="Войти на сайте", url=f"{base_url}/auth?mode=login&redirect=%2Fassistant")],
        [InlineKeyboardButton(text="Регистрация на сайте", url=f"{base_url}/auth?mode=signup&redirect=%2Fassistant")],
      ]
    )

  return InlineKeyboardMarkup(inline_keyboard=buttons)
