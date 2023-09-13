import contextlib
from datetime import datetime, timedelta

from cashews import cache
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated

from pyromod.utils.errors import TimeoutConversationError
from sticker.scheduler import add_delete_message_job
from sticker.single_utils import Client
from sticker import bot, log

MSG_PUBLIC = """您好，我发现此群组为公开群组，您需要联系创建者打开 `管理员批准后才能入群` 功能，我就能更好地工作。"""
MSG_SUCCESS = """验证成功，您已经成为群组的一员了！"""
MSG_FAILURE = """验证失败，请重试。"""
MSG = """您好 %s ，当前群组开启了验证功能。

您需要在 30 秒内发送任意一个 贴纸 来完成验证。"""
ADMIN_MSG = """管理员邀请，自动放行。"""


@bot.on_chat_member_updated()
async def invite(client: Client, chat_member_updated: ChatMemberUpdated):
    chat = chat_member_updated.chat
    old_chat_member = chat_member_updated.old_chat_member
    if await cache.get(f"cid:{chat.id}"):
        return
    member = chat_member_updated.new_chat_member
    old_member = chat_member_updated.old_chat_member
    if not member:
        return
    if not member.user:
        return
    user = member.user
    old_user = old_member.user if old_member else None
    if user.is_verified or user.is_bot or user.is_deleted or user.is_support:
        return
    if member.status not in {ChatMemberStatus.MEMBER}:
        return
    if (
        old_user
        and old_user.id == user.id
        and old_user.status
        in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.RESTRICTED,
        }
    ):
        return
    if user.is_self:
        with contextlib.suppress(Exception):
            await log(chat, chat_member_updated.from_user, "NEW_GROUP")
        if chat.username:
            with contextlib.suppress(Exception):
                await client.send_message(chat.id, MSG_PUBLIC)
        return
    from_user = chat_member_updated.from_user
    if from_user and from_user.id == user.id:
        from_user = None
    if from_user.is_self:
        return
    if (
        user
        and from_user
        and (await bot.get_chat_member(chat.id, from_user.id)).status
        in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
    ):
        try:
            msg = await client.send_message(chat.id, ADMIN_MSG)
        except Exception:
            return
        add_delete_message_job(msg)
        return
    try:
        msg = await client.send_message(chat.id, MSG % user.mention)
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
            await bot.ban_chat_member(
                chat.id, user.id, datetime.now() + timedelta(minutes=5)
            )
        with contextlib.suppress(Exception):
            await log(chat, user, "FAIL_TIMEOUT")
