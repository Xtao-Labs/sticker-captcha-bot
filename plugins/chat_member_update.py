import contextlib
from datetime import datetime, timedelta

from cashews import cache
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated

from pyromod.utils.errors import TimeoutConversationError
from sticker.languages import MSG_PUBLIC, ADMIN_MSG, MSG, VERIFY_TIME
from sticker.scheduler import add_delete_message_job
from sticker.service_message import ServiceMessage
from sticker.single_utils import Client
from sticker import bot, log


@bot.on_chat_member_updated()
async def invite(client: Client, chat_member_updated: ChatMemberUpdated):
    chat = chat_member_updated.chat
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
        and old_member.status
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
    if from_user and from_user.is_self:
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
        msg = await client.send_message(chat.id, MSG % (user.mention, user.mention))
    except Exception:
        return
    try:
        with contextlib.suppress(Exception):
            await log(chat, user, "REQUEST")
        msg_ = await client.listen(chat.id, filters=filters.user(user.id), timeout=VERIFY_TIME)
        with contextlib.suppress(Exception):
            await msg.delete()
        if not msg_.sticker:
            with contextlib.suppress(Exception):
                await bot.ban_chat_member(
                    chat.id, user.id, datetime.now() + timedelta(minutes=5)
                )
            with contextlib.suppress(Exception):
                await log(chat, user, "FAIL_ERROR")
            await ServiceMessage.try_delete(user.id, chat.id)
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
        await ServiceMessage.try_delete(user.id, chat.id)
