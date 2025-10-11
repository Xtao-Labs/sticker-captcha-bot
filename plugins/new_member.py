from typing import TYPE_CHECKING
from functools import partial

from sticker.functions.verification_system import verification_system
from sticker.languages import MSG, MSG_FAILURE, MSG_SUCCESS
from sticker.scheduler import (
    add_decline_request_job,
    add_approve_request_job,
    add_send_message_text_job,
    rem_decline_request_job,
)
from sticker import bot, log, LogAction

if TYPE_CHECKING:
    from pyrogram.types import ChatJoinRequest, Chat, User
    from sticker.single_utils import Client


async def on_timeout(chat: "Chat", user: "User"):
    add_send_message_text_job(user.id, MSG_FAILURE)
    add_decline_request_job(chat.id, user.id, 1)
    await log(chat, user, LogAction.FAIL_TIMEOUT)


async def on_success(chat: "Chat", user: "User"):
    add_send_message_text_job(user.id, MSG_SUCCESS)
    add_approve_request_job(chat.id, user.id)
    await log(chat, user, LogAction.ACCEPT)
    rem_decline_request_job(chat.id, user.id)


@bot.on_chat_join_request()
async def new_member(_: "Client", chat_join_request: "ChatJoinRequest"):
    chat = chat_join_request.chat
    user = chat_join_request.from_user
    if not chat or not user:
        return
    timeout = partial(on_timeout, chat, user)
    success = partial(on_success, chat, user)
    result = await verification_system.request_verification(
        chat.id, user.id, success, None, timeout
    )
    if not result:
        # 重复忽略
        return
    add_decline_request_job(chat.id, user.id)
    await log(chat, user, LogAction.REQUEST)
    add_send_message_text_job(user.id, MSG % (chat.title, chat.title))
