# 技术实现原理

## 系统架构

```
┌────────────────────────────────────────────────────────┐
│                    Cursor IDE                          │
│                                                        │
│  ┌──────────┐    stdio     ┌───────────────────────┐  │
│  │  AI Chat  │◄───────────►│  MCP Memory Server    │  │
│  │  (Agent)  │  JSON-RPC   │  (Bun + TypeScript)   │  │
│  └──────────┘              └───────────┬───────────┘  │
│       ▲                                │              │
│       │                        ┌───────┴───────┐      │
│  .cursor/rules/                │               │      │
│  memory-auto.md          ┌────┴────┐    ┌─────┴───┐  │
│  (行为指令)               │global.db│    │project/ │  │
│                          │(全局记忆)│    │ *.db    │  │
│                          └─────────┘    │(项目记忆)│  │
│                                         └─────────┘  │
│                          ~/.cursor/memory/            │
└────────────────────────────────────────────────────────┘
```

### 通信链路

1. Cursor 启动时根据 `~/.cursor/mcp.json` 的配置，以子进程方式启动 Memory Server
2. AI Agent 与 Memory Server 之间通过 **stdio**（标准输入/输出）进行 **JSON-RPC 2.0** 通信
3. `.cursor/rules/memory-auto.md` 作为 Cursor Rule 在每次对话时自动注入 AI 的 system prompt，指导 AI 何时调用记忆工具

### 组件职责

| 组件 | 文件 | 职责 |
|------|------|------|
| MCP 服务器 | `src/index.ts` | 注册 6 个 MCP 工具，接收 JSON-RPC 请求，参数校验（Zod），路由到存储层 |
| 存储层 | `src/store.ts` | SQLite 数据库管理（连接池缓存、WAL 模式）、FTS5 全文索引、CRUD 操作、搜索策略、去重逻辑 |
| 类型定义 | `src/types.ts` | Memory、MemoryCategory、MemoryScope、MemorySource 等 TypeScript 类型 |
| 行为指令 | `.cursor/rules/memory-auto.md` | 指导 AI 自动保存/召回的行为规范：何时保存、如何分类、重要性评估标准 |
| MCP 配置 | `~/.cursor/mcp.json` | 向 Cursor 注册 Memory Server 的启动命令、参数、环境变量 |

---

## 技术选型

| 技术 | 选择 | 为什么不选其他方案 |
|------|------|-------------------|
| 运行时 | **Bun** | 原生 TypeScript 执行（无需 tsc/tsx 编译步骤）；内置 `bun:sqlite`（无需编译 better-sqlite3 原生模块）；冷启动 < 100ms（MCP 子进程场景关键指标）。Node.js 需要额外的 tsx 或编译步骤，better-sqlite3 在部分系统上编译失败率高 |
| 存储 | **SQLite + FTS5** | 嵌入式零运维（无需启动数据库服务）；单文件数据库便于备份迁移；WAL 模式支持并发读写；FTS5 内置全文搜索无需外部依赖。Redis 需要额外进程；ChromaDB/FAISS 对"记忆"场景过重；JSON 文件无搜索能力 |
| 协议 | **MCP over stdio** | Cursor 原生支持的标准协议；子进程模式由 Cursor 自动管理生命周期；无需额外网络端口 |
| 参数校验 | **Zod** | MCP SDK 内置 Zod 依赖，零额外成本；自动生成 JSON Schema 供客户端展示工具描述 |

---

## 数据库设计

### 双库架构

```
~/.cursor/memory/
├── global.db             # 全局记忆库（跨所有项目共享）
└── projects/
    ├── my-chat.db        # my-chat 项目记忆
    ├── web-app.db        # web-app 项目记忆
    └── ...
```

