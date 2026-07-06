import { getOne, getAll } from "./index.js";

export interface BotStats {
  totalUsers: number;
  totalDownloads: number;
  activeUsers: number;
  bannedUsers: number;
}

export interface UserStats {
  userId: number;
  username: string | null;
  firstName: string | null;
  totalDownloads: number;
  completedDownloads: number;
  failedDownloads: number;
  totalFileSize: number;
  lastDownloadAt: string | null;
}

export interface DownloadRecord {
  id: number;
  user_id: number;
  url: string;
  status: string;
  file_size: number | null;
  duration: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  username: string | null;
  first_name: string | null;
}

export function getBotStats(): BotStats {
  const totalUsers = getOne<{ c: number }>("SELECT COUNT(*) as c FROM users")?.c ?? 0;
  const totalDownloads = getOne<{ c: number }>("SELECT COUNT(*) as c FROM downloads")?.c ?? 0;

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const activeUsers = getOne<{ c: number }>(
    "SELECT COUNT(*) as c FROM users WHERE last_activity > ?",
    [sevenDaysAgo]
  )?.c ?? 0;

  const bannedUsers = getOne<{ c: number }>(
    "SELECT COUNT(*) as c FROM users WHERE is_banned = 1"
  )?.c ?? 0;

  return { totalUsers, totalDownloads, activeUsers, bannedUsers };
}

export function getUserStats(userId: number): UserStats | null {
  const user = getOne<{ id: number; username: string | null; first_name: string | null }>(
    "SELECT id, username, first_name FROM users WHERE id = ?",
    [userId]
  );

  if (!user) return null;

  const stats = getOne<{
    total: number;
    completed: number;
    failed: number;
    totalFileSize: number;
    lastDownloadAt: string | null;
  }>(
    `SELECT
      COUNT(*) as total,
      SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
      SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
      COALESCE(SUM(file_size), 0) as totalFileSize,
      MAX(completed_at) as lastDownloadAt
     FROM downloads WHERE user_id = ?`,
    [userId]
  );

  return {
    userId: user.id,
    username: user.username,
    firstName: user.first_name,
    totalDownloads: stats?.total ?? 0,
    completedDownloads: stats?.completed ?? 0,
    failedDownloads: stats?.failed ?? 0,
    totalFileSize: stats?.totalFileSize ?? 0,
    lastDownloadAt: stats?.lastDownloadAt ?? null,
  };
}

export function getRecentDownloads(limit = 10): DownloadRecord[] {
  return getAll<DownloadRecord>(
    `SELECT d.*, u.username, u.first_name
     FROM downloads d
     LEFT JOIN users u ON d.user_id = u.id
     ORDER BY d.created_at DESC
     LIMIT ?`,
    [limit]
  );
}

export function getAllUsersWithStats(
  limit: number,
  offset: number
): (UserStats & { registration_date: string; is_banned: number })[] {
  return getAll<UserStats & { registration_date: string; is_banned: number }>(
    `SELECT
      u.id as userId,
      u.username,
      u.first_name as firstName,
      u.registration_date,
      u.is_banned,
      COUNT(d.id) as totalDownloads,
      SUM(CASE WHEN d.status = 'completed' THEN 1 ELSE 0 END) as completedDownloads,
      SUM(CASE WHEN d.status = 'failed' THEN 1 ELSE 0 END) as failedDownloads,
      COALESCE(SUM(d.file_size), 0) as totalFileSize,
      MAX(d.completed_at) as lastDownloadAt
     FROM users u
     LEFT JOIN downloads d ON u.id = d.user_id
     GROUP BY u.id
     ORDER BY u.registration_date DESC
     LIMIT ? OFFSET ?`,
    [limit, offset]
  );
}
