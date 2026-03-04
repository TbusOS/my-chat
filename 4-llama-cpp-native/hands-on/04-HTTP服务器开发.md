# HTTP 服务器开发

## 本章目标

实现 HTTP API 服务器：
1. 基础架构
2. REST API
3. WebSocket
4. 完整代码

---

## 1.1 基础架构

### 1.1.1 使用 llama.cpp 内置服务器

```bash
# 启动服务器
./build/bin/llama-server \
  -m models/llama-2-7b-chat.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080
```

### 1.1.2 API 调用

```bash
# 聊天 API
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# 补全 API
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Once upon a time"
  }'
```

---

## 1.2 自定义服务器

### 1.2.1 使用 httplib

```cpp
#include <httplib.h>
#include "llama.h"
#include <iostream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class LLamaServer {
private:
    llama_model* model = nullptr;
    llama_context* ctx = nullptr;
    httplib::Server svr;

public:
    bool init(const std::string& model_path) {
        llama_model_params mparams = llama_model_default_params();
        model = llama_load_model_from_file(model_path.c_str(), mparams);
        if (!model) return false;

        llama_context_params cparams = llama_context_default_params();
        cparams.n_ctx = 2048;
        ctx = llama_new_context_with_model(model, cparams);
        return ctx != nullptr;
    }

    std::string chat(const std::string& message) {
        std::string prompt = "User: " + message + "\nAssistant:";

        std::vector<llama_token> tokens = llama_tokenize(ctx, prompt.c_str(), true);

        for (int i = 0; i < 256; i++) {
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

            if (token == llama_token_eos(ctx)) {
                break;
            }

            std::cout << llama_token_to_piece(ctx, token);
            tokens.push_back(token);
        }

        return "";
    }

    void setup_routes() {
        // 聊天 API
        svr.Post("/v1/chat/completions", [this](const httplib::Request& req, httplib::Response& res) {
            auto body = json::parse(req.body);
            auto message = body["messages"].back()["content"].get<std::string>();

            std::string response = chat(message);

            json result = {
                {"choices", json::array({
                    {{"message", {{"role", "assistant"}, {"content", response}}}}
                })}
            };

            res.set_content(result.dump(), "application/json");
        });

        // 健康检查
        svr.Get("/health", [](const httplib::Request& req, httplib::Response& res) {
            res.set_content("{\"status\":\"ok\"}", "application/json");
        });
    }

    void run(int port = 8080) {
        setup_routes();
        std::cout << "Server running on http://localhost:" << port << "\n";
        svr.listen("0.0.0.0", port);
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <model.gguf>\n";
        return 1;
    }

    LLamaServer server;
    if (!server.init(argv[1])) {
        std::cerr << "Failed to init\n";
        return 1;
    }

    server.run(8080);
    return 0;
}
```

---

## 1.3 编译

```bash
# 安装 httplib
git clone https://github.com/hphudev/mrdoob.git

# 编译
g++ -std=c++17 -O3 -o server server.cpp \
    -I../include -I../.. \
    -L. -llama -lm -pthread
```

---

## 1.4 本章小结

- ✅ 使用内置服务器
- ✅ REST API
- ✅ 自定义服务器
- ✅ 编译运行
