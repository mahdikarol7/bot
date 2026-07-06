import { z } from "zod";
import dotenv from "dotenv";
import path from "path";

dotenv.config({ override: true });

const envSchema = z.object({
  BOT_TOKEN: z.string().min(1, "BOT_TOKEN is required"),
  ADMIN_IDS: z
    .string()
    .min(1, "ADMIN_IDS is required")
    .transform((val) =>
      val
        .split(",")
        .map((id) => id.trim())
        .filter(Boolean)
    ),
  DATA_DIR: z.string().default("./data"),
  MAX_CONCURRENT_DOWNLOADS: z.coerce.number().int().positive().default(3),
  MAX_FILE_SIZE_MB: z.coerce.number().int().positive().default(150),
  DOWNLOAD_TIMEOUT_SEC: z.coerce.number().int().positive().default(300),
  RATE_LIMIT_MAX: z.coerce.number().int().positive().default(5),
  RATE_LIMIT_WINDOW_MS: z.coerce.number().int().positive().default(3600000),
  LOG_LEVEL: z
    .enum(["trace", "debug", "info", "warn", "error", "fatal"])
    .default("info"),
  DEFAULT_QUALITY: z
    .enum(["360", "480", "720", "1080"])
    .default("720"),
  CACHE_MAX_SIZE_GB: z.coerce.number().positive().default(0.5),
  CACHE_EXPIRE_DAYS: z.coerce.number().positive().default(7),
  CACHE_DIR: z.string().default("cache"),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error("Invalid environment configuration:");
  for (const issue of parsed.error.issues) {
    console.error(`  ${issue.path.join(".")}: ${issue.message}`);
  }
  process.exit(1);
}

const env = parsed.data;

export const config = {
  botToken: env.BOT_TOKEN,
  adminIds: env.ADMIN_IDS.map(Number),
  dataDir: path.resolve(env.DATA_DIR),
  maxConcurrentDownloads: env.MAX_CONCURRENT_DOWNLOADS,
  maxFileSizeMB: env.MAX_FILE_SIZE_MB,
  downloadTimeoutSec: env.DOWNLOAD_TIMEOUT_SEC,
  rateLimitMax: env.RATE_LIMIT_MAX,
  rateLimitWindowMs: env.RATE_LIMIT_WINDOW_MS,
  logLevel: env.LOG_LEVEL,
  tempDir: path.resolve(env.DATA_DIR, "temp"),
  dbPath: path.resolve(env.DATA_DIR, "bot.sqlite"),
  defaultQuality: env.DEFAULT_QUALITY,
  cacheDir: path.resolve(env.DATA_DIR, env.CACHE_DIR),
  cacheMaxSizeGB: env.CACHE_MAX_SIZE_GB,
  cacheExpireDays: env.CACHE_EXPIRE_DAYS,
} as const;

export type Config = typeof config;
