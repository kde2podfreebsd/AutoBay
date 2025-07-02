from bot import bot

@bot.callback_query_handler(func=lambda call: call.data == "ignore")
async def ignore(call):
    await bot.answer_callback_query(call.id)