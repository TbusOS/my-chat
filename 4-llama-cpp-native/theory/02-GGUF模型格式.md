# GGUF 模型格式

## 本章目标

理解 GGUF 格式：
1. 什么是 GGUF
2. 文件结构
3. Tensor 存储
4. 使用方法

---

## 1.1 什么是 GGUF？

### 1.1.1 GGUF 介绍

**GGUF** (GPT-Generated Unified Format)：
- llama.cpp 推出的模型格式
- 替代旧的 GGML 格式
- 支持量化

### 1.1.2 特点

- 单文件存储
- 支持多种量化
- 高效加载

---

## 1.2 文件结构

```
┌─────────────────────┐
│ Header              │  Magic, version, metadata
├─────────────────────┤
│ Vocabulary          │  Token 列表
├─────────────────────┤
│ Tensor Info         │  名称, 形状, 类型, 偏移
├─────────────────────┤
│ Tensor Data         │  实际权重数据
└─────────────────────┘
```

### 1.2.1 Header

```c
// GGUF 头
struct gguf_header {
    uint32_t magic;        // "GGUF"
    uint32_t version;      // 版本号
    uint64_t n_tensors;   // Tensor 数量
    uint64_t n_kv;        // 键值对数量
};
```

---

## 1.3 Tensor 信息

### 1.3.1 元数据

每个 Tensor 包含：
- 名称
- 形状 (n_dims)
- 各维度大小
- 类型 (fp32, q4_0, q4_1, etc.)
- 偏移量

### 1.3.2 查看模型结构

```bash
# 使用 llama.cpp 工具
./build/bin/llama-gguf -i model.gguf --verbose
```

---

## 1.4 量化类型

| 类型 | 位宽 | 精度 |
|------|------|------|
| F16 | 16 | 原始 |
| Q8_0 | 8 | 高 |
| Q6_K | 6 | 中 |
| Q5_K | 5 | 中 |
| Q4_K | 4 | 低 |
| Q3_K | 3 | 很低 |

---

## 1.5 使用方法

### 1.5.1 加载模型

```c
struct gguf_context * ctx = gguf_init_from_file("model.gguf", NULL);
```

### 1.5.2 读取 Tensor

```c
const char *name = "model.embeddings.weight";
struct ggml_tensor * tensor = ggml_get_tensor(ctx->graph, name);

// 读取数据
float * data = (float *) tensor->data;
```

---

## 1.6 本章小结

- ✅ GGUF 简介
- ✅ 文件结构
- ✅ Tensor 信息
- ✅ 量化类型
