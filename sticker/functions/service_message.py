from typing import List

from cashews import cache

from sticker.scheduler import add_delete_message_id_job


class ServiceMessage:
    @staticmethod
    async def set_cache(uid: int, cid: int, mid: int):
        old = await ServiceMessage.get_cache(uid, cid)
        old.append(mid)
        await cache.set(f"service_message:{uid}:{cid}", old, expire=600)

    @staticmethod
    async def get_cache(uid: int, cid: int) -> List[int]:
        data = await cache.get(f"service_message:{uid}:{cid}")
        return data or []

    @staticmethod
    async def try_delete(uid: int, cid: int):
        mid = await ServiceMessage.get_cache(uid, cid)
        if mid:
            add_delete_message_id_job(cid, list(mid), 1)
