from pyrogram import filters

from sticker import bot
from sticker.functions.service_message import ServiceMessage
from sticker.single_utils import Client, Message


@bot.on_message(filters.new_chat_members, group=2)
async def service_message_handle(_: Client, message: Message):
    cid = message.chat.id
    if message.new_chat_members:
        for i in message.new_chat_members:
            if i.is_self:
                return
    user = (
        message.new_chat_members[0] if message.new_chat_members else message.from_user
    )
    if (
        user.is_self
        or user.is_verified
        or user.is_bot
        or user.is_deleted
        or user.is_support
    ):
        return
    uid = user.id
    mid = message.id
    await ServiceMessage.set_cache(uid, cid, mid)
