import fs from "fs";
import path from "path";
import { config } from "../config.js";
import { logger } from "./logger.js";

const MAX_FILE_AGE_MS = 60 * 60 * 1000; // 1 hour

export function startCleanupJob(intervalMs = 15 * 60 * 1000): NodeJS.Timeout {
  logger.info({ intervalMs }, "Starting cleanup job");

  const timer = setInterval(() => {
    cleanTempDir();
  }, intervalMs);

  return timer;
}

export function cleanTempDir(): void {
  const tempDir = config.tempDir;
  if (!fs.existsSync(tempDir)) return;

  const now = Date.now();
  let cleaned = 0;

  try {
    const files = fs.readdirSync(tempDir);
    for (const file of files) {
      const filePath = path.join(tempDir, file);
      const stat = fs.statSync(filePath);
      if (stat.isFile() && now - stat.mtimeMs > MAX_FILE_AGE_MS) {
        fs.unlinkSync(filePath);
        cleaned++;
      }
    }
    if (cleaned > 0) {
      logger.info({ cleaned }, "Cleaned up old temp files");
    }
  } catch (err) {
    logger.error({ err }, "Error during temp file cleanup");
  }
}

export function cleanAllTempFiles(): void {
  const tempDir = config.tempDir;
  if (!fs.existsSync(tempDir)) return;

  try {
    fs.rmSync(tempDir, { recursive: true, force: true });
    fs.mkdirSync(tempDir, { recursive: true });
    logger.info("Cleaned all temp files");
  } catch (err) {
    logger.error({ err }, "Error cleaning all temp files");
  }
}
