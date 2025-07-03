from bot import bot
import query_answers
import config
from db.repository import get_order, update_order_data, update_order_status
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

client_response_states = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.CLIENT_RESPONSE_ACCEPT + ":"))
async def client_accept(c):
    order_id = int(c.data.split(":")[-1])
    o = get_order(order_id)
    d = o.data
    d["response_accepted"] = True
    update_order_data(order_id, d)
    update_order_status(order_id, "new")

    await bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    await bot.send_message(
        c.message.chat.id,
        "✅ Спасибо за подтверждение. Администратор скоро выставит счёт."
    )
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Клиент подтвердил ответ по заявке #{order_id}"
    )
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.CLIENT_RESPONSE_REJECT + ":"))
async def client_reject(c):
    order_id = int(c.data.split(":")[-1])
    client_response_states[c.from_user.id] = {"order_id": order_id}
    await bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    await bot.send_message(c.message.chat.id, "❗ Напишите, пожалуйста, комментарий к ответу. После вашего ответа, заявка уйдет на повтороное рассмотрение нашим специалистом.")
    await bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: m.from_user.id in client_response_states, content_types=['text'])
async def client_comment(m):
    state = client_response_states.pop(m.from_user.id)
    order_id = state["order_id"]
    comment = m.text

    o = get_order(order_id)
    d = o.data
    d.setdefault("comments", []).append(comment)
    update_order_data(order_id, d)
    update_order_status(order_id, "new")

    await bot.send_message(m.chat.id, "❗ Ваш комментарий отправлен администратору. Ближайшее время менеджер направит Вам ответ с учетом ваших пожеланий.")
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Клиент оставил комментарий по заявке #{order_id}:\n{comment}"
    )
