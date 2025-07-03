from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from bot import bot
import query_answers
from db.repository import get_order, update_order_data
from telebot import types

respond_states = {}
RESP_STEPS = ["text", "photos", "preview"]

def _is_respond_start(data: str) -> bool:
    parts = data.split(":")
    return len(parts) == 3 and parts[0] == "admin" and parts[1] == "respond" and parts[2].isdigit()

async def prompt_text(chat_id: int, message_id: int, state: dict):
    await bot.edit_message_text(
        "✏️ Введите текст ответа для клиента:",
        chat_id=chat_id,
        message_id=message_id
    )

async def prompt_photos(chat_id: int, message_id: int, state: dict):
    text = f"✏️ Текст:\n\n{state['data']['text']}\n\n📸 Прикрепите фото или «Пропустить»:"
    kb = InlineKeyboardMarkup(row_width=1)
    order_id = state["order_id"]
    for idx, _ in enumerate(state["data"]["photos"]):
        kb.add(InlineKeyboardButton(f"📷 {idx+1}", callback_data=f"{query_answers.ADMIN_RESPOND_PHOTO_VIEW}:{idx}"))
    kb.add(
        InlineKeyboardButton("▶️ Далее", callback_data=query_answers.ADMIN_RESPOND_NEXT),
        InlineKeyboardButton("Пропустить", callback_data=query_answers.ADMIN_RESPOND_PHOTOS_SKIP),
        InlineKeyboardButton("↩️ Назад", callback_data=f"{query_answers.ADMIN_RESPOND}:{order_id}"),
        InlineKeyboardButton("⬅️ Админ-меню", callback_data=query_answers.ADMIN)
    )
    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=kb)

async def show_preview(chat_id: int, message_id: int, state: dict):
    text = f"👀 Предпросмотр ответа:\n\n{state['data']['text']}"
    kb = InlineKeyboardMarkup(row_width=1)
    for idx, _ in enumerate(state["data"]["photos"]):
        kb.add(InlineKeyboardButton(f"📷 {idx+1}", callback_data=f"{query_answers.ADMIN_RESPOND_PHOTO_VIEW}:{idx}"))
    order_id = state["order_id"]
    kb.add(
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"{query_answers.ADMIN_RESPOND}:{order_id}"),
        InlineKeyboardButton("🚀 Отправить ответ", callback_data=query_answers.ADMIN_RESPOND_SEND),
        InlineKeyboardButton("↩️ Назад", callback_data=query_answers.ADMIN_RESPOND_BACK),
        InlineKeyboardButton("⬅️ Админ-меню", callback_data=query_answers.ADMIN)
    )
    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: _is_respond_start(c.data))
async def admin_respond_start(c):
    order_id = int(c.data.split(":")[2])
    respond_states[c.from_user.id] = {
        "order_id": order_id,
        "step": "text",
        "data": {"text": "", "photos": []},
        "message_id": c.message.message_id
    }
    await prompt_text(c.message.chat.id, c.message.message_id, respond_states[c.from_user.id])
    await bot.answer_callback_query(c.id)

@bot.message_handler(
    func=lambda m: m.from_user.id in respond_states and respond_states[m.from_user.id]["step"] == "text",
    content_types=['text']
)
async def handle_respond_text(m):
    st = respond_states[m.from_user.id]
    st["data"]["text"] = m.text
    st["step"] = "photos"
    await bot.delete_message(m.chat.id, m.message_id)
    await prompt_photos(m.chat.id, st["message_id"], st)

@bot.message_handler(
    func=lambda m: m.from_user.id in respond_states and respond_states[m.from_user.id]["step"] == "photos",
    content_types=['photo']
)
async def handle_respond_photo(m):
    st = respond_states[m.from_user.id]
    st["data"]["photos"].append(m.photo[-1].file_id)
    await bot.delete_message(m.chat.id, m.message_id)
    await prompt_photos(m.chat.id, st["message_id"], st)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.ADMIN_RESPOND_PHOTOS_SKIP)
async def handle_skip_photos(c):
    st = respond_states[c.from_user.id]
    st["data"]["photos"] = []
    st["step"] = "preview"
    await bot.answer_callback_query(c.id)
    await show_preview(c.message.chat.id, st["message_id"], st)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.ADMIN_RESPOND_NEXT)
async def handle_next(c):
    st = respond_states[c.from_user.id]
    if st["step"] != "photos":
        await bot.answer_callback_query(c.id)
        return
    st["step"] = "preview"
    await bot.answer_callback_query(c.id)
    await show_preview(c.message.chat.id, st["message_id"], st)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_RESPOND_PHOTO_VIEW + ":"))
async def handle_view_photo(c):
    st = respond_states[c.from_user.id]
    idx = int(c.data.split(":")[-1])
    await bot.send_photo(c.message.chat.id, st["data"]["photos"][idx])
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.ADMIN_RESPOND_BACK)
async def handle_back(c):
    st = respond_states[c.from_user.id]
    st["step"] = "photos"
    await bot.answer_callback_query(c.id)
    await prompt_photos(c.message.chat.id, st["message_id"], st)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.ADMIN_RESPOND_SEND)
