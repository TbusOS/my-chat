# Cursor Memory Server

基于 MCP（Model Context Protocol）的 Cursor IDE 持久化记忆系统。让 AI 在跨对话、跨会话中保持上下文记忆，实现类似 Claude Memory 的体验。

## 核心能力

- 跨对话持久化记忆：重启 Cursor、新开对话，AI 自动召回之前的上下文
- 双层记忆架构：全局记忆（跨项目共享）+ 项目记忆（项目独立隔离）
- 混合保存模式：AI 自动判断 + 用户手动控制（"记住这个"/"忘掉这个"）
- 智能搜索：英文 FTS5 全文搜索 + 中文 bigram LIKE 双策略
- 自动去重：新记忆与已有记忆相似度 > 80% 时自动合并更新
- 加权召回：按 `importance * recencyWeight` 排序，重要且新鲜的记忆优先

## 文档

- [使用说明](docs/usage-guide.md) — 环境依赖、安装配置、使用方式、故障排查
- [技术实现原理](docs/technical-design.md) — 系统架构、数据库设计、搜索算法、召回机制

## 项目结构

```
20-cursor-memory-server/
├── src/
│   ├── index.ts       # MCP 服务器入口 + 6 个工具注册
│   ├── store.ts       # SQLite 存储层（FTS5 + LIKE 双搜索引擎）
│   └── types.ts       # TypeScript 类型定义
├── docs/
│   ├── usage-guide.md       # 使用说明
│   └── technical-design.md  # 技术实现原理
├── package.json
├── tsconfig.json
└── README.md
```

## 快速开始

```bash
cd 20-cursor-memory-server

bash install.sh help                        # 查看帮助
bash install.sh all /path/to/your-project   # 全部搞定：MCP Server + 项目规则
bash install.sh global                      # 或只装全局 MCP Server
bash install.sh project /path/to/project    # 单独给某个项目启用记忆
```

然后重启 Cursor，开始对话即可。详细步骤见 [使用说明](docs/usage-guide.md)。
