import { getOne, getAll, runQuery } from "./index.js";

export interface User {
  id: number;
  username: string | null;
  first_name: string | null;
  registration_date: string;
  last_activity: string;
  download_count: number;
  is_banned: number;
}

export function createOrUpdateUser(
  telegramId: number,
  username: string | null,
  firstName: string | null
): User {
  const now = new Date().toISOString();
  const existing = getOne<User>("SELECT * FROM users WHERE id = ?", [telegramId]);

  if (existing) {
    runQuery(
      `UPDATE users SET username = ?, first_name = ?, last_activity = ? WHERE id = ?`,
      [username, firstName, now, telegramId]
    );
    return { ...existing, username, first_name: firstName, last_activity: now };
  }

  runQuery(
    `INSERT INTO users (id, username, first_name, registration_date, last_activity) VALUES (?, ?, ?, ?, ?)`,
    [telegramId, username, firstName, now, now]
  );

  return {
    id: telegramId,
    username,
    first_name: firstName,
    registration_date: now,
    last_activity: now,
    download_count: 0,
    is_banned: 0,
  };
}

export function getUser(telegramId: number): User | undefined {
  return getOne<User>("SELECT * FROM users WHERE id = ?", [telegramId]);
}

export function incrementDownloadCount(userId: number): void {
  runQuery(
    `UPDATE users SET download_count = download_count + 1, last_activity = ? WHERE id = ?`,
    [new Date().toISOString(), userId]
  );
}

export function banUser(telegramId: number): void {
  runQuery("UPDATE users SET is_banned = 1 WHERE id = ?", [telegramId]);
}

export function unbanUser(telegramId: number): void {
  runQuery("UPDATE users SET is_banned = 0 WHERE id = ?", [telegramId]);
}

export function getAllUsers(limit: number, offset: number): User[] {
  return getAll<User>(
    "SELECT * FROM users ORDER BY registration_date DESC LIMIT ? OFFSET ?",
    [limit, offset]
  );
}

export function getUserCount(): number {
  const row = getOne<{ count: number }>("SELECT COUNT(*) as count FROM users");
  return row?.count ?? 0;
}
