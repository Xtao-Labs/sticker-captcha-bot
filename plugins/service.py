import contextlib

from datetime import datetime, timedelta

from pyrogram.enums import MessageServiceType, ChatMemberStatus
from pyrogram import filters

from sticker.scheduler import add_delete_message_job
from sticker.single_utils import Client, Message
from sticker import bot, log

from pyromod.utils.errors import TimeoutConversationError

MSG = """您好 %s ，当前群组开启了验证功能。

您需要在 30 秒内发送任意一个 贴纸 来完成验证。"""
ADMIN_MSG = """管理员邀请，自动放行。"""


@bot.on_message(filters.service)
async def chat_members_handle(client: Client, message: Message):
    if message.service != MessageServiceType.NEW_CHAT_MEMBERS:
        return
    chat = message.chat
    if message.new_chat_members:
        for i in message.new_chat_members:
            if i.is_self:
                return
    user = message.new_chat_members[0] if message.new_chat_members else message.from_user
    if user.is_self or user.is_verified or user.is_bot or user.is_deleted or user.is_support:
        return
    if message.new_chat_members and message.from_user and (
            await bot.get_chat_member(chat.id, message.from_user.id)
    ).status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
        try:
            msg = await message.reply(ADMIN_MSG)
        except Exception:
            return
        add_delete_message_job(msg)
        return
    try:
        msg = await message.reply(MSG % user.mention)
    except Exception:
        return
    try:
        with contextlib.suppress(Exception):
            await log(chat, user, "REQUEST")
        msg_ = await client.listen(chat.id, filters=filters.user(user.id), timeout=30)
        with contextlib.suppress(Exception):
            await msg.delete()
        if not msg_.sticker:
            with contextlib.suppress(Exception):
                await message.delete()
            with contextlib.suppress(Exception):
                await bot.ban_chat_member(chat.id, user.id, datetime.now() + timedelta(minutes=5))
            with contextlib.suppress(Exception):
                await log(chat, user, "FAIL_ERROR")
        else:
            with contextlib.suppress(Exception):
                await log(chat, user, "ACCEPT")
        with contextlib.suppress(Exception):
            await msg_.delete()
    except TimeoutConversationError:
        with contextlib.suppress(Exception):
            await msg.delete()
        with contextlib.suppress(Exception):
            await message.delete()
        with contextlib.suppress(Exception):
            await bot.ban_chat_member(chat.id, user.id, datetime.now() + timedelta(minutes=5))
        with contextlib.suppress(Exception):
            await log(chat, user, "FAIL_TIMEOUT")
