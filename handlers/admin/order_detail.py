from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import query_answers
from db.repository import get_order, update_order_data, update_order_status
from telebot import types

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

# Состояние для выставления счёта
invoice_states = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_ORDER + ":"))
async def admin_order_detail(c):
    order_id = int(c.data.split(":")[-1])
    o = get_order(order_id)
    d = o.data
    label = TYPE_MAP.get(o.type, o.type)

    # Статус оплаты для админа
    if o.type in ("details_to", "details_order"):
        if not d.get("responses"):
            pay_label = "Ждёт ответа администратора"
        elif not d.get("response_accepted"):
            pay_label = "Ждёт подтверждения клиента"
        elif not d.get("service_price"):
            pay_label = "Ждёт выставления счёта"
        else:
            pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"
    else:  # для авто
        pay_label = "Оплачено" if o.payment_status == "paid" else "Ждёт оплаты"

    # Собираем текст
    text = (
        f"{label} #{o.id}\n"
        f"Пользователь: @{o.username} ({o.user_id})\n"
        f"Статус заявки: {STATUS_LABEL[o.status]}\n"
        f"Статус оплаты: {pay_label}\n\n"
    )

    # Детали заявки
    if o.type == "details_to":
        text += (
            f"🚗 Марка: {d['brand']}\n"
            f"🚗 Модель: {d['model']}\n"
            f"🗓️ Год: {d['year']}\n"
            f"🔑 VIN: {d['vin']}\n"
            f"🔧 Деталь: {d['name']}\n"
            f"🔗 Ссылка: {d.get('link') or '—'}\n\n"
        )
        # Комментарии клиента
        for idx, comm in enumerate(d.get("comments", []), start=1):
            text += f"💬 Комментарий #{idx}: {comm}\n\n"

    elif o.type == "auto":
        text += (
            f"🚗 Модель: {d['model']}\n"
            f"🗓️ Год: {d['year']}\n"
            f"🔧 Привод: {', '.join(d['drive'])}\n"
            f"⛽ Топливо: {', '.join(d['fuel'])}\n\n"
        )

    # Формируем кнопки
    buttons = []

    if o.status == "new":
        if o.type == "details_to":
            if d.get("comments") and not d.get("response_accepted"):
                # правки от клиента
                buttons.append(
                    InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{order_id}")
                )
            elif d.get("response_accepted") and not d.get("service_price"):
                # подтверждён ответ, ещё без счёта
                buttons.append(
                    InlineKeyboardButton("👁 Просмотреть ответы", callback_data=f"{query_answers.ADMIN_VIEW_RESPONSE}:{order_id}")
                )
                buttons.append(
                    InlineKeyboardButton("💰 Выставить счёт", callback_data=f"{query_answers.ADMIN_INVOICE}:{order_id}")
                )
            else:
                # новая заявка
                buttons.append(
                    InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{order_id}")
                )
        else:
            # авто или details_order
            buttons.append(
                InlineKeyboardButton("🛠️ Взять в работу", callback_data=f"{query_answers.ADMIN_TAKE}:{order_id}")
            )

    elif o.status == "in_progress":
        if o.type == "details_to":
            # в работе: всегда просмотр ответов
            buttons.append(
                InlineKeyboardButton("👁 Просмотреть ответы", callback_data=f"{query_answers.ADMIN_VIEW_RESPONSE}:{order_id}")
            )
            # добавить ответ, если клиент ещё не подтвердил
            if not d.get("response_accepted"):
                buttons.append(
                    InlineKeyboardButton("💬 Добавить ответ", callback_data=f"{query_answers.ADMIN_RESPOND}:{order_id}")
                )
        elif o.type == "auto":
            buttons.append(
                InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"{query_answers.ADMIN_CLOSE}:{order_id}")
            )
        else:
            buttons.append(
                InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"{query_answers.ADMIN_CLOSE}:{order_id}")
            )

    buttons.append(InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN))

    # Собираем разметку
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(*buttons)

    # Фото клиента для details_to
    if o.type == "details_to":
        for idx, _ in enumerate(d.get("photos", [])):
            markup.add(
                InlineKeyboardButton(
                    f"📷 {idx+1}",
                    callback_data=f"{query_answers.ADMIN_ORDER_PHOTO_VIEW}:{order_id}:{idx}"
                )
            )

    await bot.edit_message_text(
        text,
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_INVOICE + ":"))
async def admin_invoice_start(c):
    order_id = int(c.data.split(":")[-1])
    invoice_states[c.from_user.id] = order_id
    await bot.send_message(
        c.message.chat.id,
        f"💰 Введите сумму для счёта заявки #{order_id}:"
    )
    await bot.answer_callback_query(c.id)


@bot.message_handler(
    func=lambda m: m.from_user.id in invoice_states and m.text.isdigit(),
    content_types=['text']
)
async def admin_invoice_send(m):
    order_id = invoice_states.pop(m.from_user.id)
    amount = int(m.text)

    o = get_order(order_id)
    d = o.data
    d["service_price"] = amount
    update_order_data(order_id, d)

    # Ссылка YooMoney
    from services.yoomoney_service import YooMoney
    ym = YooMoney()
    url, uuid_tx = ym.create_quickpay(amount, target=f"Заявка #{order_id}")

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔗 Перейти к оплате", url=url),
        InlineKeyboardButton("✅ Я оплатил", callback_data=f"check_yoomoney:{order_id}:{uuid_tx}")
    )

    summary = (
        f"📬 Оплата по вашей заявке:\n\n"
        f"{'🚗 Модель: ' + d['model'] if o.type=='auto' else '🚗 Марка: ' + d['brand']}\n"
        # При необходимости можно добавить остальные поля
        f"\n💰 Сумма: {amount} ₽"
    )
    await bot.send_message(o.user_id, summary, reply_markup=markup)
    await bot.send_message(m.chat.id, f"✅ Счёт выставлен по заявке #{order_id}")
