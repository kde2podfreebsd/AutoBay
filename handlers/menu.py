from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import db, json, config

def paginate(items, page):
    size = config.PAGE_SIZE
    start = (page - 1) * size
    end = start + size
    return items[start:end], page > 1, end < len(items)

start_text = (
    'Выберите пункт меню:\n\n'
    '🛠 Запчасти - Заказать подбор любой автодетали по описанию. Сначала подбор - потом оплата.\n'
    'Стоимость услуги - 8800 рублей + Цена детали\n\n'
    '🚗 Авто - услуга подбора авто по фильтрам.\n'
    'Стоимость услуги - 88000 рублей\n\n'
    '❓ FAQ - как пользоваться этим ботом'
)

faq_text = (
    "Этот бот помогает вам быстро и удобно заказать подбор автомобиля или автозапчастей:\n\n"
    "1. 🛠 Выберите «Запчасти» и опишите, что нужно найти. Сначала вы получите бесплатное превью, "
    "далее оплатите услугу (8800 ₽), затем получите предложение по конкретной детали.\n\n"
    "2. 🚗 Выберите «Авто» и укажите параметры (модель, год, топливо, привод), далее оплатите услугу "
    "(88000 ₽).\n\n"
    "3. После оплаты вам придёт уведомление, менеджер свяжется с вами в личных сообщениях для уточнений.\n\n"
    "4. Всё общение происходит через бота — никаких лишних сообщений в чате."
)

@bot.message_handler(commands=['start'])
async def start(msg):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('🛠 Запчасти', callback_data='menu_parts'),
        InlineKeyboardButton('🚗 Авто', callback_data='menu_auto'),
        InlineKeyboardButton('📦 Мои заказы', callback_data='menu_my_orders'),
        InlineKeyboardButton('❓ FAQ', callback_data='menu_faq')
    )
    await bot.send_message(msg.chat.id, start_text, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data == 'menu_faq')
async def menu_faq(call):
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️ Меню', callback_data='menu_start'))
    await bot.edit_message_text(faq_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(lambda c: c.data == 'menu_my_orders')
async def my_orders(call):
    page = 1
    orders = db.get_user_orders(call.from_user.id)
    page_orders, has_prev, has_next = paginate(orders, page)
    chat_id, msg_id = call.message.chat.id, call.message.message_id
    if not orders:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️ Меню', callback_data='menu_start'))
        await bot.edit_message_text('У вас нет заказов', chat_id, msg_id, reply_markup=markup)
        return
    lines = []
    for o in page_orders:
        data = json.loads(o['data'])
        if o['type'] == 'parts':
            type_str = '🛠 Запчасти'
            details = data['details']
        else:
            type_str = '🚗 Авто'
            fuel = ', '.join([k for k,v in data['fuel'].items() if v])
            details = (
                f"Модель: {data['model']}\n"
                f"Год: {data['year']}\n"
                f"Топливо: {fuel}\n"
                f"Привод: {data['drive']}"
            )
        status_map = {
            'new': 'Ждет обработки',
            'in_work': 'В работе',
            'closed': 'Закрыто',
            'paid': 'Оплачена, ждите менеджера'
        }
        status_str = status_map.get(o['status'], o['status'])
        lines.append(f"{type_str}\n{details}\nСтатус: {status_str}")
    text = '\n\n'.join(lines)
    markup = InlineKeyboardMarkup()
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton('⬅️', callback_data=f'my_orders_page_{page-1}'))
    nav.append(InlineKeyboardButton(str(page), callback_data='noop'))
    if has_next:
        nav.append(InlineKeyboardButton('➡️', callback_data=f'my_orders_page_{page+1}'))
    markup.row(*nav)
    markup.add(InlineKeyboardButton('↩️ Меню', callback_data='menu_start'))
    await bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data.startswith('my_orders_page_'))
async def my_orders_page(call):
    page = int(call.data.rsplit('_',1)[1])
    orders = db.get_user_orders(call.from_user.id)
    page_orders, has_prev, has_next = paginate(orders, page)
    chat_id, msg_id = call.message.chat.id, call.message.message_id
    lines = []
    for o in page_orders:
        data = json.loads(o['data'])
        if o['type'] == 'parts':
            type_str = '🛠 Запчасти'
            details = data['details']
        else:
            type_str = '🚗 Авто'
            fuel = ', '.join([k for k,v in data['fuel'].items() if v])
            details = (
                f"Модель: {data['model']}\n"
                f"Год: {data['year']}\n"
                f"Топливо: {fuel}\n"
                f"Привод: {data['drive']}"
            )
        status_map = {
            'new': 'Ждет обработки',
            'in_work': 'В работе',
            'closed': 'Закрыто',
            'paid': 'Оплачена, ждите менеджера'
        }
        status_str = status_map.get(o['status'], o['status'])
        lines.append(f"{type_str}\n{details}\nСтатус: {status_str}")
    text = '\n\n'.join(lines)
    markup = InlineKeyboardMarkup()
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton('⬅️', callback_data=f'my_orders_page_{page-1}'))
    nav.append(InlineKeyboardButton(str(page), callback_data='noop'))
    if has_next:
        nav.append(InlineKeyboardButton('➡️', callback_data=f'my_orders_page_{page+1}'))
    markup.row(*nav)
    markup.add(InlineKeyboardButton('↩️ Меню', callback_data='menu_start'))
    await bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data == 'menu_start')
async def back_to_start(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('🛠 Запчасти', callback_data='menu_parts'),
        InlineKeyboardButton('🚗 Авто', callback_data='menu_auto'),
        InlineKeyboardButton('📦 Мои заказы', callback_data='menu_my_orders'),
        InlineKeyboardButton('❓ FAQ', callback_data='menu_faq')
    )
    await bot.edit_message_text(start_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(lambda c: c.data == 'noop')
async def noop(call):
    await bot.answer_callback_query(call.id, '')