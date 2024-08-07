import contextlib

from pyrogram.types import ChatJoinRequest
from pyrogram import filters

from sticker.languages import MSG, MSG_SUCCESS, MSG_FAILURE, VERIFY_TIME
from sticker.single_utils import Client
from sticker.scheduler import add_decline_request_job, rem_decline_request_job
from sticker import bot, log, LogAction

from pyromod.utils.errors import TimeoutConversationError


@bot.on_chat_join_request()
async def new_member(client: Client, chat_join_request: ChatJoinRequest):
    chat = chat_join_request.chat
    user = chat_join_request.from_user
    add_decline_request_job(chat_join_request)
    try:
        await log(chat, user, LogAction.REQUEST)
        await client.ask(
            user.id,
            MSG % (chat.title, chat.title),
            filters=filters.sticker,
            timeout=VERIFY_TIME,
        )
        with contextlib.suppress(Exception):
            await client.send_message(user.id, MSG_SUCCESS)
        await chat_join_request.approve()
        await log(chat, user, LogAction.ACCEPT)
        rem_decline_request_job(chat_join_request)
    except TimeoutConversationError:
        with contextlib.suppress(Exception):
            await client.send_message(user.id, MSG_FAILURE)
        with contextlib.suppress(Exception):
            await chat_join_request.decline()
        await log(chat, user, LogAction.FAIL_TIMEOUT)
