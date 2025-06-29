# handlers/admin.py

from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import db, config, json
from yoomoney_payment_widget import ym

_admin = {}

def paginate(items, page):
    size = config.PAGE_SIZE
    start = (page - 1) * size
    end = start + size
    return items[start:end], page > 1, end < len(items)

@bot.message_handler(commands=['admin'])
async def admin_menu(msg):
    if msg.from_user.id not in config.ADMINS:
        return
    # подсчёт заявок по статусам
    count_new = len(db.get_orders_by_status('new'))
    count_paid = len(db.get_orders_by_status('paid'))
    count_work = len(db.get_orders_by_status('in_work'))
    count_closed = len(db.get_orders_by_status('closed'))
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'🆕 Новые заявки ({count_new})', callback_data='adm_new_1'),
        InlineKeyboardButton(f'💰 Оплаченные услуги ({count_paid})', callback_data='adm_paid_1'),
        InlineKeyboardButton(f'⚙️ В работе ({count_work})', callback_data='adm_work_1'),
        InlineKeyboardButton(f'✅ Закрытые ({count_closed})', callback_data='adm_closed_1'),
        InlineKeyboardButton('🚪 Выйти', callback_data='admin_exit')
    )
    await bot.send_message(msg.chat.id, 'Админ-панель:', reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data == 'admin_exit')
async def admin_exit(call):
    await bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(lambda c: c.data == 'admin_start')
async def admin_start(call):
    if call.from_user.id not in config.ADMINS:
        return
    # обновляем меню с актуальными числами
    count_new = len(db.get_orders_by_status('new'))
    count_paid = len(db.get_orders_by_status('paid'))
    count_work = len(db.get_orders_by_status('in_work'))
    count_closed = len(db.get_orders_by_status('closed'))
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f'🆕 Новые заявки ({count_new})', callback_data='adm_new_1'),
        InlineKeyboardButton(f'💰 Оплаченные услуги ({count_paid})', callback_data='adm_paid_1'),
        InlineKeyboardButton(f'⚙️ В работе ({count_work})', callback_data='adm_work_1'),
        InlineKeyboardButton(f'✅ Закрытые ({count_closed})', callback_data='adm_closed_1'),
        InlineKeyboardButton('🚪 Выйти', callback_data='admin_exit')
    )
    await bot.edit_message_text('Админ-панель:', call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data.startswith(('adm_new_','adm_paid_','adm_work_','adm_closed_')))
async def admin_list(call):
    if call.from_user.id not in config.ADMINS:
        return
    _, status_key, page_str = call.data.split('_', 2)
    page = int(page_str)
    status_map = {'new':'new', 'paid':'paid', 'work':'in_work', 'closed':'closed'}
    status = status_map[status_key]
    orders = db.get_orders_by_status(status)
    page_orders, has_prev, has_next = paginate(orders, page)

    chat_id, msg_id = call.message.chat.id, call.message.message_id
    if not page_orders:
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton('↩️ Назад', callback_data='admin_start')
        )
        await bot.edit_message_text('Нет заявок', chat_id, msg_id, reply_markup=markup)
        return

    markup = InlineKeyboardMarkup(row_width=1)
    for o in page_orders:
        created = o['created_at'].strftime('%Y-%m-%d %H:%M')
        icon = '🔧' if o['type']=='parts' else '🚗'
        label = f"{icon} #{o['id']} @{o['username']} — {created}"
        markup.add(InlineKeyboardButton(label, callback_data=f"adm_view_{status_key}_{o['id']}"))

    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton('⬅️', callback_data=f'adm_{status_key}_{page-1}'))
    nav.append(InlineKeyboardButton(str(page), callback_data='noop'))
    if has_next:
        nav.append(InlineKeyboardButton('➡️', callback_data=f'adm_{status_key}_{page+1}'))
    markup.row(*nav)
    markup.add(InlineKeyboardButton('↩️ Назад', callback_data='admin_start'))

    await bot.edit_message_text(f"Заявки ({status_key}) — страница {page}", chat_id, msg_id, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data.startswith('adm_view_'))
