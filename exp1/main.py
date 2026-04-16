import os
import sys

# 将项目根目录加入环境变量，以便于从不同层级引入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.download import download_enwik8
from tools.divide import slice_dataset
from tools.record import ExperimentLogger
from tools.draw import plot_results
from cp.legency import TRADITIONAL_COMPRESSORS

def run_experiment_1():
    print("="*50)
    print("开始执行 实验一：传统算法压缩基线")
    print("="*50)
    
    # 1. 下载数据
    # enwik8_path = download_enwik8(data_dir="data")
    
    # 2. 数据切片
    print("\n--- 正在准备数据切片 ---")
    slices_paths = slice_dataset(input_file=enwik8_path, out_dir="data")
    
    # 3. 初始化日志记录器
    logger = ExperimentLogger(log_dir="exp1/logs")
    
    # 4. 执行压缩与测试
    print("\n--- 开始进行压缩测试 ---")
    # 为了图表连贯，我们按大小顺序遍历
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
    logger.save_to_csv("results.csv")
    
    # 6. 绘制实验报告要求的两张图表
    print("\n--- 正在生成图表 ---")
    plot_results(csv_path="exp1/logs/results.csv", out_dir="exp1/logs")
    print("\n实验一执行完毕！请查看 exp1/logs/ 下的 CSV 数据和图表。")

if __name__ == "__main__":
    run_experiment_1()