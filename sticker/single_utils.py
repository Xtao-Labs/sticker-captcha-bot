import contextlib
from os import sep, remove, mkdir
from os.path import exists
from typing import Optional

from pyrogram import Client
from pyrogram.types import Message

from pyromod.utils.errors import TimeoutConversationError, ListenerCanceled

from sqlitedict import SqliteDict

# init folders
if not exists("data"):
    mkdir("data")
sqlite = SqliteDict(f"data{sep}data.sqlite", autocommit=True)


def safe_remove(name: str) -> None:
    with contextlib.suppress(FileNotFoundError):
        remove(name)


class Client(Client):  # noqa
    async def listen(self, chat_id, filters=None, timeout=None) -> Optional[Message]:
        return

    async def ask(
        self, chat_id, text, filters=None, timeout=None, *args, **kwargs
    ) -> Optional[Message]:
        return

    def cancel_listener(self, chat_id):
        """Cancel the conversation with the given chat_id."""


class Message(Message):  # noqa
    async def delay_delete(self, delete_seconds: int = 60) -> Optional[bool]:
        return

    async def safe_delete(self, revoke: bool = True) -> None:
        return
