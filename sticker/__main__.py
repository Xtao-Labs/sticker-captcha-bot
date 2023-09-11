from pyrogram import idle

from sticker import bot, logs


async def main():
    await bot.start()
    logs.info("bot started.")
    await idle()
    await bot.stop()


bot.run(main())
