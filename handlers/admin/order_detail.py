from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import get_order

TYPE_MAP = {
    "auto": "Услуга подбора автомобиля",
    "details_to": "Деталь для ТО",
    "details_order": "Деталь на заказ",
}
STATUS_LABEL = {
    "new": "Ждёт обработки",
    "in_progress": "В работе",
    "closed": "Закрыта",
}
PAY_LABEL = {
    "pending": "Ждёт оплаты",
    "paid": "Оплачено",
}

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_ORDER))
async def admin_order_detail(c):
    # callback_data = "admin:order:<id>"
    order_id = int(c.data.split(":")[-1])
    o = get_order(order_id)
    d = o.data
    label = TYPE_MAP.get(o.type, o.type)
    text = (
        f"{label} #{o.id}\n"
        f"Пользователь: @{o.username} ({o.user_id})\n"
        f"Статус заявки: {STATUS_LABEL[o.status]}\n"
        f"Статус оплаты: {PAY_LABEL[o.payment_status]}\n\n"
    )
    if o.type == "auto":
        text += (
            f"🚗 Модель: {d['model']}\n"
            f"🗓️ Год: {d['year']}\n"
            f"🔧 Привод: {', '.join(d['drive'])}\n"
            f"⛽ Топливо: {', '.join(d['fuel'])}\n\n"
        )

    buttons = []
    if o.status == "new":
        buttons.append(InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{o.id}"))
    elif o.status == "in_progress":
        buttons.append(InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"{query_answers.ADMIN_CLOSE}:{o.id}"))
    buttons.append(InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(*buttons)

    await bot.edit_message_text(
        text,
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)