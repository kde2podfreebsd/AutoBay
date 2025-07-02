from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers

@bot.callback_query_handler(func=lambda call: call.data == query_answers.FAQ)
async def faq(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Назад в меню", callback_data=query_answers.MENU))
    await bot.edit_message_text("Здесь будет текст FAQ", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    await bot.answer_callback_query(call.id)