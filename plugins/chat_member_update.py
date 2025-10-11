import asyncio
import contextlib
from functools import partial
from time import time
from typing import Dict, TYPE_CHECKING

from cashews import cache
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.types import ChatMemberUpdated

from sticker.functions.verification_system import verification_system
from sticker.languages import MSG_PUBLIC, ADMIN_MSG, MSG, VERIFY_TIME
from sticker.scheduler import add_ban_chat_member_job, add_delete_message_id_job
from sticker.functions.service_message import ServiceMessage
from sticker.single_utils import Client, Message
from sticker import bot, log, LogAction

if TYPE_CHECKING:
    from pyrogram.types import Chat, User


lock_map_lock = asyncio.Lock()
lock_map: Dict[int, asyncio.Lock] = {}


async def get_lock(chat_id: int):
    async with lock_map_lock:
        lock = lock_map.get(chat_id)
        if not lock:
            lock = asyncio.Lock()
            lock_map[chat_id] = lock
    return lock


async def send_message_raw(client: "Client", chat: "Chat", user: "User"):
    return await client.send_message(chat.id, MSG % (user.mention, user.mention))


async def send_message(client: "Client", chat: "Chat", user: "User"):
    n_time = time()
    lock = await get_lock(chat.id)
    async with lock:
        if time() - n_time > 30:
            # 认为此任务已过期
            return
        key = f"msg:{chat.id}:{user.id}"
        try:
            msg: "Message" = await send_message_raw(client, chat, user)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            msg: "Message" = await send_message_raw(client, chat, user)
        await msg.delay_delete(VERIFY_TIME + 5)
        await cache.set(key, msg.id, expire=VERIFY_TIME + 5)
        await log(chat, user, LogAction.REQUEST)


async def delete_message(chat: "Chat", user: "User"):
    key2 = f"msg:{chat.id}:{user.id}"
    msg = await cache.get(key2)
    if msg:
        add_delete_message_id_job(chat.id, msg, 1)


async def on_timeout(chat: "Chat", user: "User"):
    await delete_message(chat, user)
    add_ban_chat_member_job(chat.id, user.id)
    await log(chat, user, LogAction.FAIL_TIMEOUT)
    await ServiceMessage.try_delete(user.id, chat.id)


async def on_failed(chat: "Chat", user: "User"):
    await delete_message(chat, user)
    add_ban_chat_member_job(chat.id, user.id)
    await log(chat, user, LogAction.FAIL_ERROR)
    await ServiceMessage.try_delete(user.id, chat.id)


async def on_success(chat: "Chat", user: "User"):
    await delete_message(chat, user)
    await log(chat, user, LogAction.ACCEPT)


async def start_verify(client: "Client", chat: "Chat", user: "User"):
    timeout = partial(on_timeout, chat, user)
    success = partial(on_success, chat, user)
    failed = partial(on_failed, chat, user)
    result = await verification_system.request_verification(
        chat.id, user.id, success, failed, timeout
    )
    if not result:
        # 重复忽略
        return
    client.loop.create_task(send_message(client, chat, user))


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
    if (
        (user.verification_status and user.verification_status.is_verified)
        or user.is_bot
        or user.is_deleted
        or user.is_support
    ):
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
