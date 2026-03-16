# 使用说明

## 一键安装（推荐）

```bash
cd 20-cursor-memory-server

# 查看帮助
bash install.sh help

# 全部搞定：MCP Server + 为指定项目添加记忆规则
bash install.sh all /path/to/your-project
```

也可以分步执行：

```bash
# 第一步：全局安装（检查 Bun、安装依赖、验证 Server、写入 MCP 配置）
bash install.sh global

# 第二步：为某个项目启用记忆（创建 .cursor/rules/memory-auto.md）
bash install.sh project /path/to/my-app
bash install.sh project /path/to/another-app   # 可以给多个项目分别启用
bash install.sh project .                       # 或用 . 表示当前目录
```

安装完成后**重启 Cursor** 即可使用。

---

## 环境依赖

### macOS

```bash
# 安装 Bun
curl -fsSL https://bun.sh/install | bash

# 验证
bun --version   # 需要 >= 1.0.0
```

系统要求：
- macOS 12 (Monterey) 或更高版本
- Apple Silicon (M1/M2/M3/M4) 或 Intel x86_64
- Cursor IDE 已安装

### Linux

```bash
# 安装 Bun
curl -fsSL https://bun.sh/install | bash

# 验证
bun --version   # 需要 >= 1.0.0
```

系统要求：
- Linux kernel 5.6 或更高（需要 io_uring 支持）
- glibc >= 2.27（Ubuntu 18.04+、Debian 10+、CentOS 8+、Fedora 28+）
- x86_64 或 aarch64 架构
- Cursor IDE 已安装

### Windows (WSL2)

```bash
# 在 WSL2 中安装 Bun
curl -fsSL https://bun.sh/install | bash
```

原生 Windows 暂不支持（Bun 的 Windows 支持仍在完善中），建议使用 WSL2。

### 关于 SQLite

**无需单独安装**。Bun 内置了 `bun:sqlite` 模块，包含完整的 SQLite 引擎和 FTS5 扩展，不需要系统级的 sqlite3 包。

---

## 安装配置

### 第一步：安装项目依赖

```bash
cd 20-cursor-memory-server
bun install
```

### 第二步：验证服务器启动

```bash
bun run src/index.ts
```

正常情况下会在 stderr 输出 `cursor-memory MCP server running on stdio`，按 `Ctrl+C` 退出。

如果报错，检查：
- Bun 版本是否 >= 1.0.0
- 是否在正确的目录下执行了 `bun install`

### 第三步：确认 MCP 注册

检查 `~/.cursor/mcp.json` 中是否包含 memory server 的配置：

```json
{
  "mcpServers": {
    "memory": {
      "command": "bun",
      "args": ["run", "/你的绝对路径/20-cursor-memory-server/src/index.ts"],
      "env": {
        "MEMORY_DIR": "/你的用户目录/.cursor/memory"
      }
    }
  }
}
```

注意事项：
- `args` 中的路径必须是**绝对路径**，不支持 `~` 或相对路径
- `MEMORY_DIR` 指定数据库文件存储位置，默认 `~/.cursor/memory`
- 如果文件中已有其他 MCP server 配置（如 playwright），在 `mcpServers` 对象中追加即可

### 第四步：确认 Cursor Rule

检查项目根目录下是否存在 `.cursor/rules/memory-auto.md`。这个文件指导 AI 在对话中自动保存和召回记忆。

关键配置：文件 frontmatter 中的 `alwaysApply: true` 确保每次对话都生效。

### 第五步：重启 Cursor

重启 Cursor IDE 使 MCP 配置生效。重启后 Cursor 会自动以子进程方式启动 Memory Server。

---

## 使用方式

### 自动模式（零操作）

配置完成后，一切自动运行：

1. **每次新对话**：AI 自动调用 `memory_get_context`，召回之前保存的记忆
2. **对话过程中**：AI 检测到重要信息时自动保存，你无需说任何特殊指令
3. **跨对话/跨重启**：记忆持久化在 SQLite 中，重启 Cursor 不会丢失

AI 会自动识别并保存以下类型的信息：

| 类型 | 示例 |
|------|------|
| 技术决策 | "我们决定用 PostgreSQL 而不是 MySQL" |
| 架构设计 | "API 层使用 REST，前端 React + Next.js" |
| 用户偏好 | "我喜欢函数式风格" / "用中文回复" |
| 项目进展 | "登录功能已完成" / "数据库迁移完毕" |
| Bug 记录 | "FTS5 不支持中文分词，改用 LIKE 方案" |