async def admin_view(call):
    if call.from_user.id not in config.ADMINS:
        return
    payload = call.data[len('adm_view_'):]
    status_key, oid_str = payload.split('_',1)
    oid = int(oid_str)

    o = db.get_order(oid)
    data = json.loads(o['data'])
    created = o['created_at'].strftime('%Y-%m-%d %H:%M')

    if o['type']=='parts':
        text = f"🔧 Заявка #{oid}\n👤 @{o['username']}\n📄 {data.get('details')}"
        # как была оплачена услуга
        if data.get('service_paid'):
            if data.get('service_uuid'):
                text += f"\n💰 Услуга оплачена через YooMoney (uuid: {data['service_uuid']})"
            elif data.get('service_payment_id'):
                text += f"\n💰 Услуга оплачена через ЮKасса (payment id: {data['service_payment_id']})"
        # ссылку на чек YooMoney (услуга)
        if data.get('service_payment_id') and data.get('service_uuid') is None:
            # при ЮKасса чек в Телеграме автоматически, можно ссылку не выводить
            pass
        # выставленный счет (стоимость детали)
        if data.get('invoice_sent'):
            text += f"\n💳 Счёт выставлен: {data.get('invoice_amount')} ₽"
        # как был выставлен счет: yoomoney или yookassa
        if data.get('invoice_uuid'):
            text += f"\n🔗 Ссылка на оплату детали (YooMoney): {data['invoice_uuid']}"
        if data.get('invoice_provider_id'):
            text += f"\n🔎 Invoice ЮKасса (message_id: {data['invoice_message_id']})"
        # как была оплачена деталь
        if data.get('part_paid'):
            if data.get('part_uuid'):
                text += f"\n✅ Деталь оплачена через YooMoney (uuid: {data['part_uuid']})"
            elif data.get('part_payment_id'):
                text += f"\n✅ Деталь оплачена через ЮKасса (payment id: {data['part_payment_id']})"
        text += f"\n⏱ {created}"
    else:
        fuel = ', '.join(k for k,v in data['fuel'].items() if v)
        text = (
            f"🚗 Заявка #{oid}\n👤 @{o['username']}\n"
            f"🚘 {data['model']}\n📅 {data['year']}\n⛽ {fuel}\n🔧 {data['drive']}\n⏱ {created}"
        )

    markup = InlineKeyboardMarkup(row_width=1)
    if status_key=='new':
        markup.add(InlineKeyboardButton('Взять в работу', callback_data=f'adm_take_{oid}'))
    elif status_key=='paid':
        markup.add(InlineKeyboardButton('Выставить счёт', callback_data=f'adm_invoice_{oid}'))
    elif status_key=='work':
        if o['type']=='parts' and (not o['reply_text'] or data.get('comments')):
            markup.add(InlineKeyboardButton('Добавить ответ', callback_data=f'adm_add_{oid}'))
        if o['type']=='auto':
            markup.add(InlineKeyboardButton('Закрыть заявку', callback_data=f'adm_close_{oid}'))

    if o['type']=='parts':
        if data.get('service_uuid'):
            markup.add(InlineKeyboardButton('☑️ Чек YooMoney (услуга)', 
                url=f"https://yoomoney.ru/details-print?payment-id={data['service_payment_id']}"))
        if data.get('invoice_uuid'):
            markup.add(InlineKeyboardButton('☑️ Ссылка YooMoney (деталь)', 
                url=data['invoice_uuid']))
        if data.get('invoice_message_id'):
            markup.add(InlineKeyboardButton('🔎 Чек ЮKасса (деталь)', 
                callback_data=f'yooka_receipt_part_{oid}'))
        if o['reply_text']:
            markup.add(InlineKeyboardButton('Просмотреть ответ', callback_data=f'adm_show_reply_{oid}'))

    markup.add(InlineKeyboardButton('↩️ Назад', callback_data='admin_start'))

    await bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data.startswith('yooka_receipt_'))
