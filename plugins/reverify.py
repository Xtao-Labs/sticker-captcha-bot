import contextlib
from functools import partial

from typing import TYPE_CHECKING

from cashews import cache
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

from sticker.functions.verification_system import verification_system
from sticker.languages import RE_MSG, VERIFY_TIME
from sticker.scheduler import add_ban_chat_member_job, add_delete_message_id_job
from sticker.single_utils import Message, Client
from sticker import bot, log, LogAction

if TYPE_CHECKING:
    from pyrogram.types import Chat, User, ChatMember


async def delete_message(chat: "Chat", user: "User"):
    key2 = f"msg:{chat.id}:{user.id}"
    msg = await cache.get(key2)
    if msg:
        add_delete_message_id_job(chat.id, msg, 1)


async def on_timeout(chat: "Chat", user: "User", member: "ChatMember"):
    await delete_message(chat, user)
    if member.status not in [
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    ]:
        add_ban_chat_member_job(chat.id, user.id)
    await log(chat, user, LogAction.FAIL_TIMEOUT)


async def on_failed(chat: "Chat", user: "User", member: "ChatMember"):
    await delete_message(chat, user)
    if member.status not in [
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    ]:
        add_ban_chat_member_job(chat.id, user.id)
    await log(chat, user, LogAction.FAIL_ERROR)


async def on_success(chat: "Chat", user: "User"):
    await delete_message(chat, user)
    await log(chat, user, LogAction.ACCEPT)


async def start_verify(reply_to: "Message", chat: "Chat", user: "User"):
    timeout = partial(on_timeout, chat, user)
    success = partial(on_success, chat, user)
    failed = partial(on_failed, chat, user)
    result = await verification_system.request_verification(
        chat.id, user.id, success, failed, timeout
    )
    if not result:
        # 重复忽略
        return
    with contextlib.suppress(Exception):
        msg = await reply_to.reply(RE_MSG % (user.mention, user.mention))
        key = f"msg:{chat.id}:{user.id}"
        await msg.delay_delete(VERIFY_TIME + 5)
        await cache.set(key, msg.id, expire=VERIFY_TIME + 5)
    await log(chat, user, LogAction.REQUEST)


@bot.on_message(filters=filters.group & filters.command("reverify"))
async def re_verify(client: Client, message: Message):
    reply_to: "Message" = message.reply_to_message
    if not message.from_user or not reply_to:
        msg: Message = await message.reply("请回复一条消息来使 Ta 重新验证。")
        await message.delay_delete(10)
        await msg.delay_delete(10)
        return
    if not reply_to.from_user:
        return
    chat = message.chat
    user = message.from_user
    member = await client.get_chat_member(chat.id, user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return

    user = reply_to.from_user
    if (
        user.is_self
        or (user.verification_status and user.verification_status.is_verified)
        or user.is_bot
        or user.is_deleted
        or user.is_support
    ):
        return
    member = await client.get_chat_member(chat.id, user.id)
    await message.delay_delete(1)
    if member.status in [
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    ]:
        return
    await start_verify(reply_to, chat, user)
