import os
import sys
import time
import subprocess

# === 动态路径寻址 ===
# 当前脚本所在目录: exp2/gptzip
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录: 退三层 (gptzip -> exp2 -> IT_Exp260416)
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
# 将项目根目录加入环境变量，以找到 tools 和 cp
sys.path.append(ROOT_DIR)

from tools.logger import setup_console_logger
from tools.record import ExperimentLogger

def ensure_gptzip_repo():
    """确保 GPTzip 仓库已克隆到根目录的 cp/GPTzip 目录下"""
    repo_path = os.path.join(ROOT_DIR, "cp", "GPTzip")
    script_path = os.path.join(repo_path, "gptzip.py")
    
    if not os.path.exists(repo_path):
        print(f"[准备] 正在克隆 GPTzip 仓库到 {repo_path} ...")
        subprocess.check_call(["git", "clone", "https://github.com/erika-n/GPTzip.git", repo_path])
    else:
        print(f"[准备] GPTzip 仓库已存在于 {repo_path}，跳过克隆。")
        
    return script_path

def ensure_model():
    """使用国内魔搭社区(ModelScope)高速下载 GPT-2 到本地，突破 HF 限速"""
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError:
        print("[错误] 未安装 modelscope，请先在此环境运行 pytorchsetup.py")
        sys.exit(1)

    model_dir = os.path.join(ROOT_DIR, "models")
    os.makedirs(model_dir, exist_ok=True)
    save_path = os.path.join(model_dir, "GPTzip_gpt2")

    if os.path.exists(save_path):
        print(f"[准备] GPT-2 模型已存在于 {save_path}，跳过下载。")
    else:
        print(f"[准备] 正在从 ModelScope 高速下载 gpt2 模型到 {save_path} ...")
        snapshot_download(model_id="AI-ModelScope/gpt2", local_dir=save_path)
        
    return save_path

def patch_script_inplace(script_path, model_path):
    """
    【核心补丁】
    1. 替换模型路径为本地路径以突破限速。
    2. 修复原作者由于粗心导致的 .gpz.gpz 命名 BUG。
    3. 修复 Windows 系统下自动转换换行符导致“逐字节校验”失败的跨平台 BUG。
    """
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
        
    safe_path = os.path.abspath(model_path).replace("\\", "/")
    need_write = False
    
    # 修复 1：模型路径
    if f'"{safe_path}"' not in code:
        code = code.replace('"gpt2"', f'"{safe_path}"')
        need_write = True
        
    # 修复 2：原作者的后缀名 BUG
    if 'zip_file[:-4] != ".gpz":' in code:
        code = code.replace('zip_file[:-4] != ".gpz":', 'zip_file[-4:] != ".gpz":')
        need_write = True

    # 修复 3：Windows 换行符导致写入字节增加的 BUG (读取时和写入时均禁用转换)
    if 'open(text_file, encoding="utf-8")' in code:
        code = code.replace('open(text_file, encoding="utf-8")', 'open(text_file, "r", encoding="utf-8", newline="")')
        need_write = True
        
    if 'open(text_file, "w", encoding="utf-8")' in code:
        code = code.replace('open(text_file, "w", encoding="utf-8")', 'open(text_file, "w", encoding="utf-8", newline="")')
        need_write = True

    if need_write:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("[准备] 已修改 gptzip.py：本地模型路径 + 修复后缀漏洞 + 修复 Windows 换行符字节校验漏洞！")

def run_gptzip():
    # 日志输出到当前文件夹 (exp2/gptzip/logs)
    log_dir = os.path.join(CURRENT_DIR, "logs")
    setup_console_logger(log_dir=log_dir, prefix="gptzip")

    print("="*50)
    print("开始执行 实验二：GPTzip (GPT-2) 独立压缩测试 (纯本地模型版)")
    print("="*50)

    # 1. 准备仓库和模型，并打补丁
    gptzip_script = ensure_gptzip_repo()
    model_path = ensure_model()
    patch_script_inplace(gptzip_script, model_path)

    # 2. 准备输出目录和记录器 (exp2/gptzip/outputs)
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    logger = ExperimentLogger(out_dir=out_dir)

    # 3. 指定测试切片 (仅测试 1KB)
    slice_name = "1KB"
    # 使用绝对路径去根目录找 data
    raw_path = os.path.join(ROOT_DIR, "data", "enwik8", "enwik8_1KB.txt")

    if not os.path.exists(raw_path):
        print(f"[错误] 找不到输入文件 {raw_path}。请确保已运行 exp1。")
        return

    raw_size = os.path.getsize(raw_path)
    print(f"\n[测试切片]: {slice_name} ({raw_size} Bytes)")
    
    # === 动态设备检测 ===
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"  -> 正在启动纯本地模型推理 (🔥 GPU 加速开启: {device_name}，由于串行解码限制，仍需等待数秒)...")
        else:
            print(f"  -> 正在启动纯本地模型推理 (🐢 CPU 模式，请耐心等待)...")
    except ImportError:
        print(f"  -> 正在启动纯本地模型推理 (未知设备)...")
    # ==========================

    comp_path = os.path.join(temp_dir, f"{slice_name}_GPTzip.gpz")
    decomp_path = os.path.join(temp_dir, f"{slice_name}_GPTzip.dec.txt")

    # 4. 执行压缩
    start_t = time.perf_counter()
    comp_cmd = [sys.executable, gptzip_script, "-z", raw_path, "-o", comp_path]
    res_comp = subprocess.run(comp_cmd, capture_output=True, text=True)
    
    if res_comp.returncode != 0:
        print(f"[错误] 压缩失败:\n{res_comp.stderr}")
        return
        
    comp_time = time.perf_counter() - start_t
    comp_size = os.path.getsize(comp_path)

    # 5. 执行解压
    start_t = time.perf_counter()
    decomp_cmd = [sys.executable, gptzip_script, "-u", comp_path, "-o", decomp_path]
    res_decomp = subprocess.run(decomp_cmd, capture_output=True, text=True)
    
    if res_decomp.returncode != 0:
        print(f"[错误] 解压失败:\n{res_decomp.stderr}")
        return
        
    decomp_time = time.perf_counter() - start_t

    # 6. 无损校验
    with open(raw_path, 'rb') as f1, open(decomp_path, 'rb') as f2:
        is_lossless = (f1.read() == f2.read())

    bpb = (comp_size * 8) / raw_size
    comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
    decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

    print(f"  [结果] BPB={bpb:.4f}, 压时={comp_time:.2f}s, 解时={decomp_time:.2f}s, 校验={'通过' if is_lossless else '失败'}")

    # 7. 写入日志
    logger.results.append({
        "Method": "GPTzip (GPT-2)",
        "Slice": slice_name,
        "Raw_Size(B)": raw_size,
        "Comp_Size(B)": comp_size,
        "BPB": bpb,
        "Comp_Time(s)": comp_time,
        "Decomp_Time(s)": decomp_time,
        "Comp_Throughput(MB/s)": comp_throughput,
        "Decomp_Throughput(MB/s)": decomp_throughput,
        "Lossless": is_lossless
    })

    csv_name = "gptzip_results.csv"
    logger.save_to_csv(csv_name)
    print("\nGPTzip 实验执行完毕！")
    print(f"- 数据结果已保存至: {os.path.join(out_dir, csv_name)}")

if __name__ == "__main__":
    run_gptzip()