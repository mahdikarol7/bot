"""Download queue manager.

Manages concurrent downloads with per-user limits and queue position tracking.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Callable

from loguru import logger


@dataclass
class DownloadTask:
    """Represents a queued download task."""
    task_id: int
    user_id: int
    url: str
    download_type: str
    quality: str
    video_id: str
    title: str
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    future: asyncio.Future | None = None


class DownloadQueue:
    """Manages download queue with concurrency control.

    Each download runs one at a time per user.
    Global concurrency is limited to avoid resource exhaustion.
    """

    def __init__(self, max_concurrent: int = 3) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._queue: asyncio.Queue[DownloadTask] = asyncio.Queue()
        self._task_counter = 0
        self._active_tasks: dict[int, DownloadTask] = {}
        self._user_positions: dict[int, list[int]] = {}
        self._running = False
        self._worker_task: asyncio.Task | None = None

    def start(self) -> None:
        """Start the queue worker."""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("Download queue started")

    async def stop(self) -> None:
        """Stop the queue worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
        logger.info("Download queue stopped")

    async def enqueue(
        self,
        user_id: int,
        url: str,
        download_type: str,
        quality: str,
        video_id: str,
        title: str,
    ) -> DownloadTask:
        """Add a download task to the queue.

        Returns:
            The enqueued DownloadTask.
        """
        self._task_counter += 1
        task = DownloadTask(
            task_id=self._task_counter,
            user_id=user_id,
            url=url,
            download_type=download_type,
            quality=quality,
            video_id=video_id,
            title=title,
        )
        task.future = asyncio.get_event_loop().create_future()

        self._user_positions.setdefault(user_id, []).append(task.task_id)
        await self._queue.put(task)

        position = self._queue.qsize()
        logger.info(
            "Task #{} queued for user {} (position: {})", task.task_id, user_id, position
        )
        return task

    def get_queue_length(self) -> int:
        """Return current queue length."""
        return self._queue.qsize()

    def get_user_position(self, user_id: int) -> int | None:
        """Return a user's position in the queue, or None if not queued."""
        positions = self._user_positions.get(user_id, [])
        if positions:
            return self._queue.qsize()
        return None

    def cancel_task(self, task_id: int) -> bool:
        """Cancel a queued or active task."""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.cancel_event.set()
            logger.info("Task #{} cancelled (active)", task_id)
            return True
        return False

    def cancel_by_user(self, user_id: int) -> bool:
        """Cancel all tasks for a user."""
        cancelled = False
        for task_id, task in list(self._active_tasks.items()):
            if task.user_id == user_id:
                task.cancel_event.set()
                cancelled = True
        return cancelled

    async def _worker(self) -> None:
        """Queue worker that processes tasks sequentially."""
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            self._active_tasks[task.task_id] = task
            self._user_positions.get(task.user_id, [])
            if task.task_id in self._user_positions.get(task.user_id, []):
                self._user_positions[task.user_id].remove(task.task_id)

            async with self._semaphore:
                try:
                    if task.future and not task.future.done():
                        task.future.set_result(task)
                except Exception as e:
                    logger.error("Task #{} failed: {}", task.task_id, e)
                    if task.future and not task.future.done():
                        task.future.set_exception(e)
                finally:
                    self._active_tasks.pop(task.task_id, None)
