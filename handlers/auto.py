# handlers/auto.py
from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import db, config, json
from yookassa_payment_widget import send_yookassa_invoice
from yoomoney_payment_widget import ym

_auto = {}

@bot.callback_query_handler(lambda c: c.data == 'menu_auto')
async def auto_start(call):
    _auto[call.from_user.id] = {
        'step': 'model',
        'data': {},
        'chat_id': call.message.chat.id,
        'msg_id': call.message.message_id
    }
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton('↩️ Меню', callback_data='menu_start'))
    await bot.edit_message_text(
        "Укажите модель авто:",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(lambda c: c.data == 'auto_back_model')
async def auto_back_model(call):
    st = _auto[call.from_user.id]
    st['step'] = 'model'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    sent = await bot.send_message(
        st['chat_id'],
        "Укажите модель авто:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
        )
    )
    st['msg_id'] = sent.message_id

@bot.message_handler(func=lambda m: _auto.get(m.from_user.id, {}).get('step') == 'model')
async def auto_model(msg):
    st = _auto[msg.from_user.id]
    st['data']['model'] = msg.text
    st['step'] = 'year'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    await bot.delete_message(msg.chat.id, msg.message_id)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('↩️ Назад', callback_data='auto_back_model'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        f"Укажите минимально допустимый год выпуска:\nМодель: {st['data']['model']}",
        reply_markup=markup
    )
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data == 'auto_back_year')
async def auto_back_year(call):
    st = _auto[call.from_user.id]
    st['step'] = 'year'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('↩️ Назад', callback_data='auto_back_model'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        f"Укажите минимально допустимый год выпуска:\nМодель: {st['data']['model']}",
        reply_markup=markup
    )
    st['msg_id'] = sent.message_id

