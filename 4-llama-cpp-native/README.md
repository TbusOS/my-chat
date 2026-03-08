# llama.cpp 原生实现教程

## 概述

llama.cpp 是一个纯 C++ 实现的 LLM 推理框架，支持 GGUF 格式模型量化，可在 CPU/GPU 上高效运行。

## 核心特点

- 纯 C++ 实现，无 Python 依赖
- 支持多种量化格式（4bit, 5bit, 8bit 等）
- 苹果 Silicon 优化（Metal 加速）
- Windows/Linux/macOS 全平台支持

## 环境要求

- C++ 编译器（GCC/Clang/MSVC）
- CMake 3.16+
- 可选：CUDA/Metal 支持

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

### 2. 构建

```bash
# Linux/macOS
mkdir build
cd build
cmake ..
make -j$(nproc)

# macOS (Apple Silicon + Metal)
cmake .. -DLLAMA_METAL=ON
make -j$(nproc)

# Windows
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
```

### 3. 下载模型

```bash
# 使用 HuggingFace CLI
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF llama-2-7b-chat.Q4_K_M.gguf --local-dir models/

# 或用 wget/curl 直接下载
```

### 4. 运行

```bash
# 交互式对话
./build/bin/llama-cli -m models/llama-2-7b-chat.Q4_K_M.gguf -n 256 -p "Write a hello world program in Python:"

# 加载模型
./build/bin/llama-load -m models/llama-2-7b-chat.Q4_K_M.gguf

# 批量推理
./build/bin/llama-bench -m models/llama-2-7b-chat.Q4_K_M.gguf
```

## C++ API 使用

### 基本推理

