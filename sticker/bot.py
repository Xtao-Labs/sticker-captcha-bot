import pyromod.listen
from pyrogram import Client

from sticker.config import Config

bot = Client(
    "sticker",
    bot_token=Config.BOT_TOKEN,
    session_string=Config.STRING_SESSION,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    ipv6=Config.IPV6,
    proxy=Config.PROXY,
    plugins={"root": "plugins"},
)