@bot.message_handler(func=lambda m: _auto.get(m.from_user.id, {}).get('step') == 'year')
async def auto_year(msg):
    st = _auto[msg.from_user.id]
    st['data']['year'] = msg.text
    st['data']['fuel'] = {k: False for k in ('бензин', 'дизель', 'электро', 'гибрид')}
    st['step'] = 'fuel'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    await bot.delete_message(msg.chat.id, msg.message_id)
    markup = InlineKeyboardMarkup(row_width=1)
    for t, sel in st['data']['fuel'].items():
        icon = '✅' if sel else '❌'
        markup.add(InlineKeyboardButton(f"{icon} {t}", callback_data=f"fuel_toggle_{t}"))
    markup.add(
        InlineKeyboardButton('✅ Подтвердить', callback_data='fuel_confirm'),
        InlineKeyboardButton('↩️ Назад', callback_data='auto_back_year'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        f"Выберите типы топлива:\nМодель: {st['data']['model']}\nГод: {st['data']['year']}",
        reply_markup=markup
    )
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data.startswith('fuel_toggle_'))
async def fuel_toggle(call):
    st = _auto[call.from_user.id]
    t = call.data.split('_', 2)[2]
    st['data']['fuel'][t] = not st['data']['fuel'][t]
    markup = InlineKeyboardMarkup(row_width=1)
    for k, v in st['data']['fuel'].items():
        icon = '✅' if v else '❌'
        markup.add(InlineKeyboardButton(f"{icon} {k}", callback_data=f"fuel_toggle_{k}"))
    markup.add(
        InlineKeyboardButton('✅ Подтвердить', callback_data='fuel_confirm'),
        InlineKeyboardButton('↩️ Назад', callback_data='auto_back_year'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    await bot.edit_message_text(
        f"Выберите типы топлива:\nМодель: {st['data']['model']}\nГод: {st['data']['year']}",
        st['chat_id'], st['msg_id'], reply_markup=markup
    )

@bot.callback_query_handler(lambda c: c.data == 'fuel_confirm')
async def fuel_confirm(call):
    st = _auto[call.from_user.id]
    chosen = [k for k, v in st['data']['fuel'].items() if v]
    if not chosen:
        await bot.answer_callback_query(call.id, 'Выберите хотя бы один тип топлива.')
        return
    st['step'] = 'drive'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('полный', callback_data='drive_полный'),
        InlineKeyboardButton('задний', callback_data='drive_задний'),
        InlineKeyboardButton('передний', callback_data='drive_передний'),
        InlineKeyboardButton('↩️ Назад', callback_data='fuel_confirm_back'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    fuel_list = ", ".join(chosen)
    sent = await bot.send_message(
        st['chat_id'],
        f"Укажите тип привода:\nМодель: {st['data']['model']}\nГод: {st['data']['year']}\nТопливо: {fuel_list}",
        reply_markup=markup
    )
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data == 'fuel_confirm_back')
async def fuel_confirm_back(call):
    st = _auto[call.from_user.id]
    st['step'] = 'fuel'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    markup = InlineKeyboardMarkup(row_width=1)
    for k, v in st['data']['fuel'].items():
        icon = '✅' if v else '❌'
        markup.add(InlineKeyboardButton(f"{icon} {k}", callback_data=f"fuel_toggle_{k}"))
    markup.add(
        InlineKeyboardButton('✅ Подтвердить', callback_data='fuel_confirm'),
        InlineKeyboardButton('↩️ Назад', callback_data='auto_back_year'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        f"Выберите типы топлива:\nМодель: {st['data']['model']}\nГод: {st['data']['year']}",
        reply_markup=markup
    )
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data.startswith('drive_'))
async def drive_chosen(call):
    st = _auto[call.from_user.id]
    drive = call.data.split('_', 1)[1]
    st['data']['drive'] = drive
    st['step'] = 'pay'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    oid = db.create_order(call.from_user.id, call.from_user.username, 'auto', st['data'])
    fuel_list = ", ".join([k for k, v in st['data']['fuel'].items() if v])
    text = (
        f"Ваша заявка:\n"
        f"Модель: {st['data']['model']}\n"
        f"Год: {st['data']['year']}\n"
        f"Топливо: {fuel_list}\n"
        f"Привод: {drive}"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Оплатить через YooMoney', callback_data=f'auto_pay_ym_{oid}'),
        InlineKeyboardButton('Оплатить через ЮKассу', callback_data=f'auto_pay_uk_{oid}')
    )
    markup.add(
        InlineKeyboardButton('↩️ Назад', callback_data='auto_back_drive'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(st['chat_id'], text, reply_markup=markup)
    st['msg_id'] = sent.message_id
    st['order_id'] = oid

@bot.callback_query_handler(lambda c: c.data == 'auto_back_drive')
async def auto_back_drive(call):
    st = _auto[call.from_user.id]
    st['step'] = 'drive'
    await bot.delete_message(st['chat_id'], st['msg_id'])
    fuel_list = ", ".join([k for k, v in st['data']['fuel'].items() if v])
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('полный', callback_data='drive_полный'),
        InlineKeyboardButton('задний', callback_data='drive_задний'),
        InlineKeyboardButton('передний', callback_data='drive_передний'),
        InlineKeyboardButton('↩️ Назад', callback_data='fuel_confirm'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    sent = await bot.send_message(
        st['chat_id'],
        f"Укажите тип привода:\nМодель: {st['data']['model']}\nГод: {st['data']['year']}\nТопливо: {fuel_list}",
        reply_markup=markup
    )
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data.startswith('auto_pay_ym_'))
async def auto_pay_ym(call):
    oid = int(call.data.rsplit('_', 1)[1])
    # создаём YooMoney quickpay
    url, uuid_tx = ym.create_quickpay(88000, 'AutoBay')
    o = db.get_order(oid)
    data = json.loads(o['data'])
    data['payment_uuid'] = uuid_tx
    db.update_order_data_and_status(oid, data, 'await_payment')
    # предлогаем оплатить и проверить
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Перейти к оплате', url=url),
        InlineKeyboardButton('Я оплатил', callback_data=f'auto_ym_check_{oid}')
    )
    markup.add(
        InlineKeyboardButton('↩️ Назад', callback_data='drive_полный' if data['drive']=='полный' else f'drive_{data["drive"]}'),
        InlineKeyboardButton('↩️ Меню', callback_data='menu_start')
    )
    await bot.edit_message_text(
        "Для оплаты услуги перейдите по ссылке и нажмите «Я оплатил», когда завершите оплату.",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data.startswith('auto_ym_check_'))
async def auto_ym_check(call):
    oid = int(call.data.rsplit('_', 1)[1])
    o = db.get_order(oid)
    data = json.loads(o['data'])
    uuid_tx = data.get('payment_uuid')
    if not uuid_tx:
        await bot.answer_callback_query(call.id, 'UUID платежа не найден.')
        return
    paid, op_id = ym.check_tx(uuid_tx)
    if not paid:
        await bot.answer_callback_query(call.id, 'Платёж не найден. Попробуйте позже.')
        return
    # сохраняем статус
    data['payment_id'] = op_id
    db.update_order_data_and_status(oid, data, 'new')
    receipt_url = f"https://yoomoney.ru/details-print?payment-id={op_id}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('☑️ Показать чек', url=receipt_url)
    )
    await bot.edit_message_text(
        "✅ Ваша заявка оплачена. С вами свяжется менеджер.",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Заявка №{oid} (auto) оплачена через YooMoney, payment id: {op_id}"
    )

@bot.callback_query_handler(lambda c: c.data.startswith('auto_pay_uk_'))
async def auto_pay_uk(call):
    oid = int(call.data.rsplit('_', 1)[1])
    # выставляем ЮKасса invoice
    await send_yookassa_invoice(
        chat_id=call.message.chat.id,
        title=f"Оплата заявки #{oid}",
        description=f"Оплата заявки #{oid} (Авто) — 88000 ₽",
        order_id=oid,
        amount=88000
    )
    await bot.answer_callback_query(call.id)
