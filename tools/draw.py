import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_results(csv_path, out_dir):
    if not os.path.exists(csv_path):
        print(f"找不到日志文件 {csv_path}，无法绘图。")
        return

    df = pd.DataFrame(pd.read_csv(csv_path))
    os.makedirs(out_dir, exist_ok=True)
    
    # 设置图表字体以支持中文 (Windows默认微软雅黑)
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 将 Slice 转换为数值(Byte)以便于横坐标排序
    size_map = {"1KB": 1024, "10KB": 10240, "100KB": 102400, "1MB": 1048576}
    df['Size_Num'] = df['Slice'].map(size_map)
    # 按照 Size_Num 排序，保证后续画图 X 轴顺序正确
    df.sort_values('Size_Num', inplace=True)

    methods = df['Method'].unique()

    # --- 图1: 文本长度 — 压缩效率(BPB) 曲线图 ---
    plt.figure(figsize=(10, 6))
    for m in methods:
        sub_df = df[df['Method'] == m]
        plt.plot(sub_df['Slice'], sub_df['BPB'], marker='o', label=m)
        
    plt.title("文本长度与压缩效率(BPB)关系")
    plt.xlabel("文本长度切片")
    plt.ylabel("Bits Per Byte (BPB) - 越低越好")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(out_dir, "length_vs_bpb.png"))
    plt.close()

    # --- 图2: 压缩效率(BPB) — 吞吐量(MB/s) 散点图 ---
    plt.figure(figsize=(10, 6))
    df_1mb = df[df['Slice'] == '1MB']
    
    for _, row in df_1mb.iterrows():
        plt.scatter(row['BPB'], row['Comp_Throughput(MB/s)'], s=100, label=row['Method'])
        plt.annotate(row['Method'], (row['BPB'], row['Comp_Throughput(MB/s)']), xytext=(5,5), textcoords='offset points')

    plt.title("1MB切片下：压缩效率(BPB) vs 压缩吞吐量(MB/s)")
    plt.xlabel("Bits Per Byte (BPB) - 越低越好")
    plt.ylabel("压缩吞吐量 (MB/s) - 越高越好")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(out_dir, "bpb_vs_throughput.png"))
    plt.close()

    # --- 图3: 相对压缩时间趋势图 (以 gzip 为基准) ---
    plt.figure(figsize=(10, 6))
    
    base_method = 'gzip' if 'gzip' in methods else methods[0]
    # 提取基准方法的数据，并确保顺序一致
    base_df = df[df['Method'] == base_method].sort_values('Size_Num')
    
    for m in methods:
        sub_df = df[df['Method'] == m].sort_values('Size_Num')
        
        # 计算相对倍数，使用 .values 确保按顺序对齐除法
        relative_times = sub_df['Comp_Time(s)'].values / np.maximum(base_df['Comp_Time(s)'].values, 1e-9)
        
        # 直接使用等距的分类标签 sub_df['Slice'] 作为 X 轴
        plt.plot(sub_df['Slice'], relative_times, marker='s', label=f"{m} (基准为 {base_method})")
    
    plt.title(f"相对压缩时间趋势图 (以 {base_method} 耗时为 1.0 倍)")
    plt.xlabel("文本长度切片")
    plt.ylabel("相对耗时倍数")
    plt.yscale('log') 
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(out_dir, "relative_time_trend.png"))
    plt.close()

    print(f"[Draw] 3 张图表已生成并保存至 {out_dir} 目录。")