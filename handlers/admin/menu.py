from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import query_answers
from db.repository import get_orders_count_by_status

@bot.message_handler(commands=['admin'])
async def admin_menu_msg(message):
    if message.from_user.id not in config.ADMINS:
        return
    new_count = get_orders_count_by_status('new')
    in_prog_count = get_orders_count_by_status('in_progress')
    closed_count = get_orders_count_by_status('closed')
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"🆕 Новые заявки ({new_count})", callback_data=query_answers.ADMIN_NEW),
        InlineKeyboardButton(f"⚙️ В работе ({in_prog_count})", callback_data=query_answers.ADMIN_IN_PROGRESS),
        InlineKeyboardButton(f"✅ Закрытые ({closed_count})", callback_data=query_answers.ADMIN_CLOSED),
        InlineKeyboardButton("💰 Цены услуг", callback_data=query_answers.ADMIN_PRICES),
        InlineKeyboardButton("🚪 Выход", callback_data=query_answers.ADMIN_EXIT)
    )
    await bot.send_message(message.chat.id, "🔧 Админ-меню", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == query_answers.ADMIN)
async def admin_menu_cb(c):
    if c.from_user.id not in config.ADMINS:
        await bot.answer_callback_query(c.id, text="Доступ запрещён", show_alert=True)
        return
    new_count = get_orders_count_by_status('new')
    in_prog_count = get_orders_count_by_status('in_progress')
    closed_count = get_orders_count_by_status('closed')
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"🆕 Новые заявки ({new_count})", callback_data=query_answers.ADMIN_NEW),
        InlineKeyboardButton(f"⚙️ В работе ({in_prog_count})", callback_data=query_answers.ADMIN_IN_PROGRESS),
        InlineKeyboardButton(f"✅ Закрытые ({closed_count})", callback_data=query_answers.ADMIN_CLOSED),
        InlineKeyboardButton("💰 Цены услуг", callback_data=query_answers.ADMIN_PRICES),
        InlineKeyboardButton("🚪 Выход", callback_data=query_answers.ADMIN_EXIT)
    )
    await bot.edit_message_text(
        "🔧 Админ-меню",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda call: call.data == query_answers.ADMIN_EXIT)
async def admin_exit(call):
    if call.from_user.id not in config.ADMINS:
        await bot.answer_callback_query(call.id, text="Доступ запрещён", show_alert=True)
        return
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await bot.answer_callback_query(call.id)
