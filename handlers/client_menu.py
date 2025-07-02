from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from handlers.client_auto import auto_states  # для сброса состояния автоподбора
from handlers.client_details_to import details_to_states  # для сброса state «детали для ТО»

@bot.message_handler(commands=['start'])
async def start(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Детали для ТО", callback_data=query_answers.DETAILS_TO),
        InlineKeyboardButton("Детали на заказ", callback_data=query_answers.DETAILS_ORDER),
        InlineKeyboardButton("Подбор авто", callback_data=query_answers.AUTO),
        InlineKeyboardButton("Мои заявки", callback_data=query_answers.ORDERS),
        InlineKeyboardButton("FAQ", callback_data=query_answers.FAQ)
    )
    await bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == query_answers.MENU)
async def menu(call):
    # Сбрасываем все клиентские стейты
    auto_states.pop(call.from_user.id, None)
    details_to_states.pop(call.from_user.id, None)

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Детали для ТО", callback_data=query_answers.DETAILS_TO),
        InlineKeyboardButton("Детали на заказ", callback_data=query_answers.DETAILS_ORDER),
        InlineKeyboardButton("Подбор авто", callback_data=query_answers.AUTO),
        InlineKeyboardButton("Мои заявки", callback_data=query_answers.ORDERS),
        InlineKeyboardButton("FAQ", callback_data=query_answers.FAQ)
    )
    await bot.edit_message_text(
        "Главное меню",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)
