"""
pyromod - A monkeypatcher add-on for Pyrogram
Copyright (C) 2020 Cezar H. <https://github.com/usernein>

This file is part of pyromod.

pyromod is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyromod is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyromod.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import contextlib
import functools

import pyrogram

from sticker.scheduler import add_delete_message_job
from ..utils import patch, patchable
from ..utils.errors import ListenerCanceled, TimeoutConversationError

pyrogram.errors.ListenerCanceled = ListenerCanceled
LOCK = asyncio.Lock()
DONE = []
DONE_MAP = {}


@patch(pyrogram.client.Client)
class Client:
    @patchable
    def __init__(self, *args, **kwargs):
        self.listening = {}
        self.using_mod = True

        self.old__init__(*args, **kwargs)

    @patchable
    async def listen(self, chat_id, filters=None, timeout=None):
        if type(chat_id) != int:
            chat = await self.get_chat(chat_id)
            chat_id = chat.id

        future = self.loop.create_future()
        future.add_done_callback(functools.partial(self.clear_listener, chat_id))
        self.listening.update({chat_id: {"future": future, "filters": filters}})
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.exceptions.TimeoutError as e:
            raise TimeoutConversationError() from e

    @patchable
    async def ask(self, chat_id, text, filters=None, timeout=None, *args, **kwargs):
        request = await self.send_message(chat_id, text, *args, **kwargs)
        response = await self.listen(chat_id, filters, timeout)
        response.request = request
        return response

    @patchable
    def clear_listener(self, chat_id, future):
        with contextlib.suppress(KeyError):
            if future == self.listening[chat_id]["future"]:
                self.listening.pop(chat_id, None)

    @patchable
    def cancel_listener(self, chat_id):
        listener = self.listening.get(chat_id)
        if not listener or listener["future"].done():
            return

        listener["future"].set_exception(ListenerCanceled())
        self.clear_listener(chat_id, listener["future"])

    @patchable
    def cancel_all_listener(self):
        for chat_id in self.listening:
            self.cancel_listener(chat_id)


@patch(pyrogram.handlers.message_handler.MessageHandler)
class MessageHandler:
    @patchable
    def __init__(self, callback: callable, filters=None):
        self.user_callback = callback
        self.old__init__(self.resolve_listener, filters)

    @patchable
    async def resolve_listener(self, client, message, *args):
        global LOCK, DONE
        async with LOCK:
            listener = client.listening.get(message.chat.id)
            if listener and DONE_MAP.get(id(self)) == id(listener):
                with contextlib.suppress(ValueError):
                    DONE.remove(listener)
                    del DONE_MAP[id(self)]
                if not listener["future"].done():
                    listener["future"].set_result(message)
                    return
                if listener["future"].done():
                    client.clear_listener(message.chat.id, listener["future"])
        await self.user_callback(client, message, *args)

    @patchable
    async def check(self, client, update):
        global LOCK, DONE
        async with LOCK:
            listener = client.listening.get(update.chat.id)
            if listener and (listener not in DONE) and (not listener["future"].done()):
                if callable(listener["filters"]):
                    result = await listener["filters"](client, update)
                    if result:
                        DONE.append(listener)
                        DONE_MAP[id(self)] = id(listener)
                        return True
                else:
                    DONE.append(listener)
                    DONE_MAP[id(self)] = id(listener)
                    return True
        return await self.filters(client, update) if callable(self.filters) else True


@patch(pyrogram.types.user_and_chats.chat.Chat)
class Chat(pyrogram.types.Chat):
    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def ask(self, *args, **kwargs):
        return self._client.ask(self.id, *args, **kwargs)

    @patchable
    def cancel_listener(self):
        return self._client.cancel_listener(self.id)


@patch(pyrogram.types.user_and_chats.user.User)
class User(pyrogram.types.User):
    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def ask(self, *args, **kwargs):
        return self._client.ask(self.id, *args, **kwargs)

    @patchable
    def cancel_listener(self):
        return self._client.cancel_listener(self.id)


@patch(pyrogram.types.messages_and_media.Message)
class Message(pyrogram.types.Message):
    @patchable
    async def safe_delete(self, revoke: bool = True):
        try:
            return await self._client.delete_messages(
                chat_id=self.chat.id, message_ids=self.id, revoke=revoke
            )
        except Exception as e:  # noqa
            return False

    @patchable
    async def delay_delete(self, delay: int = 60):
        add_delete_message_job(self, delay)
