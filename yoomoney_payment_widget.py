from bot import bot
from yoomoney import Client, Quickpay
from config import YOOMONEY_PROVIDER_TOKEN, YOOMONEY_CLIENT_CARDID
import uuid, db, json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class YooMoney:
    def __init__(self):
        self.client = Client(YOOMONEY_PROVIDER_TOKEN)

    def create_quickpay(self, amount: int, target: str = "AutoBay"):
        """
        amount — сумма в рублях,
        target — строка-подсказка («AutoBay»)
        возвращает (url, uuid_label)
        """
        uuid_tx = str(uuid.uuid4())
        quickpay = Quickpay(
            receiver=str(YOOMONEY_CLIENT_CARDID),
            quickpay_form="shop",
            targets=target,
            paymentType="SB",
            sum=amount,
            label=uuid_tx
        )
        return quickpay.base_url, uuid_tx

    def check_tx(self, uuid_tx: str):
        """
        проверяет по label (uuid_tx) статус платежа;
        возвращает (True, operation_id) или (False, None)
        """
        history = self.client.operation_history(label=uuid_tx)
        for op in history.operations:
            if op.label == uuid_tx:
                if op.status == 'success':
                    return True, op.operation_id
                return False, None
        return False, None

ym = YooMoney()


@bot.callback_query_handler(lambda c: c.data.startswith('parts_ym_check_'))
async def check_service_payment(call):
    oid = int(call.data.rsplit('_', 1)[1])
    o = db.get_order(oid)
    data = json.loads(o['data'])
    uuid_tx = data.get('service_uuid')
    if not uuid_tx:
        await bot.answer_callback_query(call.id, 'Ошибка: UUID платежа не найден.')
        return

    paid, op_id = ym.check_tx(uuid_tx)
    if not paid:
        await bot.answer_callback_query(call.id, 'Платёж не найден. Повторите после оплаты.')
        return

    # помечаем оплату услуги
    data['service_paid'] = True
    data['service_payment_id'] = op_id
    db.update_order_data_and_status(oid, data, 'paid')

    # строим чек-кнопку
    receipt_url = f"https://yoomoney.ru/details-print?payment-id={op_id}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('☑️ Показать чек', url=receipt_url)
    )
    # редактируем сообщение
    await bot.edit_message_text(
        "✅ Услуга по подбору запчасти оплачена. С вами свяжется менеджер.",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )
    # уведомляем админа
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Оплачена услуга по заказу #{oid} через YooMoney, payment id: {op_id}"
    )


@bot.callback_query_handler(lambda c: c.data.startswith('parts_ym_part_check_'))
async def check_part_payment(call):
    oid = int(call.data.rsplit('_', 1)[1])
    o = db.get_order(oid)
    data = json.loads(o['data'])
    uuid_tx = data.get('part_uuid')
    if not uuid_tx:
        await bot.answer_callback_query(call.id, 'Ошибка: UUID платежа не найден.')
        return

    paid, op_id = ym.check_tx(uuid_tx)
    if not paid:
        await bot.answer_callback_query(call.id, 'Платёж не найден. Повторите после оплаты.')
        return

    # помечаем оплату детали
    data['part_paid'] = True
    data['part_payment_id'] = op_id
    db.update_order_data_and_status(oid, data, 'closed')

    # чек-кнопка клиенту
    receipt_url = f"https://yoomoney.ru/details-print?payment-id={op_id}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('☑️ Показать чек', url=receipt_url)
    )
    await bot.edit_message_text(
        "Ваша заявка оплачена, ближайшее время с вами в ЛС телеграмма свяжется менеджер. Проверьте, что у вас открыты личные сообщения.",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup
    )

    # уведомляем админа
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        f"Деталь оплачена по заказу #{oid} через YooMoney, payment id: {op_id}"
    )