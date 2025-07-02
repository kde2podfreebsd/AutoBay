# handlers/orders.py

from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
import config
from services.paginator import build_pagination
from db.repository import get_orders_count, get_orders

TYPE_MAP = {"auto": "Услуга подбора автомобиля"}
PAY_MAP = {"paid": "Оплачено", "pending": "Ждёт оплаты"}
STATUS_MAP = {"new": "Ждёт обработки", "in_progress": "В работе", "closed": "Закрыта"}

@bot.callback_query_handler(func=lambda call: call.data.startswith(query_answers.ORDERS))
async def handle_orders(call):
    parts = call.data.split(":")
    page = 1 if len(parts) == 1 else int(parts[2])
    user_id = call.from_user.id
    total = get_orders_count(user_id)
    orders = get_orders(user_id, (page-1)*config.PAGE_SIZE, config.PAGE_SIZE)

    if not orders:
        text = "У вас нет заявок"
    else:
        o = orders[0]
        text = (
            f"Тип: {TYPE_MAP.get(o.type, o.type)}\n"
            f"Статус оплаты: {PAY_MAP[o.payment_status]}\n"
            f"Статус заявки: {STATUS_MAP[o.status]}\n\n"
        )
        if o.type == "auto":
            d = o.data
            text += (
                f"🚗 Модель: {d['model']}\n"
                f"🗓️ Год: {d['year']}\n"
                f"🔧 Привод: {', '.join(d['drive'])}\n"
                f"⛽ Топливо: {', '.join(d['fuel'])}"
            )

    markup = build_pagination(page, total, config.PAGE_SIZE, query_answers.ORDERS_PAGE)
    if orders:
        o = orders[0]
        if o.payment_status == "pending":
            markup.add(
                InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{o.id}"),
                InlineKeyboardButton("💳 Оплатить через YooKassa", callback_data=f"{query_answers.PAY_YOOKASSA}:{o.id}")
            )
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))

    await bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)
