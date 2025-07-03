from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from handlers.client_auto import auto_states 
from handlers.client_details_to import details_to_states  

@bot.message_handler(commands=['start', 'menu'])
async def start(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🛠️ Детали для ТО", callback_data=query_answers.DETAILS_TO),
        InlineKeyboardButton("📦 Детали на заказ", callback_data=query_answers.DETAILS_ORDER),
        InlineKeyboardButton("🚘 Подбор авто", callback_data=query_answers.AUTO),
        InlineKeyboardButton("📑 Мои заявки", callback_data=query_answers.ORDERS),
        InlineKeyboardButton("❓ FAQ / Помощь", callback_data=query_answers.FAQ)
    )
    await bot.send_message(message.chat.id, f"Привет, <b>{message.chat.first_name}!</b>\n\n🏠 Главное меню", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == query_answers.MENU)
async def menu(call):
    auto_states.pop(call.from_user.id, None)
    details_to_states.pop(call.from_user.id, None)

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🛠️ Детали для ТО", callback_data=query_answers.DETAILS_TO),
        InlineKeyboardButton("📦 Детали на заказ", callback_data=query_answers.DETAILS_ORDER),
        InlineKeyboardButton("🚘 Подбор авто", callback_data=query_answers.AUTO),
        InlineKeyboardButton("📑 Мои заявки", callback_data=query_answers.ORDERS),
        InlineKeyboardButton("❓ FAQ / Помощь", callback_data=query_answers.FAQ)
    )
    await bot.edit_message_text(
        f"Привет, <b>{call.message.chat.first_name}!</b>\n\n🏠 Главное меню",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )
    await bot.answer_callback_query(call.id)
