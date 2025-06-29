# main.py
import asyncio
import db
from bot import bot

db.init_db()

import handlers.menu
import handlers.parts
import handlers.auto
import handlers.admin

if __name__ == '__main__':
    asyncio.run(bot.infinity_polling())
