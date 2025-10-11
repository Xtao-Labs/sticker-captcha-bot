import asyncio
import time
import hashlib
from typing import Dict, Tuple, Optional, Callable, Any, TYPE_CHECKING

from dataclasses import dataclass

from sticker.scheduler import scheduler, delay_time
from sticker.languages import VERIFY_TIME

if TYPE_CHECKING:
    from apscheduler.job import Job


@dataclass
class VerificationRequest:
    """验证请求数据类"""

    chat_id: int
    user_id: int
    created_time: float
    on_success: Callable[[], Any]
    on_failed: Callable[[], Any]
    is_processed: bool = False


class OptimizedUserVerificationSystem:
    """
    优化版的用户验证系统 - 使用分段锁提高并发性能
    """

    def __init__(self, lock_pool_size: int = 16):
        self.timeout_seconds = VERIFY_TIME
        self.lock_pool_size = lock_pool_size

        # 存储验证请求: key = (chat_id, user_id), value = VerificationRequest
        self._verification_requests: Dict[Tuple[int, int], VerificationRequest] = {}

        # 分段锁池 - 根据chat_id或user_id的哈希选择锁
        self._lock_pool = [asyncio.Lock() for _ in range(lock_pool_size)]

        # 全局锁用于清理操作（不频繁）
        self._global_lock = asyncio.Lock()

        # 后台清理任务
        self._cleanup_task: Optional["Job"] = None
        self._is_running = False

    def _get_lock(self, key: str) -> asyncio.Lock:
        """根据key获取对应的分段锁"""
        # 使用哈希选择锁，确保相同key总是选择同一个锁
        hash_val = hashlib.md5(key.encode()).hexdigest()
        lock_index = int(hash_val, 16) % self.lock_pool_size
        return self._lock_pool[lock_index]

    def _get_request_lock(self, user_id: int) -> asyncio.Lock:
        """获取验证请求对应的锁"""
        return self._get_lock(str(user_id))

    async def start(self):
        """启动验证系统"""
        if not self._is_running:
            self._is_running = True
            self._cleanup_task = scheduler.add_job(
                self._cleanup_expired_requests,
                "interval",
                seconds=60,
            )

    async def stop(self):
        """停止验证系统"""
        self._is_running = False
        if self._cleanup_task:
            scheduler.remove_job(self._cleanup_task.id)

    async def request_verification(
        self,
        chat_id: int,
        user_id: int,
        on_success: Callable[[], Any],
        on_failed: Callable[[], Any],
        on_timeout: Callable[[], Any],
    ) -> bool:
        """
        请求验证 - 使用细粒度锁
        """
        # 获取该请求对应的锁
        request_lock = self._get_request_lock(user_id)

        async with request_lock:
            key = (chat_id, user_id)

            # 检查是否已有待处理请求
            if key in self._verification_requests:
                existing_request = self._verification_requests[key]
                if not existing_request.is_processed:
                    return False  # 已有待处理请求，忽略新请求

            # 创建新请求
            request = VerificationRequest(
                chat_id=chat_id,
                user_id=user_id,
                created_time=time.time(),
                on_success=on_success,
                on_failed=on_failed,
            )

            self._verification_requests[key] = request

            # 启动超时检查任务
            scheduler.add_job(
                self._check_timeout,
                "date",
                id=f"{chat_id}|{user_id}|check_timeout",
                name=f"{chat_id}|{user_id}|check_timeout",
                args=(chat_id, user_id, on_timeout),
                run_date=delay_time(self.timeout_seconds),
                replace_existing=True,
            )

            return True

    async def verify_code(
        self,
        chat_id: int,
        user_id: int,
    ) -> Optional[bool]:
        """
        验证用户输入 - 使用细粒度锁
        """
        # 获取该请求对应的锁
        request_lock = self._get_request_lock(user_id)

        async with request_lock:
            key = (chat_id, user_id)

            if key not in self._verification_requests:
                return None

            request = self._verification_requests[key]

            # 检查是否已处理
            if request.is_processed:
                return None

            # 检查是否超时
            if time.time() - request.created_time > self.timeout_seconds:
                return None

            request.is_processed = True

            scheduler.add_job(
                self._cleanup_successful_requests,
                "date",
                id=f"{chat_id}|{user_id}|cleanup_successful_requests",
                name=f"{chat_id}|{user_id}|cleanup_successful_requests",
                args=(chat_id, user_id),
                run_date=delay_time(5),
                replace_existing=True,
            )

            return True

    async def _check_timeout(
        self,
        chat_id: int,
        user_id: int,
        on_timeout: Callable[[], Any],
    ):
        """检查验证超时"""
        # 获取该请求对应的锁
        request_lock = self._get_request_lock(user_id)

        async with request_lock:
            key = (chat_id, user_id)

            if key in self._verification_requests:
                request = self._verification_requests[key]

                # 检查是否未处理
                if not request.is_processed:
                    request.is_processed = True
                    await on_timeout()

    async def _cleanup_successful_requests(self, chat_id: int, user_id: int):
        """清理已成功处理的请求 - 使用细粒度锁"""
        request_lock = self._get_request_lock(user_id)

        async with request_lock:
            key = (chat_id, user_id)
            if key in self._verification_requests:
                request = self._verification_requests[key]
                if request.is_processed:
                    del self._verification_requests[key]

    async def _cleanup_expired_requests(self):
        """定期清理过期的验证请求 - 使用全局锁"""
        if self._is_running:
            async with self._global_lock:
                current_time = time.time()
                expired_keys = []

                for key, request in self._verification_requests.items():
                    # 清理超过2倍超时时间的请求（确保超时处理已完成）
                    if current_time - request.created_time > self.timeout_seconds * 2:
                        expired_keys.append(key)

                # 逐个删除过期请求（需要获取对应的分段锁）
                for key in expired_keys:
                    chat_id, user_id = key
                    request_lock = self._get_request_lock(user_id)

                    async with request_lock:
                        # 再次检查，防止在获取锁的过程中请求状态发生变化
                        if (
                            key in self._verification_requests
                            and current_time
                            - self._verification_requests[key].created_time
                            > self.timeout_seconds * 2
                        ):
                            del self._verification_requests[key]

    async def get_request(
        self, chat_id: int, user_id: int
    ) -> Optional[VerificationRequest]:
        """获取特定的验证请求"""
        request_lock = self._get_request_lock(user_id)
        async with request_lock:
            return self._verification_requests.get((chat_id, user_id))

    async def get_pending_request(self, user_id: int) -> Optional[VerificationRequest]:
        """获取待处理的验证请求"""
        request_lock = self._get_request_lock(user_id)
        async with request_lock:
            for (chat_id, uid), request in self._verification_requests.items():
                if uid == user_id and not request.is_processed:
                    return request
            return None


verification_system = OptimizedUserVerificationSystem()
