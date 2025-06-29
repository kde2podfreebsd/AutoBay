from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import db, config, json
from yookassa_payment_widget import send_yookassa_invoice
from yoomoney_payment_widget import ym

_state = {}
_feedback = {}

@bot.callback_query_handler(lambda c: c.data == 'menu_parts')
async def parts_start(call):
    _state[call.from_user.id] = {
        'step':'await_details',
        'chat_id':call.message.chat.id,
        'msg_id':call.message.message_id
    }
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    await bot.edit_message_text(
        "Введите наименование запчасти и/или её параметры одним сообщением:",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: _state.get(m.from_user.id,{}).get('step')=='await_details')
async def parts_got_details(msg):
    user_id = msg.from_user.id
    st = _state[user_id]
    await bot.delete_message(st['chat_id'], st['msg_id'])
    await bot.delete_message(msg.chat.id, msg.message_id)
    details = msg.text
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('✅ Подтвердить', callback_data='parts_preview_confirm'),
        InlineKeyboardButton('✏️ Изменить', callback_data='parts_preview_change'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        f"Превью заявки:\n{details}",
        reply_markup=markup
    )
    _state[user_id] = {
        'step':'preview',
        'details':details,
        'chat_id':st['chat_id'],
        'msg_id':sent.message_id
    }

@bot.callback_query_handler(lambda c: c.data == 'parts_preview_change')
async def parts_preview_change(call):
    user_id = call.from_user.id
    st = _state.get(user_id)
    if not st or st.get('step')!='preview':
        return
    await bot.delete_message(st['chat_id'], st['msg_id'])
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        "Введите наименование запчасти и/или её параметры одним сообщением:",
        reply_markup=markup
    )
    _state[user_id] = {
        'step':'await_details',
        'chat_id':st['chat_id'],
        'msg_id':sent.message_id
    }
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data == 'parts_preview_confirm')
async def parts_preview_confirm(call):
    user_id = call.from_user.id
    st = _state[user_id]
    oid = db.create_order(user_id, call.from_user.username, 'parts', {'details':st['details']})
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    await bot.edit_message_text(
        "Ваша заявка отправлена. Ожидайте ответа менеджера.",
        st['chat_id'], st['msg_id'], reply_markup=markup
    )
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Новая заявка #{oid} от @{call.from_user.username}:\n🔧 {st['details']}"
    )
    del _state[user_id]

@bot.callback_query_handler(lambda c: c.data.startswith('parts_client_ok_'))
async def parts_client_ok(call):
    oid = int(call.data.split('_')[-1])
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Оплатить через YooMoney', callback_data=f'parts_pay_ym_{oid}'),
        InlineKeyboardButton('Оплатить через ЮKасса', callback_data=f'parts_pay_uk_{oid}')
    )
    await bot.edit_message_text(
        "Выберите способ оплаты услуги подбора (8 800 ₽):",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data.startswith('parts_pay_ym_'))
async def parts_pay_ym(call):
    oid = int(call.data.rsplit('_',1)[1])
    url, uuid_tx = ym.create_quickpay(8800, 'AutoBay')
    o = db.get_order(oid)
    data = json.loads(o['data'])
    data['service_uuid'] = uuid_tx
    db.update_order_data_and_status(oid, data, 'await_service_payment')
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Перейти к оплате', url=url),
        InlineKeyboardButton('Я оплатил', callback_data=f'parts_ym_check_{oid}')
    )
    await bot.edit_message_text(
        "Для оплаты услуги перейдите по ссылке и нажмите «Я оплатил», когда завершите оплату.",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data.startswith('parts_pay_uk_'))
async def parts_pay_uk(call):
    oid = int(call.data.rsplit('_',1)[1])
    await send_yookassa_invoice(
        chat_id=call.message.chat.id,
        title=f"Оплата услуги по подбору #{oid}",
        description=f"Оплата услуги по подбору запчасти #{oid} — 8800 ₽",
        order_id=oid,
        amount=8800
    )
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data.startswith('parts_client_not_'))
async def parts_client_not(call):
    oid = int(call.data.rsplit('_',1)[1])
    _feedback[call.from_user.id] = {
        'order_id': oid,
        'chat_id': call.message.chat.id,
        'msg_id': call.message.message_id,
        'step': 'collect_comment'
    }
    await bot.edit_message_text(
        'Пожалуйста, напишите комментарии с вашими пожеланиями:',
        call.message.chat.id, call.message.message_id
    )
    await bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: _feedback.get(m.from_user.id, {}).get('step')=='collect_comment')
async def parts_collect_comment(msg):
    fb = _feedback.pop(msg.from_user.id)
    comment = msg.text
    o = db.get_order(fb['order_id'])
    data = json.loads(o['data'])
    data.setdefault('comments', []).append(comment)
    db.update_order_data_and_status(fb['order_id'], data, 'in_work')
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Клиент не удовлетворен заявкой #{fb['order_id']}, комментарий:\n{comment}"
    )
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    await bot.send_message(
        msg.chat.id,
        'Спасибо! Ваш комментарий отправлен менеджеру и заявка открыта заново.',
        reply_markup=markup
    )

@bot.callback_query_handler(lambda c: c.data.startswith('parts_pay_part_uk_'))
async def parts_pay_part_uk(call):
    oid = int(call.data.rsplit('_',1)[1])
    data = json.loads(db.get_order(oid)['data'])
    amount = data.get('invoice_amount', 0)
    await send_yookassa_invoice(
        chat_id=call.message.chat.id,
        title=f"Оплата детали #{oid}",
        description=f"Оплата детали по заказу #{oid} — {amount} ₽",
        order_id=oid,
        amount=amount
    )
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data.startswith('parts_pay_part_ym_'))
async def parts_pay_part_ym(call):
    oid = int(call.data.rsplit('_',1)[1])
    data = json.loads(db.get_order(oid)['data'])
    amount = data.get('invoice_amount', 0)
    url, uuid_tx = ym.create_quickpay(amount, 'AutoBay')
    data['part_uuid'] = uuid_tx
    db.update_order_data_and_status(oid, data, 'await_part_payment')
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Перейти к оплате', url=url),
        InlineKeyboardButton('Я оплатил', callback_data=f'parts_ym_part_check_{oid}')
    )
    await bot.edit_message_text(
        "Для оплаты стоимости детали перейдите по ссылке и нажмите «Я оплатил», когда завершите оплату.",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)