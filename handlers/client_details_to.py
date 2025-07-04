from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import create_order

details_to_states = {}

STEPS = ["brand", "model", "year", "vin", "name", "link", "photos", "review"]

def format_summary(data: dict, step: str) -> str:
    """Формирует сводку по уже введённым полям, в зависимости от текущего шага."""
    step_idx = STEPS.index(step)
    lines = []
    for field, label in [
        ("brand", "🚗 Марка"),
        ("model", "🚗 Модель"),
        ("year", "🗓️ Год"),
        ("vin", "🔑 VIN"),
        ("name", "🔧 Деталь")
    ]:
        if data.get(field) and step_idx > STEPS.index(field):
            lines.append(f"{label}: {data[field]}")

    if step == "review":
        link = data.get("link", "")
        lines.append(f"🔗 Ссылка: {link or '—'}")
    elif step_idx > STEPS.index("link") and data.get("link"):
        lines.append(f"🔗 Ссылка: {data['link']}")

    if step == "review":
        cnt = len(data.get("photos", []))
        lines.append(f"📸 Фото: {cnt} шт." if cnt else "📸 Фото: —")
    elif step_idx >= STEPS.index("photos"):
        cnt = len(data.get("photos", []))
        lines.append(f"📸 Фото: {cnt} шт.")

    return "\n".join(lines)

async def render_step(chat_id: int, message_id: int, data: dict, step: str):
    """Редактирует сообщение, отображая текст и клавиатуру текущего шага."""
    summary = format_summary(data, step)
    markup = InlineKeyboardMarkup(row_width=1)

    if step == "brand":
        text = f"🚗 Введите марку автомобиля:\n\n{summary}"
        markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))

    elif step == "model":
        text = f"🚗 Введите модель автомобиля:\n\n{summary}"
        markup.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    elif step == "year":
        text = f"🗓️ Введите год выпуска:\n\n{summary}"
        markup.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    elif step == "vin":
        text = f"🔑 Введите VIN:\n\n{summary}"
        markup.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    elif step == "name":
        text = f"🔧 Введите наименование детали:\n\n{summary}"
        markup.add(
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    elif step == "link":
        text = f"🔗 Введите ссылку на товар с любого сайта(или нажмите «Пропустить»):\n\n{summary}"
        markup.add(
            InlineKeyboardButton("Пропустить", callback_data=query_answers.DETAILS_TO_LINK_SKIP),
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    elif step == "photos":
        text = f"📸 Прикрепите фото (можно несколько) или нажмите «Пропустить»:\n\n{summary}"
        for i in range(len(data.get("photos", []))):
            markup.add(
                InlineKeyboardButton(f"📷 {i+1}", callback_data=f"{query_answers.DETAILS_TO_PHOTO_VIEW}:{i}")
            )
        markup.add(
            InlineKeyboardButton("▶️ Далее", callback_data=query_answers.DETAILS_TO_NEXT),
            InlineKeyboardButton("Пропустить", callback_data=query_answers.DETAILS_TO_PHOTOS_SKIP),
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    elif step == "review":
        text = f"✅ Проверьте заявку:\n\n{format_summary(data, 'review')}"
        for i in range(len(data.get("photos", []))):
            markup.add(
                InlineKeyboardButton(f"📷 {i+1}", callback_data=f"{query_answers.DETAILS_TO_PHOTO_VIEW}:{i}")
            )
        markup.add(
            InlineKeyboardButton("✏️ Редактировать", callback_data=query_answers.DETAILS_TO_EDIT),
            InlineKeyboardButton("🚀 Отправить заявку", callback_data=query_answers.DETAILS_TO_SEND),
            InlineKeyboardButton("↩️ Назад", callback_data=query_answers.DETAILS_TO_BACK),
            InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
        )

    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO)
async def start_details_to(c):
    details_to_states[c.from_user.id] = {
        "step": "brand",
        "data": {"brand": "", "model": "", "year": "", "vin": "", "name": "", "link": "", "photos": []},
        "message_id": c.message.message_id
    }
    state = details_to_states[c.from_user.id]
    await render_step(c.message.chat.id, state["message_id"], state["data"], "brand")
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO_BACK)
async def details_to_back(c):
    state = details_to_states[c.from_user.id]
    idx = STEPS.index(state["step"])
    if idx > 0:
        state["step"] = STEPS[idx - 1]
    await render_step(c.message.chat.id, state["message_id"], state["data"], state["step"])
    await bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: m.from_user.id in details_to_states, content_types=['text'])
async def details_to_text(m):
    state = details_to_states[m.from_user.id]
    step = state["step"]
    await bot.delete_message(m.chat.id, m.message_id)
    if step in ["brand", "model", "year", "vin", "name", "link"]:
        state["data"][step] = m.text
        next_idx = STEPS.index(step) + 1
        state["step"] = STEPS[next_idx]
        await render_step(m.chat.id, state["message_id"], state["data"], state["step"])

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO_LINK_SKIP)
async def details_to_link_skip(c):
    state = details_to_states[c.from_user.id]
    state["data"]["link"] = ""
    state["step"] = "photos"
    await render_step(c.message.chat.id, state["message_id"], state["data"], "photos")
    await bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: m.from_user.id in details_to_states, content_types=['photo'])
async def details_to_photo(m):
    state = details_to_states[m.from_user.id]
    if state["step"] != "photos":
        return
    file_id = m.photo[-1].file_id
    state["data"]["photos"].append(file_id)
    await bot.delete_message(m.chat.id, m.message_id)
    await render_step(m.chat.id, state["message_id"], state["data"], "photos")

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO_PHOTOS_SKIP)
async def details_to_photos_skip(c):
    state = details_to_states[c.from_user.id]
    state["data"]["photos"] = []
    state["step"] = "review"
    await render_step(c.message.chat.id, state["message_id"], state["data"], "review")
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO_NEXT)
async def details_to_next(c):
    state = details_to_states[c.from_user.id]
    if state["step"] == "photos":
        state["step"] = "review"
        await render_step(c.message.chat.id, state["message_id"], state["data"], "review")
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.DETAILS_TO_PHOTO_VIEW))
async def details_to_photo_view(c):
    state = details_to_states[c.from_user.id]
    idx = int(c.data.split(":", 2)[2])
    file_id = state["data"]["photos"][idx]
    await bot.send_photo(c.message.chat.id, file_id)
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO_EDIT)
async def details_to_edit(c):
    await start_details_to(c)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.DETAILS_TO_SEND)
async def details_to_send(c):
    state = details_to_states[c.from_user.id]
    order_id = create_order(
        user_id=c.from_user.id,
        username=c.from_user.username or "",
        type="details_to",
        data=state["data"]
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))
    await bot.edit_message_text(
        f"📬 Ваша заявка принята. Ближайшее время менеджер обработает вашу заявку и направит ответ в телеграмм бота.",
        chat_id=c.message.chat.id,
        message_id=state["message_id"],
        reply_markup=markup
    )
    details_to_states.pop(c.from_user.id, None)