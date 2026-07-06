import { Context } from "grammy";
import { logger } from "../utils/logger.js";

interface WaiterEntry {
  userId: number;
  ctx: Context;
  resolve: (filePath: string | null) => void;
}

interface DownloadLockEntry {
  videoId: string;
  waiters: WaiterEntry[];
}

const activeVideoDownloads = new Map<string, DownloadLockEntry>();

export function isVideoDownloading(videoId: string): boolean {
  return activeVideoDownloads.has(videoId);
}

export function acquireDownloadLock(
  videoId: string,
  userId: number,
  ctx: Context
): Promise<string | null> | null {
  const existing = activeVideoDownloads.get(videoId);

  if (!existing) {
    activeVideoDownloads.set(videoId, { videoId, waiters: [] });
    return null;
  }

  logger.info({ videoId, userId }, "Video already downloading, attaching waiter");

  return new Promise<string | null>((resolve) => {
    existing.waiters.push({ userId, ctx, resolve });
  });
}

export function releaseDownloadLock(videoId: string, filePath?: string): void {
  const entry = activeVideoDownloads.get(videoId);
  if (!entry) return;

  activeVideoDownloads.delete(videoId);

  for (const waiter of entry.waiters) {
    waiter.resolve(filePath ?? null);
  }

  if (entry.waiters.length > 0) {
    logger.info(
      { videoId, waiterCount: entry.waiters.length },
      "Released download lock, notified waiters"
    );
  }
}

export function failDownloadLock(videoId: string): void {
  const entry = activeVideoDownloads.get(videoId);
  if (!entry) return;

  activeVideoDownloads.delete(videoId);

  for (const waiter of entry.waiters) {
    waiter.resolve(null);
  }

  if (entry.waiters.length > 0) {
    logger.info(
      { videoId, waiterCount: entry.waiters.length },
      "Download failed, notified waiters"
    );
  }
}