async def admin_show_yooka_receipt(call):
    _, kind, oid_str = call.data.split('_', 2)
    oid = int(oid_str)
    data = json.loads(db.get_order(oid)['data'])
    if kind == 'service':
        chat_id = data.get('service_invoice_chat_id')
        msg_id = data.get('service_invoice_message_id')
    else:
        chat_id = data.get('part_invoice_chat_id')
        msg_id = data.get('part_invoice_message_id')
    if chat_id and msg_id:
        await bot.forward_message(call.message.chat.id, chat_id, msg_id)
    else:
        await bot.answer_callback_query(call.id, 'Чек не найден.')

@bot.callback_query_handler(lambda c: c.data.startswith('adm_take_'))
async def admin_take(call):
    oid = int(call.data.rsplit('_',1)[1])
    db.assign_order(oid, call.from_user.id)
    await bot.answer_callback_query(call.id, f'Взял в работу #{oid}')
    call.data = 'adm_work_1'
    await admin_list(call)

@bot.callback_query_handler(lambda c: c.data.startswith('adm_close_'))
async def admin_close(call):
    oid = int(call.data.rsplit('_',1)[1])
    db.update_order_status(oid, 'closed')
    await bot.answer_callback_query(call.id, f'Закрыл заявку #{oid}')
    call.data = 'adm_work_1'
    await admin_list(call)

@bot.callback_query_handler(lambda c: c.data.startswith('adm_invoice_'))
async def admin_invoice(call):
    if call.from_user.id not in config.ADMINS:
        return
    oid = int(call.data.rsplit('_', 1)[1])
    _admin[call.from_user.id] = {'order_id': oid, 'step': 'invoice_amount'}
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    sent = await bot.send_message(call.message.chat.id, 'Введите сумму для счёта (в рублях):')
    _admin[call.from_user.id]['msg_id'] = sent.message_id

@bot.message_handler(func=lambda m: m.from_user.id in _admin and _admin[m.from_user.id]['step']=='invoice_amount')
async def admin_collect_invoice_amount(msg):
    st = _admin[msg.from_user.id]
    text = msg.text.strip()
    if not text.isdigit():
        await bot.send_message(msg.chat.id, 'Введите корректное число.')
        return
    st.update({'amount': int(text), 'step': 'invoice_comment'})
    await bot.delete_message(msg.chat.id, msg.message_id)
    reply = f"Счёт на сумму {st['amount']} ₽"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('✅ Отправить счёт', callback_data='adm_send_invoice'),
        InlineKeyboardButton('❌ Отмена', callback_data='adm_invoice_cancel')
    )
    sent = await bot.send_message(msg.chat.id, reply, reply_markup=markup)
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data=='adm_invoice_comment')
async def admin_invoice_comment(call):
    st = _admin[call.from_user.id]
    st['step'] = 'invoice_collect_comment'
    await bot.delete_message(call.message.chat.id, st['msg_id'])
    sent = await bot.send_message(call.message.chat.id, 'Введите комментарий для клиента:')
    st['msg_id'] = sent.message_id

@bot.message_handler(func=lambda m: m.from_user.id in _admin and _admin[m.from_user.id]['step']=='invoice_collect_comment')
async def admin_save_invoice_comment(msg):
    st = _admin[msg.from_user.id]
    st['comment'] = msg.text
    st['step'] = 'ready_to_send_invoice'
    await bot.delete_message(msg.chat.id, msg.message_id)
    reply = f"Счёт #{st['order_id']} — {st['amount']} ₽\nКомментарий: {st['comment']}"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('✅ Отправить счёт', callback_data='adm_send_invoice'),
        InlineKeyboardButton('❌ Отмена', callback_data='adm_invoice_cancel')
    )
    sent = await bot.send_message(msg.chat.id, reply, reply_markup=markup)
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data=='adm_invoice_cancel')
async def admin_invoice_cancel(call):
    _admin.pop(call.from_user.id, None)
    await bot.answer_callback_query(call.id, 'Отмена')
    await admin_start(call)

