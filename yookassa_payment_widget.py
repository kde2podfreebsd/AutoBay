# from bot import bot
# import config, db, json
# from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

# async def send_yookassa_invoice(chat_id, title, description, order_id, amount, prefix='uk'):
#     payload = f"{prefix}_{order_id}"
#     prices = [LabeledPrice(label=title, amount=amount * 100)]
#     await bot.send_invoice(
#         chat_id=chat_id,
#         title=title,
#         description=description,
#         invoice_payload=payload,
#         provider_token=config.YOOKASSA_PROVIDER_TOKEN,
#         currency='RUB',
#         prices=prices,
#         start_parameter=f"order{prefix}{order_id}"
#     )

# @bot.pre_checkout_query_handler(lambda q: True)
# async def process_pre_checkout(query):
#     await bot.answer_pre_checkout_query(query.id, ok=True)

# @bot.message_handler(content_types=['successful_payment'])
# async def handle_successful_payment(msg):
#     payload = msg.successful_payment.invoice_payload
#     provider_id = msg.successful_payment.provider_payment_charge_id

#     # ===== первая оплата услуги parts или авто (prefix uk_) =====
#     if payload.startswith('uk_'):
#         oid = int(payload.split('_',1)[1])
#         o = db.get_order(oid)

#         if o['type'] == 'auto':
#             db.update_order_status(oid, 'new')
#             await bot.send_message(
#                 msg.chat.id,
#                 "Ваша заявка оплачена, ближайшее время с вами в ЛС телеграмма свяжется менеджер. Проверьте, что у вас открыты личные сообщения",
#             )
#             await bot.send_message(
#                 config.ADMIN_CHAT_ID,
#                 f"Заявка №{oid} (auto) оплачена через ЮKассу, payment id: {provider_id}"
#             )
#         else:
#             # parts — оплата услуги
#             data = json.loads(o['data'])
#             data['service_paid'] = True
#             data['service_payment_id'] = provider_id
#             db.update_order_data_and_status(oid, data, 'paid')
#             await bot.send_message(
#                 msg.chat.id,
#                 "✅ Услуга по подбору запчасти оплачена. С вами свяжется менеджер.",
#             )
#             await bot.send_message(
#                 config.ADMIN_CHAT_ID,
#                 f"Оплачена услуга по заказу №{oid} (parts) через ЮKассу, payment id: {provider_id}"
#             )
#         return

#     # ===== вторая оплата стоимости детали (prefix uk2_) =====
#     if payload.startswith('uk2_'):
#         oid = int(payload.split('_',1)[1])
#         o = db.get_order(oid)
#         if o['type'] == 'parts':
#             data = json.loads(o['data'])
#             data['part_paid'] = True
#             data['part_payment_id'] = provider_id
#             db.update_order_data_and_status(oid, data, 'closed')
#             await bot.send_message(
#                 msg.chat.id,
#                 "Ваша заявка оплачена, ближайшее время с вами в ЛС телеграмма свяжется менеджер. Проверьте, что у вас открыты личные сообщения",
#             )
#             await bot.send_message(
#                 config.ADMIN_CHAT_ID,
#                 f"Деталь оплачена по заявке #{oid} через ЮKассу, payment id: {provider_id}"
#             )
#         return


from bot import bot
import config, db, json
from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

async def send_yookassa_invoice(chat_id, title, description, order_id, amount, prefix='uk'):
    payload = f"{prefix}_{order_id}"
    prices = [LabeledPrice(label=title, amount=amount * 100)]
    msg = await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        invoice_payload=payload,
        provider_token=config.YOOKASSA_PROVIDER_TOKEN,
        currency='RUB',
        prices=prices,
        start_parameter=f"order{prefix}{order_id}"
    )
    # сохраняем chat_id и message_id инвойса
    o = db.get_order(order_id)
    data = json.loads(o['data'])
    if prefix == 'uk':  # услуга
        data['service_invoice_chat_id'] = msg.chat.id
        data['service_invoice_message_id'] = msg.message_id
    else:  # детали
        data['part_invoice_chat_id'] = msg.chat.id
        data['part_invoice_message_id'] = msg.message_id
    db.update_order_data_and_status(order_id, data, o['status'])

@bot.pre_checkout_query_handler(lambda q: True)
async def process_pre_checkout(query):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
async def handle_successful_payment(msg):
    payload = msg.successful_payment.invoice_payload
    provider_id = msg.successful_payment.provider_payment_charge_id

    # первая оплата услуги (uk_)
    if payload.startswith('uk_'):
        oid = int(payload.split('_',1)[1])
        o = db.get_order(oid)
        data = json.loads(o['data'])
        data['service_paid'] = True
        data['service_payment_id'] = provider_id
        data['service_invoice_chat_id'] = msg.chat.id
        data['service_invoice_message_id'] = msg.message_id
        db.update_order_data_and_status(oid, data, 'paid')
        await bot.send_message(
            msg.chat.id,
            "✅ Услуга по подбору запчасти оплачена. С вами свяжется менеджер."
        )
        await bot.send_message(
            config.ADMIN_CHAT_ID,
            f"Оплачена услуга через ЮKасса, payment id: {provider_id}"
        )
        return

    # вторая оплата стоимости детали (uk2_)
    if payload.startswith('uk2_'):
        oid = int(payload.split('_',1)[1])
        o = db.get_order(oid)
        data = json.loads(o['data'])
        data['part_paid'] = True
        data['part_payment_id'] = provider_id
        data['part_invoice_chat_id'] = msg.chat.id
        data['part_invoice_message_id'] = msg.message_id
        db.update_order_data_and_status(oid, data, 'closed')
        await bot.send_message(
            msg.chat.id,
            "Ваша заявка оплачена, ближайшее время с вами свяжется менеджер."
        )
        await bot.send_message(
            config.ADMIN_CHAT_ID,
            f"Деталь оплачена по заявке через ЮKасса, payment id: {provider_id}"
        )
        return