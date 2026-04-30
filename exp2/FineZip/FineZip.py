import os
import sys
import time
import subprocess
import shutil
import json

# === 动态路径寻址 ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.append(ROOT_DIR)

from tools.logger import setup_console_logger
from tools.record import ExperimentLogger

def run_finezip_ac():
    log_dir = os.path.join(CURRENT_DIR, "logs")
    setup_console_logger(log_dir=log_dir, prefix="finezip")

    print("="*50)
    print("开始执行 实验二：FineZip (Arithmetic Coding) 独立压缩测试")
    print("="*50)

    # 1. 定位共享的本地 GPT-2 模型
    model_path = os.path.join(ROOT_DIR, "exp2", "models", "GPTzip_gpt2")
    if not os.path.exists(model_path):
        print(f"[错误] 找不到 GPT-2 模型: {model_path}")
        print("请确保你已经成功运行过 exp2/gptzip/GPTzip.py 并下载了模型。")
        return

    # 2. 定位 FineZip 的核心脚本
    ac_script_dir = os.path.join(CURRENT_DIR, "FineZip", "AC")
    ac_script = os.path.join(ac_script_dir, "eval_ac.py")
    if not os.path.exists(ac_script):
        print(f"[错误] 找不到 FineZip 核心脚本: {ac_script}")
        return

    # 3. 准备输出与临时沙盒目录
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    logger = ExperimentLogger(out_dir=out_dir)

    # 指定测试切片
    slice_name = "1KB"
    raw_filename = f"enwik8_{slice_name}.txt" # 默认名称 enwik8_1KB.txt
    raw_path = os.path.join(ROOT_DIR, "data", "enwik8", raw_filename)
    
    if not os.path.exists(raw_path):
        print(f"[错误] 找不到输入文件 {raw_path}。")
        return
        
    raw_size = os.path.getsize(raw_path)
    
    # 【沙盒机制】：把原始文本拷贝到 temp 目录，防止 eval_ac.py 污染原始 data 文件夹
    temp_raw_path = os.path.join(temp_dir, raw_filename)
    shutil.copy2(raw_path, temp_raw_path)

    print(f"\n[测试切片]: {slice_name} ({raw_size} Bytes)")
    print(f"  -> 正在复用本地 GPT-2 模型启动 FineZip 推理 ({model_path})...")

    # 构建调用命令
    cmd = [
        sys.executable, ac_script,
        "--model", model_path,       
        "--tokenizer", model_path,   
        "--batch_size", "1",
        "--context_size", "512",
        "--input_file", temp_raw_path, # 传入沙盒文件
        "--AC_output_dir", temp_dir,   # 输出到 temp
        "--encode_decode", "1"
    ]
    
    # 4. 运行 FineZip
    start_t = time.perf_counter()
    res = subprocess.run(cmd, cwd=ac_script_dir, capture_output=True, text=True)
    total_time = time.perf_counter() - start_t

    if res.returncode != 0:
        print(f"[错误] FineZip 执行失败:\n{res.stderr}")
        return

    # 5. 捕获产物并重命名对齐 (统一规范化)
    # FineZip 默认生成的压缩包叫 0_AC.txt，解压文件叫 xxx_AC_decoded_text.txt
    orig_comp_path = os.path.join(temp_dir, "0_AC.txt")
    comp_path = os.path.join(temp_dir, f"{slice_name}_FineZip.ac") # 后缀改为 .ac (Arithmetic Coding)
    if os.path.exists(orig_comp_path):
        shutil.move(orig_comp_path, comp_path)
        
    orig_dec_path = os.path.join(temp_dir, f"{raw_filename[:-4]}_AC_decoded_text.txt")
    decomp_path = os.path.join(temp_dir, f"{slice_name}_FineZip.dec.txt")
    if os.path.exists(orig_dec_path):
        shutil.move(orig_dec_path, decomp_path)

    # 6. 计算尺寸与耗时拆分
    comp_size = os.path.getsize(comp_path) if os.path.exists(comp_path) else 0
    
    # 解析 metrics.json 提取精确的压缩耗时
    metrics_file = os.path.join(temp_dir, "metrics.json")
    comp_time = 0.0
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r', encoding='utf-8') as mf:
            metrics = json.load(mf)
            # eval_ac.py 把压缩时间记作了 '$T'
            comp_time = metrics.get('$T', total_time / 2)
    else:
        comp_time = total_time / 2

    # 解压耗时 = 总耗时 - 压缩耗时 (扣除细微的进程开销)
    decomp_time = max(0.01, total_time - comp_time)

    # 7. 无损校验
    is_lossless = False
    if os.path.exists(decomp_path):
        with open(raw_path, 'rb') as f1, open(decomp_path, 'rb') as f2:
            is_lossless = (f1.read() == f2.read())

    bpb = (comp_size * 8) / raw_size if raw_size > 0 else 0
    comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
    decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

    print(f"  [结果] BPB={bpb:.4f}, 压时={comp_time:.2f}s, 解时={decomp_time:.2f}s, 校验={'通过' if is_lossless else '失败'}")

    # 8. 写入日志对齐 GPTzip 格式
    logger.results.append({
        "Method": "FineZip (GPT-2)", 
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
    
    csv_name = "finezip_results.csv"
    logger.save_to_csv(csv_name)
    
    # 扫尾清理沙盒里的无用文件
    if os.path.exists(temp_raw_path): os.remove(temp_raw_path)
    if os.path.exists(metrics_file): os.remove(metrics_file)

    print("\nFineZip 实验执行完毕！")
    print(f"- 数据结果已保存至: {os.path.join(out_dir, csv_name)}")

if __name__ == "__main__":
    run_finezip_ac()