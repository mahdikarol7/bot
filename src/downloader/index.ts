import fs from "fs";
import path from "path";
import { execFile } from "child_process";
import { promisify } from "util";
import { Context, InputFile } from "grammy";

const execFileAsync = promisify(execFile);
const TELEGRAM_MAX_SIZE = 50 * 1024 * 1024;

import { config } from "../config.js";
import { logger } from "../utils/logger.js";
import { downloadVideo } from "./ytdlp.js";
import { validateYouTubeUrl } from "./validator.js";
import {
  createOrUpdateUser,
  incrementDownloadCount,
  getUser,
} from "../database/users.js";
import { runQuery, getOne } from "../database/index.js";
import { extractVideoId } from "../utils/videoId.js";
import {
  getCachedVideo,
  storeCachedVideo,
  updateCacheHit,
  getCacheDir,
} from "../cache/index.js";
import {
  acquireDownloadLock,
  releaseDownloadLock,
  failDownloadLock,
} from "../cache/lock.js";
import { runCacheCleanup } from "../cache/cleanup.js";

interface DownloadJob {
  userId: number;
  url: string;
  ctx: Context;
  quality: string;
  videoId?: string;
}

interface UserRateLimit {
  timestamps: number[];
}

const activeDownloads = new Map<number, boolean>();
const rateLimits = new Map<number, UserRateLimit>();
const userQualities = new Map<number, string>();
let concurrentCount = 0;
const downloadQueue: DownloadJob[] = [];

function isRateLimited(userId: number): boolean {
  const now = Date.now();
  const userRate = rateLimits.get(userId);

  if (!userRate) {
    rateLimits.set(userId, { timestamps: [now] });
    return false;
  }

  userRate.timestamps = userRate.timestamps.filter(
    (t) => now - t < config.rateLimitWindowMs
  );

  if (userRate.timestamps.length >= config.rateLimitMax) {
    return true;
  }

  userRate.timestamps.push(now);
  return false;
}

function processQueue(): void {
  while (
    concurrentCount < config.maxConcurrentDownloads &&
    downloadQueue.length > 0
  ) {
    const job = downloadQueue.shift()!;
    concurrentCount++;
    executeDownload(job).finally(() => {
      concurrentCount--;
      processQueue();
    });
  }
}

