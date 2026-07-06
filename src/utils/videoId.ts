import { execFile } from "child_process";
import { promisify } from "util";
import { logger } from "./logger.js";

const execFileAsync = promisify(execFile);

const URL_VIDEO_ID_PATTERNS = [
  /(?:youtube\.com\/watch\?.*?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
];

function extractVideoIdFromUrl(url: string): string | null {
  for (const pattern of URL_VIDEO_ID_PATTERNS) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

export async function extractVideoId(url: string): Promise<string | null> {
  const fromUrl = extractVideoIdFromUrl(url);
  if (fromUrl) return fromUrl;

  try {
    const { stdout } = await execFileAsync(
      "yt-dlp",
      [url, "--dump-json", "--skip-download", "--no-playlist"],
      { timeout: 15_000, maxBuffer: 1024 * 1024 }
    );
    const info = JSON.parse(stdout);
    return info.id ?? null;
  } catch (err) {
    logger.warn({ err, url }, "Failed to extract video ID via yt-dlp");
    return null;
  }
}
