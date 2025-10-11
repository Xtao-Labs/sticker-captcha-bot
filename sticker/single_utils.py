from typing import Optional

from pyrogram import Client as PyroClient
from pyrogram.types import Message as PyroMessage


class Client(PyroClient):
    """Custom Client class to add additional methods if needed."""


class Message(PyroMessage):
    async def delay_delete(self, delete_seconds: int = 60) -> Optional[bool]:
        return

    async def safe_delete(self, revoke: bool = True) -> None:
        return
