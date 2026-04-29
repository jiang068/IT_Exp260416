import os
import sys
import time
import subprocess

# === 动态路径寻址 ===
# 当前脚本所在目录: exp2/gptzip
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录: 退三层 (gptzip -> exp2 -> IT_Exp260416)
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
# 将项目根目录加入环境变量，以找到 tools 和 cp (如果你还需要 cp 里的 legency)
sys.path.append(ROOT_DIR)

from tools.logger import setup_console_logger
from tools.record import ExperimentLogger

def ensure_gptzip_submodule():
    """验证 GPTzip 子模块是否存在于当前目录下"""
    script_path = os.path.join(CURRENT_DIR, "GPTzip", "gptzip.py")
    if not os.path.exists(script_path):
        print(f"[错误] 找不到子模块 {script_path}。")
        print(f"请在 {CURRENT_DIR} 目录下运行: git clone https://github.com/erika-n/GPTzip.git")
        sys.exit(1)
    return script_path

def ensure_model():
    """将模型下载到本实验专属的 exp2/gptzip/GPTzip_gpt2 目录"""
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError:
        print("[错误] 未安装 modelscope，请在此环境中运行: uv pip install modelscope")
        sys.exit(1)

    # 模型路径直接落在 exp2/gptzip/GPTzip_gpt2
    save_path = os.path.join(CURRENT_DIR, "GPTzip_gpt2")

    if os.path.exists(save_path):
        print(f"[准备] GPT-2 模型已存在于 {save_path}，跳过下载。")
    else:
        print(f"[准备] 正在从 ModelScope 高速下载 gpt2 模型到 {save_path} ...")
        snapshot_download(model_id="AI-ModelScope/gpt2", local_dir=save_path)
        
    return save_path

def run_gptzip():
    log_dir = os.path.join(CURRENT_DIR, "logs")
    setup_console_logger(log_dir=log_dir, prefix="gptzip")

    print("="*50)
    print("开始执行 实验二：GPTzip 独立压缩测试 (Submodule 架构版)")
    print("="*50)

    # 1. 验证子模块与获取模型绝对路径
    gptzip_script = ensure_gptzip_submodule()
    model_path = ensure_model()

    # 2. 准备输出目录
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    logger = ExperimentLogger(out_dir=out_dir)

    # 3. 指定测试切片
    slice_name = "1KB"
    raw_path = os.path.join(ROOT_DIR, "data", "enwik8", "enwik8_1KB.txt")

    if not os.path.exists(raw_path):
        print(f"[错误] 找不到输入文件 {raw_path}。")
        return

    raw_size = os.path.getsize(raw_path)
    print(f"\n[测试切片]: {slice_name} ({raw_size} Bytes)")
    
    # === 动态设备检测 ===
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"  -> 正在启动模型推理 (🔥 GPU 加速开启: {device_name})...")
        else:
            print(f"  -> 正在启动纯本地模型推理 (🐢 CPU 模式，请耐心等待)...")
    except ImportError:
        pass

    comp_path = os.path.join(temp_dir, f"{slice_name}_GPTzip.gpz")
    decomp_path = os.path.join(temp_dir, f"{slice_name}_GPTzip.dec.txt")

    # 4. 执行压缩 (加入 -m 参数传递模型路径)
    start_t = time.perf_counter()
    comp_cmd = [sys.executable, gptzip_script, "-z", raw_path, "-o", comp_path, "-m", model_path]
    res_comp = subprocess.run(comp_cmd, capture_output=True, text=True)
    
    if res_comp.returncode != 0:
        print(f"[错误] 压缩失败:\n{res_comp.stderr}")
        return
        
    comp_time = time.perf_counter() - start_t
    comp_size = os.path.getsize(comp_path)

    # 5. 执行解压 (加入 -m 参数)
    start_t = time.perf_counter()
    decomp_cmd = [sys.executable, gptzip_script, "-u", comp_path, "-o", decomp_path, "-m", model_path]
    res_decomp = subprocess.run(decomp_cmd, capture_output=True, text=True)
    
    if res_decomp.returncode != 0:
        print(f"[错误] 解压失败:\n{res_decomp.stderr}")
        return
        
    decomp_time = time.perf_counter() - start_t

    # 6. 无损校验
    with open(raw_path, 'rb') as f1, open(decomp_path, 'rb') as f2:
        is_lossless = (f1.read() == f2.read())

    bpb = (comp_size * 8) / raw_size
    print(f"  [结果] BPB={bpb:.4f}, 压时={comp_time:.2f}s, 解时={decomp_time:.2f}s, 校验={'通过' if is_lossless else '失败'}")

    logger.results.append({
        "Method": "GPTzip (GPT-2)", "Slice": slice_name, "Raw_Size(B)": raw_size,
        "Comp_Size(B)": comp_size, "BPB": bpb, "Comp_Time(s)": comp_time,
        "Decomp_Time(s)": decomp_time, 
        "Comp_Throughput(MB/s)": (raw_size/1024/1024)/comp_time if comp_time>0 else 0,
        "Decomp_Throughput(MB/s)": (raw_size/1024/1024)/decomp_time if decomp_time>0 else 0,
        "Lossless": is_lossless
    })
    
    csv_name = "gptzip_results.csv"
    logger.save_to_csv(csv_name)
    print("\nGPTzip 实验执行完毕！")
    print(f"- 数据结果已保存至: {os.path.join(out_dir, csv_name)}")

if __name__ == "__main__":
    run_gptzip()