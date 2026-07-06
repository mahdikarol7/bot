import { Bot, Context } from "grammy";
import { config } from "../config.js";
import { adminGuard } from "../bot/middleware.js";
import { handleAdminCallback } from "./callbacks.js";
import {
  mainMenuText,
  mainMenuKeyboard,
  statsPanelText,
  statsKeyboard,
  userListText,
  userListKeyboard,
} from "./panels.js";
import { banUser, unbanUser } from "../database/users.js";

export function setupAdminCommands(bot: Bot): void {
  const guard = adminGuard(config.adminIds);

  bot.command("admin", guard, async (ctx) => {
    await ctx.reply(mainMenuText(), {
      reply_markup: mainMenuKeyboard(),
    });
  });

  bot.command("adminstats", guard, async (ctx) => {
    await ctx.reply(statsPanelText(), {
      reply_markup: statsKeyboard(),
    });
  });

  bot.command("adminusers", guard, async (ctx) => {
    const page = parseInt(ctx.match || "0", 10);
    await ctx.reply(userListText(page), {
      reply_markup: userListKeyboard(page),
    });
  });

  bot.command("ban", guard, async (ctx) => {
    const args = ctx.match?.split(" ");
    const userId = args?.[0] ? parseInt(args[0], 10) : NaN;

    if (isNaN(userId)) {
      await ctx.reply("Usage: /ban <user_id>");
      return;
    }

    banUser(userId);
    await ctx.reply(`User ${userId} has been banned.`);
  });

  bot.command("unban", guard, async (ctx) => {
    const args = ctx.match?.split(" ");
    const userId = args?.[0] ? parseInt(args[0], 10) : NaN;

    if (isNaN(userId)) {
      await ctx.reply("Usage: /unban <user_id>");
      return;
    }

    unbanUser(userId);
    await ctx.reply(`User ${userId} has been unbanned.`);
  });

  bot.callbackQuery(/^admin:/, guard, handleAdminCallback);
}

export function setupAdminCallbacks(bot: Bot): void {
  // Callbacks are already set up in setupAdminCommands via bot.callbackQuery
}
