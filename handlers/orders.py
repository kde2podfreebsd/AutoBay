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
STATUS_MAP = {
    "new": "Ждёт обработки",
    "in_progress": "В работе",
    "closed": "Закрыта",
}

@bot.callback_query_handler(func=lambda call: call.data.startswith(query_answers.ORDERS))
async def handle_orders(call):
    parts = call.data.split(":")
    page = 1 if call.data == query_answers.ORDERS else int(parts[-1])
    user_id = call.from_user.id
    total = get_orders_count(user_id)
    orders = get_orders(user_id, (page - 1) * config.PAGE_SIZE, config.PAGE_SIZE)
    if not orders:
        text = "У вас нет заявок"
    else:
        o = orders[0]
        d = o.data
        label = TYPE_MAP.get(o.type, o.type)
        if o.type == "auto":
            pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"
        elif o.type == "details_to":
            if not d.get("service_price"):
                pay_label = "Ждёт выставления счёта"
            else:
                pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"
        else:
            if not d.get("service_paid"):
                pay_label = "Ждёт оплаты услуги"
            elif not d.get("invoice_price"):
                pay_label = "Ждёт выставления счёта"
            else:
                pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"
        text = (
            f"Тип: {label}\n"
            f"Статус оплаты: {pay_label}\n"
            f"Статус заявки: {STATUS_MAP.get(o.status, o.status)}\n\n"
        )
        if o.type == "auto":
            text += (
                f"🚗 Модель: {d['model']}\n"
                f"🗓️ Год: {d['year']}\n"
                f"🔧 Привод: {', '.join(d['drive'])}\n"
                f"⛽ Топливо: {', '.join(d['fuel'])}"
            )
        else:
            text += (
                f"🚗 Марка: {d['brand']}\n"
                f"🚗 Модель: {d['model']}\n"
                f"🗓️ Год: {d['year']}\n"
                f"🔑 VIN: {d['vin']}\n"
                f"🔧 Деталь: {d['name']}"
            )

    markup = InlineKeyboardMarkup(row_width=1)

    if orders and o.type == "auto" and o.payment_status == "pending":
        markup.add(InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{o.id}"))
        markup.add(InlineKeyboardButton("💳 Оплатить через YooKassa", callback_data=f"{query_answers.PAY_YOOKASSA}:{o.id}"))

    if orders and o.type == "details_to" and d.get("service_price") and o.payment_status == "pending":
        markup.add(InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{o.id}"))

    if orders and o.type == "details_order" and not d.get("service_paid"):
        markup.add(InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{o.id}"))

    if orders and o.type == "details_order" and d.get("service_paid") and d.get("invoice_price") and o.payment_status == "pending":
        markup.add(InlineKeyboardButton("💸 Оплатить счёт", callback_data=f"{query_answers.PAY_YOOMONEY}:{o.id}"))

    paginator = build_pagination(page, total, config.PAGE_SIZE, query_answers.ORDERS_PAGE)
    for row in paginator.keyboard:
        markup.row(*row)
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))

    await bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    await bot.answer_callback_query(call.id)
