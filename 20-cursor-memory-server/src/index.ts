import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  globalDb,
  projectDb,
  addMemory,
  searchMemories,
  listMemories,
  updateMemory,
  deleteMemory,
  getContext,
  closeAll,
} from "./store.js";
import type { MemoryCategory, MemoryScope } from "./types.js";

const CATEGORY_VALUES = [
  "decision",
  "architecture",
  "preference",
  "progress",
  "bug",
  "general",
] as const;

const server = new McpServer({
  name: "cursor-memory",
  version: "1.0.0",
});

function resolveProjectName(): string {
  if (process.env.PROJECT_NAME) return process.env.PROJECT_NAME;
  const cwd = process.cwd();
  const parts = cwd.split("/").filter(Boolean);
  return parts[parts.length - 1] || "default";
}

function getTargetDb(scope: MemoryScope) {
  const projectName = resolveProjectName();
  if (scope === "global") return [globalDb()];
  if (scope === "project") return [projectDb(projectName)];
  return [globalDb(), projectDb(projectName)];
}

function formatMemory(m: any, scope?: string): string {
  const tag = scope ? `[${scope}]` : "";
  const tags = m.tags ? ` tags:${m.tags}` : "";
  return `${tag}[#${m.id}] (${m.category}, importance:${m.importance}${tags}) ${m.content} — ${m.updated_at}`;
}

// --- Tool: memory_add ---
server.tool(
  "memory_add",
  "Save a new memory. Use this to persist important decisions, preferences, architecture choices, progress notes, or bug records.",
  {
    content: z.string().describe("The memory content to save"),
    category: z
      .enum(CATEGORY_VALUES)
      .optional()
      .describe("Category: decision, architecture, preference, progress, bug, general"),
    tags: z.string().optional().describe("Comma-separated tags for this memory"),
    importance: z
      .number()
      .min(1)
      .max(10)
      .optional()
      .describe("Importance level 1-10 (default 5)"),
    scope: z
      .enum(["global", "project"])
      .optional()
      .describe("Where to save: 'global' (all projects) or 'project' (current project only). Default: project"),
    source: z
      .enum(["auto", "manual"])
      .optional()
      .describe("Whether this was auto-detected or manually requested"),
  },
  async (args) => {
    const scope = args.scope || "project";
    const db = scope === "global" ? globalDb() : projectDb(resolveProjectName());
    const memory = addMemory(
      db,
      args.content,
      (args.category as MemoryCategory) || "general",
      args.tags || null,
      args.importance || 5,
      args.source || "auto"
    );
    return {
      content: [
        {
          type: "text" as const,
          text: `Memory saved (${scope}): ${formatMemory(memory)}`,
        },
      ],
    };
  }
);

// --- Tool: memory_search ---
server.tool(
  "memory_search",
  "Search memories using full-text search. Returns the most relevant memories matching the query.",
  {
    query: z.string().describe("Search query (keywords or natural language)"),
    category: z.enum(CATEGORY_VALUES).optional().describe("Filter by category"),
    scope: z
      .enum(["global", "project", "both"])
      .optional()
      .describe("Search scope: global, project, or both (default: both)"),
    limit: z.number().min(1).max(50).optional().describe("Max results (default 20)"),
  },
  async (args) => {
    const scope = (args.scope as MemoryScope) || "both";
    const limit = args.limit || 20;
    const dbs = getTargetDb(scope);
    const results: string[] = [];

    for (const db of dbs) {
      const isGlobal = db === globalDb();
      const scopeLabel = isGlobal ? "global" : "project";
      const memories = searchMemories(
        db,
        args.query,
        args.category as MemoryCategory | undefined,
        limit
      );
      for (const m of memories) {
        results.push(formatMemory(m, scopeLabel));
      }
    }

    return {
      content: [
        {
          type: "text" as const,
          text: results.length > 0
            ? `Found ${results.length} memories:\n\n${results.join("\n")}`
            : "No memories found matching the query.",
        },
      ],
    };
  }
);