@bot.callback_query_handler(lambda c: c.data=='adm_send_invoice')
async def admin_send_invoice(call):
    st = _admin.pop(call.from_user.id)
    oid = st['order_id']
    amount = st['amount']
    comment = st.get('comment')
    o = db.get_order(oid)
    data = json.loads(o['data'])

    data['invoice_sent'] = True
    data['invoice_amount'] = amount
    ym_url, invoice_uuid = ym.create_quickpay(amount, 'AutoBay')
    data['invoice_uuid'] = ym_url
    db.update_order_data_and_status(oid, data, 'paid')

    client_id = o['user_id']
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('Оплатить через YooMoney', callback_data=f'parts_pay_part_ym_{oid}'),
        InlineKeyboardButton('Оплатить через ЮKасса', callback_data=f'parts_pay_part_uk_{oid}')
    )
    await bot.send_message(
        client_id,
        f"Счёт на сумму {amount} ₽" + (f"\nКомментарий: {comment}" if comment else ""),
        reply_markup=markup
    )

    await bot.answer_callback_query(call.id, 'Счёт отправлен клиенту')
    await bot.send_message(call.message.chat.id, f"Счёт по заказу #{oid} отправлен.")

@bot.callback_query_handler(lambda c: c.data.startswith('adm_add_'))
async def admin_add(call):
    oid = int(call.data.rsplit('_',1)[1])
    _admin[call.from_user.id] = {'order_id': oid, 'text': '', 'media': [], 'step': 'text'}
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    sent = await bot.send_message(call.message.chat.id, 'Напишите текст ответа:')
    _admin[call.from_user.id]['prompt_id'] = sent.message_id

@bot.message_handler(func=lambda m: m.from_user.id in _admin and _admin[m.from_user.id]['step']=='text')
async def admin_collect_text(msg):
    st = _admin[msg.from_user.id]
    st['text'] = msg.text
    st['step'] = 'buttons'
    await bot.delete_message(msg.chat.id, st['prompt_id'])
    buttons = InlineKeyboardMarkup(row_width=1)
    buttons.add(
        InlineKeyboardButton('➕ Добавить фото', callback_data='adm_photo'),
        InlineKeyboardButton('✏️ Изменить текст', callback_data='adm_change_text'),
        InlineKeyboardButton('✅ Отправить', callback_data='adm_finish'),
        InlineKeyboardButton('❌ Отмена', callback_data='adm_cancel')
    )
    for i in range(len(st['media'])):
        buttons.add(InlineKeyboardButton(f'🔎 {i+1}', callback_data=f'adm_view_photo_{i}'))
    sent = await bot.send_message(msg.chat.id, f"Текст ответа:\n{st['text']}", reply_markup=buttons)
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data=='adm_photo')
async def admin_add_photo(call):
    st = _admin[call.from_user.id]
    if len(st['media']) >= 10:
        await bot.answer_callback_query(call.id, 'Максимум 10 фото')
        return
    st['step'] = 'photo'
    await bot.delete_message(call.message.chat.id, st['msg_id'])
    sent = await bot.send_message(call.message.chat.id, 'Пришлите фото:')
    st['prompt_id'] = sent.message_id

