import contextlib

from pyrogram.types import ChatMemberUpdated

from sticker.single_utils import Client
from sticker import bot, log

MSG_PUBLIC = """您好，我发现此群组为公开群组，您需要联系创建者打开 `管理员批准后才能入群` 功能，我就能更好地工作。"""
MSG_SUCCESS = """验证成功，您已经成为群组的一员了！"""
MSG_FAILURE = """验证失败，请重试。"""


@bot.on_chat_member_updated()
async def invite(client: Client, chat_member_updated: ChatMemberUpdated):
    chat = chat_member_updated.chat
    if user := chat_member_updated.new_chat_member:
        if user.user.is_self:
            with contextlib.suppress(Exception):
                await log(chat, user.invited_by, "NEW_GROUP")
        if user.user.is_self and chat.username:
            with contextlib.suppress(Exception):
                await client.send_message(chat.id, MSG_PUBLIC)
