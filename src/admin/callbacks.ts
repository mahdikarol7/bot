import { Context } from "grammy";
import { banUser, unbanUser } from "../database/users.js";
import {
  mainMenuText,
  mainMenuKeyboard,
  statsPanelText,
  statsKeyboard,
  userListText,
  userListKeyboard,
  userDetailText,
  userDetailKeyboard,
  downloadsText,
  downloadsKeyboard,
} from "./panels.js";

export async function handleAdminCallback(ctx: Context): Promise<void> {
  const data = ctx.callbackQuery?.data;
  if (!data || !data.startsWith("admin:")) return;

  await ctx.answerCallbackQuery();

  const parts = data.split(":");
  const action = parts[1];

  switch (action) {
    case "menu": {
      await ctx.editMessageText(mainMenuText(), {
        reply_markup: mainMenuKeyboard(),
      });
      break;
    }

    case "stats": {
      await ctx.editMessageText(statsPanelText(), {
        reply_markup: statsKeyboard(),
      });
      break;
    }

    case "users": {
      const page = parseInt(parts[2] || "0", 10);
      await ctx.editMessageText(userListText(page), {
        reply_markup: userListKeyboard(page),
      });
      break;
    }

    case "user": {
      const userId = parseInt(parts[2], 10);
      await ctx.editMessageText(userDetailText(userId), {
        reply_markup: userDetailKeyboard(userId),
      });
      break;
    }

    case "ban": {
      const userId = parseInt(parts[2], 10);
      banUser(userId);
      await ctx.editMessageText(userDetailText(userId), {
        reply_markup: userDetailKeyboard(userId),
      });
      await ctx.reply(`User ${userId} has been banned.`);
      break;
    }

    case "unban": {
      const userId = parseInt(parts[2], 10);
      unbanUser(userId);
      await ctx.editMessageText(userDetailText(userId), {
        reply_markup: userDetailKeyboard(userId),
      });
      await ctx.reply(`User ${userId} has been unbanned.`);
      break;
    }

    case "downloads": {
      await ctx.editMessageText(downloadsText(), {
        reply_markup: downloadsKeyboard(),
      });
      break;
    }
  }
}