async function executeDownload(job: DownloadJob): Promise<void> {
  const { userId, url, ctx, quality, videoId } = job;
  const now = new Date().toISOString();

  runQuery(
    `INSERT INTO downloads (user_id, url, status, created_at) VALUES (?, ?, 'downloading', ?)`,
    [userId, url, now]
  );

  const row = getOne<{ id: number }>(
    "SELECT id FROM downloads WHERE user_id = ? ORDER BY id DESC LIMIT 1",
    [userId]
  );
  const downloadId = row?.id;

  try {
    const result = await downloadVideo(url, userId, quality, async (status) => {
      try {
        const msgId = ctx.message!.message_id + 1;
        await ctx.api.editMessageText(ctx.chat!.id, msgId, status);
      } catch {
        // Message might not exist yet
      }
    });

    runQuery(
      `UPDATE downloads SET status = 'completed', file_path = ?, file_size = ?, duration = ?, completed_at = ? WHERE id = ?`,
      [result.filePath, result.fileSize, result.duration, new Date().toISOString(), downloadId ?? 0]
    );

    incrementDownloadCount(userId);

    if (videoId) {
      storeCachedVideo(videoId, result.filePath, result.fileSize);
    }

    const caption = `${result.title}\n\nDuration: ${formatDuration(result.duration)} | Size: ${formatSize(result.fileSize)}`;

    let filePathToSend = result.filePath;
    let needsCleanup = false;

    if (result.fileSize > TELEGRAM_MAX_SIZE) {
      try {
        filePathToSend = await compressVideo(result.filePath);
        needsCleanup = true;
      } catch {
        filePathToSend = result.filePath;
      }
    }

    try {
      await ctx.api.sendVideo(ctx.chat!.id, new InputFile(filePathToSend), { caption });
    } catch (sendErr) {
      logger.error({ err: sendErr, userId }, "Failed to send video");
      await ctx.reply("Failed to send the video. Try /quality 360.");
    } finally {
      if (needsCleanup && fs.existsSync(filePathToSend)) fs.unlinkSync(filePathToSend);
      if (fs.existsSync(result.filePath)) fs.unlinkSync(result.filePath);
    }

    try {
      await ctx.api.deleteMessage(ctx.chat!.id, ctx.message!.message_id + 1);
    } catch {}

    if (videoId) {
      const cachedPath = path.join(getCacheDir(), `${videoId}.mp4`);
      releaseDownloadLock(videoId, fs.existsSync(cachedPath) ? cachedPath : undefined);
      runCacheCleanup();
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : "Unknown error";

    if (videoId) {
      failDownloadLock(videoId);
    }

    runQuery(
      `UPDATE downloads SET status = 'failed', error_message = ? WHERE id = ?`,
      [errorMsg, downloadId ?? 0]
    );

    try {
      await ctx.api.editMessageText(ctx.chat!.id, ctx.message!.message_id + 1, `Error: ${errorMsg}`);
    } catch {
      await ctx.reply(`Error: ${errorMsg}`);
    }
  } finally {
    activeDownloads.delete(userId);
  }
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function compressVideo(filePath: string): Promise<string> {
  const compressedPath = filePath.replace(".mp4", "_compressed.mp4");
  const { stdout } = await execFileAsync("ffprobe", [
    "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", filePath,
  ]);
  const duration = parseFloat(stdout.trim()) || 60;
  const targetBitrate = Math.floor((TELEGRAM_MAX_SIZE * 8 * 0.9) / duration);
  await execFileAsync("ffmpeg", [
    "-i", filePath, "-b:v", `${targetBitrate}`, "-b:a", "128k",
    "-movflags", "+faststart", "-y", compressedPath,
  ], { timeout: 300000 });
  return compressedPath;
}

export async function queueDownload(ctx: Context, url: string): Promise<void> {
  const userId = ctx.from!.id;

  const validation = validateYouTubeUrl(url);
  if (!validation.valid) {
    await ctx.reply(validation.error!);
    return;
  }

  const user = getUser(userId);
  if (user?.is_banned) {
    await ctx.reply("Your account has been banned. Contact an admin for assistance.");
    return;
  }

  const videoId = await extractVideoId(validation.url!);

  if (videoId) {
    const cached = getCachedVideo(videoId);
    if (cached) {
      updateCacheHit(videoId);
      await ctx.reply("Video found in cache, sending...");
      const caption = `Cached video\n\nSize: ${formatSize(cached.file_size)}`;
      let cachedPath = cached.file_path;
      let cachedNeedsCleanup = false;
      if (cached.file_size > TELEGRAM_MAX_SIZE) {
        try {
          cachedPath = await compressVideo(cached.file_path);
          cachedNeedsCleanup = true;
        } catch {}
      }
      try {
        await ctx.api.sendVideo(ctx.chat!.id, new InputFile(cachedPath), { caption });
      } catch (sendErr) {
        logger.error({ err: sendErr, userId }, "Failed to send cached video");
        await ctx.reply("Failed to send the cached video.");
      } finally {
        if (cachedNeedsCleanup && fs.existsSync(cachedPath)) fs.unlinkSync(cachedPath);
      }
      return;
    }

    const lockResult = acquireDownloadLock(videoId, userId, ctx);
    if (lockResult !== null) {
      await ctx.reply("This video is already being downloaded. You'll receive it when ready.");
      const filePath = await lockResult;
      if (filePath && fs.existsSync(filePath)) {
        let lockPath = filePath;
        let lockNeedsCleanup = false;
        const lockStat = fs.statSync(filePath);
        if (lockStat.size > TELEGRAM_MAX_SIZE) {
          try {
            lockPath = await compressVideo(filePath);
            lockNeedsCleanup = true;
          } catch {}
        }
        try {
          await ctx.api.sendVideo(ctx.chat!.id, new InputFile(lockPath));
        } catch {
          await ctx.reply("Failed to send the video.");
        } finally {
          if (lockNeedsCleanup && fs.existsSync(lockPath)) fs.unlinkSync(lockPath);
        }
      } else {
        await ctx.reply("The download failed. Please try again later.");
      }
      return;
    }
  }

  if (activeDownloads.has(userId)) {
    if (videoId) failDownloadLock(videoId);
    await ctx.reply("You already have a download in progress. Please wait for it to finish.");
    return;
  }

  if (isRateLimited(userId)) {
    if (videoId) failDownloadLock(videoId);
    const remaining = Math.ceil(
      (config.rateLimitWindowMs - (Date.now() - (rateLimits.get(userId)?.timestamps[0] ?? 0))) / 60000
    );
    await ctx.reply(`Rate limit exceeded. You can download ${config.rateLimitMax} videos per hour. Try again in ${remaining} minutes.`);
    return;
  }

  createOrUpdateUser(userId, ctx.from!.username ?? null, ctx.from!.first_name ?? null);
  activeDownloads.set(userId, true);

  await ctx.reply("Queued for download...");

  downloadQueue.push({ userId, url: validation.url!, ctx, quality: userQualities.get(userId) ?? config.defaultQuality, videoId: videoId ?? undefined });
  processQueue();
}

export function setUserQuality(userId: number, quality: string): void {
  userQualities.set(userId, quality);
}

export function getUserQuality(userId: number): string {
  return userQualities.get(userId) ?? config.defaultQuality;
}

export function getQueueStatus(): { active: number; queued: number } {
  return {
    active: concurrentCount,
    queued: downloadQueue.length,
  };
}