> **注意**：llama.cpp API 更新频繁，以下示例基于 2024-2025 年的 API。
> 如果编译报错，请参考 [llama.cpp examples](https://github.com/ggerganov/llama.cpp/tree/master/examples) 获取最新用法。

```cpp
#include "llama.h"
#include <cstdio>
#include <string>
#include <vector>

int main() {
    // 初始化后端
    llama_backend_init();

    // 加载模型
    struct llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 0;  // CPU 推理，GPU 设为 99

    struct llama_model * model = llama_model_load_from_file(
        "models/llama-2-7b-chat.Q4_K_M.gguf", mparams
    );
    if (!model) {
        fprintf(stderr, "Failed to load model\n");
        return 1;
    }

    // 创建上下文
    struct llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx   = 512;
    cparams.n_batch = 512;

    struct llama_context * ctx = llama_init_from_model(model, cparams);

    // 分词
    const char * prompt = "Write a hello world program in Python:";
    const int n_prompt_tokens_max = 256;
    std::vector<llama_token> tokens(n_prompt_tokens_max);
    int n_tokens = llama_tokenize(model, prompt, strlen(prompt),
                                   tokens.data(), n_prompt_tokens_max,
                                   true, false);
    tokens.resize(n_tokens);

    // 创建 batch 并评估 prompt
    llama_batch batch = llama_batch_init(512, 0, 1);
    for (int i = 0; i < n_tokens; i++) {
        llama_batch_add(batch, tokens[i], i, { 0 }, (i == n_tokens - 1));
    }
    llama_decode(ctx, batch);

    // 创建采样器
    llama_sampler * sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.8f));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(42));

    // 自回归生成
    std::string response;
    int n_cur = n_tokens;

    for (int i = 0; i < 256; i++) {
        llama_token token = llama_sampler_sample(sampler, ctx, -1);

        // 结束条件
        if (llama_token_is_eog(model, token)) break;

        // 转换为文本
        char buf[128];
        int n = llama_token_to_piece(model, token, buf, sizeof(buf), 0, true);
        response.append(buf, n);

        // 准备下一步
        llama_batch_clear(batch);
        llama_batch_add(batch, token, n_cur++, { 0 }, true);
        llama_decode(ctx, batch);
    }

    printf("%s\n", response.c_str());

    // 清理
    llama_sampler_free(sampler);
    llama_batch_free(batch);
    llama_free(ctx);
    llama_model_free(model);
    llama_backend_free();

    return 0;
}
```

### 服务器模式

```cpp
// 启动 HTTP 服务器
./build/bin/llama-server -m models/llama-2-7b-chat.Q4_K_M.gguf -c 512

# 然后可以调用 API
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 模型量化

### 使用 llama.cpp 量化

```bash
# 将 FP16 模型转换为 Q4_K_M
./build/bin/llama-quantize models/llama-2-7b-fp16.gguf models/llama-2-7b-q4_k_m.gguf Q4_K_M

# 可用量化类型
# Q2_K, Q3_K, Q4_0, Q4_K, Q5_0, Q5_K, Q6_K, Q8_0
```

### 量化对比

| 类型 | 大小 | 质量 | 速度 |
|------|------|------|------|
| FP16 | 100% | 最好 | 最慢 |
| Q8_0 | 25% | 很好 | 快 |
| Q4_K | 12.5% | 好 | 很快 |
| Q3_K | 10% | 一般 | 最快 |

## 嵌入向量

```cpp
#include "llama.h"

// 获取文本嵌入
std::vector<float> get_embeddings(struct llama_context* ctx, const char* text) {
    std::vector<llama_token> tokens = tokenize(ctx, text);

    llama_decode(ctx, tokens.data(), tokens.size());

    // 获取最后一层的 embedding
    float* embeddings = llama_get_embeddings(ctx);
    std::vector<float> result(embeddings, embeddings + llama_n_embd(ctx));

    return result;
}
```

## 性能优化

### CPU 推理

```cpp
struct llama_context_params cparams = llama_context_default_params();
cparams.n_ctx = 2048;
cparams.n_threads = 8;              // CPU 线程数
cparams.n_threads_batch = 8;        // 批处理线程数
```

### GPU 推理

```bash
# CUDA（新版使用 GGML_CUDA）
cmake .. -DGGML_CUDA=ON
# 旧版本使用 -DLLAMA_CUBLAS=ON

# Metal (macOS)
cmake .. -DGGML_METAL=ON
# 旧版本使用 -DLLAMA_METAL=ON

# 设置 GPU 层数
mparams.n_gpu_layers = 32;  // 0 = 仅 CPU
```

### 批量处理

```cpp
// 同时处理多个 prompt
std::vector<std::string> prompts = {
    "Hello, how are you?",
    "What is the capital of France?",
    "Write a poem about AI."
};

// 批量 tokenize
std::vector<std::vector<llama_token>> batch_tokens;
for (auto& p : prompts) {
    batch_tokens.push_back(tokenize(ctx, p));
}

// 批量推理
for (int i = 0; i < batch_tokens.size(); i++) {
    llama_decode(ctx, batch_tokens[i].data(), batch_tokens[i].size());
}
```

## 完整项目示例

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_llama_app)

set(CMAKE_CXX_STANDARD 17)

# 链接 llama.cpp
add_executable(my_app main.cpp)
target_link_libraries(my_app llama)
```

### main.cpp

```cpp
#include <iostream>
#include <string>
#include <vector>
#include "llama.h"

class LlamaEngine {
private:
    llama_model* model = nullptr;
    llama_context* ctx = nullptr;

public:
    bool load(const std::string& model_path, int n_gpu_layers = 0) {
        struct llama_model_params mparams = llama_model_default_params();
        mparams.n_gpu_layers = n_gpu_layers;

        model = llama_load_model_from_file(model_path.c_str(), mparams);
        if (!model) return false;

        struct llama_context_params cparams = llama_context_default_params();
        cparams.n_ctx = 2048;
        cparams.n_threads = 4;

        ctx = llama_new_context_with_model(model, cparams);
        return ctx != nullptr;
    }

    std::string generate(const std::string& prompt, int max_tokens = 256) {
        std::vector<llama_token> tokens = ::tokenize(ctx, prompt);

        std::string result;
        for (int i = 0; i < max_tokens; i++) {
            llama_decode(ctx, tokens.data(), tokens.size());

            auto logits = llama_get_logits_ith(ctx, 0);
            auto n_vocab = llama_n_vocab(model);

            // 采样
            llama_token token = 0;
            float max_logit = logits[0];
            for (int j = 1; j < n_vocab; j++) {
                if (logits[j] > max_logit) {
                    max_logit = logits[j];
                    token = j;
                }
            }

            if (token == llama_token_eos(ctx)) break;

            result += llama_token_to_piece(ctx, token);
            tokens = {token};
        }

        return result;
    }

    ~LlamaEngine() {
        if (ctx) llama_free(ctx);
        if (model) llama_free_model(model);
    }
};

int main() {
    LlamaEngine engine;

    if (!engine.load("models/llama-2-7b-chat.Q4_K_M.gguf")) {
        std::cerr << "Failed to load model\n";
        return 1;
    }

    std::string response = engine.generate("Write a hello world in Python:");
    std::cout << response << std::endl;

    return 0;
}
```

## 参考资源

- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [llama.cpp wiki](https://github.com/ggerganov/llama.cpp/wiki)
- [GGUF 格式](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [HuggingFace GGUF 模型](https://huggingface.co/models?library=gguf)
