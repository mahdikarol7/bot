import { execFile } from "child_process";
import fs from "fs";
import path from "path";
import https from "https";
import http from "http";
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
      "--no-check-certificates",
      "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "--extractor-args", "youtube:player_client=tv_embedded,web_creator,web",
      "--extractor-retries", "3",
      "--merge-output-format", "mp4",
      "--print-json",
    ];

    const { stdout, stderr } = await execFileAsync("yt-dlp", args, {
      timeout: config.downloadTimeoutSec * 1000,
      maxBuffer: 50 * 1024 * 1024,
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
  } catch (ytdlpErr) {
    // yt-dlp failed - try cobalt fallback
    logger.warn({ err: ytdlpErr }, "yt-dlp failed, trying cobalt fallback");
    onProgress?.("yt-dlp failed, trying alternative download...");

    try {
      await downloadViaCobalt(url, outputPath);

      if (!fs.existsSync(outputPath)) {
        throw new Error("Cobalt download completed but output file not found");
      }

      const stat = fs.statSync(outputPath);
      onProgress?.("Download complete, sending video...");

      return {
        filePath: outputPath,
        title: "YouTube Video",
        duration: 0,
        fileSize: stat.size,
      };
    } catch (cobaltErr) {
      // Both failed
      if (fs.existsSync(outputPath)) {
        fs.unlinkSync(outputPath);
      }

      const errMsg = ytdlpErr instanceof Error ? ytdlpErr.message : "Unknown error";
      if (errMsg.includes("Sign in") || errMsg.includes("bot")) {
        throw new Error("YouTube is blocking this video. Please try a different video or try again later.");
      }
      throw new Error(`Download failed: ${errMsg.substring(0, 200)}`);
    }
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

function downloadFile(url: string, destPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const file = fs.createWriteStream(destPath);
    client.get(url, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        downloadFile(res.headers.location!, destPath).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      res.pipe(file);
      file.on("finish", () => { file.close(); resolve(); });
      file.on("error", reject);
    }).on("error", reject);
  });
}

async function downloadViaCobalt(url: string, outputPath: string): Promise<void> {
  const body = JSON.stringify({ url, downloadMode: "auto", filenameStyle: "basic" });

  return new Promise((resolve, reject) => {
    const req = https.request("https://api.cobalt.tools/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", async () => {
        try {
          const json = JSON.parse(data);
          if (json.status === "tunnel" || json.status === "redirect") {
            await downloadFile(json.url, outputPath);
            resolve();
          } else {
            reject(new Error(json.error?.message || "Cobalt download failed"));
          }
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}
