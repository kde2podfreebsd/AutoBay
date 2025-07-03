from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import (
    get_order,
    update_order_data,
    get_service_price,
)
from services.yoomoney_service import YooMoney

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

invoice_states = {}


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith(query_answers.ADMIN_ORDER + ":") and c.data.count(":") == 2)
async def admin_order_detail(c):
    order_id = int(c.data.split(":")[-1])
    o = get_order(order_id)
    d = o.data
    label = TYPE_MAP.get(o.type, o.type)

    service_price = get_service_price(o.type) if o.type == "details_order" else d.get("service_price", 0)
    service_paid = d.get("service_paid", False)
    if o.type == "auto" and o.payment_status == "paid":
        service_paid = True

    service_label = None
    if o.type in ("auto", "details_order"):
        service_label = "Услуга оплачена" if service_paid else f"Ждёт оплаты услуги ({service_price} ₽)"

    if o.type == "details_to":
        if not d.get("responses"):
            order_pay_label = "Ждёт ответа администратора"
        elif not d.get("response_accepted"):
            order_pay_label = "Ждёт подтверждения клиента"
        elif not d.get("service_price"):
            order_pay_label = "Ждёт выставления счёта"
        else:
            order_pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"
    elif o.type == "details_order":
        if not d.get("responses"):
            order_pay_label = "Ждёт ответа администратора"
        elif not d.get("response_accepted"):
            order_pay_label = "Ждёт подтверждения клиента"
        elif not d.get("invoice_price"):
            order_pay_label = "Ждёт выставления счёта"
        else:
            order_pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"
    else:
        order_pay_label = None

    text = (
        f"{label} #{o.id}\n"
        f"Пользователь: @{o.username} ({o.user_id})\n"
        f"Статус заявки: {STATUS_LABEL[o.status]}\n"
    )
    if service_label:
        text += f"Статус оплаты услуги: {service_label}\n"
    if order_pay_label:
        text += f"Статус оплаты заявки: {order_pay_label}\n"
    text += "\n"

    if o.type in ("details_to", "details_order"):
        text += (
            f"🚗 Марка: {d['brand']}\n"
            f"🚗 Модель: {d['model']}\n"
            f"🗓️ Год: {d['year']}\n"
            f"🔑 VIN: {d['vin']}\n"
            f"🔧 Деталь: {d['name']}\n"
            f"🔗 Ссылка: {d.get('link') or '—'}\n\n"
        )
        for idx, comm in enumerate(d.get("comments", []), start=1):
            text += f"💬 Комментарий #{idx}: {comm}\n\n"
    elif o.type == "auto":
        text += (
            f"🚗 Модель: {d['model']}\n"
            f"🗓️ Год: {d['year']}\n"
            f"🔧 Привод: {', '.join(d['drive'])}\n"
            f"⛽ Топливо: {', '.join(d['fuel'])}\n\n"
        )

    buttons = []

    if o.status == "new":
        if o.type == "auto" and service_paid:
            buttons.append(InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{order_id}"))
        elif o.type == "details_order" and service_paid:
            buttons.append(InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{order_id}"))
        elif o.type == "details_to":
            buttons.append(InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{order_id}"))

    if o.status == "in_progress":
        if o.type in ("details_to", "details_order"):
            buttons.append(InlineKeyboardButton("👁 Просмотреть ответы", callback_data=f"{query_answers.ADMIN_VIEW_RESPONSE}:{order_id}"))
            if not d.get("response_accepted"):
                buttons.append(InlineKeyboardButton("💬 Добавить ответ", callback_data=f"{query_answers.ADMIN_RESPOND}:{order_id}"))
            if o.type == "details_to" and d.get("response_accepted") and not d.get("service_price"):
                buttons.append(InlineKeyboardButton("💰 Выставить счёт", callback_data=f"{query_answers.ADMIN_INVOICE}:{order_id}"))
            if o.type == "details_order" and d.get("response_accepted") and not d.get("invoice_price"):
                buttons.append(InlineKeyboardButton("💰 Выставить счёт", callback_data=f"{query_answers.ADMIN_INVOICE}:{order_id}"))
            if o.type == "details_to" and o.payment_status == "paid":
                buttons.append(InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"{query_answers.ADMIN_CLOSE}:{order_id}"))
            if o.type == "details_order" and o.payment_status == "paid" and service_paid:
                buttons.append(InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"{query_answers.ADMIN_CLOSE}:{order_id}"))
        elif o.type == "auto" and service_paid:
            buttons.append(InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"{query_answers.ADMIN_CLOSE}:{order_id}"))

    buttons.append(InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(*buttons)

    if o.type in ("details_to", "details_order"):
        for idx, _ in enumerate(d.get("photos", [])):
            markup.add(InlineKeyboardButton(f"📷 {idx + 1}", callback_data=f"{query_answers.ADMIN_ORDER_PHOTO_VIEW}:{order_id}:{idx}"))

    await bot.edit_message_text(text, chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=markup)
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith(query_answers.ADMIN_ORDER_PHOTO_VIEW + ":"))
async def admin_order_photo_view(c):
    parts = c.data.split(":")
    order_id = int(parts[-2])
    idx = int(parts[-1])
    o = get_order(order_id)
    if o is None:
        await bot.answer_callback_query(c.id, "Заявка не найдена", show_alert=True)
        return
    photos = o.data.get("photos", [])
    if 0 <= idx < len(photos):
        await bot.send_photo(c.message.chat.id, photos[idx])
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_INVOICE + ":"))
async def admin_invoice_start(c):
    order_id = int(c.data.split(":")[-1])
    invoice_states[c.from_user.id] = order_id
    await bot.send_message(c.message.chat.id, f"💰 Введите сумму для счёта заявки #{order_id}:")
    await bot.answer_callback_query(c.id)


@bot.message_handler(func=lambda m: m.from_user.id in invoice_states and m.text.isdigit(), content_types=["text"])
async def admin_invoice_send(m):
    order_id = invoice_states.pop(m.from_user.id)
    amount = int(m.text)
    o = get_order(order_id)
    d = o.data
    if o.type == "details_to":
        d["service_price"] = amount
    else:
        d["invoice_price"] = amount
    update_order_data(order_id, d)
    ym = YooMoney()
    url, uuid_tx = ym.create_quickpay(amount, target=f"Заявка #{order_id}")
    summary = (
        f"📬 Оплата по вашей заявке:\n\n"
        f"🚗 Марка: {d['brand']}\n"
        f"🚗 Модель: {d['model']}\n"
        f"🗓️ Год: {d['year']}\n"
        f"🔑 VIN: {d['vin']}\n"
        f"🔧 Деталь: {d['name']}\n"
        f"🔗 Ссылка: {d.get('link') or '—'}\n\n"
        f"💰 Сумма: {amount} ₽"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔗 Перейти к оплате", url=url),
        InlineKeyboardButton("✅ Я оплатил", callback_data=f"check_yoomoney:{order_id}:{uuid_tx}")
    )
    await bot.send_message(o.user_id, summary, reply_markup=markup)
    await bot.send_message(m.chat.id, f"✅ Счёт выставлен по заявке #{order_id}")
