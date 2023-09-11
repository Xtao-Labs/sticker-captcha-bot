import contextlib
import sys
from cashews import cache
from datetime import datetime, timezone
from logging import getLogger, StreamHandler, CRITICAL, INFO, basicConfig, DEBUG

from coloredlogs import ColoredFormatter
import pyromod.listen
from pyrogram import Client

from sticker.config import Config
from sticker.scheduler import scheduler

cache.setup("mem://")
logs = getLogger(__name__)
logging_format = "%(levelname)s [%(asctime)s] [%(name)s] %(message)s"
logging_handler = StreamHandler()
logging_handler.setFormatter(ColoredFormatter(logging_format))
root_logger = getLogger()
root_logger.setLevel(DEBUG if Config.DEBUG else CRITICAL)
root_logger.addHandler(logging_handler)
pyro_logger = getLogger("pyrogram")
pyro_logger.setLevel(CRITICAL)
pyro_logger.addHandler(logging_handler)
basicConfig(level=DEBUG if Config.DEBUG else INFO)
logs.setLevel(DEBUG if Config.DEBUG else INFO)

# easy check
if not Config.API_ID:
    logs.error("Api-ID Not Found!")
    sys.exit(1)
elif not Config.API_HASH:
    logs.error("Api-Hash Not Found!")
    sys.exit(1)

start_time = datetime.now(timezone.utc)

with contextlib.suppress(ImportError):
    import uvloop  # noqa

    uvloop.install()

if not scheduler.running:
    scheduler.start()
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


async def log(chat, user, action):
    if not Config.LOG_CHANNEL:
        return
    me = await bot.get_me()
    event = {
        "FAIL_ERROR": "回答错误",
        "FAIL_TIMEOUT": "回答超时",
        "ACCEPT": "通过验证",
        "NEW_GROUP": "加入群组",
        "REQUEST": "发起验证",
    }
    msg = """#%s
群组: %s
群组id: <code>%s</code>
用户: #id%s
OPBot: #bot%s
事件: %s"""
    msg %= (action, chat.title, chat.id, user.id if user else "", me.id, event[action])
    await bot.send_message(Config.LOG_CHANNEL, msg)
