from pyrogram import idle

from sticker import bot, logs, scheduler
from sticker.functions.verification_system import verification_system


async def main():
    await bot.start()
    me = await bot.get_me()
    if not scheduler.running:
        scheduler.start()
    await verification_system.start()
    logs.info(f"bot @{me.username} started.")
    await idle()
    await verification_system.stop()
    await bot.stop()


bot.run(main())
