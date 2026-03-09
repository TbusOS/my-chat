# macOS Ollama 部署指南

在 macOS 主机上运行 Ollama，为虚拟机中的应用提供 LLM 推理服务。

## 架构

```
macOS 主机 (Apple Silicon)
├── Ollama 服务 (<网桥IP>:11434)
├── qwen2.5:7b   → 中文对话
└── gemma2:9b    → 英文对话/推理

虚拟机 (Linux, 4GB 内存)
└── 应用服务 → 连接 macOS:11434
```

## 硬件要求

- Apple Silicon Mac (M1/M2/M3/M4)
- 建议 16GB+ 统一内存（虚拟机分配 4GB 后，主机剩余 12GB+）

## 安装

```bash
# 1. 安装 Ollama
brew install ollama

# 2. 设置监听地址
# 安全做法：只监听虚拟机网段接口（推荐）
# 先查看虚拟机网桥 IP: ifconfig | grep -B1 "10.211"
launchctl setenv OLLAMA_HOST <你的网桥IP>    # 通过上面的命令查看

# 或监听所有地址（不推荐，局域网内其他人也能访问）
# launchctl setenv OLLAMA_HOST 0.0.0.0

# 3. 启动服务
brew services start ollama

# 4. 下载模型
ollama pull qwen2.5:7b
ollama pull gemma2:9b
```

## 管理脚本

```bash
chmod +x ollama-manager.sh

./ollama-manager.sh start    # 启动服务
./ollama-manager.sh stop     # 停止服务
./ollama-manager.sh restart  # 重启服务
./ollama-manager.sh status   # 查看状态和模型
./ollama-manager.sh test     # 测试模型（含耗时）
```

## 虚拟机连接

虚拟机中将 Ollama 地址配置为 macOS 主机 IP：

```
# 查看虚拟机默认网关（即 macOS 主机 IP）
ip route | grep default

# 通常为 10.211.55.1（Parallels）或 192.168.x.1（VMware）
# 在应用配置中将 Ollama 地址设为:
http://<macOS主机IP>:11434
```

## 模型性能参考（M3 / 24GB）

| 模型 | 大小 | 生成速度 | 适用场景 |
|------|------|---------|---------|
| qwen2.5:7b | 4.7 GB | ~18 tokens/s | 中文对话 |
| gemma2:9b | 5.4 GB | ~14 tokens/s | 英文对话、推理 |

## 安全注意事项

- **不要使用 `0.0.0.0`**：会暴露到 Wi-Fi 局域网，同网络的人都能白嫖你的模型
- **推荐绑定虚拟机网桥 IP**：只允许虚拟机访问，外部无法连接
- Ollama 默认无认证，绑定地址是最重要的安全措施
- 脚本支持通过 `OLLAMA_BIND_ADDR` 环境变量自定义绑定地址

## 其他事项

- Ollama 按需加载模型，空闲 5 分钟自动卸载，不会常驻内存
- 两个模型可同时加载（约 12GB），但通常不会同时使用
- 虚拟机分配 4GB 内存即可，省出资源给 Ollama
