from typing import TYPE_CHECKING
from pyrogram import filters

from sticker import bot
from sticker.functions.verification_system import verification_system

if TYPE_CHECKING:
    from sticker.single_utils import Message


@bot.on_message(filters=filters.group & ~filters.service, group=1)
async def clean_message(_, message: "Message"):
    if not message.from_user:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    request = await verification_system.get_request(chat_id, user_id)
    if not request:
        return
    await message.delay_delete(1)
    result = await verification_system.verify_code(request.chat_id, request.user_id)
    if not result:
        # 已被处理
        return
    if message.sticker:
        await request.on_success()
    elif request.on_failed:
        await request.on_failed()


@bot.on_message(filters=filters.private & filters.sticker, group=1)
async def clean_sticker_private(_, message: "Message"):
    user_id = message.chat.id
    request = await verification_system.get_pending_request(user_id)
    if not request:
        return
    result = await verification_system.verify_code(request.chat_id, request.user_id)
    if not result:
        # 已被处理
        return
    await request.on_success()
