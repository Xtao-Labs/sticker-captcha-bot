from cashews import cache
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

from pyromod.utils.errors import TimeoutConversationError
from sticker.languages import RE_MSG, VERIFY_TIME
from sticker.scheduler import add_ban_chat_member_job
from sticker.single_utils import Message, Client
from sticker import bot, log, LogAction


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
        or user.is_verified
        or user.is_bot
        or user.is_deleted
        or user.is_support
    ):
        return
    member = await client.get_chat_member(chat.id, user.id)
    await message.delay_delete(1)
    key = f"wait:{chat.id}:{user.id}"
    await cache.set(key, "True", expire=VERIFY_TIME + 5)
    try:
        msg = await reply_to.reply(RE_MSG % (user.mention, user.mention))
    except Exception as _:
        return
    try:
        msg_ = await client.listen(
            chat.id, filters=filters.user(user.id), timeout=VERIFY_TIME
        )
        await msg.delay_delete(1)
        await msg_.delay_delete(1)
        if not msg_.sticker:
            await reply_to.delay_delete(1)
            if member.status not in [
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
            ]:
                add_ban_chat_member_job(chat.id, user.id)
            await log(chat, user, LogAction.FAIL_ERROR)
        else:
            await cache.delete(key)
            await log(chat, user, LogAction.ACCEPT)
    except TimeoutConversationError:
        await msg.delay_delete(1)
        await reply_to.delay_delete(1)
        if member.status not in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        ]:
            add_ban_chat_member_job(chat.id, user.id)
        await log(chat, user, LogAction.FAIL_TIMEOUT)
