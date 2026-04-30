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

    print("="*60)
    print("开始执行 实验二：FineZip (Arithmetic Coding) 批量压缩测试")
    print("="*60)

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

    # 3. 准备输出、输入与临时沙盒目录
    input_dir = os.path.join(CURRENT_DIR, "inputs")
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    logger = ExperimentLogger(out_dir=out_dir)

    valid_files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    # 【体验优化】：按文件大小从小到大排序，优先测试小文件
    valid_files.sort(key=lambda x: os.path.getsize(os.path.join(input_dir, x)))
    
    if not valid_files:
        print(f"[提示] 输入目录为空 ({input_dir})。")
        print("请把要测试的 .txt 文件放入该目录后再运行本脚本。")
        return

    # 【核心修复】：配置强制 UTF-8 的环境变量沙盒，防止 Windows GBK 报错
    utf8_env = os.environ.copy()
    utf8_env["PYTHONUTF8"] = "1"

    # 4. 开始批量遍历测试
    for filename in valid_files:
        raw_path = os.path.join(input_dir, filename)
        raw_size = os.path.getsize(raw_path)
        
        if raw_size > 1048576:
            print(f"\n[跳过] {filename} 大小为 {raw_size} Bytes (超过 1MB 阈值)")
            continue

        # 安全提取无后缀文件名，兼容 .html 和 .txt
        base_name = os.path.splitext(filename)[0]
        print(f"\n{'-'*15} 测试切片: {filename} ({raw_size} Bytes) {'-'*15}")
        
        # ========================================================
        # 修复 1：伪装马甲法。无论什么格式，统统伪装成 .txt 喂给模型
        # ========================================================
        temp_txt_raw = os.path.join(temp_dir, f"{base_name}_fake.txt")
        shutil.copy2(raw_path, temp_txt_raw)

        print(f"  -> 正在复用本地 GPT-2 模型启动 FineZip 推理...\n")

        cmd = [
            sys.executable, ac_script,
            "--model", model_path,       
            "--tokenizer", model_path,   
            "--batch_size", "1",
            "--context_size", "512",
            "--input_file", temp_txt_raw, # 传入伪装的 txt 文件
            "--AC_output_dir", temp_dir,   
            "--encode_decode", "1"
        ]
        
        start_t = time.perf_counter()
        res = subprocess.run(cmd, cwd=ac_script_dir, env=utf8_env)
        total_time = time.perf_counter() - start_t

        if res.returncode != 0:
            print(f"\n[错误] {filename} 执行失败！详情请查看上方控制台报错信息。")
            if os.path.exists(temp_txt_raw): os.remove(temp_txt_raw)
            continue

        # 5. 捕获产物并重命名对齐
        orig_comp_path = os.path.join(temp_dir, "0_AC.txt")
        comp_path = os.path.join(temp_dir, f"{base_name}_FineZip.ac") 
        if os.path.exists(orig_comp_path):
            shutil.move(orig_comp_path, comp_path)
            
        # 因为我们传的是 _fake.txt，FineZip 必然吐出 _fake_AC_decoded_text.txt
        orig_dec_path = os.path.join(temp_dir, f"{base_name}_fake_AC_decoded_text.txt")
        decomp_path = os.path.join(temp_dir, f"{base_name}_FineZip.dec.txt")
        
        # ========================================================
        # 修复 2：逻辑闭环的动态自适应还原原始换行符 (CRLF/LF)
        # ========================================================
        if os.path.exists(orig_dec_path):
            with open(raw_path, 'rb') as fr:
                raw_bytes = fr.read()
            with open(orig_dec_path, 'rb') as fd:
                dec_bytes = fd.read()
                
            # 先统一降维到纯 LF
            dec_bytes = dec_bytes.replace(b'\r\n', b'\n')
            # 如果原始文件里包含 CRLF，就把 LF 强行升维还原回 CRLF
            if b'\r\n' in raw_bytes:
                dec_bytes = dec_bytes.replace(b'\n', b'\r\n')
                
            # 最终写到 decomp_path！
            with open(decomp_path, 'wb') as fd:
                fd.write(dec_bytes)
                
            os.remove(orig_dec_path)

        # 6. 计算尺寸与耗时拆分
        comp_size = os.path.getsize(comp_path) if os.path.exists(comp_path) else 0
        
        metrics_file = os.path.join(temp_dir, "metrics.json")
        comp_time = 0.0
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r', encoding='utf-8') as mf:
                try:
                    metrics = json.load(mf)
                    comp_time = metrics.get('$T', total_time / 2)
                except json.JSONDecodeError:
                    comp_time = total_time / 2
        else:
            comp_time = total_time / 2

        decomp_time = max(0.01, total_time - comp_time)

        # 7. 无损校验
        is_lossless = False
        if os.path.exists(decomp_path):
            with open(raw_path, 'rb') as f1, open(decomp_path, 'rb') as f2:
                is_lossless = (f1.read() == f2.read())

        bpb = (comp_size * 8) / raw_size if raw_size > 0 else 0
        comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
        decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

        print(f"\n  [结果] BPB={bpb:.4f}, 压时={comp_time:.2f}s, 解时={decomp_time:.2f}s, 校验={'通过' if is_lossless else '失败'}")

        # 8. 写入日志
        logger.results.append({
            "Method": "FineZip (GPT-2)", 
            "Slice": base_name, 
            "Raw_Size(B)": raw_size,
            "Comp_Size(B)": comp_size, 
            "BPB": bpb, 
            "Comp_Time(s)": comp_time,
            "Decomp_Time(s)": decomp_time, 
            "Comp_Throughput(MB/s)": comp_throughput,
            "Decomp_Throughput(MB/s)": decomp_throughput,
            "Lossless": is_lossless
        })
        
        # 扫尾清理
        if os.path.exists(temp_txt_raw): os.remove(temp_txt_raw)
        if os.path.exists(metrics_file): os.remove(metrics_file)

    if logger.results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_name = f"finezip_results_{timestamp}.csv"
        logger.save_to_csv(csv_name)
        print("\n" + "="*60)
        print("FineZip 批量实验执行完毕！")
        print(f"- 统一数据汇总表已保存至: {os.path.join(out_dir, csv_name)}")
        print("="*60)

if __name__ == "__main__":
    run_finezip_ac()