### 手动控制

你也可以直接告诉 AI 做记忆操作：

**保存记忆：**
- "记住这个"
- "记住：我们的数据库密码策略是 bcrypt + salt"
- "remember this decision"

**查看记忆：**
- "列出所有记忆"
- "查看项目记忆"
- "看看全局记忆里有什么"

**搜索记忆：**
- "搜索关于数据库的记忆"
- "有没有关于 React 的记忆"

**删除记忆：**
- "忘掉这个"
- "删除记忆 #5"

**更新记忆：**
- "把记忆 #3 的重要性改为 9"
- "更新记忆 #7 的内容"

---

## 数据管理

### 数据存储位置

```
~/.cursor/memory/
├── global.db             # 全局记忆（所有项目共享）
└── projects/
    ├── my-chat.db        # my-chat 项目的记忆
    ├── web-app.db        # web-app 项目的记忆
    └── ...
```

- `global.db`：存储跨项目通用信息，如语言偏好、通用编码规范
- `projects/` 下的文件：每个项目独立一个数据库，项目名从当前工作目录自动检测

### 手动查看数据

每个 `.db` 文件都是标准 SQLite 数据库，可用任何 SQLite 工具查看：

```bash
# 查看全局记忆
sqlite3 ~/.cursor/memory/global.db \
  "SELECT id, category, importance, substr(content,1,60) FROM memories ORDER BY importance DESC;"

# 查看某项目的全部记忆
sqlite3 ~/.cursor/memory/projects/my-chat.db \
  "SELECT * FROM memories ORDER BY updated_at DESC;"

# 统计各分类记忆数量
sqlite3 ~/.cursor/memory/projects/my-chat.db \
  "SELECT category, count(*) FROM memories GROUP BY category;"
```

### 备份与迁移

```bash
# 备份整个记忆库
cp -r ~/.cursor/memory/ ~/memory-backup-$(date +%Y%m%d)/

# 迁移到新机器
scp -r ~/.cursor/memory/ newmachine:~/.cursor/memory/
```

### 清空记忆

```bash
# 清空所有记忆（全局 + 所有项目）
rm -rf ~/.cursor/memory/

# 只清空某个项目的记忆
rm ~/.cursor/memory/projects/my-chat.db

# 只清空全局记忆
rm ~/.cursor/memory/global.db
```

下次 MCP Server 启动时会自动重建空数据库。

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEMORY_DIR` | `~/.cursor/memory` | 数据库文件存储目录 |
| `PROJECT_NAME` | 自动检测（cwd 最后一段目录名） | 当前项目名称，决定使用哪个项目数据库 |

在 `~/.cursor/mcp.json` 的 `env` 字段中设置：

```json
{
  "env": {
    "MEMORY_DIR": "/custom/path/to/memory",
    "PROJECT_NAME": "my-project"
  }
}
```

一般情况下不需要手动设置 `PROJECT_NAME`，系统会从 Cursor 打开的项目目录自动检测。

---

## 故障排查

### MCP Server 未启动 / Cursor 中看不到记忆工具

**检查 MCP 配置路径：**
```bash
cat ~/.cursor/mcp.json
```
确认 `args` 中的路径是正确的绝对路径。

**手动测试启动：**
```bash
bun run /你的路径/20-cursor-memory-server/src/index.ts
```
应输出 `cursor-memory MCP server running on stdio`。如果报错，根据错误信息排查。

**检查 Bun 安装：**
```bash
which bun && bun --version
```

### 记忆未自动保存

- 确认 `.cursor/rules/memory-auto.md` 文件存在
- 确认文件 frontmatter 中有 `alwaysApply: true`
- 在对话中直接问 AI："你能看到 memory 相关的 MCP 工具吗？" 来验证工具是否可用

### 中文搜索无结果

系统对中文使用 LIKE 模糊匹配（而非 FTS5）。如果搜索无结果：
- 尝试更短的关键词（如"数据库"而不是"数据库连接池配置优化"）
- 尝试用 `memory_list` 浏览所有记忆，确认数据确实存在

### 数据库损坏

极少见，但如果发生：
```bash
# 检查数据库完整性
sqlite3 ~/.cursor/memory/global.db "PRAGMA integrity_check;"

# 如果返回非 "ok"，删除并重建
rm ~/.cursor/memory/global.db
```

### 重启 Cursor 后记忆丢失

记忆不会丢失，但如果 MCP Server 未启动，AI 无法调用记忆工具。检查 Cursor 的 MCP 日志或按上述步骤验证 Server 是否正常启动。
