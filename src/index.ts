import dotenv from "dotenv";
dotenv.config();

const PROXY_URL = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || process.env.ALL_PROXY;
if (PROXY_URL) {
  const { setupProxy } = await import("./proxy.js");
  setupProxy(PROXY_URL);
}

import { config } from "./config.js";
import { initDatabase, saveDatabase } from "./database/index.js";
import { createBot } from "./bot/index.js";
import { startCleanupJob, cleanTempDir } from "./utils/cleanup.js";
import { startCacheCleanupJob } from "./cache/cleanup.js";
import { logger } from "./utils/logger.js";

async function main(): Promise<void> {
  if (PROXY_URL) {
    logger.info({ proxy: PROXY_URL }, "Proxy configured");
  }
  logger.info("Starting YouTube Shorts Downloader Bot...");

  await initDatabase();
  logger.info("Database initialized");

  const bot = createBot();
  logger.info("Bot created");

  logger.info("Connecting to Telegram...");
  try {
    const me = await bot.api.getMe();
    logger.info({ id: me.id, username: me.username }, "Bot verified with Telegram API");
  } catch (err) {
    logger.fatal({ err }, "Failed to connect to Telegram. Check your BOT_TOKEN and internet connection.");
    process.exit(1);
  }

  const cleanupTimer = startCleanupJob();
  const cacheCleanupTimer = startCacheCleanupJob();
  logger.info("Cleanup jobs started");

  const shutdown = async (): Promise<void> => {
    logger.info("Shutting down...");
    clearInterval(cleanupTimer);
    clearInterval(cacheCleanupTimer);
    saveDatabase();
    cleanTempDir();
    bot.stop();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  bot.start({
    onStart: (botInfo) => {
      logger.info({ username: botInfo.username }, "Bot is now running. Send /start in Telegram to begin.");
    },
  });
}

main().catch((err) => {
  logger.fatal({ err }, "Failed to start bot");
  process.exit(1);
});
