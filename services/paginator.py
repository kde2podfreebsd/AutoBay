from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import math

def build_pagination(page: int, total_items: int, page_size: int, prefix: str) -> InlineKeyboardMarkup:
    total_pages = math.ceil(total_items / page_size) if total_items else 1
    markup = InlineKeyboardMarkup(row_width=3)
    prev_page = page - 1 if page > 1 else total_pages
    next_page = page + 1 if page < total_pages else 1
    markup.add(
        InlineKeyboardButton("<", callback_data=f"{prefix}:{prev_page}"),
        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"),
        InlineKeyboardButton(">", callback_data=f"{prefix}:{next_page}")
    )
    return markup