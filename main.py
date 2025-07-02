import asyncio
from bot import bot
from db.repository import init_db

import handlers.base
import handlers.client_menu
import handlers.faq
import handlers.orders
import handlers.admin.menu
import handlers.admin.orders
import handlers.admin.order_detail
import handlers.admin.order_actions
import handlers.admin.service_prices
import handlers.client_auto
import handlers.payments.yoomoney
import handlers.payments.yookassa
import handlers.client_details_to
import handlers.client_response
import handlers.admin.order_detail_responses

init_db()

if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())
