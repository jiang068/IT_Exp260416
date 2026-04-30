import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
OUT_DIR = os.path.join(ROOT_DIR, "exp2", "assets")
os.makedirs(OUT_DIR, exist_ok=True)

def load_all_data():
    """搜刮 exp1 和 exp2 所有的 CSV 数据并合并"""
    all_dfs = []
    
    # 1. 加载传统算法数据
    legency_files = glob.glob(os.path.join(ROOT_DIR, "exp1", "outputs", "*.csv"))
    if legency_files:
        df_leg = pd.read_csv(max(legency_files, key=os.path.getctime))
        df_leg['Category'] = 'Traditional'
        all_dfs.append(df_leg)
        
    # 2. 加载大模型算法数据
    for llm_method in ['finezip', 'gptzip', 'llmzip']:
        llm_files = glob.glob(os.path.join(ROOT_DIR, "exp2", llm_method, "outputs", "*.csv"))
        if llm_files:
            df_llm = pd.read_csv(max(llm_files, key=os.path.getctime))
            df_llm['Category'] = 'LLM'
            all_dfs.append(df_llm)
            
    if not all_dfs:
        print("[错误] 未找到任何 CSV 数据！")
        return None
        
    df = pd.concat(all_dfs, ignore_index=True)
    return df

def clean_data(df):
    """进行极其严苛的数据清洗与对齐"""
    # 统一提取标识符
    df['Raw_Identifier'] = df['File'].fillna(df['Slice']).astype(str)
    
    def infer_dataset(row):
        ident = row['Raw_Identifier'].lower()
        bpb = row['BPB']
        # 修复 LLMzip 中重名的 10KB (BPB > 1.5 且为 10KB 时，是 Alice)
        if 'alice' in ident or (ident == '10kb' and 1.5 < bpb < 2.5 and 'LLMzip' in row['Method']):
            return 'alice_in_wonderland'
        elif 'cp' in ident or 'html' in ident:
            return 'cp.html'
        else:
            return 'enwik8'
            
    df['Dataset'] = df.apply(infer_dataset, axis=1)
    
    # 统一尺寸标度
    size_map = {1024: '1KB', 10240: '10KB', 102400: '100KB', 1048576: '1MB'}
    df['Size_Label'] = df['Raw_Size(B)'].map(size_map)
    
    # 规范排序
    df['Size_Label'] = pd.Categorical(df['Size_Label'], categories=['1KB', '10KB', '100KB', '1MB'], ordered=True)
    return df

def generate_plots(df):
    print("="*60)
    print("正在生成终极学术对比图表...")
    
    # 核心方法筛选 (选几个代表即可，不然图太挤)
    target_methods = ['gzip', 'xz', 'zstd', 'GPTzip (GPT-2)', 'FineZip (GPT-2)', 'LLMzip (GPT-2)']
    df_plot = df[df['Method'].isin(target_methods)]

    # ==========================================
    # 图 1：极限压缩率的规模效应 (enwik8 趋势图)
    # ==========================================
    plt.figure(figsize=(12, 7))
    df_enwik8 = df_plot[df_plot['Dataset'] == 'enwik8']
    
    sns.lineplot(data=df_enwik8, x='Size_Label', y='BPB', hue='Method', style='Category', 
                 markers=True, dashes=False, linewidth=2.5, markersize=10)
    
    plt.title('传统算法 vs LLM大模型：压缩率(BPB)随文本长度变化', fontsize=16, pad=15)
    plt.xlabel('文本大小', fontsize=13)
    plt.ylabel('BPB (比特/字节，越低越好)', fontsize=13)
    plt.grid(True, linestyle='-.', alpha=0.6)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, '01_BPB_Scale_Trend.png'), dpi=300)
    plt.close()

    # ==========================================
    # 图 2：跨领域文本先验对抗 (10KB 级别)
    # ==========================================
    plt.figure(figsize=(12, 7))
    df_10kb = df_plot[df_plot['Size_Label'] == '10KB']
    
    sns.barplot(data=df_10kb, x='Dataset', y='BPB', hue='Method', edgecolor='black')
    
    plt.title('结构化代码(html) vs 自然语言(小说/维基) 压缩率对比', fontsize=16, pad=15)
    plt.xlabel('数据集类型', fontsize=13)
    plt.ylabel('BPB (越低越好)', fontsize=13)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, '02_Cross_Domain_BPB.png'), dpi=300)
    plt.close()

    # ==========================================
    # 图 3：吞吐量与压缩率的终极权衡 (散点图)
    # ==========================================
    plt.figure(figsize=(10, 8))
    # 取 100KB 作为基准对比，因为 LLM 没跑 1MB
    df_tradeoff = df_plot[df_plot['Size_Label'] == '100KB'].copy()
    
    # 绘图
    scatter = sns.scatterplot(data=df_tradeoff, x='BPB', y='Decomp_Throughput(MB/s)', 
                              hue='Method', style='Category', s=200, edgecolor='black')
    
    # 为每个点打上标签
    for line in range(0,df_tradeoff.shape[0]):
         scatter.text(df_tradeoff.BPB.iloc[line]+0.02, 
                      df_tradeoff['Decomp_Throughput(MB/s)'].iloc[line], 
                      df_tradeoff.Method.iloc[line], horizontalalignment='left', 
                      size='medium', color='black', weight='semibold')

    plt.title('BPB vs 解压吞吐量 (100KB量级)', fontsize=16, pad=15)
    plt.xlabel('压缩率 BPB (越靠左越好)', fontsize=13)
    plt.ylabel('解压吞吐量 MB/s (Log坐标，越靠上越快)', fontsize=13)
    plt.yscale('log')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xlim(0.8, 3.2) # 规范视角
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, '03_Tradeoff_Scatter.png'), dpi=300)
    plt.close()

    print(f"✅ 三张终极对比图已生成，存放在：{OUT_DIR}")

if __name__ == "__main__":
    df_all = load_all_data()
    if df_all is not None:
        df_cleaned = clean_data(df_all)
        generate_plots(df_cleaned)