import { Context } from "grammy";
import { getUser, createOrUpdateUser } from "../database/users.js";
import { formatDate } from "../utils/format.js";
import { setUserQuality, getUserQuality } from "../downloader/index.js";
import { config } from "../config.js";
import { getAllCachedEntries, removeCachedVideo, getCacheDir } from "../cache/index.js";
import fs from "fs";

export async function startCommand(ctx: Context): Promise<void> {
  const userId = ctx.from!.id;
  const username = ctx.from!.username ?? null;
  const firstName = ctx.from!.first_name ?? null;

  createOrUpdateUser(userId, username, firstName);

  await ctx.reply(
    "Welcome to YouTube Shorts Downloader!\n\n" +
      "Send me a YouTube or YouTube Shorts link and I'll download the video for you.\n\n" +
      "Supported formats:\n" +
      "- youtube.com/shorts/...\n" +
      "- youtube.com/watch?v=...\n" +
      "- youtu.be/...\n\n" +
      "Commands:\n" +
      "/help - Show usage instructions\n" +
      "/status - Check your account status\n" +
      "/myinfo - View your detailed info\n" +
      `/quality - Set download quality (${config.defaultQuality}p by default)`
  );
}

export async function helpCommand(ctx: Context): Promise<void> {
  await ctx.reply(
    "How to use this bot:\n\n" +
      "1. Find a YouTube video or Shorts link\n" +
      "2. Send the link to this chat\n" +
      "3. Wait for the download to complete\n" +
      "4. The video will be sent to you automatically\n\n" +
      "Supported links:\n" +
      "- youtube.com/shorts/...\n" +
      "- youtube.com/watch?v=...\n" +
      "- youtu.be/...\n\n" +
      "Rate limit: You can download up to 5 videos per hour.\n\n" +
      "File limit: Maximum video size is 50MB.\n\n" +
      "Commands:\n" +
      "/start - Welcome message\n" +
      "/status - Check your account\n" +
      "/myinfo - View your info\n" +
      "/quality - Set video quality\n" +
      "/clearcache - Clear download cache"
  );
}

export async function statusCommand(ctx: Context): Promise<void> {
  const user = getUser(ctx.from!.id);
  if (!user) {
    await ctx.reply("You are not registered. Send /start to register.");
    return;
  }

  const status = user.is_banned ? "BANNED" : "Active";
  await ctx.reply(
    `Account Status: ${status}\n` +
      `Downloads: ${user.download_count}\n` +
      `Last Active: ${formatDate(user.last_activity)}`
  );
}

export async function myInfoCommand(ctx: Context): Promise<void> {
  const user = getUser(ctx.from!.id);
  if (!user) {
    await ctx.reply("You are not registered. Send /start to register.");
    return;
  }

  await ctx.reply(
    `Your Information:\n\n` +
      `Telegram ID: ${user.id}\n` +
      `Username: ${user.username ? "@" + user.username : "N/A"}\n` +
      `Name: ${user.first_name || "N/A"}\n` +
      `Registered: ${formatDate(user.registration_date)}\n` +
      `Last Active: ${formatDate(user.last_activity)}\n` +
      `Total Downloads: ${user.download_count}\n` +
      `Status: ${user.is_banned ? "Banned" : "Active"}`
  );
}

const VALID_QUALITIES = ["360", "480", "720", "1080"];

export async function qualityCommand(ctx: Context): Promise<void> {
  const userId = ctx.from!.id;
  const arg = typeof ctx.match === "string" ? ctx.match.trim() : "";

  if (!arg || !VALID_QUALITIES.includes(arg)) {
    const current = getUserQuality(userId);
    await ctx.reply(
      `Current quality: ${current}p\n\n` +
        "Usage: /quality <resolution>\n\n" +
        "Available options:\n" +
        "- /quality 360 - 360p (smallest file)\n" +
        "- /quality 480 - 480p\n" +
        "- /quality 720 - 720p (default)\n" +
        "- /quality 1080 - 1080p (largest file)"
    );
    return;
  }

  setUserQuality(userId, arg);
  await ctx.reply(`Quality set to ${arg}p for your next downloads.`);
}

export async function clearCacheCommand(ctx: Context): Promise<void> {
  const entries = getAllCachedEntries();
  if (entries.length === 0) {
    await ctx.reply("Cache is empty.");
    return;
  }
  let freed = 0;
  for (const entry of entries) {
    if (fs.existsSync(entry.file_path)) {
      const stat = fs.statSync(entry.file_path);
      freed += stat.size;
      fs.unlinkSync(entry.file_path);
    }
    removeCachedVideo(entry.video_id);
  }
  const freedMB = (freed / (1024 * 1024)).toFixed(1);
  await ctx.reply(`Cache cleared!\nRemoved ${entries.length} videos, freed ${freedMB}MB.`);
}
