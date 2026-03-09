"""
内核源码 RAG 索引构建

将 Linux 内核源码切分成有意义的代码块，构建 BM25 和可选的语义向量索引。

切分策略（不是按固定行数切，而是按代码语义）：
1. 函数级别切分 - 每个 C 函数作为一个文档
2. 结构体/枚举定义 - 每个类型定义作为一个文档
3. 宏定义块 - 相关宏定义组合为一个文档

用法:
    python rag/scripts/build_index.py --source /path/to/linux-kernel
    python rag/scripts/build_index.py --source /path/to/linux-kernel --arch arm32,arm64
    python rag/scripts/build_index.py --source /path/to/linux-kernel --semantic  # 同时构建语义索引
"""

import argparse
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.retriever import BM25Index, SemanticIndex


# 优先索引的目录（ARM32/ARM64 + 核心子系统）
PRIORITY_DIRS = [
    "arch/arm",
    "arch/arm64",
    "kernel",
    "drivers/usb",
    "drivers/base",
    "drivers/pci",
    "drivers/i2c",
    "drivers/spi",
    "drivers/gpio",
    "drivers/irqchip",
    "mm",
    "net/core",
    "net/ipv4",
    "fs/ext4",
    "fs/proc",
    "fs/sysfs",
    "include/linux",
    "include/asm-generic",
]

# 排除的目录
EXCLUDE_DIRS = {
    "Documentation",
    "tools",
    "scripts",
    "samples",
    "usr",
    ".git",
    "debian",
}

# 索引的文件后缀
INDEX_EXTENSIONS = {".c", ".h", ".S"}


def find_source_files(source_dir: Path, arch_filter: list[str] | None = None) -> list[Path]:
    """
    查找需要索引的源码文件

    优先级：
    1. PRIORITY_DIRS 中的文件
    2. 其他目录的 .c/.h/.S 文件
    """
    files = []

    # 如果指定了架构过滤，调整优先目录
    priority_dirs = list(PRIORITY_DIRS)
    if arch_filter:
        arch_specific = []
        for arch in arch_filter:
            arch_specific.append(f"arch/{arch}")
            arch_specific.append(f"include/asm-{arch}" if arch != "arm64" else "include/asm-generic")
        # 把指定架构的目录放到最前面
        priority_dirs = arch_specific + [d for d in priority_dirs if not d.startswith("arch/")]

    # 先收集优先目录
    for rel_dir in priority_dirs:
        dir_path = source_dir / rel_dir
        if not dir_path.exists():
            continue
        for f in dir_path.rglob("*"):
            if f.suffix in INDEX_EXTENSIONS and f.is_file():
                files.append(f)

    # 再收集其他目录（去重）
    priority_set = set(str(f) for f in files)
    for f in source_dir.rglob("*"):
        if str(f) in priority_set:
            continue
        if f.suffix not in INDEX_EXTENSIONS or not f.is_file():
            continue
        # 排除无关目录
        rel_parts = f.relative_to(source_dir).parts
        if rel_parts and rel_parts[0] in EXCLUDE_DIRS:
            continue
        files.append(f)

    return files


def split_into_chunks(file_path: Path, source_dir: Path) -> list[dict]:
    """
    将源码文件按语义切分成代码块

    切分规则：
    - C 函数定义（包含函数签名 + 函数体）
    - 结构体/联合体/枚举定义
    - 宏定义块（连续的 #define）
    - 其他代码按 80 行为单位切分
    """
    try:
        content = file_path.read_text(errors="replace")
    except Exception:
        return []

    rel_path = str(file_path.relative_to(source_dir))
    lines = content.split("\n")
    chunks = []

    # 汇编文件按标签切分
    if file_path.suffix == ".S":
        return _split_asm(lines, rel_path)

    # C/H 文件按函数和类型定义切分
    i = 0
    while i < len(lines):
        # 检测函数定义开始
        func_match = _detect_function_start(lines, i)
        if func_match:
            start, end = func_match
            chunk_content = "\n".join(lines[start:end + 1])
            if len(chunk_content.strip()) > 20:
                chunks.append({
                    "path": rel_path,
                    "content": chunk_content,
                    "line_start": start + 1,
                    "line_end": end + 1,
                })
            i = end + 1
            continue

        # 检测结构体/枚举定义
        struct_match = _detect_struct_start(lines, i)
        if struct_match:
            start, end = struct_match
            chunk_content = "\n".join(lines[start:end + 1])
            if len(chunk_content.strip()) > 20:
                chunks.append({
                    "path": rel_path,
                    "content": chunk_content,
                    "line_start": start + 1,
                    "line_end": end + 1,
                })
            i = end + 1
            continue

        # 检测连续宏定义
        macro_match = _detect_macro_block(lines, i)
        if macro_match:
            start, end = macro_match
            chunk_content = "\n".join(lines[start:end + 1])
            if len(chunk_content.strip()) > 20:
                chunks.append({
                    "path": rel_path,
                    "content": chunk_content,
                    "line_start": start + 1,
                    "line_end": end + 1,
                })
            i = end + 1
            continue

        # 跳过空行和单行注释
        i += 1

    # 如果没有识别到任何结构，按固定大小切分
    if not chunks and len(lines) > 10:
        chunk_size = 80
        for start in range(0, len(lines), chunk_size):
            end = min(start + chunk_size, len(lines))
            chunk_content = "\n".join(lines[start:end])
            if len(chunk_content.strip()) > 20:
                chunks.append({
                    "path": rel_path,
                    "content": chunk_content,
                    "line_start": start + 1,
                    "line_end": end,
                })

    return chunks


