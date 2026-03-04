# CUDA 加速实现

## 本章目标

实现 CUDA 加速：
1. CUDA 环境
2. 编译支持
3. GPU 推理
4. 性能优化

---

## 1.1 CUDA 环境

### 1.1.1 安装 CUDA Toolkit

```bash
# 检查 CUDA
nvcc --version
nvidia-smi
```

### 1.1.2 安装 cuDNN

```bash
# 下载 cuDNN (需要 NVIDIA 账号)
# 解压并复制
sudo cp include/cudnn.h /usr/local/cuda/include/
sudo cp lib64/libcudnn* /usr/local/cuda/lib64/
```

---

## 1.2 编译 CUDA 版本

### 1.2.1 CMake 配置

```bash
# 启用 CUDA
cd llama.cpp
mkdir build && cd build

cmake .. -DLLAMA_CUBLAS=ON \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES="80"

make -j$(nproc)
```

### 1.2.2 验证

```bash
# 检查 GPU 支持
./build/bin/llama-cli -m models/llama-2-7b-chat.Q4_K_M.gguf --verbose
```

---

## 1.3 GPU 推理代码

### 1.3.1 设置 GPU 层数

```cpp
// 加载模型时指定 GPU 层数
llama_model_params mparams = llama_model_default_params();
mparams.n_gpu_layers = 43;  // 全部层放到 GPU

struct llama_model* model = llama_load_model_from_file(
    "model.gguf",
    mparams
);
```

### 1.3.2 完整示例

```cpp
#include "llama.h"
#include <iostream>

int main() {
    // 配置
    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 43;  // 全部层在 GPU

    // 加载模型
    llama_model* model = llama_load_model_from_file(
        "models/llama-2-7b-chat.Q4_K_M.gguf",
        mparams
    );

    if (!model) {
        std::cerr << "Failed to load model\n";
        return 1;
    }

    // 创建上下文
    llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx = 2048;
    cparams.n_threads = 4;
    cparams.n_threads_batch = 4;

    llama_context* ctx = llama_new_context_with_model(model, cparams);

    // 推理
    const char* prompt = "Hello, how are you?";
    auto tokens = llama_tokenize(ctx, prompt, true);

    for (int i = 0; i < 100; i++) {
        llama_decode(ctx, tokens.data(), tokens.size());
        tokens.clear();

        auto logits = llama_get_logits_ith(ctx, 0);
        auto n_vocab = llama_n_vocab(model);

        llama_token token = 0;
        float max_logit = logits[0];
        for (int j = 1; j < n_vocab; j++) {
            if (logits[j] > max_logit) {
                max_logit = logits[j];
                token = j;
            }
        }

        if (token == llama_token_eos(ctx)) break;

        std::cout << llama_token_to_piece(ctx, token);
        tokens.push_back(token);
    }

    std::cout << "\n";

    llama_free(ctx);
    llama_free_model(model);

    return 0;
}
```

---

## 1.4 性能优化

### 1.4.1 批处理

```cpp
// 批量处理多个 prompt
std::vector<std::string> prompts = {
    "Hello",
    "How are you",
    "What's up"
};

// 批量推理
for (auto& prompt : prompts) {
    auto tokens = llama_tokenize(ctx, prompt.c_str(), true);
    llama_decode(ctx, tokens.data(), tokens.size());
}
```

### 1.4.2 异步处理

```cpp
// 使用 CUDA 流处理多个请求
// 需要较复杂的异步逻辑
```

---

## 1.5 对比

### 1.5.1 性能对比

| 模式 | Token/秒 |
|------|----------|
| CPU | 5-10 |
| CUDA | 30-50 |
| CUDA + 量化 | 50-80 |

---

## 1.6 本章小结

- ✅ CUDA 环境安装
- ✅ 编译 CUDA 版本
- ✅ GPU 推理代码
- ✅ 性能对比
