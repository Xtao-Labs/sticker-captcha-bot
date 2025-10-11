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

import pyrogram

from sticker.scheduler import add_delete_message_job
from ..utils import patch, patchable


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
