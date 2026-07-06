import { Bot } from "grammy";
import { config } from "../config.js";
import { authMiddleware, loggerMiddleware } from "./middleware.js";
import { startCommand, helpCommand, statusCommand, myInfoCommand, qualityCommand } from "./commands.js";
import { messageHandler } from "./handlers.js";
import { setupAdminCommands, setupAdminCallbacks } from "../admin/index.js";
import { logger } from "../utils/logger.js";

export function createBot(): Bot {
  const bot = new Bot(config.botToken);

  bot.use(loggerMiddleware);
  bot.use(authMiddleware);

  bot.command("start", startCommand);
  bot.command("help", helpCommand);
  bot.command("status", statusCommand);
  bot.command("myinfo", myInfoCommand);
  bot.command("quality", qualityCommand);

  setupAdminCommands(bot);
  setupAdminCallbacks(bot);

  bot.on("message:text", messageHandler);

  bot.catch((err) => {
    logger.error({ err: err.message }, "Bot error");
  });

  return bot;
}
