import initSqlJs, { Database as SqlJsDatabase } from "sql.js";
import fs from "fs";
import path from "path";
import { config } from "../config.js";
import { logger } from "../utils/logger.js";

let db: SqlJsDatabase;

export async function initDatabase(): Promise<void> {
  const dir = path.dirname(config.dbPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(config.tempDir)) {
    fs.mkdirSync(config.tempDir, { recursive: true });
  }
  if (!fs.existsSync(config.cacheDir)) {
    fs.mkdirSync(config.cacheDir, { recursive: true });
  }

  const SQL = await initSqlJs();

  if (fs.existsSync(config.dbPath)) {
    const buffer = fs.readFileSync(config.dbPath);
    db = new SQL.Database(buffer);
  } else {
    db = new SQL.Database();
  }

  db.run("PRAGMA foreign_keys = ON");
  runMigrations();
  saveDatabase();
  logger.info({ dbPath: config.dbPath }, "Database initialized");

  setInterval(() => saveDatabase(), 30_000);
}

function runMigrations(): void {
  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY,
      username TEXT,
      first_name TEXT,
      registration_date TEXT NOT NULL,
      last_activity TEXT NOT NULL,
      download_count INTEGER DEFAULT 0,
      is_banned INTEGER DEFAULT 0
    )
  `);
  db.run(`
    CREATE TABLE IF NOT EXISTS downloads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      url TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      file_path TEXT,
      file_size INTEGER,
      duration INTEGER,
      error_message TEXT,
      created_at TEXT NOT NULL,
      completed_at TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id)
    )
  `);
  db.run("CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id)");
  db.run("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)");

  db.run(`
    CREATE TABLE IF NOT EXISTS cache (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      video_id TEXT NOT NULL UNIQUE,
      file_path TEXT NOT NULL,
      file_size INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      last_used TEXT NOT NULL,
      hit_count INTEGER DEFAULT 1
    )
  `);
  db.run("CREATE INDEX IF NOT EXISTS idx_cache_video_id ON cache(video_id)");
}

export function saveDatabase(): void {
  if (!db) return;
  try {
    const data = db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(config.dbPath, buffer);
  } catch (err) {
    logger.error({ err }, "Failed to save database");
  }
}

export function getDb(): SqlJsDatabase {
  if (!db) throw new Error("Database not initialized. Call initDatabase() first.");
  return db;
}

export function runQuery(
  sql: string,
  params?: (string | number | null)[]
): void {
  try {
    if (params) {
      db.run(sql, params);
    } else {
      db.run(sql);
    }
  } catch (err) {
    logger.error({ err, sql }, "Database query failed");
    throw err;
  }
}

export function getOne<T>(sql: string, params?: (string | number | null)[]): T | undefined {
  const stmt = db.prepare(sql);
  try {
    if (params) stmt.bind(params);
    if (stmt.step()) {
      const row = stmt.getAsObject();
      return row as T;
    }
    return undefined;
  } finally {
    stmt.free();
  }
}

export function getAll<T>(sql: string, params?: (string | number | null)[]): T[] {
  const results: T[] = [];
  const stmt = db.prepare(sql);
  try {
    if (params) stmt.bind(params);
    while (stmt.step()) {
      results.push(stmt.getAsObject() as T);
    }
    return results;
  } finally {
    stmt.free();
  }
}
