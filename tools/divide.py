import os
import sys
import argparse

# === 动态路径寻址 ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

# 默认的切片档位
DEFAULT_SIZES = {
    "1KB": 1024,
    "10KB": 10240,
    "100KB": 102400,
    "1MB": 1048576
}

def slice_file(input_file, out_dir="data", sizes=None):
    """
    泛用型二进制切片函数
    """
    if sizes is None:
        sizes = DEFAULT_SIZES

    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print(f"[错误] 找不到文件: {input_file}")
        return {}

    file_size = os.path.getsize(input_file)
    base_name = os.path.basename(input_file)
    name_part, ext = os.path.splitext(base_name)

    # 【兼容性修正】：如果原文件没有后缀（例如原始的 enwik8），默认赋予 .txt 后缀
    if ext == "":
        ext = ".txt"

    slices_paths = {}
    
    # 只需要读取到我们需要的最大尺寸即可，节省内存
    max_size_needed = max(sizes.values())
    read_size = min(file_size, max_size_needed)

    with open(input_file, 'rb') as f:
        content = f.read(read_size)

    print(f"\n{'-'*15} 正在切片: {base_name} (原大小: {file_size} Bytes) {'-'*15}")

    for size_name, size_bytes in sizes.items():
        # 【容量拦截】：如果原文件都没这个切片大，直接跳过，防止生成虚假文件
        if file_size < size_bytes:
            print(f"  [跳过] {size_name.ljust(5)} (原文件过小, 无法切出完整 {size_bytes} Bytes)")
            continue

        out_name = f"{name_part}_{size_name}{ext}"
        out_path = os.path.join(out_dir, out_name)
        
        with open(out_path, 'wb') as out_f:
            out_f.write(content[:size_bytes])
            
        print(f"  [成功] 生成切片: {out_name} ({size_bytes} Bytes)")
        slices_paths[size_name] = out_path

    return slices_paths

def main():
    parser = argparse.ArgumentParser(description="泛用型二进制文件批量切片工具")
    parser.add_argument("-i", "--inputs", nargs='+', help="指定要切片的文件路径列表")
    parser.add_argument("-o", "--outdir", default=os.path.join(ROOT_DIR, "data", "slices"), help="输出目录")
    args = parser.parse_args()

    print("="*60)
    print("开始执行：批量文件切片流水线")
    print("="*60)

    # =================================================================
    # 🛠️ 快捷配置区：如果不带参数运行本脚本，默认会切片以下文件
    # =================================================================
    target_files = args.inputs if args.inputs else [
        # 在这里填入你想要默认切片的文件绝对或相对路径
        os.path.join(ROOT_DIR, "data", "enwik8", "enwik8"),
        # os.path.join(ROOT_DIR, "data", "some_image.png"), 
        # os.path.join(ROOT_DIR, "data", "sample_code.c"),
    ]
    
    target_out_dir = args.outdir

    # 开始批量处理
    processed_count = 0
    for file_path in target_files:
        if os.path.exists(file_path):
            slice_file(input_file=file_path, out_dir=target_out_dir)
            processed_count += 1
        else:
            print(f"\n[警告] 忽略无效路径: {file_path}")

    print("\n" + "="*60)
    print(f"切片任务完成！共处理了 {processed_count} 个文件。")
    print(f"切片产物存放于: {target_out_dir}")
    print("="*60)

if __name__ == "__main__":
    main()