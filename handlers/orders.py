from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
import config
from services.paginator import build_pagination
from db.repository import get_orders_count, get_orders

TYPE_MAP = {
    "auto": "Услуга подбора автомобиля",
    "details_to": "Деталь для ТО",
    "details_order": "Деталь на заказ",
}
PAY_MAP = {
    "paid": "Оплачено",
    "pending": "Ждёт оплаты"
}
STATUS_MAP = {
    "new": "Ждёт обработки",
    "in_progress": "В работе",
    "closed": "Закрыта"
}

@bot.callback_query_handler(func=lambda call: call.data.startswith(query_answers.ORDERS))
async def handle_orders(call):
    parts = call.data.split(":")
    if parts[0] == query_answers.ORDERS and len(parts) == 1:
        page = 1
    elif call.data.startswith(query_answers.ORDERS_PAGE):
        page = int(parts[-1])
    else:
        await bot.answer_callback_query(call.id)
        return

    user_id = call.from_user.id
    total = get_orders_count(user_id)
    orders = get_orders(user_id, (page - 1) * config.PAGE_SIZE, config.PAGE_SIZE)

    if not orders:
        text = "У вас нет заявок"
    else:
        o = orders[0]
        label = TYPE_MAP.get(o.type, o.type)
        data = o.data

        # Статус оплаты
        if o.payment_status == "pending" and data.get("responses") and not data.get("response_accepted"):
            pay_label = "Ждёт подтверждения от клиента"
        else:
            pay_label = PAY_MAP.get(o.payment_status, o.payment_status)

        text = (
            f"Тип: {label}\n"
            f"Статус оплаты: {pay_label}\n"
            f"Статус заявки: {STATUS_MAP.get(o.status, o.status)}\n\n"
        )

        if o.type == "auto":
            d = o.data
            text += (
                f"🚗 Модель: {d['model']}\n"
                f"🗓️ Год: {d['year']}\n"
                f"🔧 Привод: {', '.join(d['drive'])}\n"
                f"⛽ Топливо: {', '.join(d['fuel'])}"
            )
        elif o.type == "details_to":
            d = o.data
            text += (
                f"🚗 Марка: {d['brand']}\n"
                f"🚗 Модель: {d['model']}\n"
                f"🗓️ Год: {d['year']}\n"
                f"🔑 VIN: {d['vin']}\n"
                f"🔧 Деталь: {d['name']}"
            )

    # Собираем клавиатуру
    markup = InlineKeyboardMarkup(row_width=1)

    # Для заявки авто с pending—добавляем кнопки оплаты
    if orders and o.type == "auto" and o.payment_status == "pending":
        markup.add(
            InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{o.id}")
        )
        markup.add(
            InlineKeyboardButton("💳 Оплатить через YooKassa", callback_data=f"{query_answers.PAY_YOOKASSA}:{o.id}")
        )

    # Добавляем пагинацию
    paginator = build_pagination(page, total, config.PAGE_SIZE, query_answers.ORDERS_PAGE)
    for row in paginator.keyboard:
        markup.row(*row)

    # Кнопка выхода в меню
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))

    await bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)
