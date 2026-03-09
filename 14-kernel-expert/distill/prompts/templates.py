"""
蒸馏 Prompt 模板

用 Opus 4.6 生成内核专家训练数据的各类 prompt 模板
"""

# 原理解释类（30%）
PRINCIPLE_TEMPLATE = """你是 Linux 内核资深专家，精通 ARM32 和 ARM64 架构。

## 知识库上下文
{yaml_content}

## 要求
基于以上知识库信息，生成 {count} 个关于「{topic}」的原理解释问答对。

规则：
1. 问题要具体，不能太宽泛（如"讲讲内存管理"太宽，"ARM64 四级页表如何处理 48 位虚拟地址的转换"才合适）
2. 回答深度要达到内核开发者水平
3. 回答必须引用具体的结构体、函数名、源文件路径
4. 涉及架构差异时要对比 ARM32 和 ARM64
5. 涉及执行上下文时要明确标注（进程/软中断/硬中断）

输出 JSON 数组：
[{{"question": "...", "answer": "...", "category": "principle", "subsystem": "{subsystem}", "arch": "{arch}"}}]
"""

# 调用链分析类（20%）
CALL_CHAIN_TEMPLATE = """你是 Linux 内核资深专家，精通 ARM32 和 ARM64 架构。

## 知识库上下文
{yaml_content}

## 内核源码参考
{source_code}

## 要求
基于以上信息，生成 {count} 个关于内核调用链的问答对。

回答必须包含：
1. 从触发源到用户代码的完整调用链
2. 每个函数标注所在文件（如 drivers/base/dd.c）
3. 每个函数标注执行上下文（进程/软中断/硬中断）
4. 解释调用链中关键函数的作用
5. 如果存在异步分界（如中断 → WorkQueue），要明确标注

格式示例：
```
[触发] USB 设备插入
  usb_hub_port_connect()     [drivers/usb/core/hub.c]     进程上下文
    usb_new_device()         [drivers/usb/core/hub.c]     进程上下文
      device_add()           [drivers/base/core.c]        进程上下文
        ...
          drv->probe()       [用户代码]                    进程上下文
```

输出 JSON 数组：
[{{"question": "...", "answer": "...", "category": "call_chain", "subsystem": "{subsystem}", "arch": "{arch}"}}]
"""

# 代码阅读类（20%）
CODE_READING_TEMPLATE = """你是 Linux 内核资深专家，精通 ARM32 和 ARM64 架构。

## 知识库上下文
{yaml_content}

## 内核代码片段
```c
{source_code}
```

## 要求
基于以上代码和知识库，生成 {count} 个代码阅读问答对。

问题类型：
- "这段代码的功能是什么？"
- "第 X 行的 INIT_WORK 注册的回调 my_handler 何时会被调用？"
- "这个 probe 函数做了哪些初始化？"
- "这段代码有什么潜在问题？"

回答要求：
1. 逐行或逐块解释代码逻辑
2. 标注异步机制的绑定和触发关系
3. 指出函数指针的实际调用路径
4. 标注执行上下文和可睡眠性
5. 如果有 bug 风险要指出（如在中断上下文中睡眠）

输出 JSON 数组：
[{{"question": "...", "answer": "...", "category": "code_reading", "subsystem": "{subsystem}", "arch": "{arch}"}}]
"""

# 对比分析类（10%）
COMPARISON_TEMPLATE = """你是 Linux 内核资深专家，精通 ARM32 和 ARM64 架构。

## ARM32 知识库
{arm32_yaml}

## ARM64 知识库
{arm64_yaml}

## 要求
生成 {count} 个 ARM32 vs ARM64 对比分析的问答对。

对比维度：
- 异常处理入口和向量表结构
- 页表级数和地址空间布局
- 中断控制器（GIC-400 vs GICv3）
- 系统调用指令和 ABI
- 上下文切换和寄存器保存
- 内存屏障指令
- 特权级模型（模式 vs 异常级别）

回答要求：
1. 明确列出两种架构的差异
2. 解释差异的设计原因
3. 引用具体的源文件和函数
4. 实际开发中的影响

输出 JSON 数组：
[{{"question": "...", "answer": "...", "category": "comparison", "subsystem": "{subsystem}", "arch": "both"}}]
"""

# 调试场景类（10%）
DEBUG_TEMPLATE = """你是 Linux 内核资深专家，精通 ARM32 和 ARM64 架构。

## 知识库上下文
{yaml_content}

## 要求
生成 {count} 个内核调试场景的问答对。

场景类型：
- 在错误的上下文中调用了不兼容的 API（如 softirq 中调用 mutex_lock）
- 资源泄漏（URB 未释放、中断未注销）
- 竞态条件（缺少锁保护）
- 中断处理中的错误（没有清除中断源、过长的处理时间）
- 驱动卸载时的清理顺序错误

回答要求：
1. 说明问题的根本原因
2. 说明可能的症状（panic、死锁、数据损坏等）
3. 给出排查方法（用什么工具、看什么日志）
4. 给出正确的修复方案
5. 引用相关的内核 API 和约束

输出 JSON 数组：
[{{"question": "...", "answer": "...", "category": "debug", "subsystem": "{subsystem}", "arch": "{arch}"}}]
"""

# API 用法类（10%）
API_USAGE_TEMPLATE = """你是 Linux 内核资深专家，精通 ARM32 和 ARM64 架构。

## 知识库上下文
{yaml_content}

## 要求
生成 {count} 个内核 API 用法的问答对。

问题类型：
- "devm_request_irq 和 request_irq 的区别？"
- "什么时候用 spin_lock_irqsave 而不是 spin_lock？"
- "GFP_KERNEL 和 GFP_ATOMIC 分别在什么场景使用？"
- "copy_to_user 为什么不能在中断上下文中调用？"

回答要求：
1. API 的函数签名和参数含义
2. 执行上下文约束（能否睡眠、能否在中断中调用）
3. 返回值含义和错误处理
4. 与相关 API 的对比
5. 实际使用的最佳实践和代码示例

输出 JSON 数组：
[{{"question": "...", "answer": "...", "category": "api_usage", "subsystem": "{subsystem}", "arch": "{arch}"}}]
"""

TEMPLATES = {
    "principle": PRINCIPLE_TEMPLATE,
    "call_chain": CALL_CHAIN_TEMPLATE,
    "code_reading": CODE_READING_TEMPLATE,
    "comparison": COMPARISON_TEMPLATE,
    "debug": DEBUG_TEMPLATE,
    "api_usage": API_USAGE_TEMPLATE,
}
