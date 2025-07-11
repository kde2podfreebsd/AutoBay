from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import query_answers

@bot.callback_query_handler(func=lambda call: call.data == query_answers.FAQ)
async def faq(call):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🔙 Назад в меню", callback_data=query_answers.MENU))

    text = (
        "❓ <b>F.A.Q</b>\n\n"
        "🤖 <b>Этот бот поможет вам с:</b>\n\n"
        "• 🚘 Подбором автомобилей под ключ\n"
        "• 🛠️ Поиском редких автозапчастей на заказ\n"
        "• 🔧 Деталями для планового ТО\n\n"

        "------------------------------\n\n"

        "🚘 <b>Подбор автомобиля</b>\n"
        "1️⃣ Укажите модель, год выпуска, привод и тип топлива\n"
        "2️⃣ Оплатите услугу подбора — <b>88 000 ₽</b>\n"
        "3️⃣ С вами свяжется менеджер для индивидуальной консультации\n\n"
        "💳 Оплата доступна двумя способами:\n"
        "• <b>YooMoney (без НДС на кошелек)</b> — рекомендовано, быстрый приём\n"
        "• <b>YooKassa (с НДС 20%)</b> — обработка до 3 рабочих дней\n\n"

        "------------------------------\n\n"

        "🛠️ <b>Детали для ТО</b>\n"
        "1️⃣ Укажите авто, VIN, год, нужную деталь\n"
        "2️⃣ Прикрепите ссылку на деталь из онлайн-магазина (e.g. Ebay) и/или фото (при необходимости)\n"
        "3️⃣ Менеджер предложит варианты\n"
        "4️⃣ После согласования заявки через телеграм-бота вы оплачиваете счёт через платежную систему YooMoney\n\n"

        "------------------------------\n\n"

        "📦 <b>Детали на заказ</b>\n"
        "1️⃣ Заполните данные автомобиля и нужной детали\n"
        "2️⃣ Оплатите услугу подбора — <b>8800 ₽</b> через платежную систему YooMoney\n"
        "3️⃣ Менеджер подготовит предложения\n"
        "4️⃣ После согласования вы получаете счёт с точной стоимостью детали\n"
        "5️⃣ Оплатите счёт прямо в Telegram-боте через платежную систему YooMoney\n"
        "6️⃣ С вами свяжется менеджер и завершит заказ\n\n"

        "------------------------------\n\n"

        "⚠️ Проверьте, что у Вас открыты личные сообщения, что бы наш менеджер смог Вам написать\n\n"

        "📎 Вы можете прикреплять:\n"
        "• Ссылки на деталь из онлайн-магазина\n"
        "• Несколько фото из чата\n"
        "• Комментарии к заявке\n\n"
        "• Оплчивать услуги напрямую в боте через карту, СБП или проводить платеж с НДС\n\n"

        "🔒 Все ваши заявки видит только администратор. После оплаты вы получите обратную связь.\n"
        "📬 Все действия — через этот бот. Уведомления приходят автоматически.\n\n"

        "Спасибо, что выбираете нас! 🙏\n\n"

        '<b>ООО "ФОРСАЖ"\nИНН:7728282160</b>'
    )

    await bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
    await bot.answer_callback_query(call.id)
