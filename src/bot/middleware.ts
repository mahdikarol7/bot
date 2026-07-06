import { Context, NextFunction } from "grammy";
import { createOrUpdateUser, getUser } from "../database/users.js";
import { logger } from "../utils/logger.js";

export async function authMiddleware(ctx: Context, next: NextFunction): Promise<void> {
  if (!ctx.from) return next();

  const { id, username, first_name } = ctx.from;
  createOrUpdateUser(id, username ?? null, first_name ?? null);

  const user = getUser(id);
  if (user?.is_banned) {
    await ctx.reply("Your account has been banned. Contact an administrator for assistance.");
    return;
  }

  return next();
}

export async function loggerMiddleware(ctx: Context, next: NextFunction): Promise<void> {
  const start = Date.now();
  const updateType = ctx.update.message
    ? "message"
    : ctx.update.callback_query
      ? "callback_query"
      : "other";

  logger.info(
    {
      userId: ctx.from?.id,
      username: ctx.from?.username,
      updateType,
      chatId: ctx.chat?.id,
    },
    "Incoming update"
  );

  await next();

  const ms = Date.now() - start;
  logger.debug({ ms }, "Update processed");
}

export function adminGuard(allowedIds: number[]) {
  return async (ctx: Context, next: NextFunction): Promise<void> => {
    if (!ctx.from || !allowedIds.includes(ctx.from.id)) {
      await ctx.reply("Access denied. Admin only.");
      return;
    }
    return next();
  };
}
