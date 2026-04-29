import os
import sys

# === 动态路径寻址 ===
# 当前脚本所在目录: exp1
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录: 退一层 (exp1 -> IT_Exp260416)
ROOT_DIR = os.path.dirname(CURRENT_DIR)
# 将项目根目录加入环境变量，以便找到 tools
sys.path.append(ROOT_DIR)

from tools.divide import slice_dataset
from tools.record import ExperimentLogger
from tools.draw import plot_results
from tools.logger import setup_console_logger

# 【修改这里】：因为 legency.py 现在和 main.py 在同一个目录下，直接导入即可
from legency import TRADITIONAL_COMPRESSORS

def run_experiment_1():
    # 日志和输出目录内聚到 exp1 目录下
    log_dir = os.path.join(CURRENT_DIR, "logs")
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    
    setup_console_logger(log_dir=log_dir, prefix="exp1")
    
    print("="*50)
    print("开始执行 实验一：传统算法压缩基线")
    print("="*50)
    
    # 1. 检查本地数据集
    print("\n--- 正在检查数据集 ---")
    enwik8_path = os.path.join(ROOT_DIR, "data", "enwik8", "enwik8")
    if not os.path.exists(enwik8_path):
        print(f"[错误] 找不到原始数据集 {enwik8_path}。请参考 README 手动下载并解压。")
        sys.exit(1)
    print(f"[成功] 已检测到本地数据集: {enwik8_path}")
    
    # 2. 数据切片
    print("\n--- 正在准备数据切片 ---")
    out_slice_dir = os.path.join(ROOT_DIR, "data", "enwik8")
    slices_paths = slice_dataset(input_file=enwik8_path, out_dir=out_slice_dir)
    
    # 3. 初始化结果记录器
    logger = ExperimentLogger(out_dir=out_dir)
    
    # 4. 执行压缩与测试
    print("\n--- 开始进行压缩测试 ---")
    slice_order = ["1KB", "10KB", "100KB", "1MB"]
    
    for slice_name in slice_order:
        raw_path = slices_paths[slice_name]
        print(f"\n[测试切片]: {slice_name}")
        
        for method_name, (comp_fn, decomp_fn) in TRADITIONAL_COMPRESSORS.items():
            logger.record_and_verify(
                method_name=method_name,
                slice_name=slice_name,
                raw_path=raw_path,
                compress_func=comp_fn,
                decompress_func=decomp_fn
            )
            
    # 5. 保存结果到 CSV
    csv_name = "results.csv"
    logger.save_to_csv(csv_name)
    
    # 6. 绘制图表
    print("\n--- 正在生成图表 ---")
    plot_results(csv_path=os.path.join(out_dir, csv_name), out_dir=out_dir)
    
    print("\n实验一执行完毕！")
    print(f"- CSV和图表产物位于: {out_dir}")
    print(f"- 原始控制台日志位于: {log_dir}")

if __name__ == "__main__":
    run_experiment_1()