import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# 忽略 Seaborn 的一些常规版本警告
warnings.filterwarnings('ignore')

# 设置中文字体以防方块乱码 (兼容 Windows)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def extract_dataset_name(filename):
    """智能解析文件名，提取数据集核心名称"""
    name_no_ext = os.path.splitext(filename)[0]
    if '_' in name_no_ext:
        return name_no_ext.rsplit('_', 1)[0]
    return name_no_ext

def plot_results(csv_path, out_dir="outputs"):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    if df.empty:
        print("[Draw] ⚠️ CSV数据为空，跳过绘图。")
        return

    # 1. 解析出独立的 Dataset 列
    if 'File' in df.columns:
        df['Dataset'] = df['File'].apply(extract_dataset_name)
    else:
        df['Dataset'] = 'default_dataset'

    # ====================================================================
    # 核心修复 1：为 Slice 建立严谨的物理容量排序，杜绝字母乱序 (如 1MB 排在 100KB 前面)
    # ====================================================================
    slice_order = df[['Slice', 'Raw_Size(B)']].drop_duplicates().sort_values('Raw_Size(B)')['Slice'].tolist()
    df['Slice'] = pd.Categorical(df['Slice'], categories=slice_order, ordered=True)
    
    df = df.sort_values(by=['Dataset', 'Raw_Size(B)'])

    generated_plots = 0

    dataset_sizes = df.groupby('Dataset')['Raw_Size(B)'].nunique()
    trend_datasets = dataset_sizes[dataset_sizes > 1].index

    # ====================================================================
    # 图表 1：纯净版趋势图 (仅为拥有多个尺寸的数据集绘制)
    # ====================================================================
    for ds in trend_datasets:
        ds_df = df[df['Dataset'] == ds]
        
        # 1.1 BPB vs 切片大小
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=ds_df, x='Slice', y='BPB', hue='Method', marker='o', linewidth=2, markersize=8)
        plt.title(f'[{ds}] 压缩率随切片大小变化趋势', fontsize=14, pad=15)
        plt.xlabel('切片大小', fontsize=12)
        plt.ylabel('BPB (Bits Per Byte, 越低越好)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'trend_bpb_{ds}.png'), dpi=300)
        plt.close()
        generated_plots += 1

        # ====================================================================
        # 核心修复 2：利用 pd.melt (数据透视表) 彻底解决 Seaborn 的图例崩溃 Bug
        # ====================================================================
        try:
            time_df = ds_df.melt(id_vars=['Slice', 'Method'], 
                                 value_vars=['Comp_Time(s)', 'Decomp_Time(s)'],
                                 var_name='Time_Type', value_name='Time(s)')
            # 汉化图例
            time_df['Time_Type'] = time_df['Time_Type'].replace({'Comp_Time(s)': '压缩', 'Decomp_Time(s)': '解压'})

            plt.figure(figsize=(10, 6))
            # style 参数会自动为压缩和解压分配实线和虚线
            sns.lineplot(data=time_df, x='Slice', y='Time(s)', hue='Method', style='Time_Type', markers=True, dashes=True)
            plt.title(f'[{ds}] 耗时随切片大小变化趋势', fontsize=14, pad=15)
            plt.xlabel('切片大小', fontsize=12)
            plt.ylabel('耗时 (秒, Log对数坐标)', fontsize=12)
            plt.yscale('log') 
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, f'trend_time_{ds}.png'), dpi=300)
            plt.close()
            generated_plots += 1
        except Exception as e:
            print(f"[Draw] ⚠️ 画耗时折线图失败: {e}")

    # ====================================================================
    # 图表 2：跨数据类型横向对比图
    # ====================================================================
    size_datasets = df.groupby('Slice')['Dataset'].nunique()
    cross_sizes = size_datasets[size_datasets > 1].index

    for sz in cross_sizes:
        sz_df = df[df['Slice'] == sz]
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=sz_df, x='Dataset', y='BPB', hue='Method')
        plt.title(f'[{sz} 级别] 同体积不同数据类型的压缩率对抗', fontsize=14, pad=15)
        plt.xlabel('数据集类型', fontsize=12)
        plt.ylabel('BPB (越低越好)', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.legend(title='算法', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f'cross_dataset_bpb_{sz}.png'), dpi=300)
        plt.close()
        generated_plots += 1

    print(f"[Draw] 🎨 成功生成了 {generated_plots} 张智能化多维度图表，请在 {out_dir} 目录查看！")

if __name__ == "__main__":
    # 支持直接运行本脚本来重绘最后一次的 CSV
    import glob
    # 动态适配路径，无论是在 tools 还是根目录运行都能找到 CSV
    csv_search_path = os.path.join("..", "exp1", "outputs", "*.csv") if os.path.basename(os.getcwd()) == "tools" else os.path.join("exp1", "outputs", "*.csv")
    
    csv_files = glob.glob(csv_search_path)
    if csv_files:
        latest_csv = max(csv_files, key=os.path.getctime)
        print(f"正在读取最新 CSV 数据: {latest_csv}")
        out_dir = os.path.dirname(latest_csv)
        plot_results(latest_csv, out_dir)
    else:
        print("未找到任何 CSV 文件，请确保路径正确。")