def _detect_function_start(lines: list[str], pos: int) -> tuple[int, int] | None:
    """检测 C 函数定义，返回 (start_line, end_line)"""
    if pos >= len(lines):
        return None

    line = lines[pos].strip()

    # 跳过预处理指令、注释、空行
    if not line or line.startswith("#") or line.startswith("//") or line.startswith("/*"):
        return None

    # 函数定义的启发式匹配：
    # 类型 函数名(参数) {
    # 可能跨多行
    func_pattern = re.compile(
        r'^(?:static\s+)?(?:inline\s+)?(?:__[a-z_]+\s+)*'
        r'(?:void|int|long|unsigned\s+\w*|bool|ssize_t|size_t|'
        r'struct\s+\w+\s*\*?|enum\s+\w+|[a-z_]+_t\s*\*?)\s+'
        r'(\w+)\s*\('
    )

    if not func_pattern.match(line):
        return None

    # 找到函数体的开始 '{'
    brace_start = None
    scan_limit = min(pos + 10, len(lines))
    for j in range(pos, scan_limit):
        if "{" in lines[j]:
            brace_start = j
            break

    if brace_start is None:
        return None

    # 从 '{' 开始找配对的 '}'
    brace_count = 0
    end = brace_start
    for j in range(brace_start, len(lines)):
        brace_count += lines[j].count("{") - lines[j].count("}")
        if brace_count == 0:
            end = j
            break
    else:
        end = len(lines) - 1

    # 限制单个函数块最大 200 行
    if end - pos > 200:
        end = pos + 200

    return (pos, end)


def _detect_struct_start(lines: list[str], pos: int) -> tuple[int, int] | None:
    """检测结构体/联合体/枚举定义"""
    if pos >= len(lines):
        return None

    line = lines[pos].strip()
    struct_pattern = re.compile(
        r'^(?:typedef\s+)?(?:struct|union|enum)\s+\w*\s*\{'
    )

    # 检查当前行或下一行是否有 {
    if not re.match(r'^(?:typedef\s+)?(?:struct|union|enum)\s+', line):
        return None

    brace_start = None
    for j in range(pos, min(pos + 3, len(lines))):
        if "{" in lines[j]:
            brace_start = j
            break

    if brace_start is None:
        return None

    # 找配对的 }
    brace_count = 0
    end = brace_start
    for j in range(brace_start, len(lines)):
        brace_count += lines[j].count("{") - lines[j].count("}")
        if brace_count == 0:
            end = j
            break
    else:
        end = len(lines) - 1

    # 包含可能的 } __attribute__(...) name; 行
    if end + 1 < len(lines) and lines[end + 1].strip().startswith("}"):
        end += 1

    if end - pos > 150:
        end = pos + 150

    return (pos, end)


def _detect_macro_block(lines: list[str], pos: int) -> tuple[int, int] | None:
    """检测连续的宏定义块"""
    if pos >= len(lines):
        return None

    line = lines[pos].strip()
    if not line.startswith("#define"):
        return None

    # 找连续的 #define 行（包括续行 \\）
    end = pos
    for j in range(pos, len(lines)):
        stripped = lines[j].strip()
        if stripped.startswith("#define") or stripped.endswith("\\") or (
            j > pos and not stripped and j - end < 2
        ):
            end = j
        elif stripped.startswith("#") and not stripped.startswith("#define"):
            # #ifdef, #endif 等也包含在块内
            end = j
        else:
            break

    if end == pos:
        return None  # 单个 #define，不值得单独成块

    return (pos, end)


