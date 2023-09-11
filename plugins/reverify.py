import contextlib

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

from datetime import datetime, timedelta

from pyromod.utils.errors import TimeoutConversationError
from sticker.scheduler import add_delete_message_job
from sticker.single_utils import Message, Client
from sticker import bot, log

MSG = """您好 %s ，您被管理员要求重新验证。

您需要在 30 秒内发送任意一个 贴纸 来完成验证。"""


@bot.on_message(filters=filters.group & filters.command("reverify"))
async def re_verify(client: Client, message: Message):
    if not message.from_user or not message.reply_to_message:
        msg: Message = await message.reply("请回复一条消息来使 Ta 重新验证。")
        add_delete_message_job(message, 10)
        add_delete_message_job(msg, 10)
        return
    if not message.reply_to_message.from_user:
        return
    chat = message.chat
    user = message.from_user
    member = await client.get_chat_member(chat.id, user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return

    user = message.reply_to_message.from_user
    if (
        user.is_self
        or user.is_verified
        or user.is_bot
        or user.is_deleted
        or user.is_support
    ):
        return
    member = await client.get_chat_member(chat.id, user.id)
    with contextlib.suppress(Exception):
        await message.delete()
    try:
        msg = await message.reply_to_message.reply(MSG % user.mention)
    except Exception as _:
        return
    try:
        msg_ = await client.listen(chat.id, filters=filters.user(user.id), timeout=30)
        with contextlib.suppress(Exception):
            await msg.delete()
        if not msg_.sticker:
            with contextlib.suppress(Exception):
                await message.reply_to_message.delete()
            if member.status not in [
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
            ]:
                with contextlib.suppress(Exception):
                    await bot.ban_chat_member(
                        chat.id, user.id, datetime.now() + timedelta(minutes=5)
                    )
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
            await message.reply_to_message.delete()
        if member.status not in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        ]:
            with contextlib.suppress(Exception):
                await bot.ban_chat_member(
                    chat.id, user.id, datetime.now() + timedelta(minutes=5)
                )
        with contextlib.suppress(Exception):
            await log(chat, user, "FAIL_TIMEOUT")
