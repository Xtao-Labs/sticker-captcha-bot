import contextlib
import datetime
from typing import Union, List

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.types import ChatJoinRequest

from sticker.languages import VERIFY_TIME
from sticker.single_utils import Message

scheduler = AsyncIOScheduler(timezone="Asia/ShangHai")


async def delete_message(message: Message) -> bool:
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


async def decline_request(chat_join_request: ChatJoinRequest):
    with contextlib.suppress(Exception):
        await chat_join_request.decline()
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


def add_delete_message_id_job(
    chat_id: int, message_id: Union[int, List[int]], delete_seconds: int = 60
):
    scheduler.add_job(
        delete_message_id,
        "date",
        id=f"{chat_id}|{message_id}|delete_message",
        name=f"{chat_id}|{message_id}|delete_message",
        args=[chat_id, message_id],
        run_date=datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        + datetime.timedelta(seconds=delete_seconds),
        replace_existing=True,
    )


def add_delete_message_job(message: Message, delete_seconds: int = 60):
    scheduler.add_job(
        delete_message,
        "date",
        id=f"{message.chat.id}|{message.id}|delete_message",
        name=f"{message.chat.id}|{message.id}|delete_message",
        args=[message],
        run_date=datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        + datetime.timedelta(seconds=delete_seconds),
        replace_existing=True,
    )


def add_decline_request_job(chat_join_request: ChatJoinRequest):
    scheduler.add_job(
        decline_request,
        "date",
        id=f"{chat_join_request.chat.id}|{chat_join_request.from_user.id}|decline_request",
        name=f"{chat_join_request.chat.id}|{chat_join_request.from_user.id}|decline_request",
        args=[chat_join_request],
        run_date=datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        + datetime.timedelta(seconds=VERIFY_TIME),
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


def rem_decline_request_job(chat_join_request: ChatJoinRequest):
    if job := scheduler.get_job(
        f"{chat_join_request.chat.id}|{chat_join_request.from_user.id}|decline_request"
    ):
        job.remove()
