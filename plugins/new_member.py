import contextlib

from pyrogram.types import ChatJoinRequest
from pyrogram import filters

from sticker.single_utils import Client
from sticker import bot

from pyromod.utils.errors import TimeoutConversationError


MSG = """您好，群组 %s 开启了验证功能。

您需要在 30 秒内发送任意一个 贴纸 来完成验证。"""
MSG_SUCCESS = """验证成功，您已经成为群组的一员了！"""
MSG_FAILURE = """验证失败，请重试。"""


@bot.on_chat_join_request()
async def new_member(client: Client, chat_join_request: ChatJoinRequest):
    chat = chat_join_request.chat
    user = chat_join_request.from_user
    try:
        await client.ask(user.id, MSG % chat.title, filters=filters.sticker, timeout=30)
        with contextlib.suppress(Exception):
            await client.send_message(user.id, MSG_SUCCESS)
        await chat_join_request.approve()
    except TimeoutConversationError:
        with contextlib.suppress(Exception):
            await client.send_message(user.id, MSG_FAILURE)
        await chat_join_request.decline()
