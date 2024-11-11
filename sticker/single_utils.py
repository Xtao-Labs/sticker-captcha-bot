from typing import Optional

from pyrogram import Client
from pyrogram.types import Message


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
