import { Database } from "bun:sqlite";
import { mkdirSync, existsSync } from "fs";
import { join } from "path";
import type { Memory, MemoryCategory, MemorySource } from "./types.js";

const MEMORY_DIR = process.env.MEMORY_DIR || join(process.env.HOME!, ".cursor", "memory");
const PROJECTS_DIR = join(MEMORY_DIR, "projects");

function ensureDirs() {
  if (!existsSync(MEMORY_DIR)) mkdirSync(MEMORY_DIR, { recursive: true });
  if (!existsSync(PROJECTS_DIR)) mkdirSync(PROJECTS_DIR, { recursive: true });
}

function initDb(db: Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS memories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT NOT NULL,
      category TEXT DEFAULT 'general',
      tags TEXT,
      importance INTEGER DEFAULT 5,
      source TEXT DEFAULT 'auto',
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now')),
      access_count INTEGER DEFAULT 0
    );
  `);

  const hasFts = db
    .query("SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'")
    .get();

  if (!hasFts) {
    db.exec(`
      CREATE VIRTUAL TABLE memories_fts USING fts5(
        content, category, tags,
        content=memories, content_rowid=id
      );

      -- Triggers to keep FTS in sync
      CREATE TRIGGER memories_ai AFTER INSERT ON memories BEGIN
        INSERT INTO memories_fts(rowid, content, category, tags)
        VALUES (new.id, new.content, new.category, new.tags);
      END;

      CREATE TRIGGER memories_ad AFTER DELETE ON memories BEGIN
        INSERT INTO memories_fts(memories_fts, rowid, content, category, tags)
        VALUES ('delete', old.id, old.content, old.category, old.tags);
      END;

      CREATE TRIGGER memories_au AFTER UPDATE ON memories BEGIN
        INSERT INTO memories_fts(memories_fts, rowid, content, category, tags)
        VALUES ('delete', old.id, old.content, old.category, old.tags);
        INSERT INTO memories_fts(rowid, content, category, tags)
        VALUES (new.id, new.content, new.category, new.tags);
      END;
    `);
  }
}

const dbCache = new Map<string, Database>();

function getDb(path: string): Database {
  let db = dbCache.get(path);
  if (!db) {
    db = new Database(path);
    db.exec("PRAGMA journal_mode=WAL");
    initDb(db);
    dbCache.set(path, db);
  }
  return db;
}

export function globalDb(): Database {
  ensureDirs();
  return getDb(join(MEMORY_DIR, "global.db"));
}

export function projectDb(projectName: string): Database {
  ensureDirs();
  const safeName = projectName.replace(/[^a-zA-Z0-9_-]/g, "_");
  return getDb(join(PROJECTS_DIR, `${safeName}.db`));
}

export function addMemory(
  db: Database,
  content: string,
  category: MemoryCategory = "general",
  tags: string | null = null,
  importance: number = 5,
  source: MemorySource = "auto"
): Memory {
  const existing = searchMemories(db, content, undefined, 1);
  if (existing.length > 0) {
    const similarity = contentOverlap(existing[0].content, content);
    if (similarity > 0.8) {
      return updateMemory(db, existing[0].id, content, category, tags, importance);
    }
  }

  const stmt = db.prepare(`
    INSERT INTO memories (content, category, tags, importance, source)
    VALUES (?, ?, ?, ?, ?)
  `);
  const result = stmt.run(content, category, tags, importance, source);
  const row = db.query("SELECT last_insert_rowid() as id").get() as { id: number };
  const id = row.id;
  return db.query("SELECT * FROM memories WHERE id = ?").get(id) as Memory;
}

export function searchMemories(
  db: Database,
  query: string,
  category?: MemoryCategory,
  limit: number = 20
): Memory[] {
  const trimmed = query.trim();
  if (!trimmed) return listMemories(db, category, limit);

  const hasChinese = /[\u4e00-\u9fff]/.test(trimmed);

  if (hasChinese) {
    return searchByLike(db, trimmed, category, limit);
  }

  const ftsQuery = trimmed
    .replace(/[^\w\s]/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => `"${t}"`)
    .join(" OR ");

  if (!ftsQuery) return searchByLike(db, trimmed, category, limit);

  try {
    let sql = `
      SELECT m.*, bm25(memories_fts) as rank
      FROM memories_fts fts
      JOIN memories m ON m.id = fts.rowid
      WHERE memories_fts MATCH ?
    `;
    const params: (string | number)[] = [ftsQuery];

    if (category) {
      sql += " AND m.category = ?";
      params.push(category);
    }

    sql += " ORDER BY rank LIMIT ?";
    params.push(limit);

    const results = db.query(sql).all(...params) as Memory[];
    if (results.length > 0) return results;
    return searchByLike(db, trimmed, category, limit);
  } catch {
    return searchByLike(db, trimmed, category, limit);
  }
}

function searchByLike(
  db: Database,
  query: string,
  category?: MemoryCategory,
  limit: number = 20
): Memory[] {
  const keywords = extractKeywords(query);
  if (keywords.length === 0) return listMemories(db, category, limit);

  const conditions = keywords.map(() =>
    "(content LIKE ? OR tags LIKE ? OR category LIKE ?)"
  );
  let sql = `SELECT * FROM memories WHERE (${conditions.join(" OR ")})`;
  const params: (string | number)[] = [];

  for (const kw of keywords) {
    const like = `%${kw}%`;
    params.push(like, like, like);
  }

  if (category) {
    sql += " AND category = ?";
    params.push(category);
  }

  sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?";
  params.push(limit);

  return db.query(sql).all(...params) as Memory[];
}

function extractKeywords(text: string): string[] {
  const cjkChunks = text.match(/[\u4e00-\u9fff]+/g) || [];
  const latinWords = text
    .replace(/[\u4e00-\u9fff]+/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 1);

  const keywords: string[] = [...latinWords];

  for (const chunk of cjkChunks) {
    keywords.push(chunk);
    if (chunk.length > 2) {
      for (let i = 0; i <= chunk.length - 2; i++) {
        keywords.push(chunk.slice(i, i + 2));
      }
    }
  }

  return [...new Set(keywords)];
}

export function listMemories(
  db: Database,
  category?: MemoryCategory,
  limit: number = 20
): Memory[] {
  let sql = "SELECT * FROM memories";
  const params: (string | number)[] = [];

  if (category) {
    sql += " WHERE category = ?";
    params.push(category);
  }

  sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?";
  params.push(limit);

  return db.query(sql).all(...params) as Memory[];
}

export function updateMemory(
  db: Database,
  id: number,
  content?: string,
  category?: MemoryCategory,
  tags?: string | null,
  importance?: number
): Memory {
  const current = db.query("SELECT * FROM memories WHERE id = ?").get(id) as Memory | null;
  if (!current) throw new Error(`Memory with id ${id} not found`);

  db.query(`
    UPDATE memories SET
      content = ?,
      category = ?,
      tags = ?,
      importance = ?,
      updated_at = datetime('now')
    WHERE id = ?
  `).run(
    content ?? current.content,
    category ?? current.category,
    tags !== undefined ? tags : current.tags,
    importance ?? current.importance,
    id
  );

  return db.query("SELECT * FROM memories WHERE id = ?").get(id) as Memory;
}

export function deleteMemory(db: Database, id: number): boolean {
  const result = db.query("DELETE FROM memories WHERE id = ?").run(id);
  return result.changes > 0;
}

export function getContext(
  projectName: string,
  limit: number = 30
): Memory[] {
  const gDb = globalDb();
  const pDb = projectDb(projectName);

  const globalMemories = gDb.query(`
    SELECT *, 'global' as scope FROM memories
    ORDER BY
      importance * (1.0 / (1 + (julianday('now') - julianday(updated_at)))) DESC
    LIMIT ?
  `).all(Math.ceil(limit / 2)) as (Memory & { scope: string })[];

  const projectMemories = pDb.query(`
    SELECT *, 'project' as scope FROM memories
    ORDER BY
      importance * (1.0 / (1 + (julianday('now') - julianday(updated_at)))) DESC
    LIMIT ?
  `).all(Math.ceil(limit / 2)) as (Memory & { scope: string })[];

  const all = [...projectMemories, ...globalMemories];

  all.sort((a, b) => {
    const scoreA = a.importance * recencyWeight(a.updated_at);
    const scoreB = b.importance * recencyWeight(b.updated_at);
    return scoreB - scoreA;
  });

  const ids = all.slice(0, limit);

  for (const m of ids) {
    const target = (m as any).scope === "global" ? gDb : pDb;
    target.query("UPDATE memories SET access_count = access_count + 1 WHERE id = ?").run(m.id);
  }

  return ids;
}

function recencyWeight(dateStr: string): number {
  const daysAgo = (Date.now() - new Date(dateStr + "Z").getTime()) / 86400000;
  return 1 / (1 + daysAgo * 0.1);
}

function contentOverlap(a: string, b: string): number {
  const setA = new Set(a.split(/\s+/));
  const setB = new Set(b.split(/\s+/));
  let overlap = 0;
  for (const w of setA) if (setB.has(w)) overlap++;
  return (2 * overlap) / (setA.size + setB.size);
}

export function closeAll() {
  for (const db of dbCache.values()) db.close();
  dbCache.clear();
}
