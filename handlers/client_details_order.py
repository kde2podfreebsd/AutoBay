from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import create_order, get_service_price

details_order_states = {}
STEPS = ["brand", "model", "year", "vin", "name", "link", "photos", "review"]


def format_summary(data: dict, step: str) -> str:
    idx = STEPS.index(step)
    lines = []
    for field, label in [
        ("brand", "🚗 Марка"),
        ("model", "🚗 Модель"),
        ("year", "🗓️ Год"),
        ("vin", "🔑 VIN"),
        ("name", "🔧 Деталь"),
    ]:
        if data.get(field) and idx > STEPS.index(field):
            lines.append(f"{label}: {data[field]}")
    if step == "review":
        lines.append(f"🔗 Ссылка: {data.get('link') or '—'}")
    elif idx > STEPS.index("link") and data.get("link"):
        lines.append(f"🔗 Ссылка: {data['link']}")
    cnt = len(data.get("photos", []))
    if idx >= STEPS.index("photos"):
        if step == "review":
            lines.append(f"📸 Фото: {cnt} шт." if cnt else "📸 Фото: —")
        else:
            lines.append(f"📸 Фото: {cnt} шт.")
    return "\n".join(lines)


async def render_step(chat_id, mid, data, step):
    summary = format_summary(data, step)
    kb = InlineKeyboardMarkup(row_width=1)

    if step == "brand":
        text = f"🚗 Введите марку автомобиля:\n\n{summary}"
        kb.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))

    elif step == "model":
        text = f"🚗 Введите модель автомобиля:\n\n{summary}"
        kb.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    elif step == "year":
        text = f"🗓️ Введите год выпуска:\n\n{summary}"
        kb.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    elif step == "vin":
        text = f"🔑 Введите VIN:\n\n{summary}"
        kb.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    elif step == "name":
        text = f"🔧 Введите наименование детали:\n\n{summary}"
        kb.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    elif step == "link":
        text = f"🔗 Введите ссылку на товар с любого сайта(или нажмите «Пропустить»):\n\n{summary}"
        kb.add(
            InlineKeyboardButton("Пропустить", callback_data=query_answers.DETAILS_ORDER_LINK_SKIP),
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    elif step == "photos":
        text = f"📸 Прикрепите фото (можно несколько) или «Пропустить»:\n\n{summary}"
        for i in range(len(data.get("photos", []))):
            kb.add(InlineKeyboardButton(f"📷 {i + 1}", callback_data=f"{query_answers.DETAILS_ORDER_PHOTO_VIEW}:{i}"))
        kb.add(
            InlineKeyboardButton("▶️ Далее", callback_data=query_answers.DETAILS_ORDER_NEXT),
            InlineKeyboardButton("Пропустить", callback_data=query_answers.DETAILS_ORDER_PHOTOS_SKIP),
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    elif step == "review":
        price = get_service_price("details_order")
        text = f"✅ Проверьте заявку:\n\n{format_summary(data, 'review')}\n\n💰 Стоимость услуги подбора: {price} ₽"
        for i in range(len(data.get("photos", []))):
            kb.add(InlineKeyboardButton(f"📷 {i + 1}", callback_data=f"{query_answers.DETAILS_ORDER_PHOTO_VIEW}:{i}"))
        kb.add(
            InlineKeyboardButton("🚀 Отправить заявку", callback_data=query_answers.DETAILS_ORDER_SEND),
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_ORDER_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
        )

    await bot.edit_message_text(text, chat_id=chat_id, message_id=mid, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER)
async def start_details_order(c):
    details_order_states[c.from_user.id] = {
        "step": "brand",
        "data": {"brand": "", "model": "", "year": "", "vin": "", "name": "", "link": "", "photos": []},
        "message_id": c.message.message_id,
    }
    st = details_order_states[c.from_user.id]
    await render_step(c.message.chat.id, st["message_id"], st["data"], "brand")
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER_BACK)
async def details_order_back(c):
    st = details_order_states[c.from_user.id]
    idx = STEPS.index(st["step"])
    if idx > 0:
        st["step"] = STEPS[idx - 1]
    await render_step(c.message.chat.id, st["message_id"], st["data"], st["step"])
    await bot.answer_callback_query(c.id)


@bot.message_handler(func=lambda m: m.from_user.id in details_order_states, content_types=["text"])
async def details_order_text(m):
    st = details_order_states[m.from_user.id]
    step = st["step"]
    await bot.delete_message(m.chat.id, m.message_id)
    if step in ["brand", "model", "year", "vin", "name", "link"]:
        st["data"][step] = m.text
        st["step"] = STEPS[STEPS.index(step) + 1]
        await render_step(m.chat.id, st["message_id"], st["data"], st["step"])


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER_LINK_SKIP)
async def details_order_link_skip(c):
    st = details_order_states[c.from_user.id]
    st["data"]["link"] = ""
    st["step"] = "photos"
    await render_step(c.message.chat.id, st["message_id"], st["data"], "photos")
    await bot.answer_callback_query(c.id)


@bot.message_handler(func=lambda m: m.from_user.id in details_order_states, content_types=["photo"])
async def details_order_photo(m):
    st = details_order_states[m.from_user.id]
    if st["step"] == "photos":
        st["data"]["photos"].append(m.photo[-1].file_id)
        await bot.delete_message(m.chat.id, m.message_id)
        await render_step(m.chat.id, st["message_id"], st["data"], "photos")


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER_PHOTOS_SKIP)
async def details_order_photos_skip(c):
    st = details_order_states[c.from_user.id]
    st["data"]["photos"] = []
    st["step"] = "review"
    await render_step(c.message.chat.id, st["message_id"], st["data"], "review")
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER_NEXT)
async def details_order_next(c):
    st = details_order_states[c.from_user.id]
    if st["step"] == "photos":
        st["step"] = "review"
        await render_step(c.message.chat.id, st["message_id"], st["data"], "review")
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith(query_answers.DETAILS_ORDER_PHOTO_VIEW))
async def details_order_photo_view(c):
    try:
        idx = int(c.data.split(":", 2)[2])
    except (ValueError, IndexError):
        await bot.answer_callback_query(c.id, "Неверные данные", show_alert=True)
        return
    st = details_order_states.get(c.from_user.id)
    if not st:
        await bot.answer_callback_query(c.id, "Сессия закончилась", show_alert=True)
        return
    photos = st["data"]["photos"]
    if 0 <= idx < len(photos):
        await bot.send_photo(c.message.chat.id, photos[idx])
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER_EDIT)
async def details_order_edit(c):
    await start_details_order(c)


@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_ORDER_SEND)
async def details_order_send(c):
    st = details_order_states[c.from_user.id]
    price = get_service_price("details_order")
    st["data"]["service_price"] = price
    order_id = create_order(
        user_id=c.from_user.id,
        username=c.from_user.username or "",
        type="details_order",
        data=st["data"],
    )
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{order_id}"),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU),
    )
    await bot.edit_message_text(
        f"📬 Ваша заявка создана. Оплатите услугу подбора:",
        chat_id=c.message.chat.id,
        message_id=st["message_id"],
        reply_markup=kb,
    )
    details_order_states.pop(c.from_user.id, None)
    await bot.answer_callback_query(c.id)
