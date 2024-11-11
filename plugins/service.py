from pyrogram import filters
from pyrogram.enums import MessageServiceType

from sticker import bot
from sticker.functions.service_message import ServiceMessage
from sticker.single_utils import Client, Message


@bot.on_message(filters.service)
async def service_message_handle(_: Client, message: Message):
    if message.service != MessageServiceType.NEW_CHAT_MEMBERS:
        return
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
