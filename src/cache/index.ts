import fs from "fs";
import path from "path";
import { config } from "../config.js";
import { logger } from "../utils/logger.js";
import { runQuery, getOne, getAll } from "../database/index.js";

export interface CacheEntry {
  id: number;
  video_id: string;
  file_path: string;
  file_size: number;
  created_at: string;
  last_used: string;
  hit_count: number;
}

export function getCacheDir(): string {
  if (!fs.existsSync(config.cacheDir)) {
    fs.mkdirSync(config.cacheDir, { recursive: true });
  }
  return config.cacheDir;
}

export function getCachedVideo(videoId: string): CacheEntry | undefined {
  const entry = getOne<CacheEntry>(
    "SELECT * FROM cache WHERE video_id = ?",
    [videoId]
  );
  if (!entry) return undefined;

  if (!fs.existsSync(entry.file_path)) {
    runQuery("DELETE FROM cache WHERE video_id = ?", [videoId]);
    return undefined;
  }

  return entry;
}

export function storeCachedVideo(
  videoId: string,
  sourceFilePath: string,
  fileSize: number
): void {
  try {
    const cacheDir = getCacheDir();
    const cachedPath = path.join(cacheDir, `${videoId}.mp4`);

    if (!fs.existsSync(sourceFilePath)) return;

    fs.copyFileSync(sourceFilePath, cachedPath);

    const now = new Date().toISOString();
    runQuery(
      `INSERT OR REPLACE INTO cache (video_id, file_path, file_size, created_at, last_used, hit_count)
       VALUES (?, ?, ?, ?, ?, 1)`,
      [videoId, cachedPath, fileSize, now, now]
    );

    logger.info({ videoId, fileSize }, "Video stored in cache");
  } catch (err) {
    logger.error({ err, videoId }, "Failed to store video in cache");
  }
}

export function updateCacheHit(videoId: string): void {
  const now = new Date().toISOString();
  runQuery(
    "UPDATE cache SET last_used = ?, hit_count = hit_count + 1 WHERE video_id = ?",
    [now, videoId]
  );
}

export function getAllCachedEntries(): CacheEntry[] {
  return getAll<CacheEntry>("SELECT * FROM cache ORDER BY last_used ASC, hit_count ASC");
}

export function removeCachedVideo(videoId: string): void {
  const entry = getOne<CacheEntry>(
    "SELECT file_path FROM cache WHERE video_id = ?",
    [videoId]
  );
  if (entry && fs.existsSync(entry.file_path)) {
    fs.unlinkSync(entry.file_path);
  }
  runQuery("DELETE FROM cache WHERE video_id = ?", [videoId]);
}
