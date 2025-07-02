from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import update_order_status, get_order
from handlers.admin.order_detail import admin_order_detail

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_TAKE))
async def admin_take_order(c):
    order_id = int(c.data.split(":")[-1])
    update_order_status(order_id, "in_progress")
    await bot.answer_callback_query(c.id, text="Заявка взята в работу 🛠️", show_alert=True)
    c.data = f"{query_answers.ADMIN_ORDER}:{order_id}"
    await admin_order_detail(c)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.ADMIN_CLOSE))
async def admin_close_order(c):
    order_id = int(c.data.split(":")[-1])
    update_order_status(order_id, "closed")
    await bot.answer_callback_query(c.id, text="Заявка закрыта ✅", show_alert=True)
    c.data = f"{query_answers.ADMIN_ORDER}:{order_id}"
    await admin_order_detail(c)