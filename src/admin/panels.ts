import { InlineKeyboard } from "grammy";
import { getBotStats, getUserStats, getAllUsersWithStats, getRecentDownloads } from "../database/stats.js";
import { getUser } from "../database/users.js";
import { formatDate, formatFileSize } from "../utils/format.js";

export function mainMenuKeyboard(): InlineKeyboard {
  return new InlineKeyboard()
    .text("Statistics", "admin:stats")
    .text("Users", "admin:users:0")
    .row()
    .text("Recent Downloads", "admin:downloads:0");
}

export function mainMenuText(): string {
  return "Admin Panel\n\nSelect an option below:";
}

export function statsPanelText(): string {
  const stats = getBotStats();
  return (
    "Bot Statistics\n\n" +
    `Total Users: ${stats.totalUsers}\n` +
    `Total Downloads: ${stats.totalDownloads}\n` +
    `Active Users (7d): ${stats.activeUsers}\n` +
    `Banned Users: ${stats.bannedUsers}`
  );
}

export function statsKeyboard(): InlineKeyboard {
  return new InlineKeyboard().text("Back", "admin:menu");
}

const USERS_PER_PAGE = 10;

export function userListText(page: number): string {
  const users = getAllUsersWithStats(USERS_PER_PAGE, page * USERS_PER_PAGE);
  if (users.length === 0) {
    return "Users\n\nNo users found.";
  }

  let text = `Users (page ${page + 1})\n\n`;
  for (const user of users) {
    const status = user.is_banned ? " [BANNED]" : "";
    text += `${user.userId} - @${user.username || "N/A"}${status}\n`;
    text += `  Downloads: ${user.totalDownloads} | Since: ${formatDate(user.registration_date)}\n\n`;
  }
  return text;
}

export function userListKeyboard(page: number): InlineKeyboard {
  const users = getAllUsersWithStats(USERS_PER_PAGE, page * USERS_PER_PAGE);
  const kb = new InlineKeyboard();

  for (const user of users) {
    kb.text(`@${user.username || user.userId}`, `admin:user:${user.userId}`).row();
  }

  const navButtons: { text: string; data: string }[] = [];
  if (page > 0) {
    navButtons.push({ text: "Prev", data: `admin:users:${page - 1}` });
  }
  navButtons.push({ text: "Back", data: "admin:menu" });

  const nextPage = getAllUsersWithStats(USERS_PER_PAGE, (page + 1) * USERS_PER_PAGE);
  if (nextPage.length > 0) {
    navButtons.push({ text: "Next", data: `admin:users:${page + 1}` });
  }

  kb.row(...navButtons.map((b) => ({ text: b.text, callback_data: b.data })));
  return kb;
}

export function userDetailText(userId: number): string {
  const stats = getUserStats(userId);
  if (!stats) return "User not found.";

  return (
    "User Details\n\n" +
    `Telegram ID: ${stats.userId}\n` +
    `Username: ${stats.username ? "@" + stats.username : "N/A"}\n` +
    `Name: ${stats.firstName || "N/A"}\n` +
    `Total Downloads: ${stats.totalDownloads}\n` +
    `Completed: ${stats.completedDownloads}\n` +
    `Failed: ${stats.failedDownloads}\n` +
    `Total Size: ${formatFileSize(stats.totalFileSize)}\n` +
    `Last Download: ${stats.lastDownloadAt ? formatDate(stats.lastDownloadAt) : "Never"}`
  );
}

export function userDetailKeyboard(userId: number): InlineKeyboard {
  const user = getUser(userId);
  const isBanned = user?.is_banned === 1;
  const kb = new InlineKeyboard();
  if (isBanned) {
    kb.text("Unban User", `admin:unban:${userId}`);
  } else {
    kb.text("Ban User", `admin:ban:${userId}`);
  }
  kb.row();
  kb.text("Back", "admin:users:0");
  return kb;
}

const DOWNLOADS_PER_PAGE = 10;

export function downloadsText(): string {
  const downloads = getRecentDownloads(DOWNLOADS_PER_PAGE);
  if (downloads.length === 0) {
    return "Recent Downloads\n\nNo downloads yet.";
  }

  let text = "Recent Downloads\n\n";
  for (const d of downloads) {
    const statusEmoji =
      d.status === "completed" ? "Done" : d.status === "failed" ? "Failed" : "Pending";
    text += `#${d.id} - ${statusEmoji}\n`;
    text += `  User: @${d.username || d.user_id}\n`;
    text += `  URL: ${d.url.substring(0, 50)}${d.url.length > 50 ? "..." : ""}\n`;
    if (d.file_size) text += `  Size: ${formatFileSize(d.file_size)}\n`;
    if (d.error_message) text += `  Error: ${d.error_message.substring(0, 80)}\n`;
    text += `  ${formatDate(d.created_at)}\n\n`;
  }
  return text;
}

export function downloadsKeyboard(): InlineKeyboard {
  return new InlineKeyboard().text("Back", "admin:menu");
}
