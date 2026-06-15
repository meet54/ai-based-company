"""Prevents idle in-house work while client project pipelines are running."""

import asyncio

_lock = asyncio.Lock()
_busy_count = 0


class WorkflowLock:
    async def acquire(self) -> None:
        global _busy_count
        await _lock.acquire()
        _busy_count += 1

    def release(self) -> None:
        global _busy_count
        _busy_count = max(0, _busy_count - 1)
        _lock.release()

    def is_busy(self) -> bool:
        return _busy_count > 0 or _lock.locked()


workflow_lock = WorkflowLock()