def _split_asm(lines: list[str], rel_path: str) -> list[dict]:
    """按汇编标签切分 .S 文件"""
    chunks = []
    current_start = 0
    label_pattern = re.compile(r'^(\w+):')

    for i, line in enumerate(lines):
        if label_pattern.match(line.strip()) and i > current_start + 5:
            chunk_content = "\n".join(lines[current_start:i])
            if len(chunk_content.strip()) > 20:
                chunks.append({
                    "path": rel_path,
                    "content": chunk_content,
                    "line_start": current_start + 1,
                    "line_end": i,
                })
            current_start = i

    # 最后一块
    if current_start < len(lines):
        chunk_content = "\n".join(lines[current_start:])
        if len(chunk_content.strip()) > 20:
            chunks.append({
                "path": rel_path,
                "content": chunk_content,
                "line_start": current_start + 1,
                "line_end": len(lines),
            })

    return chunks


def build_index(
    source_dir: Path,
    output_dir: Path,
    arch_filter: list[str] | None = None,
    build_semantic: bool = False,
    max_files: int = 0,
):
    """
    构建完整索引

    Args:
        source_dir: 内核源码根目录
        output_dir: 索引输出目录
        arch_filter: 架构过滤（如 ["arm32", "arm64"]）
        build_semantic: 是否构建语义向量索引
        max_files: 最大文件数（0 = 不限制，用于测试）
    """
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Arch filter: {arch_filter or 'all'}")
    print(f"Semantic index: {'yes' if build_semantic else 'no (BM25 only)'}")
    print()

    # 查找文件
    print("Scanning source files...")
    files = find_source_files(source_dir, arch_filter)
    if max_files > 0:
        files = files[:max_files]
    print(f"Found {len(files)} source files")

    # 切分代码块
    print("Splitting into semantic chunks...")
    all_chunks = []
    start_time = time.time()

    for i, f in enumerate(files):
        chunks = split_into_chunks(f, source_dir)
        all_chunks.extend(chunks)
        if (i + 1) % 500 == 0:
            elapsed = time.time() - start_time
            print(f"  Processed {i + 1}/{len(files)} files, {len(all_chunks)} chunks ({elapsed:.1f}s)")

    elapsed = time.time() - start_time
    print(f"Total: {len(all_chunks)} chunks from {len(files)} files ({elapsed:.1f}s)")

    # 构建 BM25 索引
    print("\nBuilding BM25 index...")
    bm25 = BM25Index()
    for chunk in all_chunks:
        bm25.add_document(chunk["path"], chunk["content"], chunk["line_start"], chunk["line_end"])
    bm25.build()
    bm25.save(output_dir / "bm25.json")
    print(f"BM25 index saved ({len(bm25.documents)} documents)")

    # 构建语义索引（可选）
    if build_semantic:
        print("\nBuilding semantic index (this may take a while)...")
        semantic = SemanticIndex()
        if semantic.available:
            semantic.build(all_chunks)
            semantic.save(output_dir / "semantic")
            print(f"Semantic index saved ({len(semantic.documents)} documents)")
        else:
            print("Warning: sentence-transformers or faiss not installed, skipping semantic index")
            print("Install with: pip install sentence-transformers faiss-cpu")

    # 统计
    print(f"\n{'=' * 50}")
    print(f"Index build complete!")
    print(f"  Source files: {len(files)}")
    print(f"  Code chunks: {len(all_chunks)}")
    print(f"  Index location: {output_dir}")

    # 按目录统计
    dir_counts = {}
    for chunk in all_chunks:
        top_dir = chunk["path"].split("/")[0]
        dir_counts[top_dir] = dir_counts.get(top_dir, 0) + 1

    print(f"\nChunks by directory:")
    for d, count in sorted(dir_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {d:20s} {count}")


def main():
    parser = argparse.ArgumentParser(description="Build kernel source RAG index")
    parser.add_argument("--source", required=True, help="Linux kernel source directory")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "rag/index"), help="Index output directory")
    parser.add_argument("--arch", default="", help="Architecture filter (comma-separated, e.g. arm32,arm64)")
    parser.add_argument("--semantic", action="store_true", help="Also build semantic vector index")
    parser.add_argument("--max-files", type=int, default=0, help="Max files to index (0=unlimited, for testing)")

    args = parser.parse_args()

    source_dir = Path(args.source)
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)

    arch_filter = [a.strip() for a in args.arch.split(",") if a.strip()] or None
    output_dir = Path(args.output)

    build_index(source_dir, output_dir, arch_filter, args.semantic, args.max_files)


if __name__ == "__main__":
    main()
