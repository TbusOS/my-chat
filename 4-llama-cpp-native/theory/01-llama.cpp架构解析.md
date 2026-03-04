# llama.cpp 架构解析

## 目录

1. [架构概述](#1-架构概述)
2. [核心模块](#2-核心模块)
3. [推理流程](#3-推理流程)
4. [量化实现](#4-量化实现)

---

## 1. 架构概述

### 1.1 项目结构

```
llama.cpp/
├── ggml/              # 张量计算库
│   ├── src/ggml.c     # 核心实现
│   └── include/       # 头文件
├── src/               # 主程序
│   ├── llama.cpp      # 模型推理
│   ├── common.cpp     # 通用工具
│   └── main.cpp       # 命令行入口
├── examples/          # 示例
│   ├── chat.cpp       # 聊天示例
│   └── server.cpp     # HTTP 服务器
└── CMakeLists.txt    # 构建配置
```

---

## 2. 核心模块

### 2.1 GGML (张量库)

```c
// 张量结构
struct ggml_tensor {
    enum ggml_type type;    // 数据类型
    int n_dims;             // 维度数
    int64_t* ne;            // 每个维度大小
    float* data;            // 数据指针
    struct ggml_tensor* op; // 操作
};
```

### 2.2 支持的操作

```c
// 矩阵乘法
ggml_mul_mat();

// 注意力计算
ggml_attention();

// Softmax
ggml_softmax();
```

---

## 3. 推理流程

### 3.1 模型加载

```c
// 加载 GGUF 模型
struct llama_model* model = llama_load_model_from_file(
    "model.gguf",
    llama_model_default_params()
);
```

### 3.2 推理循环

```c
// 自回归生成
for (int i = 0; i < max_tokens; i++) {
    // 1. 计算 logits
    llama_eval(ctx, tokens, n_tokens);

    // 2. 采样
    token = sample(logits);

    // 3. 检查结束
    if (token == EOS) break;

    // 4. 添加到序列
    tokens.push_back(token);
}
```

---

## 4. 量化实现

### 4.1 量化类型

| 类型 | 位宽 | 压缩比 |
|------|------|--------|
| F16 | 16 | 1x |
| Q8_0 | 8 | 2x |
| Q4_K | 4 | 4x |
| Q3_K | 3 | 5x |

### 4.2 K-Quant 原理

```
将权重分组，每组找到最小值和缩放因子
量化: w_q = round(w / scale + offset)
反量化: w = w_q * scale - offset
```

---

## 5. 参考资源

- [llama.c](https://github.com/ggerganov/llama.cpp)
- [ggml](https://github.com/ggerganov/ggml)
- [llama.cpp 量化详解](https://github.com/ggerganov/llama.cpp/tree/master/quantize)