- **全局库**（global.db）：存储用户偏好、通用编码规范等跨项目通用信息
- **项目库**（projects/*.db）：存储项目特定的架构决策、进展、Bug 等信息
- 项目名自动检测：优先使用 `PROJECT_NAME` 环境变量，否则取 `process.cwd()` 的最后一段路径
- 项目名安全化：`replace(/[^a-zA-Z0-9_-]/g, "_")` 确保文件名合法

### 连接管理

```typescript
const dbCache = new Map<string, Database>();
```

- 使用 Map 缓存数据库连接，避免重复打开
- 每个数据库首次打开时执行 `PRAGMA journal_mode=WAL`（Write-Ahead Logging），提高并发性能
- 进程退出时（SIGINT/SIGTERM）遍历缓存逐一关闭连接

### 表结构

```sql
CREATE TABLE memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL,          -- 记忆正文
  category TEXT DEFAULT 'general', -- 分类：decision/architecture/preference/progress/bug/general
  tags TEXT,                       -- 逗号分隔的标签，用于辅助搜索
  importance INTEGER DEFAULT 5,    -- 重要性 1-10，影响召回优先级
  source TEXT DEFAULT 'auto',      -- 来源：auto（AI 自动保存）/ manual（用户主动要求）
  created_at TEXT DEFAULT (datetime('now')),  -- 创建时间 UTC
  updated_at TEXT DEFAULT (datetime('now')),  -- 最后更新时间 UTC
  access_count INTEGER DEFAULT 0   -- 被召回次数，统计热度
);
```

### FTS5 全文索引

```sql
CREATE VIRTUAL TABLE memories_fts USING fts5(
  content, category, tags,
  content=memories, content_rowid=id
);
```

FTS5 虚拟表通过三个触发器与主表保持同步：

- `memories_ai`（AFTER INSERT）：插入新记忆时同步到 FTS 索引
- `memories_ad`（AFTER DELETE）：删除记忆时从 FTS 索引中移除
- `memories_au`（AFTER UPDATE）：更新记忆时先删后插刷新 FTS 索引

---

## 搜索引擎

系统实现了双搜索引擎，根据查询内容自动选择最优策略。

### 引擎一：FTS5 全文搜索（英文）

适用条件：查询文本不包含 CJK 字符（`/[\u4e00-\u9fff]/` 检测）。

**流程：**

1. 清除特殊字符，按空格分词
2. 每个 token 加引号后用 `OR` 连接：`"React" OR "Next" OR "js"`
3. 执行 FTS5 MATCH 查询，使用 `bm25()` 函数做相关性排序
4. 如果 FTS5 无结果，自动回退到 LIKE 搜索

```sql
SELECT m.*, bm25(memories_fts) as rank
FROM memories_fts fts
JOIN memories m ON m.id = fts.rowid
WHERE memories_fts MATCH '"React" OR "Next"'
ORDER BY rank
LIMIT 20;
```

### 引擎二：Bigram LIKE 搜索（中文）

适用条件：查询文本包含中文字符。

**分词策略（`extractKeywords` 函数）：**

1. 提取完整的中文连续片段（正则 `/[\u4e00-\u9fff]+/g`）
2. 对长度 > 2 的片段，生成二字滑动窗口（bigram）
3. 提取拉丁字母单词（长度 > 1）
4. 去重后得到关键词列表

示例：`"大模型训练方案"` 分词结果 →
- 完整片段：`大模型训练方案`
- Bigram：`大模`, `模型`, `型训`, `训练`, `练方`, `方案`

```sql
SELECT * FROM memories
WHERE (content LIKE '%大模型训练方案%' OR content LIKE '%大模%' OR content LIKE '%模型%' ...)
ORDER BY importance DESC, updated_at DESC
LIMIT 20;
```

### 为什么不对中文用 FTS5？

SQLite FTS5 的默认分词器（unicode61）不支持中文分词。中文没有空格分隔，整句话会被当作一个 token 处理，导致部分匹配查询无法命中。要正确支持中文 FTS5 需要外部分词库（如 jieba），会引入重量级依赖。Bigram LIKE 方案在记忆量级（通常 < 10000 条）下性能完全够用，实现简单且无外部依赖。

---

## 记忆召回算法

`memory_get_context` 是系统的核心功能，在每次对话开始时被调用。

### 流程

1. 分别从 global.db 和 project.db 各取 `ceil(limit/2)` 条记忆
2. 数据库层排序使用 SQL 内置计算：`importance * (1.0 / (1 + (julianday('now') - julianday(updated_at))))`
3. 合并两个来源的结果
4. 在应用层按 `importance * recencyWeight` 重新排序
5. 取 top N 结果
6. 更新被召回记忆的 `access_count += 1`

### 衰减函数

```
recencyWeight(updated_at) = 1 / (1 + daysAgo * 0.1)
```

| 时间距离 | recencyWeight | importance=10 的 score | importance=3 的 score |
|---------|---------------|----------------------|---------------------|
| 今天 | 1.00 | 10.0 | 3.0 |
| 1 天前 | 0.91 | 9.1 | 2.7 |
| 7 天前 | 0.59 | 5.9 | 1.8 |
| 30 天前 | 0.25 | 2.5 | 0.75 |
| 100 天前 | 0.09 | 0.9 | 0.27 |

关键特性：**高重要性记忆衰减缓慢**。importance=10 的百天前记忆（score=0.9）仍然优于 importance=1 的今天记忆（score=1.0）。这确保了关键架构决策不会因为时间流逝而被遗忘。

### 为什么不用访问计数排序？

`access_count` 目前仅用于统计，不参与排序。原因：
- 被频繁召回的记忆不一定是最重要的，可能只是因为关键词匹配度高
- 热度排序会导致马太效应——被召回的越多排名越高，新记忆永远排不上来
- `importance * recencyWeight` 更符合人类记忆模型：重要的事记得久，不重要的渐渐淡忘

---

## 去重机制

每次调用 `memory_add` 时，在实际插入前执行去重检查。

### 流程

1. 用新记忆的 content 作为查询，搜索现有记忆（取 top 1）
2. 计算新记忆与最相似已有记忆的 **Dice 系数**：

```
overlap = 2 * |intersection(wordsA, wordsB)| / (|wordsA| + |wordsB|)
```

3. 如果 overlap > 0.8（80% 相似），则**更新**已有记忆而非新建
4. 如果 overlap <= 0.8，正常插入新记忆

### 示例

已有记忆：`"决定使用 PostgreSQL 作为主数据库"`
新记忆：`"决定使用 PostgreSQL 作为主数据库，版本 16"`

Dice 系数计算：
- wordsA = {"决定", "使用", "PostgreSQL", "作为", "主数据库"}
- wordsB = {"决定", "使用", "PostgreSQL", "作为", "主数据库，版本", "16"}
- intersection = {"决定", "使用", "PostgreSQL", "作为"} = 4
- overlap = 2 * 4 / (5 + 6) ≈ 0.73 < 0.8 → **新建**

这是一个有意的设计：当新内容有实质性新增信息时（如添加了版本号），系统倾向于保存为新记忆而非覆盖。

---

## MCP 工具设计

### 工具注册

使用 `@modelcontextprotocol/sdk` 的 `McpServer.tool()` 方法注册工具，每个工具包含：

- **名称**：MCP 工具标识符（如 `memory_add`）
- **描述**：自然语言描述，帮助 AI 理解何时该调用此工具
- **参数 Schema**：使用 Zod 定义，SDK 自动转换为 JSON Schema
- **处理函数**：接收校验后的参数，返回 `CallToolResult`

### 6 个工具概览

| 工具 | 读/写 | 核心逻辑 |
|------|-------|---------|
| `memory_add` | 写 | 去重检查 → 插入或更新 → 返回保存结果 |
| `memory_search` | 读 | 语言检测 → FTS5/LIKE 双引擎搜索 → 合并多库结果 |
| `memory_list` | 读 | 按 importance DESC, updated_at DESC 排序 → 合并多库结果 |
| `memory_update` | 写 | 查找 → 部分更新（未提供的字段保持原值）→ 触发器同步 FTS |
| `memory_delete` | 写 | DELETE → 触发器自动清理 FTS 索引 |
| `memory_get_context` | 读 | 双库查询 → 加权排序 → 更新 access_count → 返回 top N |

### 参数校验

所有工具参数使用 Zod Schema 定义，SDK 自动完成：
- 类型校验（string、number、enum）
- 范围约束（importance: min 1, max 10）
- 可选参数处理（optional + 默认值回退）
- JSON Schema 生成（供 Cursor 展示工具描述）

---

## Cursor Rule 行为指令

`.cursor/rules/memory-auto.md` 的 frontmatter 设置 `alwaysApply: true`，确保每次对话都会注入。

指令将 AI 的记忆行为规范为三个阶段：

1. **对话初始化**：自动调用 `memory_get_context` 加载上下文
2. **对话过程中**：检测到决策/偏好/架构/进展/Bug 时自动 `memory_add`
3. **对话结束/用户指令**：响应"记住"/"忘掉"等手动控制指令

指令还定义了 scope 选择规则（全局 vs 项目）、importance 评估标准（1-10 对应的场景示例）、category 分类参考表，使 AI 的记忆保存行为一致且可预测。

---

## Token 效率设计

记忆系统的一个核心设计目标是**用尽可能少的 token 传递尽可能多的有效上下文**。以下是与其他方案的对比，以及本系统在各环节的 token 优化策略。

### 与其他方案的 token 消耗对比

| 方案 | 每次对话消耗的 token | 随时间增长 | 信息密度 |
|------|-------------------|----------|---------|
| **Cursor Rules 文件** | 整个文件全量加载 | 文件越大 token 越多，线性增长 | 中：混杂了规范和记忆 |
| **粘贴聊天历史** | 完整对话记录 | 极速膨胀，一次对话可达数千 token | 低：大量寒暄、重复、探索过程 |
| **Skills 系统** | 每个相关 Skill 文件全文 | 随 Skill 数量增长 | 中：Skill 模板结构占空间 |
| **本 MCP Memory** | 仅 top N 条精炼记忆 | 总量增长但每次只加载固定条数 | **高：每条都是提炼后的结论** |

### 为什么 token 消耗低

**1. 存结论，不存过程**

一次对话可能讨论了 30 分钟才决定用 PostgreSQL，产生数千 token 的对话内容。但记忆系统只存一句话：

```
"决定使用 PostgreSQL 而非 MySQL，原因：JSON 支持更好、扩展生态更丰富"
```

这一条记忆大约 30 个 token，而原始对话可能 3000+ token。**压缩比约 100:1**。

**2. 固定上限，不随时间膨胀**

`memory_get_context` 有 `limit` 参数（默认 30），无论你使用了多长时间、积累了多少记忆，每次对话开始时加载的 token 量是有上限的。

粗略估算：
- 每条记忆平均约 50 token（一句话 + 元数据格式）
- 30 条记忆 ≈ **1500 token**
- 相当于一页 A4 纸的文字量

对比：一个写了 200 行的 Cursor Rules 文件约 3000-5000 token，且每行都加载，无法筛选。

**3. 加权排序，优先加载高价值记忆**

不是随机加载 30 条，而是按 `importance * recencyWeight` 排序后取 top 30。效果：
- 重要决策（importance=9）即使是上个月的也会被召回
- 琐碎笔记（importance=2）几天后就自然排到 30 名开外，不再占用 token

**4. 按需搜索，不全量加载**

`memory_search` 只返回匹配的记忆，不会把整个数据库灌进上下文。例如 AI 需要回忆数据库相关决策时，只搜索并返回 2-3 条匹配记忆（约 100-150 token），而非加载全部 500 条记忆。

**5. 去重压缩，避免冗余**

同一个决策被反复提到时（比如多次对话都谈到"用 PostgreSQL"），去重机制确保只存一条记忆。没有去重的话，10 次对话下来可能存了 10 条几乎一样的记忆，浪费 10 倍 token。

### Token 消耗的量化估算

假设一个活跃项目使用 6 个月，每天 2 次有效对话：

| 指标 | 数值 |
|------|------|
| 累计记忆条数 | ~300-500 条 |
| 数据库大小 | ~100-200 KB |
| 每次对话加载的记忆 | 30 条（固定上限） |
| 每次对话的记忆 token | ~1500 token |
| 对话过程中保存记忆的 token | ~100 token（工具调用 + 返回） |
| **每次对话的总记忆开销** | **~1600 token** |

对比同样的信息量如果用 Cursor Rules 文件存储，300 条记忆约 15000 token，**每次对话全量加载**。MCP Memory 方案节省约 **90%** 的 token 消耗。

### 唯一的额外开销

MCP 工具调用本身有少量 token 成本：

| 开销来源 | 估算 |
|---------|------|
| 工具描述注入（6 个工具的 JSON Schema） | ~800 token（仅首次，Cursor 会缓存） |
| `memory_get_context` 调用 + 返回 | ~1500 token |
| `memory_add` 调用 + 返回（每次保存） | ~100 token |
| `.cursor/rules/memory-auto.md` 指令注入 | ~400 token |

总计每次对话约 **2800 token** 的记忆系统开销。作为参考，一次普通对话的总 token 消耗通常在 10000-50000 之间，记忆系统占比约 **5-25%**，换来的是完整的跨对话上下文保持能力。
