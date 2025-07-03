from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers
from db.repository import update_order_payment_status, get_order, update_order_data
from services.yoomoney_service import YooMoney

ym = YooMoney()

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.PAY_YOOMONEY))
async def pay_yoomoney(c):
    _, order_id_str = c.data.split(":", 1)
    order_id = int(order_id_str)
    o = get_order(order_id)
    if o.type == "details_order":
        amount = int(o.data.get("service_price", 0) if not o.data.get("service_paid") else o.data.get("invoice_price", 0))
    else:
        amount = int(o.data.get("service_price", 0))
    if amount <= 0:
        await bot.answer_callback_query(c.id, "⚠️ Сумма не задана", show_alert=True)
        return
    url, uuid_tx = ym.create_quickpay(amount, target=f"AutoBay order {order_id}")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔗 Перейти к оплате", url=url),
        InlineKeyboardButton("✅ Я оплатил", callback_data=f"check_yoomoney:{order_id}:{uuid_tx}")
    )
    if o.type == "auto":
        markup.add(InlineKeyboardButton("◀️ Другой способ оплаты", callback_data=f"{query_answers.PAY_SELECT}:{order_id}"))
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))
    await bot.edit_message_text(f"💡 Оплата через YooMoney:\nСумма: {amount} ₽", chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=markup)
    await bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("check_yoomoney:"))
async def check_yoomoney(c):
    _, order_id_str, uuid_tx = c.data.split(":", 2)
    order_id = int(order_id_str)
    o = get_order(order_id)
    paid, _ = ym.check_tx(uuid_tx)
    if not paid:
        await bot.answer_callback_query(c.id, "❗ Платёж не найден или ещё не завершён", show_alert=True)
        return
    if o.type == "details_order":
        d = o.data
        if not d.get("service_paid"):
            d["service_paid"] = True
            update_order_data(order_id, d)
        else:
            update_order_payment_status(order_id, "paid")
    elif o.type == "auto":
        update_order_payment_status(order_id, "paid")
    else:
        update_order_payment_status(order_id, "paid")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))
    await bot.edit_message_text(f"✅ Платёж по заявке #{order_id} подтверждён.", chat_id=c.message.chat.id, message_id=c.message.message_id, reply_markup=markup)
    await bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.PAY_SELECT))
async def pay_select(c):
    _, order_id_str = c.data.split(":", 1)
    order_id = int(order_id_str)

    o = get_order(order_id)
    data = o.data
    chat_id = data.get('uk_invoice_chat_id')
    msg_id = data.get('uk_invoice_message_id')
    if chat_id and msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💸 Оплатить через YooMoney", callback_data=f"{query_answers.PAY_YOOMONEY}:{order_id}")
    )
    markup.add(
        InlineKeyboardButton("💳 Оплатить через YooKassa", callback_data=f"{query_answers.PAY_YOOKASSA}:{order_id}")
    )
    markup.add(
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    await bot.edit_message_text(
        f"📬 Ваша заявка #{order_id}. Выберите метод оплаты:",
        chat_id=c.message.chat.id,
        message_id=c.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(c.id)
