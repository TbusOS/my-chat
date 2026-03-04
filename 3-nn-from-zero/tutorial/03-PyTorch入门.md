# 第三章：PyTorch 入门

## 本章目标

掌握 PyTorch 基础：
1. 张量操作
2. 自动求导
3. nn.Module
4. 训练循环

---

## 1.1 张量 (Tensor)

### 1.1.1 什么是张量？

**张量**：多维数组（PyTorch 的核心数据结构）

```
0维: 标量 (5)
1维: 向量 ([1, 2, 3])
2维: 矩阵 ([[1, 2], [3, 4]])
3维及以上: 张量
```

### 1.1.2 创建张量

```python
import torch

# 从 Python 列表创建
x = torch.tensor([1, 2, 3])

# 创建特定形状的张量
zeros = torch.zeros(3, 4)      # 全零
ones = torch.ones(2, 3)        # 全一
rand = torch.randn(3, 3)       # 随机

# 从 NumPy 转换
import numpy as np
arr = np.array([1, 2, 3])
x = torch.from_numpy(arr)
```

### 1.1.3 张量操作

```python
# 基本运算
a = torch.tensor([1, 2, 3])
b = torch.tensor([4, 5, 6])

c = a + b      # 加法
d = a * b      # 乘法
e = a @ b.T   # 矩阵乘法

# 形状变换
x = torch.randn(2, 3)
y = x.view(3, 2)  # 形状变换
y = x.reshape(-1, 1)  # 自动推断
```

---

## 1.2 自动求导

### 1.2.1 开启求导

```python
x = torch.tensor([1., 2., 3.], requires_grad=True)

# 计算
y = x.sum()
y.backward()

# 查看梯度
print(x.grad)  # tensor([1., 1., 1.])
```

### 1.2.2 梯度的含义

```
y = x1² + x2²

当 x1=1, x2=1 时：
∂y/∂x1 = 2*x1 = 2
∂y/∂x2 = 2*x2 = 2
```

---

## 1.3 nn.Module

### 1.3.1 定义网络

```python
import torch.nn as nn

class MyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 20)
        self.fc2 = nn.Linear(20, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

model = MyNet()
print(model)
```

### 1.3.2 查看参数

```python
for name, param in model.named_parameters():
    print(f"{name}: {param.shape}")
```

---

## 1.4 训练循环

### 1.4.1 完整训练流程

```python
import torch
import torch.nn as nn
import torch.optim as optim

# 1. 准备数据
X = torch.randn(100, 10)
y = torch.randn(100, 1)

# 2. 创建模型
model = nn.Sequential(
    nn.Linear(10, 20),
    nn.ReLU(),
    nn.Linear(20, 1)
)

# 3. 定义损失函数和优化器
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 4. 训练循环
for epoch in range(1000):
    # 前向传播
    predictions = model(X)
    loss = criterion(predictions, y)

    # 反向传播
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")
```

---

## 1.5 GPU 加速

### 1.5.1 设备切换

```python
# 检查 GPU 是否可用
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 移动到 GPU
model = model.to(device)
X = X.to(device)
y = y.to(device)
```

### 1.5.2 多 GPU

```python
model = nn.DataParallel(model)
```

---

## 1.6 本章小结

- ✅ 张量操作
- ✅ 自动求导
- ✅ nn.Module 使用
- ✅ 训练循环
- ✅ GPU 加速
