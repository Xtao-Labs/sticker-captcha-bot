from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sticker.single_utils import Message, Client
from sticker import bot


@bot.on_message(filters=filters.private & filters.command("start"))
async def start(client: Client, message: Message):
    me = await client.get_me()
    await message.reply(
        f"""你好，我是 <b>{me.first_name}</b> ！

我可以主动私聊申请加入群组的新成员进行贴纸验证。""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    "Github",
                    url="https://github.com/Xtao-Labs/sticker-captcha-bot")],
                [InlineKeyboardButton(
                    "邀请入群",
                    url=f"https://t.me/{me.username}?startgroup=start&admin=can_invite_users")]
            ]))
