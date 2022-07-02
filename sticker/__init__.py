import contextlib
from coloredlogs import ColoredFormatter
from datetime import datetime, timezone
from logging import getLogger, StreamHandler, CRITICAL, INFO, basicConfig, DEBUG

from sticker.config import Config
from sticker.scheduler import scheduler
import pyromod.listen
from pyrogram import Client
import sys

logs = getLogger(__name__)
logging_format = "%(levelname)s [%(asctime)s] [%(name)s] %(message)s"
logging_handler = StreamHandler()
logging_handler.setFormatter(ColoredFormatter(logging_format))
root_logger = getLogger()
root_logger.setLevel(DEBUG if Config.DEBUG else CRITICAL)
root_logger.addHandler(logging_handler)
pyro_logger = getLogger("pyrogram")
pyro_logger.setLevel(DEBUG)
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
bot = Client("sticker",
             bot_token=Config.BOT_TOKEN,
             session_string=Config.STRING_SESSION,
             api_id=Config.API_ID,
             api_hash=Config.API_HASH,
             ipv6=Config.IPV6,
             proxy=Config.PROXY,
             plugins={"root": "plugins"})
