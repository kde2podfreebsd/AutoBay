from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import query_answers
from db.repository import get_service_price, set_service_price

SERVICE_LABELS = {
    "auto": "Подбор авто",
    "details_to": "Деталь для ТО",
    "details_order": "Деталь на заказ"
}

admin_price_states = {}

def build_prices_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    for key, label in SERVICE_LABELS.items():
        price = get_service_price(key)
        markup.add(
            InlineKeyboardButton(
                f"{label}: {price} ₽",
                callback_data=f"{query_answers.ADMIN_PRICES_SET}:{key}"
            )
        )
    markup.add(
        InlineKeyboardButton("🔙 Назад", callback_data=query_answers.ADMIN)
    )
    return markup

@bot.callback_query_handler(func=lambda c: c.data == query_answers.ADMIN_PRICES)
async def admin_prices(c):
    if c.from_user.id not in config.ADMINS:
        await bot.answer_callback_query(c.id, text="Доступ запрещён", show_alert=True)
        return
    await bot.edit_message_text(
        "💰 Настройка цен услуг",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=build_prices_markup()
    )
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_PRICES_SET))
async def admin_set_price(c):
    if c.from_user.id not in config.ADMINS:
        await bot.answer_callback_query(c.id, text="Доступ запрещён", show_alert=True)
        return
    _, key = c.data.rsplit(":", 1)
    admin_price_states[c.from_user.id] = key
    current = get_service_price(key)
    await bot.edit_message_text(
        f"Введите новую цену для услуги «{SERVICE_LABELS[key]}» (текущая цена: {current} ₽)",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id
    )
    await bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: m.from_user.id in admin_price_states)
async def handle_price_input(m):
    key = admin_price_states[m.from_user.id]
    try:
        price = int(m.text)
    except ValueError:
        await bot.send_message(m.chat.id, "Введите, пожалуйста, целое число.")
        return
    set_service_price(key, price)
    await bot.send_message(
        m.chat.id,
        f"✅ Цена для «{SERVICE_LABELS[key]}» установлена: {price} ₽"
    )
    # очистим состояние и покажем обновлённое меню
    del admin_price_states[m.from_user.id]
    await bot.send_message(
        m.chat.id,
        "💰 Настройка цен услуг",
        reply_markup=build_prices_markup()
    )
