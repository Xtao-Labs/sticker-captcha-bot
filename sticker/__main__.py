from pyrogram import idle

from sticker import bot, logs


async def main():
    await bot.start()
    me = await bot.get_me()
    logs.info(f"bot @{me.username} started.")
    await idle()
    await bot.stop()


bot.run(main())
