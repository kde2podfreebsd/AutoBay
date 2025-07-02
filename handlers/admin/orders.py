from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import query_answers
from services.paginator import build_pagination
from db.repository import get_orders_by_status, get_orders_count_by_status

TYPE_MAP = {
    "auto": "Услуга подбора автомобиля",
    "details_to": "Деталь для ТО",
    "details_order": "Деталь на заказ",
}

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_NEW))
async def admin_new(c):
    parts = c.data.split(":")
    page = int(parts[2]) if len(parts) == 3 else 1
    total = get_orders_count_by_status("new")
    orders = get_orders_by_status("new",
                                  offset=(page - 1) * config.PAGE_SIZE,
                                limit=config.PAGE_SIZE)

    markup = InlineKeyboardMarkup(row_width=1)
    if orders:
        for o in orders:
            label = TYPE_MAP.get(o.type, o.type)
            markup.add(
                InlineKeyboardButton(f"{label} #{o.id}", callback_data=f"{query_answers.ADMIN_ORDER}:{o.id}")
            )
        paginator = build_pagination(page, total, config.PAGE_SIZE, query_answers.ADMIN_NEW)
        for row in paginator.keyboard:
            markup.row(*row)
    else:
        markup.add(InlineKeyboardButton("— Заявок нет —", callback_data="ignore"))

    markup.add(InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN))

    await bot.edit_message_text(
        f"🆕 Новые заявки ({total})",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_IN_PROGRESS))
async def admin_in_progress(c):
    parts = c.data.split(":")
    page = int(parts[2]) if len(parts) == 3 else 1
    total = get_orders_count_by_status("in_progress")
    orders = get_orders_by_status("in_progress",
                                  offset=(page - 1) * config.PAGE_SIZE,
                                  limit=config.PAGE_SIZE)

    markup = InlineKeyboardMarkup(row_width=1)
    if orders:
        for o in orders:
            label = TYPE_MAP.get(o.type, o.type)
            markup.add(
                InlineKeyboardButton(f"{label} #{o.id}", callback_data=f"{query_answers.ADMIN_ORDER}:{o.id}")
            )
        paginator = build_pagination(page, total, config.PAGE_SIZE, query_answers.ADMIN_IN_PROGRESS)
        for row in paginator.keyboard:
            markup.row(*row)
    else:
        markup.add(InlineKeyboardButton("— Заявок нет —", callback_data="ignore"))

    markup.add(InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN))

    await bot.edit_message_text(
        f"⚙️ В работе ({total})",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_CLOSED))
async def admin_closed(c):
    parts = c.data.split(":")
    page = int(parts[2]) if len(parts) == 3 else 1
    total = get_orders_count_by_status("closed")
    orders = get_orders_by_status("closed",
                                  offset=(page - 1) * config.PAGE_SIZE,
                                  limit=config.PAGE_SIZE)

    markup = InlineKeyboardMarkup(row_width=1)
    if orders:
        for o in orders:
            label = TYPE_MAP.get(o.type, o.type)
            markup.add(
                InlineKeyboardButton(f"{label} #{o.id}", callback_data=f"{query_answers.ADMIN_ORDER}:{o.id}")
            )
        paginator = build_pagination(page, total, config.PAGE_SIZE, query_answers.ADMIN_CLOSED)
        for row in paginator.keyboard:
            markup.row(*row)
    else:
        markup.add(InlineKeyboardButton("— Заявок нет —", callback_data="ignore"))

    markup.add(InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN))

    await bot.edit_message_text(
        f"✅ Закрытые ({total})",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)