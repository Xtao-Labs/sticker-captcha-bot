import contextlib

from datetime import datetime, timedelta

from pyrogram.enums import MessageServiceType
from pyrogram import filters

from sticker.single_utils import Client, Message
from sticker import bot

from pyromod.utils.errors import TimeoutConversationError

MSG = """您好 %s ，当前群组开启了验证功能。

您需要在 30 秒内发送任意一个 贴纸 来完成验证。"""


@bot.on_message(filters.service)
async def chat_members_handle(client: Client, message: Message):
    if message.service != MessageServiceType.NEW_CHAT_MEMBERS:
        return
    chat = message.chat
    user = message.from_user
    if user.is_self or user.is_verified or user.is_bot or user.is_deleted or user.is_support:
        return
    try:
        msg = await message.reply(MSG % user.mention)
        msg_ = await client.listen(message.chat, filters=filters.user(user.id), timeout=30)
        with contextlib.suppress(Exception):
            await msg.delete()
        if not msg_.sticker:
            with contextlib.suppress(Exception):
                await message.delete()
            with contextlib.suppress(Exception):
                await bot.ban_chat_member(chat.id, user.id, datetime.now() + timedelta(minutes=5))
    except TimeoutConversationError:
        with contextlib.suppress(Exception):
            await message.delete()
        with contextlib.suppress(Exception):
            await bot.ban_chat_member(chat.id, user.id, datetime.now() + timedelta(minutes=5))
