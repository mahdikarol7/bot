import { config } from "../config.js";
import { logger } from "../utils/logger.js";
import { getAllCachedEntries, removeCachedVideo } from "./index.js";

const MS_PER_DAY = 24 * 60 * 60 * 1000;

export function startCacheCleanupJob(intervalMs = 30 * 60 * 1000): NodeJS.Timeout {
  logger.info({ intervalMs }, "Starting cache cleanup job");

  const timer = setInterval(() => {
    performCacheCleanup();
  }, intervalMs);

  return timer;
}

export function runCacheCleanup(): void {
  try {
    performCacheCleanup();
  } catch (err) {
    logger.error({ err }, "Error during post-download cache cleanup");
  }
}

function performCacheCleanup(): void {
  const entries = getAllCachedEntries();
  if (entries.length === 0) return;

  const now = Date.now();
  let totalSize = entries.reduce((sum, e) => sum + e.file_size, 0);
  const maxSizeBytes = config.cacheMaxSizeGB * 1024 * 1024 * 1024;
  const expireMs = config.cacheExpireDays * MS_PER_DAY;
  let cleaned = 0;

  for (const entry of entries) {
    const lastUsed = new Date(entry.last_used).getTime();
    const ageMs = now - lastUsed;

    const expired = ageMs > expireMs;
    const overLimit = totalSize > maxSizeBytes;

    if (expired || overLimit) {
      removeCachedVideo(entry.video_id);
      totalSize -= entry.file_size;
      cleaned++;
    }
  }

  if (cleaned > 0) {
    logger.info(
      { cleaned, remainingSizeMB: (totalSize / (1024 * 1024)).toFixed(1) },
      "Cache cleanup completed"
    );
  }
}
