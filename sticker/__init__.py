import contextlib
import sys
from enum import Enum

from cashews import cache
from datetime import datetime, timezone
from logging import getLogger, StreamHandler, CRITICAL, INFO, basicConfig, DEBUG

from coloredlogs import ColoredFormatter

from sticker.bot import bot
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


class LogAction(str, Enum):
    FAIL_ERROR = "FAIL_ERROR"
    FAIL_TIMEOUT = "FAIL_TIMEOUT"
    ACCEPT = "ACCEPT"
    NEW_GROUP = "NEW_GROUP"
    REQUEST = "REQUEST"


async def log(chat, user, action: LogAction):
    scheduler.add_job(
        _log,
        args=[chat, user, action],
        replace_existing=False,
    )


async def _log(chat, user, action: LogAction):
    if not Config.LOG_CHANNEL:
        return
    me = await bot.get_me()
    event = {
        LogAction.FAIL_ERROR: "回答错误",
        LogAction.FAIL_TIMEOUT: "回答超时",
        LogAction.ACCEPT: "通过验证",
        LogAction.NEW_GROUP: "加入群组",
        LogAction.REQUEST: "发起验证",
    }
    msg = """#%s
群组: %s
群组id: <code>%s</code>
用户: #id%s
昵称：<code>%s</code>
OPBot: #bot%s
事件: %s"""
    user_name = user.full_name if user else ""
    msg %= (
        action.value,
        chat.title,
        chat.id,
        user.id if user else "",
        user_name,
        me.id,
        event[action],
    )
    await bot.send_message(Config.LOG_CHANNEL, msg)