async def handle_send_response(c):
    state = respond_states[c.from_user.id]
    order_id = state["order_id"]
    o = get_order(order_id)
    client_chat = o.user_id

    if state["data"]["photos"]:
        media = [InputMediaPhoto(media=fid) for fid in state["data"]["photos"]]
        media[0].caption = state["data"]["text"]
        await bot.send_media_group(client_chat, media)
    else:
        await bot.send_message(client_chat, state["data"]["text"])

    d = o.data
    d.setdefault("responses", []).append(state["data"])
    update_order_data(order_id, d)
    del respond_states[c.from_user.id]

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Устраивает", callback_data=f"{query_answers.CLIENT_RESPONSE_ACCEPT}:{order_id}"),
        InlineKeyboardButton("❌ Не устраивает", callback_data=f"{query_answers.CLIENT_RESPONSE_REJECT}:{order_id}")
    )
    await bot.send_message(
        client_chat,
        f"📩 Ответ администратора по Вашей заявке. Пожалуйста, подтвердите или добавьте комментарий к заявке - тогда Ваша заявка будет доработана с учетом ваших замечаний.",
        reply_markup=markup
    )
    await bot.send_message(
        c.message.chat.id,
        f"✔️ Ответ отправлен клиенту по заявке #{order_id}.",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Назад к заявке", callback_data=f"{query_answers.ADMIN_ORDER}:{order_id}")
        )
    )
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(
    func=lambda c: c.data.startswith(query_answers.ADMIN_VIEW_RESPONSE + ":")
            and len(c.data.split(":")) in (3, 4)
)
async def admin_view_response(c):
    parts = c.data.split(":")
    if len(parts) == 3:
        order_id = int(parts[2])
        o = get_order(order_id)
        d = o.data
        resp_list = d.get("responses", [])
        if not resp_list:
            await bot.answer_callback_query(c.id, text="Нет ответов", show_alert=True)
            return
        kb = InlineKeyboardMarkup(row_width=1)
        for idx in range(len(resp_list)):
            kb.add(InlineKeyboardButton(f"Ответ {idx+1}", callback_data=f"{query_answers.ADMIN_VIEW_RESPONSE}:{order_id}:{idx}"))
        kb.add(InlineKeyboardButton("🔙 Назад к заявке", callback_data=f"{query_answers.ADMIN_ORDER}:{order_id}"))
        await bot.edit_message_text(
            "📄 Выберите ответ для просмотра:",
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=kb
        )
        await bot.answer_callback_query(c.id)

    elif len(parts) == 4:
        order_id = int(parts[2])
        idx = int(parts[3])
        o = get_order(order_id)
        d = o.data
        resp_list = d.get("responses", [])
        if idx < 0 or idx >= len(resp_list):
            await bot.answer_callback_query(c.id, text="Неверный номер ответа", show_alert=True)
            return
        resp = resp_list[idx]
        text = resp.get("text", "")
        kb = InlineKeyboardMarkup(row_width=1)
        for photo_idx, _ in enumerate(resp.get("photos", [])):
            kb.add(
                InlineKeyboardButton(
                    f"Фото {photo_idx+1}",
                    callback_data=f"{query_answers.ADMIN_VIEW_RESPONSE_PHOTO}:{order_id}:{idx}:{photo_idx}"
                )
            )
        kb.add(
            InlineKeyboardButton("🔙 Все ответы", callback_data=f"{query_answers.ADMIN_VIEW_RESPONSE}:{order_id}"),
            InlineKeyboardButton("🔙 Назад к заявке", callback_data=f"{query_answers.ADMIN_ORDER}:{order_id}")
        )
        await bot.edit_message_text(
            text,
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=kb
        )
        await bot.answer_callback_query(c.id)

@bot.callback_query_handler(
    func=lambda c: c.data.startswith(query_answers.ADMIN_VIEW_RESPONSE_PHOTO + ":")
)
async def handle_view_response_photo(c):
    parts = c.data.split(":")
    # ["admin","view_response","photo","<order_id>","<resp_idx>","<photo_idx>"]
    try:
        order_id = int(parts[3])
        resp_idx  = int(parts[4])
        photo_idx = int(parts[5])
    except (ValueError, IndexError):
        await bot.answer_callback_query(c.id, text="Неверный формат данных", show_alert=True)
        return

    o = get_order(order_id)
    if o is None:
        await bot.answer_callback_query(c.id, text=f"Заявка #{order_id} не найдена", show_alert=True)
        return

    resp_list = o.data.get("responses", [])
    if resp_idx < 0 or resp_idx >= len(resp_list):
        await bot.answer_callback_query(c.id, text="Ответ не найден", show_alert=True)
        return

    photos = resp_list[resp_idx].get("photos", [])
    if photo_idx < 0 or photo_idx >= len(photos):
        await bot.answer_callback_query(c.id, text="Фото не найдено", show_alert=True)
        return

    await bot.send_photo(c.message.chat.id, photos[photo_idx])
    await bot.answer_callback_query(c.id)