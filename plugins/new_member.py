import contextlib

from cashews import cache
from pyrogram.types import ChatJoinRequest
from pyrogram import filters

from plugins.languages import MSG, MSG_SUCCESS, MSG_FAILURE, VERIFY_TIME
from sticker.single_utils import Client
from sticker.scheduler import add_decline_request_job, rem_decline_request_job
from sticker import bot, log

from pyromod.utils.errors import TimeoutConversationError


@bot.on_chat_join_request()
async def new_member(client: Client, chat_join_request: ChatJoinRequest):
    chat = chat_join_request.chat
    await cache.set(f"cid:{chat.id}", "True", expire=3600, exist=True)
    user = chat_join_request.from_user
    add_decline_request_job(chat_join_request)
    try:
        with contextlib.suppress(Exception):
            await log(chat, user, "REQUEST")
        await client.ask(user.id, MSG % chat.title, filters=filters.sticker, timeout=VERIFY_TIME)
        with contextlib.suppress(Exception):
            await client.send_message(user.id, MSG_SUCCESS)
        await chat_join_request.approve()
        with contextlib.suppress(Exception):
            await log(chat, user, "ACCEPT")
        with contextlib.suppress(Exception):
            rem_decline_request_job(chat_join_request)
    except TimeoutConversationError:
        with contextlib.suppress(Exception):
            await client.send_message(user.id, MSG_FAILURE)
        with contextlib.suppress(Exception):
            await chat_join_request.decline()
        with contextlib.suppress(Exception):
            await log(chat, user, "FAIL_TIMEOUT")
