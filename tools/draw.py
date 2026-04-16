import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_results(csv_path="exp1/logs/results.csv", out_dir="exp1/logs"):
    if not os.path.exists(csv_path):
        print(f"找不到日志文件 {csv_path}，无法绘图。")
        return

    df = pd.DataFrame(pd.read_csv(csv_path))
    os.makedirs(out_dir, exist_ok=True)
    
    # 设置图表字体以支持中文 (Windows默认微软雅黑)
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 将 Slice 转换为数值(Byte)以便于横坐标排序和画图
    size_map = {"1KB": 1024, "10KB": 10240, "100KB": 102400, "1MB": 1048576}
    df['Size_Num'] = df['Slice'].map(size_map)
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
    # 通常用 1MB 切片的数据来展示吞吐量最稳定
    plt.figure(figsize=(10, 6))
    df_1mb = df[df['Slice'] == '1MB']
    
    for _, row in df_1mb.iterrows():
        plt.scatter(row['BPB'], row['Comp_Throughput(MB/s)'], s=100, label=row['Method'])
        plt.annotate(row['Method'], (row['BPB'], row['Comp_Throughput(MB/s)']), xytext=(5,5), textcoords='offset points')

    plt.title("1MB切片下：压缩效率(BPB) vs 压缩吞吐量(MB/s)")
    plt.xlabel("Bits Per Byte (BPB) - 越低越好")
    plt.ylabel("压缩吞吐量 (MB/s) - 越高越好")
    plt.grid(True, linestyle='--', alpha=0.6)
    # plt.legend() # annotate已经标了名字，可省略legend
    plt.savefig(os.path.join(out_dir, "bpb_vs_throughput.png"))
    plt.close()
    
    print(f"[Draw] 图表已生成并保存至 {out_dir} 目录。")