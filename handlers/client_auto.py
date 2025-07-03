from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import create_order, get_service_price, update_order_data, get_order
import config

auto_states = {}

def format_summary(data: dict) -> str:
    lines = []
    if data.get("model"):
        lines.append(f"🚗 Модель: {data['model']}")
    if data.get("year"):
        lines.append(f"🗓️ Год: {data['year']}")
    if data.get("drive"):
        lines.append(f"🔧 Привод: {', '.join(data['drive'])}")
    if data.get("fuel"):
        lines.append(f"⛽ Топливо: {', '.join(data['fuel'])}")
    return "\n".join(lines)

async def render_model(chat_id, message_id, data):
    text = f"🚗 Введите модель автомобиля:\n\n{format_summary(data)}"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))
    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)

async def render_year(chat_id, message_id, data):
    text = f"🗓️ Введите минимальный год выпуска:\n\n{format_summary(data)}"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("↩️ Назад", callback_data=query_answers.AUTO_BACK),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)

async def render_drive(chat_id, message_id, data):
    text = f"🔧 Выберите тип привода:\n\n{format_summary(data)}"
    markup = InlineKeyboardMarkup(row_width=1)
    for label in ("Передний", "Задний", "Полный"):
        emoji = "✅" if label in data["drive"] else "❌"
        markup.add(InlineKeyboardButton(f"{emoji} {label}", callback_data=f"{query_answers.AUTO_DRIVE_TOGGLE}:{label}"))
    markup.add(
        InlineKeyboardButton("↩️ Назад", callback_data=query_answers.AUTO_BACK),
        InlineKeyboardButton("▶️ Далее", callback_data=query_answers.AUTO_DRIVE_NEXT),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)

async def render_fuel(chat_id, message_id, data):
    text = f"⛽ Выберите тип топлива:\n\n{format_summary(data)}"
    markup = InlineKeyboardMarkup(row_width=1)
    for label in ("Бензин", "Дизель", "Электро", "Гибрид"):
        emoji = "✅" if label.lower() in data["fuel"] else "❌"
        markup.add(InlineKeyboardButton(f"{emoji} {label}", callback_data=f"{query_answers.AUTO_FUEL_TOGGLE}:{label.lower()}"))
    markup.add(
        InlineKeyboardButton("↩️ Назад", callback_data=query_answers.AUTO_BACK),
        InlineKeyboardButton("▶️ Далее", callback_data=query_answers.AUTO_FUEL_NEXT),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.AUTO)
async def auto_start(c):
    auto_states[c.from_user.id] = {
        "step": "model",
        "data": {"model": "", "year": "", "drive": [], "fuel": []},
        "message_id": c.message.message_id
    }
    await render_model(c.message.chat.id, c.message.message_id, auto_states[c.from_user.id]["data"])
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.AUTO_BACK)
async def auto_back(c):
    state = auto_states[c.from_user.id]
    step = state["step"]
    if step == "year":
        state["step"] = "model"
        await render_model(c.message.chat.id, state["message_id"], state["data"])
    elif step == "drive":
        state["step"] = "year"
        await render_year(c.message.chat.id, state["message_id"], state["data"])
    elif step == "fuel":
        state["step"] = "drive"
        await render_drive(c.message.chat.id, state["message_id"], state["data"])
    elif step == "review":
        state["step"] = "fuel"
        await render_fuel(c.message.chat.id, state["message_id"], state["data"])
    await bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: m.from_user.id in auto_states)
async def auto_flow(m):
    state = auto_states[m.from_user.id]
    step = state["step"]
    await bot.delete_message(chat_id=m.chat.id, message_id=m.message_id)

    if step == "model":
        state["data"]["model"] = m.text
        state["step"] = "year"
        await render_year(m.chat.id, state["message_id"], state["data"])
    elif step == "year":
        state["data"]["year"] = m.text
        state["step"] = "drive"
        await render_drive(m.chat.id, state["message_id"], state["data"])

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.AUTO_DRIVE_TOGGLE))
async def auto_drive_toggle(c):
    key = c.data.split(":", 1)[1]
    sel = auto_states[c.from_user.id]["data"]["drive"]
    if key in sel:
        sel.remove(key)
    else:
        sel.append(key)
    await render_drive(c.message.chat.id, auto_states[c.from_user.id]["message_id"], auto_states[c.from_user.id]["data"])
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.AUTO_DRIVE_NEXT)
async def auto_drive_next(c):
    data = auto_states[c.from_user.id]["data"]
    if not data["drive"]:
        await bot.answer_callback_query(c.id, text="⚠️ Выберите хотя бы один тип привода", show_alert=True)
        return
    auto_states[c.from_user.id]["step"] = "fuel"
    await render_fuel(c.message.chat.id, auto_states[c.from_user.id]["message_id"], data)
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.AUTO_FUEL_TOGGLE))
async def auto_fuel_toggle(c):
    fuel = c.data.split(":", 1)[1]
    sel = auto_states[c.from_user.id]["data"]["fuel"]
    if fuel in sel:
        sel.remove(fuel)
    else:
        sel.append(fuel)
    await render_fuel(c.message.chat.id, auto_states[c.from_user.id]["message_id"], auto_states[c.from_user.id]["data"])
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.AUTO_FUEL_NEXT)
async def auto_fuel_next(c):
    data = auto_states[c.from_user.id]["data"]
    if not data["fuel"]:
        await bot.answer_callback_query(c.id, text="⚠️ Выберите хотя бы один тип топлива", show_alert=True)
        return
    auto_states[c.from_user.id]["step"] = "review"
    summary = format_summary(data)
    price = get_service_price("auto")
    text = f"✅ Подтвердите заявку:\n\n{summary}\n\n💰 Стоимость услуги: {price} ₽"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🚀 Отправить заявку", callback_data=query_answers.AUTO_SEND),
        InlineKeyboardButton("↩️ Назад", callback_data=query_answers.AUTO_BACK),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    await bot.edit_message_text(text, chat_id=c.message.chat.id, message_id=auto_states[c.from_user.id]["message_id"], reply_markup=markup)
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.AUTO_SEND)
async def auto_send(c):
    state = auto_states[c.from_user.id]
    price = get_service_price("auto")
    state["data"]["service_price"] = price
    order_id = create_order(
        user_id=c.from_user.id,
        username=c.from_user.username or "",
        type="auto",
        data=state["data"]
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{order_id}"),
        InlineKeyboardButton("💳 Оплатить через YooKassa", callback_data=f"{query_answers.PAY_YOOKASSA}:{order_id}"),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    await bot.edit_message_text(
        f"📬 Ваша заявка #{order_id} создана. Выберите метод оплаты:",
        chat_id=c.message.chat.id,
        message_id=state["message_id"],
        reply_markup=markup
    )

    await bot.answer_callback_query(c.id)
    del auto_states[c.from_user.id]