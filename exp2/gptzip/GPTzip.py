import os
import sys
import time
import subprocess
import shutil

# === 动态路径寻址 ===
# 当前脚本所在目录: exp2/gptzip
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# exp2 目录 (退一层)
EXP2_DIR = os.path.dirname(CURRENT_DIR)
# 项目根目录: 退三层 (gptzip -> exp2 -> IT_Exp260416)
ROOT_DIR = os.path.dirname(EXP2_DIR)
# 将项目根目录加入环境变量，以找到 tools
sys.path.append(ROOT_DIR)

from tools.logger import setup_console_logger
from tools.record import ExperimentLogger

def run_gptzip():
    log_dir = os.path.join(CURRENT_DIR, "logs")
    setup_console_logger(log_dir=log_dir, prefix="gptzip")

    print("="*60)
    print("开始执行 实验二：GPTzip 批量压缩测试 (共享模型版)")
    print("="*60)

    # 1. 验证子模块脚本与共享模型绝对路径
    gptzip_script = os.path.join(CURRENT_DIR, "GPTzip", "gptzip.py")
    if not os.path.exists(gptzip_script):
        print(f"[错误] 找不到 GPTzip 核心脚本: {gptzip_script}")
        print("请确保已通过 git submodule 引入了代码。")
        return

    model_path = os.path.join(EXP2_DIR, "models", "GPTzip_gpt2")
    if not os.path.exists(model_path):
        print(f"[错误] 找不到 GPT-2 模型: {model_path}")
        return

    # 2. 准备输出、输入与临时沙盒目录
    input_dir = os.path.join(CURRENT_DIR, "inputs")
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    logger = ExperimentLogger(out_dir=out_dir)

    # 获取待测文件列表
    valid_files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    
    # 【体验优化】：按文件大小从小到大排序，优先跑小文件
    valid_files.sort(key=lambda x: os.path.getsize(os.path.join(input_dir, x)))

    if not valid_files:
        print(f"[提示] 输入目录为空 ({input_dir})。")
        print("请把要测试的 .txt 文件放入该目录后再运行本脚本。")
        return

    # 强制 UTF-8 环境变量，防止 Windows GBK 报错
    utf8_env = os.environ.copy()
    utf8_env["PYTHONUTF8"] = "1"

    # 3. 开始批量遍历测试
    for filename in valid_files:
        raw_path = os.path.join(input_dir, filename)
        raw_size = os.path.getsize(raw_path)
        
        # 【容量拦截器】：大于 1MB 直接忽略
        if raw_size > 1048576:
            print(f"\n[跳过] {filename} 大小为 {raw_size} Bytes (超过 1MB 阈值)")
            continue

        base_name = filename[:-4] if filename.endswith(".txt") else filename
        print(f"\n{'-'*15} 测试切片: {filename} ({raw_size} Bytes) {'-'*15}")
        
        comp_path = os.path.join(temp_dir, f"{base_name}_GPTzip.gpz")
        decomp_path = os.path.join(temp_dir, f"{base_name}_GPTzip.dec.txt")

        # --- 4. 执行压缩 ---
        print(f"  -> 正在进行压缩 (实时输出):")
        start_t = time.perf_counter()
        
        # 【核心修复：障眼法】原作者代码里写死了只接受 .txt 后缀。
        # 我们在这里创建一个临时伪装文件，骗过原作者的 if 判断！
        temp_txt_raw = os.path.join(temp_dir, f"{base_name}_fake.txt")
        shutil.copy2(raw_path, temp_txt_raw)
        
        # 注意这里把输入文件换成了伪装的 temp_txt_raw
        comp_cmd = [sys.executable, gptzip_script, "-z", temp_txt_raw, "-o", comp_path, "-m", model_path]
        res_comp = subprocess.run(comp_cmd, env=utf8_env)
        
        # 阅后即焚，销毁伪装文件
        if os.path.exists(temp_txt_raw):
            os.remove(temp_txt_raw)
        
        if res_comp.returncode != 0 or not os.path.exists(comp_path):
            print(f"\n[错误] {filename} 压缩失败！")
            continue
            
        comp_time = time.perf_counter() - start_t
        comp_size = os.path.getsize(comp_path) if os.path.exists(comp_path) else 0

        # --- 5. 执行解压 ---
        print(f"  -> 正在进行解压 (实时输出):")
        start_t = time.perf_counter()
        decomp_cmd = [sys.executable, gptzip_script, "-u", comp_path, "-o", decomp_path, "-m", model_path]
        res_decomp = subprocess.run(decomp_cmd, env=utf8_env)
        
        if res_decomp.returncode != 0:
            print(f"\n[错误] {filename} 解压失败！")
            continue
            
        decomp_time = time.perf_counter() - start_t

        # --- 6. 格式修正：动态自适应还原原始换行符 (CRLF/LF) ---
        if os.path.exists(decomp_path):
            with open(raw_path, 'rb') as fr:
                raw_bytes = fr.read()
            with open(decomp_path, 'rb') as fd:
                dec_bytes = fd.read()
                
            # 先统一降维到纯 LF
            dec_bytes = dec_bytes.replace(b'\r\n', b'\n')
            # 如果原始文件里包含 CRLF，就把 LF 强行升维还原回 CRLF
            if b'\r\n' in raw_bytes:
                dec_bytes = dec_bytes.replace(b'\n', b'\r\n')
                
            with open(decomp_path, 'wb') as fd:
                fd.write(dec_bytes)

        # --- 7. 无损校验 ---
        is_lossless = False
        if os.path.exists(decomp_path):
            with open(raw_path, 'rb') as f1, open(decomp_path, 'rb') as f2:
                is_lossless = (f1.read() == f2.read())

        bpb = (comp_size * 8) / raw_size if raw_size > 0 else 0
        comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
        decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

        print(f"\n  [结果] BPB={bpb:.4f}, 压时={comp_time:.2f}s, 解时={decomp_time:.2f}s, 校验={'通过' if is_lossless else '失败'}")

        # --- 8. 写入日志 ---
        logger.results.append({
            "Method": "GPTzip (GPT-2)", 
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

    # 9. 统一保存结果
    if logger.results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_name = f"gptzip_results_{timestamp}.csv"
        logger.save_to_csv(csv_name)
        print("\n" + "="*60)
        print("GPTzip 批量实验执行完毕！")
        print(f"- 统一数据汇总表已保存至: {os.path.join(out_dir, csv_name)}")
        print("="*60)

if __name__ == "__main__":
    run_gptzip()