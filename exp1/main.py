import os
import sys
import time

# === 动态路径寻址 ===
# 当前脚本所在目录: exp1
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录: 退一层 (exp1 -> IT_Exp260416)
ROOT_DIR = os.path.dirname(CURRENT_DIR)
# 将项目根目录加入环境变量，以便找到 tools
sys.path.append(ROOT_DIR)

from tools.record import ExperimentLogger
from tools.draw import plot_results
from tools.logger import setup_console_logger

# 导入传统压缩算法字典
from legency import TRADITIONAL_COMPRESSORS

def run_experiment_1():
    # 准备目录架构
    log_dir = os.path.join(CURRENT_DIR, "logs")
    input_dir = os.path.join(CURRENT_DIR, "inputs")
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    setup_console_logger(log_dir=log_dir, prefix="exp1")
    
    print("="*60)
    print("开始执行 实验一：传统算法压缩 批量基线测试")
    print("="*60)
    
    logger = ExperimentLogger(out_dir=out_dir)

    # 1. 扫描 inputs 目录并过滤、排序
    valid_files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    # 按文件大小从小到大排序
    valid_files.sort(key=lambda x: os.path.getsize(os.path.join(input_dir, x)))

    if not valid_files:
        print(f"\n[提示] 输入目录为空 ({input_dir})。")
        print("请将测试切片 (如 enwik8_1KB.txt) 放入该目录后再运行本脚本。")
        return

    print("\n--- 开始批量遍历测试 ---")
    
    # 2. 遍历每个文件
    for filename in valid_files:
        raw_path = os.path.join(input_dir, filename)
        raw_size = os.path.getsize(raw_path)
        
        # 容量拦截器：大于 1MB (1,048,576 Bytes) 直接忽略
        if raw_size > 1048576:
            print(f"\n[跳过] {filename} 大小为 {raw_size} Bytes (超过 1MB 阈值)")
            continue

        # =======================================================
        # 核心修正：安全拆解文件名，杜绝物理文件互相覆盖
        # =======================================================
        name_without_ext = os.path.splitext(filename)[0]
        # 提取纯粹的体积标度 (如 10KB)，专供画图脚本识别
        slice_scale = name_without_ext.split('_')[-1] if '_' in name_without_ext else name_without_ext
        
        # 终端清楚打印原始完整文件名
        print(f"\n{'-'*15} 测试切片: {filename} ({raw_size} Bytes) {'-'*15}")
        
        # 一次性读取原始二进制数据
        with open(raw_path, 'rb') as f:
            raw_data = f.read()

        # 3. 遍历每一种传统压缩算法
        for method_name, (comp_fn, decomp_fn) in TRADITIONAL_COMPRESSORS.items():
            
            # 物理文件命名：挂载完整的 filename，如 cp_10KB.html_gzip.bin 
            comp_path = os.path.join(temp_dir, f"{filename}_{method_name}.bin")
            decomp_path = os.path.join(temp_dir, f"{filename}_{method_name}.dec")
            
            # === 压缩阶段 ===
            start_t = time.perf_counter()
            comp_data = comp_fn(raw_data)
            comp_time = time.perf_counter() - start_t
            
            with open(comp_path, 'wb') as f:
                f.write(comp_data)
                
            comp_size = len(comp_data)
            
            # === 解压阶段 ===
            start_t = time.perf_counter()
            decomp_data = decomp_fn(comp_data)
            decomp_time = time.perf_counter() - start_t
            
            with open(decomp_path, 'wb') as f:
                f.write(decomp_data)

            # === 无损校验 ===
            is_lossless = (raw_data == decomp_data)

            bpb = (comp_size * 8) / raw_size if raw_size > 0 else 0
            comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
            decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

            print(f"  [{method_name.ljust(6)}] BPB={bpb:.4f}, 压时={comp_time:.4f}s, 解时={decomp_time:.4f}s, 校验={'通过' if is_lossless else '失败'}")

            # === 写入日志结构 ===
            logger.results.append({
                "Method": method_name, 
                "File": filename,      # 记录真实的物理文件名
                "Slice": slice_scale,  # 维持画图脚本需要的标度
                "Raw_Size(B)": raw_size,
                "Comp_Size(B)": comp_size, 
                "BPB": bpb, 
                "Comp_Time(s)": comp_time,
                "Decomp_Time(s)": decomp_time, 
                "Comp_Throughput(MB/s)": comp_throughput,
                "Decomp_Throughput(MB/s)": decomp_throughput,
                "Lossless": is_lossless
            })

    # 4. 所有测试结束，保存 CSV 并绘图
    if logger.results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_name = f"legency_results_{timestamp}.csv"
        
        logger.save_to_csv(csv_name)
        
        print("\n--- 正在生成图表 ---")
        csv_full_path = os.path.join(out_dir, csv_name)
        try:
            plot_results(csv_path=csv_full_path, out_dir=out_dir)
        except Exception as e:
            print(f"[警告] 画图步骤出现异常，原因: {e}")

        print("\n" + "="*60)
        print("实验一：传统算法压缩 批量执行完毕！")
        print(f"- 统一数据汇总表已保存至: {csv_full_path}")
        print(f"- 物理压缩/解压产物已保存至: {temp_dir}")
        print("="*60)

if __name__ == "__main__":
    run_experiment_1()