// --- Tool: memory_list ---
server.tool(
  "memory_list",
  "List memories sorted by importance and recency. Use to browse stored memories.",
  {
    category: z.enum(CATEGORY_VALUES).optional().describe("Filter by category"),
    scope: z
      .enum(["global", "project", "both"])
      .optional()
      .describe("List scope: global, project, or both (default: both)"),
    limit: z.number().min(1).max(50).optional().describe("Max results (default 20)"),
  },
  async (args) => {
    const scope = (args.scope as MemoryScope) || "both";
    const limit = args.limit || 20;
    const dbs = getTargetDb(scope);
    const results: string[] = [];

    for (const db of dbs) {
      const isGlobal = db === globalDb();
      const scopeLabel = isGlobal ? "global" : "project";
      const memories = listMemories(
        db,
        args.category as MemoryCategory | undefined,
        limit
      );
      for (const m of memories) {
        results.push(formatMemory(m, scopeLabel));
      }
    }

    return {
      content: [
        {
          type: "text" as const,
          text: results.length > 0
            ? `${results.length} memories:\n\n${results.join("\n")}`
            : "No memories stored yet.",
        },
      ],
    };
  }
);

// --- Tool: memory_delete ---
server.tool(
  "memory_delete",
  "Delete a memory by ID.",
  {
    id: z.number().describe("Memory ID to delete"),
    scope: z
      .enum(["global", "project"])
      .optional()
      .describe("Which database to delete from: global or project (default: project)"),
  },
  async (args) => {
    const scope = args.scope || "project";
    const db = scope === "global" ? globalDb() : projectDb(resolveProjectName());
    const deleted = deleteMemory(db, args.id);
    return {
      content: [
        {
          type: "text" as const,
          text: deleted
            ? `Memory #${args.id} deleted from ${scope} store.`
            : `Memory #${args.id} not found in ${scope} store.`,
        },
      ],
    };
  }
);

// --- Tool: memory_update ---
server.tool(
  "memory_update",
  "Update an existing memory's content, category, tags, or importance.",
  {
    id: z.number().describe("Memory ID to update"),
    content: z.string().optional().describe("New content"),
    category: z.enum(CATEGORY_VALUES).optional().describe("New category"),
    tags: z.string().optional().describe("New tags (comma-separated)"),
    importance: z.number().min(1).max(10).optional().describe("New importance level"),
    scope: z
      .enum(["global", "project"])
      .optional()
      .describe("Which database: global or project (default: project)"),
  },
  async (args) => {
    const scope = args.scope || "project";
    const db = scope === "global" ? globalDb() : projectDb(resolveProjectName());
    try {
      const memory = updateMemory(
        db,
        args.id,
        args.content,
        args.category as MemoryCategory | undefined,
        args.tags,
        args.importance
      );
      return {
        content: [
          {
            type: "text" as const,
            text: `Memory updated: ${formatMemory(memory, scope)}`,
          },
        ],
      };
    } catch (e: any) {
      return {
        content: [{ type: "text" as const, text: `Error: ${e.message}` }],
        isError: true,
      };
    }
  }
);

// --- Tool: memory_get_context ---
server.tool(
  "memory_get_context",
  "Retrieve relevant memories for the current project context. Call this at the start of a conversation to recall previous context. Returns a mix of global and project-specific memories ranked by importance and recency.",
  {
    project_name: z
      .string()
      .optional()
      .describe("Project name override (auto-detected if not provided)"),
    limit: z
      .number()
      .min(1)
      .max(100)
      .optional()
      .describe("Max memories to return (default 30)"),
  },
  async (args) => {
    const projectName = args.project_name || resolveProjectName();
    const limit = args.limit || 30;
    const memories = getContext(projectName, limit);

    if (memories.length === 0) {
      return {
        content: [
          {
            type: "text" as const,
            text: "No memories stored yet for this project or globally.",
          },
        ],
      };
    }

    const lines = memories.map((m: any) =>
      formatMemory(m, m.scope || "unknown")
    );

    return {
      content: [
        {
          type: "text" as const,
          text: `Recalled ${memories.length} memories:\n\n${lines.join("\n")}`,
        },
      ],
    };
  }
);

// --- Start server ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write("cursor-memory MCP server running on stdio\n");
}

process.on("SIGINT", () => {
  closeAll();
  process.exit(0);
});

process.on("SIGTERM", () => {
  closeAll();
  process.exit(0);
});

main().catch((err) => {
  process.stderr.write(`Fatal error: ${err}\n`);
  process.exit(1);
});
