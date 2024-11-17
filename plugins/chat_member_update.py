import asyncio
import contextlib
from time import time
from typing import Dict

from cashews import cache
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated

from pyromod.utils.errors import TimeoutConversationError
from sticker.languages import MSG_PUBLIC, ADMIN_MSG, MSG, VERIFY_TIME
from sticker.scheduler import add_ban_chat_member_job, add_delete_message_id_job
from sticker.functions.service_message import ServiceMessage
from sticker.single_utils import Client, Message
from sticker import bot, log, LogAction


lock_map_lock = asyncio.Lock()
lock_map: Dict[int, asyncio.Lock] = {}


async def get_lock(chat_id: int):
    async with lock_map_lock:
        lock = lock_map.get(chat_id)
        if not lock:
            lock = asyncio.Lock()
            lock_map[chat_id] = lock
    return lock


async def send_message(client: "Client", chat, user):
    n_time = time()
    lock = await get_lock(chat.id)
    async with lock:
        if time() - n_time > 30:
            # 认为此任务已过期
            return
        try:
            key = f"msg:{chat.id}:{user.id}"
            msg: "Message" = await client.send_message(
                chat.id, MSG % (user.mention, user.mention)
            )
            await msg.delay_delete(VERIFY_TIME + 5)
            await cache.set(key, msg.id, expire=VERIFY_TIME + 5)
        except Exception:
            return
        await log(chat, user, LogAction.REQUEST)


async def start_verify(client: "Client", chat, user):
    key = f"wait:{chat.id}:{user.id}"
    key2 = f"msg:{chat.id}:{user.id}"
    await cache.set(key, "True", expire=VERIFY_TIME + 5)
    client.loop.create_task(send_message(client, chat, user))
    try:
        msg_: "Message" = await client.listen(
            chat.id,
            filters=filters.user(user.id) & ~filters.service,
            timeout=VERIFY_TIME,
        )
        msg = await cache.get(key2)
        if msg:
            add_delete_message_id_job(chat.id, msg, 1)
        await msg_.delay_delete(1)
        if not msg_.sticker:
            add_ban_chat_member_job(chat.id, user.id)
            await log(chat, user, LogAction.FAIL_ERROR)
            await ServiceMessage.try_delete(user.id, chat.id)
        else:
            await cache.delete(key)
            await log(chat, user, LogAction.ACCEPT)
    except TimeoutConversationError:
        msg = await cache.get(key2)
        if msg:
            add_delete_message_id_job(chat.id, msg, 1)
        add_ban_chat_member_job(chat.id, user.id)
        await log(chat, user, LogAction.FAIL_TIMEOUT)
        await ServiceMessage.try_delete(user.id, chat.id)


@bot.on_chat_member_updated()
async def invite(client: Client, chat_member_updated: ChatMemberUpdated):
    chat = chat_member_updated.chat
    member = chat_member_updated.new_chat_member
    old_member = chat_member_updated.old_chat_member
    if not member:
        return
    if not member.user:
        return
    user = member.user
    old_user = old_member.user if old_member else None
    if user.is_self:
        if member.status not in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        }:
            return
        await log(chat, chat_member_updated.from_user, LogAction.NEW_GROUP)
        if chat.username:
            with contextlib.suppress(Exception):
                await client.send_message(chat.id, MSG_PUBLIC)
        return
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
        with contextlib.suppress(Exception):
            msg: "Message" = await client.send_message(chat.id, ADMIN_MSG)
            await msg.delay_delete()
        return
    await start_verify(client, chat, user)
