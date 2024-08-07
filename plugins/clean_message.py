from cashews import cache
from pyrogram import filters

from sticker import bot
from sticker.single_utils import Message


@bot.on_message(filters=filters.group & ~filters.service, group=1)
async def clean_message(_, message: "Message"):
    if not message.from_user:
        return
    cid = message.chat.id
    uid = message.from_user.id
    key = f"wait:{cid}:{uid}"
    result = await cache.get(key)
    if result:
        await message.delay_delete(1)
