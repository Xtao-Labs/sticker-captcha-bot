import os
from json import load as load_json
import sys
from yaml import load, FullLoader, safe_load
from shutil import copyfile


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


try:
    config = load(open(r"config.yml"), Loader=FullLoader)
except FileNotFoundError:
    print("The configuration file does not exist, and a new configuration file is being generated.")
    copyfile(f"{os.getcwd()}{os.sep}config.gen.yml", "config.yml")
    sys.exit(1)


class Config:
    try:
        API_ID = int(os.environ.get("API_ID", config["api_id"]))
        API_HASH = os.environ.get("API_HASH", config["api_hash"])
        BOT_TOKEN = os.environ.get("BOT_TOKEN", config["bot_token"])
        LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", config["log_channel"]))
        STRING_SESSION = os.environ.get("STRING_SESSION")
        DEBUG = strtobool(os.environ.get("PGM_DEBUG", config["debug"]))
        IPV6 = strtobool(os.environ.get("PGM_IPV6", config["ipv6"]))
        PROXY_ADDRESS = os.environ.get("PGM_PROXY_ADDRESS", config["proxy_addr"])
        PROXY_PORT = os.environ.get("PGM_PROXY_PORT", config["proxy_port"])
        PROXY = None
        if PROXY_ADDRESS and PROXY_PORT:
            PROXY = dict(
                hostname=PROXY_ADDRESS,
                port=PROXY_PORT,
            )
    except ValueError as e:
        print(e)
        sys.exit(1)
