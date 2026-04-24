from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [InlineKeyboardButton(text="Показать топ вакансий", callback_data="show_jobs")],
    ]
  )
