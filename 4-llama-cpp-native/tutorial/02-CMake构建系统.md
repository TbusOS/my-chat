# CMake 构建系统

## 本章目标

掌握 CMake 构建：
1. CMake 基础
2. CMakeLists.txt
3. 编译项目
4. 常见问题

---

## 1.1 CMake 基础

### 1.1.1 什么是 CMake？

**CMake**：跨平台的构建系统

```
CMakeLists.txt → CMake → Makefile / Ninja → 编译
```

### 1.1.2 基本命令

```bash
# 创建构建目录
mkdir build
cd build

# 配置
cmake ..

# 编译
make -j4

# 安装
make install
```

---

## 1.2 CMakeLists.txt

### 1.2.1 最小示例

```cmake
cmake_minimum_required(VERSION 3.10)
project(MyProject)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找包
find_package(Threads REQUIRED)

# 添加可执行文件
add_executable(my_app main.cpp)

# 链接库
target_link_libraries(my_app Threads::Threads)
```

### 1.2.2 完整示例

```cmake
cmake_minimum_required(VERSION 3.16)
project(llama)

# 选项
option(LLAMA_BUILD_TESTS "Build tests" OFF)
option(LLAMA_BUILD_EXAMPLES "Build examples" ON)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)

# 源文件
file(GLOB SOURCES "src/*.cpp")

# 可执行文件
add_executable(llama ${SOURCES})

# 头文件目录
target_include_directories(llama PUBLIC ${CMAKE_SOURCE_DIR}/include)

# 链接库
target_link_libraries(llama PRIVATE Threads::Threads)

# 安装
install(TARGETS llama DESTINATION bin)
```

---

## 1.3 编译 llama.cpp

### 1.3.1 基本编译

```bash
# 克隆
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# 创建构建目录
mkdir build
cd build

# 配置
cmake ..

# 编译
make -j$(nproc)
```

### 1.3.2 启用选项

```bash
# CUDA 支持
cmake .. -DLLAMA_CUBLAS=ON

# Metal 支持 (macOS)
cmake .. -DLLAMA_METAL=ON

# 统一内存
cmake .. -DLLAMA_METAL=ON -DCMAKE_BUILD_TYPE=Release
```

---

## 1.4 常见问题

### 1.4.1 编译失败

```bash
# 清理重新编译
rm -rf build
mkdir build && cd build
cmake ..
make -j4
```

### 1.4.2 找不到 CUDA

```bash
# 指定 CUDA 路径
cmake .. -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
```

---

## 1.5 本章小结

- ✅ CMake 基础
- ✅ CMakeLists.txt 编写
- ✅ 编译项目
- ✅ 常见问题解决
