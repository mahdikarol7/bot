import { execFile } from "child_process";
import fs from "fs";
import path from "path";
import { promisify } from "util";
import { config } from "../config.js";
import { logger } from "../utils/logger.js";

const execFileAsync = promisify(execFile);

export interface DownloadResult {
  filePath: string;
  title: string;
  duration: number;
  fileSize: number;
}

export async function downloadVideo(
  url: string,
  userId: number,
  quality: string = config.defaultQuality,
  onProgress?: (status: string) => void
): Promise<DownloadResult> {
  const filename = `${userId}_${Date.now()}.mp4`;
  const outputPath = path.join(config.tempDir, filename);

  onProgress?.(`Downloading video (${quality}p)...`);

  try {
    const args = [
      url,
      "-o", outputPath,
      "--format", "best",
      "--no-playlist",
      "--no-overwrites",
      "--no-warnings",
      "--merge-output-format", "mp4",
      "--print-json",
    ];

    const { stdout, stderr } = await execFileAsync("yt-dlp", args, {
      timeout: config.downloadTimeoutSec * 1000,
      maxBuffer: 10 * 1024 * 1024,
    });

    if (stderr) {
      logger.warn({ stderr }, "yt-dlp stderr output");
    }

    const info = JSON.parse(stdout);

    if (!fs.existsSync(outputPath)) {
      throw new Error("Download completed but output file not found");
    }

    const stat = fs.statSync(outputPath);

    onProgress?.("Download complete, sending video...");

    return {
      filePath: outputPath,
      title: info.title || "Untitled",
      duration: info.duration || 0,
      fileSize: stat.size,
    };
  } catch (err) {
    if (fs.existsSync(outputPath)) {
      fs.unlinkSync(outputPath);
    }

    if (err instanceof Error) {
      if ((err as NodeJS.ErrnoException).code === "ETIMEDOUT") {
        throw new Error("Download timed out. The video might be too long or the server is slow.");
      }
      const execErr = err as { stderr?: string; stdout?: string };
      const errMsg = execErr.stderr || execErr.stdout || err.message;
      if (execErr.stderr) {
        if (execErr.stderr.includes("Video unavailable")) {
          throw new Error("This video is unavailable or has been removed.");
        }
        if (execErr.stderr.includes("Private video")) {
          throw new Error("This is a private video and cannot be downloaded.");
        }

        if (execErr.stderr.includes("File is larger than max-filesize")) {
          throw new Error(`Video exceeds the ${config.maxFileSizeMB}MB size limit.`);
        }
      }
      throw new Error(`Download failed: ${errMsg.substring(0, 200)}`);
    }
    throw new Error("Download failed due to an unknown error");
  }
}

export async function getVideoInfo(url: string): Promise<{ title: string; duration: number }> {
  const { stdout } = await execFileAsync(
    "yt-dlp",
    [url, "--print-json", "--skip-download", "--no-playlist"],
    { timeout: 30000 }
  );
  const info = JSON.parse(stdout);
  return { title: info.title || "Untitled", duration: info.duration || 0 };
}