@bot.message_handler(content_types=['photo'])
async def admin_collect_photo(msg):
    if msg.from_user.id not in _admin:
        return
    st = _admin[msg.from_user.id]
    if st['step'] != 'photo':
        return
    st['media'].append(msg.photo[-1].file_id)
    await bot.delete_message(msg.chat.id, msg.message_id)
    await bot.delete_message(msg.chat.id, st['prompt_id'])
    st['step'] = 'buttons'
    buttons = InlineKeyboardMarkup(row_width=1)
    buttons.add(
        InlineKeyboardButton('➕ Добавить фото', callback_data='adm_photo'),
        InlineKeyboardButton('✏️ Изменить текст', callback_data='adm_change_text'),
        InlineKeyboardButton('✅ Отправить', callback_data='adm_finish'),
        InlineKeyboardButton('❌ Отмена', callback_data='adm_cancel')
    )
    for i in range(len(st['media'])):
        buttons.add(InlineKeyboardButton(f'🔎 {i+1}', callback_data=f'adm_view_photo_{i}'))
    sent = await bot.send_message(
        msg.chat.id,
        f"Текст ответа:\n{st['text']}\nФото ({len(st['media'])}/10)",
        reply_markup=buttons
    )
    st['msg_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data.startswith('adm_view_photo_'))
async def admin_view_photo(call):
    idx = int(call.data.rsplit('_',1)[1])
    st = _admin.get(call.from_user.id)
    if not st:
        return
    fid = st['media'][idx]
    await bot.send_photo(call.message.chat.id, fid)
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data=='adm_change_text')
async def admin_change_text(call):
    st = _admin[call.from_user.id]
    st['step'] = 'text'
    await bot.delete_message(call.message.chat.id, st['msg_id'])
    sent = await bot.send_message(call.message.chat.id, 'Напишите новый текст:')
    st['prompt_id'] = sent.message_id

@bot.callback_query_handler(lambda c: c.data=='adm_cancel')
async def admin_cancel(call):
    _admin.pop(call.from_user.id, None)
    call.data = 'adm_work_1'
    await admin_list(call)

@bot.callback_query_handler(lambda c: c.data=='adm_finish')
async def admin_finish(call):
    st = _admin.pop(call.from_user.id)
    oid = st['order_id']
    db.save_admin_reply(oid, st['text'], st['media'])
    user_id = db.get_order(oid)['user_id']

    if st['media']:
        media = []
        for i, fid in enumerate(st['media']):
            if i==0 and len(st['text'])<=1024:
                media.append(InputMediaPhoto(fid, caption=st['text']))
            else:
                media.append(InputMediaPhoto(fid))
        await bot.send_media_group(user_id, media)
        if len(st['text'])>1024:
            await bot.send_message(user_id, st['text'])
    else:
        await bot.send_message(user_id, st['text'])

    client_buttons = InlineKeyboardMarkup(row_width=1)
    client_buttons.add(
        InlineKeyboardButton('✅ Да', callback_data=f'parts_client_ok_{oid}'),
        InlineKeyboardButton('❌ Нет', callback_data=f'parts_client_not_{oid}')
    )
    await bot.send_message(user_id, 'Вас это устраивает?', reply_markup=client_buttons)

    call.data = 'adm_work_1'
    await admin_list(call)

@bot.callback_query_handler(lambda c: c.data.startswith('adm_show_reply_'))
async def admin_show_reply(call):
    oid = int(call.data.rsplit('_',1)[1])
    o = db.get_order(oid)
    data = json.loads(o['data'])
    text = o['reply_text'] or ''
    media = json.loads(o['reply_media']) if o['reply_media'] else []

    if media:
        ims = [InputMediaPhoto(fid, caption=text if i==0 else None) for i,fid in enumerate(media)]
        await bot.send_media_group(call.message.chat.id, ims)
    elif text:
        await bot.send_message(call.message.chat.id, text)

    back_status = 'work' if o['status']=='in_work' else o['status']
    back_data = f"adm_view_{back_status}_{oid}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('↩️ Назад', callback_data=back_data)
    )
    await bot.send_message(call.message.chat.id, 'Просмотр ответа:', reply_markup=markup)
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data == 'noop')
async def noop(call):
    await bot.answer_callback_query(call.id)
