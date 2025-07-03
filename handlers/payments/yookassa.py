from bot import bot
import config
from db.repository import get_order, update_order_data, update_order_payment_status
from telebot.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
import query_answers

async def _create_yookassa_invoice(chat_id: int, order_id: int, amount_rub: int):
    payload = f"uk_{order_id}"
    prices = [LabeledPrice(label="Оплата услуги", amount=amount_rub * 100)]
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("◀️ Другой способ оплаты", callback_data=f"{query_answers.PAY_SELECT}:{order_id}"),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    msg = await bot.send_invoice(
        chat_id=chat_id,
        title="💳 Оплата услуги подбора авто",
        description="Пожалуйста, оплатите услугу подбора авто",
        invoice_payload=payload,
        provider_token=config.YOOKASSA_PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter=f"orderuk{order_id}"
    )
    o = get_order(order_id)
    data = o.data
    data['uk_invoice_chat_id'] = msg.chat.id
    data['uk_invoice_message_id'] = msg.message_id
    update_order_data(order_id, data)
    return msg

@bot.callback_query_handler(func=lambda c: c.data.startswith(query_answers.PAY_YOOKASSA))
async def pay_yookassa(c):
    _, order_id_str = c.data.split(":", 1)
    order_id = int(order_id_str)
    o = get_order(order_id)
    price = int(o.data.get("service_price", 0))
    if price <= 0:
        await bot.answer_callback_query(c.id, text="⚠️ Невозможно сформировать счёт: цена не задана.", show_alert=True)
        return

    try:
        await _create_yookassa_invoice(c.message.chat.id, order_id, price)
    except Exception:
        await bot.answer_callback_query(c.id, text="⚠️ Ошибка формирования счёта. Проверьте сумму.", show_alert=True)
        return

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("◀️ Другой способ оплаты", callback_data=f"{query_answers.PAY_SELECT}:{order_id}"),
        InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU)
    )
    msg = await bot.send_message(
        c.message.chat.id,
        f"Для заявки #{order_id} вы можете выбрать другой способ или вернуться в меню:",
        reply_markup=markup
    )
    data = o.data
    data['uk_invoice_message_id_pay_select'] = msg.message_id
    update_order_data(order_id, data)
    await bot.answer_callback_query(c.id)

@bot.pre_checkout_query_handler(func=lambda q: True)
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
async def handle_successful_payment(msg):
    payload = msg.successful_payment.invoice_payload
    provider_id = msg.successful_payment.provider_payment_charge_id

    if payload.startswith('uk_'):
        order_id = int(payload.split('_', 1)[1])
        o = get_order(order_id)
        data = o.data

        if o.type == "details_order":
            data['service_paid'] = True
            update_order_data(order_id, data)
        else:
            data['service_paid'] = True
            update_order_data(order_id, data)
            update_order_payment_status(order_id, 'paid')

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("🏠 В меню", callback_data=query_answers.MENU))

        await bot.send_message(
            msg.chat.id,
            f"✅ Оплата заявки #{order_id} подтверждена.",
            reply_markup=markup
        )
        await bot.send_message(
            config.ADMIN_CHAT_ID,
            f"Оплачена заявка #{order_id}, payment_id: {provider_id}"
        )
        return
