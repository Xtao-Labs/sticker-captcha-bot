import contextlib
import datetime
from typing import Union, List, TYPE_CHECKING

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sticker.languages import VERIFY_TIME

if TYPE_CHECKING:
    from sticker.single_utils import Message

scheduler = AsyncIOScheduler(timezone="Asia/ShangHai")


def delay_time(seconds: int) -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("Asia/Shanghai")) + datetime.timedelta(
        seconds=seconds
    )


async def delete_message(message: "Message") -> bool:
    with contextlib.suppress(Exception):
        await message.delete()
        return True
    return False


async def delete_message_id(chat_id: int, message_id: Union[int, List[int]]) -> bool:
    with contextlib.suppress(Exception):
        from sticker.bot import bot

        await bot.delete_messages(chat_id, message_id)
        return True
    return False


async def decline_request(chat_id: int, user_id: int):
    with contextlib.suppress(Exception):
        from sticker.bot import bot

        await bot.decline_chat_join_request(chat_id, user_id)
        return True
    return False


async def approve_request(chat_id: int, user_id: int):
    with contextlib.suppress(Exception):
        from sticker.bot import bot

        await bot.approve_chat_join_request(chat_id, user_id)
        return True
    return False


async def ban_chat_member(chat_id: int, user_id: int):
    from sticker import bot

    with contextlib.suppress(Exception):
        await bot.ban_chat_member(
            chat_id, user_id, datetime.datetime.now() + datetime.timedelta(minutes=5)
        )
        return True
    return False


async def send_message_text(chat_id: int, text: str):
    from sticker import bot

    with contextlib.suppress(Exception):
        await bot.send_message(chat_id, text)
        return True
    return False


def add_delete_message_id_job(
    chat_id: int, message_id: Union[int, List[int]], delete_seconds: int = 60
):
    scheduler.add_job(
        delete_message_id,
        "date",
        id=f"{chat_id}|{message_id}|delete_message",
        name=f"{chat_id}|{message_id}|delete_message",
        args=[chat_id, message_id],
        run_date=delay_time(delete_seconds),
        replace_existing=True,
    )


def add_delete_message_job(message: "Message", delete_seconds: int = 60):
    scheduler.add_job(
        delete_message,
        "date",
        id=f"{message.chat.id}|{message.id}|delete_message",
        name=f"{message.chat.id}|{message.id}|delete_message",
        args=[message],
        run_date=delay_time(delete_seconds),
        replace_existing=True,
    )


def add_decline_request_job(chat_id: int, user_id: int, timeout: int = VERIFY_TIME):
    scheduler.add_job(
        decline_request,
        "date",
        id=f"{chat_id}|{user_id}|decline_request",
        name=f"{chat_id}|{user_id}|decline_request",
        args=[chat_id, user_id],
        run_date=delay_time(timeout),
        replace_existing=True,
    )


def add_approve_request_job(chat_id: int, user_id: int):
    scheduler.add_job(
        approve_request,
        id=f"{chat_id}|{user_id}|approve_request",
        name=f"{chat_id}|{user_id}|approve_request",
        args=[chat_id, user_id],
        replace_existing=True,
    )


def add_ban_chat_member_job(chat_id: int, user_id: int):
    scheduler.add_job(
        ban_chat_member,
        id=f"{chat_id}|{user_id}|ban_chat_member",
        name=f"{chat_id}|{user_id}|ban_chat_member",
        args=[chat_id, user_id],
        replace_existing=True,
    )


def add_send_message_text_job(chat_id: int, text: str):
    hash_text = hash(text)
    scheduler.add_job(
        send_message_text,
        id=f"{chat_id}|{hash_text}|send_message",
        name=f"{chat_id}|{hash_text}|send_message",
        args=[chat_id, text],
        replace_existing=True,
    )


def rem_decline_request_job(chat_id: int, user_id: int):
    if job := scheduler.get_job(f"{chat_id}|{user_id}|decline_request"):
        job.remove()
