import os
import sys
import time
import json
import torch
import numpy as np

# === 动态路径寻址 ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXP2_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(EXP2_DIR)

# 1. 挂载 tools 和 LLMzip 子模块的包路径
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(CURRENT_DIR, "LLMzip"))

from tools.logger import setup_console_logger
from tools.record import ExperimentLogger
from transformers import AutoModelForCausalLM, AutoTokenizer

# ==============================================================================
# 🌟 核心魔法 1：内存级库伪装 (Mocking) 终极版
# 我们根本不需要原作者的 llama.model (里面绑死了 fairscale 和分布式训练)。
# 直接在内存里把它拦截掉，让它返回一个空壳，彻底根除后续所有的依赖报错链！
# ==============================================================================
from unittest.mock import MagicMock
# 只要拦截了这一层，Python 就永远不会去读取原作者的 model.py 文件，
# fairscale 依赖也就不攻自破了！
sys.modules['llama.model'] = MagicMock()

# 直接从原作者源码中引入核心编码/解码类
try:
    from llama.LLMzip import LLMzip_encode, LLMzip_decode
except ImportError as e:
    # 暴露出真实的报错信息，拒绝黑盒！
    print(f"[错误] 导入 LLMzip 核心代码失败，真实原因是: {e}")
    sys.exit(1)

# ==============================================================================
# 🌟 核心魔法 2：Monkey Patch (猴子补丁) 适配器
# 将 HuggingFace 的 GPT-2 动态伪装成 LLaMA，无缝注入 LLMzip 框架
# ==============================================================================
class MockModelParams:
    def __init__(self):
        self.max_batch_size = 1
        self.max_seq_len = 1024 # GPT-2 的最大上下文

class HFModelWrapper:
    """伪装原作者的 Transformer 类"""
    def __init__(self, hf_model):
        self.hf_model = hf_model
        self.params = MockModelParams()
        self.vocab_size = hf_model.config.vocab_size
        
    def forward(self, tokens, prev_pos):
        # 原作者代码会把 tokens 放在 cuda 上，所以我们无缝对齐
        tokens = tokens.to(self.hf_model.device)
        with torch.no_grad():
            outputs = self.hf_model(tokens)
            # LLMzip 只需要序列中最后一个 Token 的概率分布
            logits = outputs.logits[:, -1, :] 
        return logits

class HFTokenizerWrapper:
    """伪装原作者的 Tokenizer 类"""
    def __init__(self, hf_tokenizer):
        self.hf_tokenizer = hf_tokenizer
        self.pad_id = hf_tokenizer.eos_token_id 
        self.bos_id = hf_tokenizer.eos_token_id # GPT-2 用 EOS 代替 BOS
        self.n_words = hf_tokenizer.vocab_size
        
    def encode(self, text, bos=False, eos=False):
        return self.hf_tokenizer.encode(text)
        
    def decode(self, tokens):
        if isinstance(tokens, int):
            tokens = [tokens]
        return self.hf_tokenizer.decode(tokens)

# ==============================================================================

def run_llmzip():
    log_dir = os.path.join(CURRENT_DIR, "logs")
    setup_console_logger(log_dir=log_dir, prefix="llmzip")

    print("="*60)
    print("开始执行 实验二：LLMzip 批量压缩测试 (GPT-2 伪装注入版)")
    print("="*60)

    # 2. 定位共享的本地 GPT-2 模型
    model_path = os.path.join(EXP2_DIR, "models", "GPTzip_gpt2")
    if not os.path.exists(model_path):
        print(f"[错误] 找不到 GPT-2 模型: {model_path}")
        return

    # 3. 准备输出、输入与临时沙盒目录
    input_dir = os.path.join(CURRENT_DIR, "inputs")
    out_dir = os.path.join(CURRENT_DIR, "outputs")
    temp_dir = os.path.join(out_dir, "temp")
    
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    logger = ExperimentLogger(out_dir=out_dir)

    valid_files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    valid_files.sort(key=lambda x: os.path.getsize(os.path.join(input_dir, x)))

    if not valid_files:
        print(f"[提示] 输入目录为空 ({input_dir})。")
        return

    # 4. 加载模型并披上“伪装”
    print("\n--- 正在加载并伪装共享的 GPT-2 模型 ---")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    hf_model = AutoModelForCausalLM.from_pretrained(model_path).to(device)
    hf_tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # 实例化适配器
    model_wrap = HFModelWrapper(hf_model)
    tok_wrap = HFTokenizerWrapper(hf_tokenizer)

    # 实例化原作者的算术编码器和解码器
    encoder = LLMzip_encode(model_wrap, tok_wrap)
    decoder = LLMzip_decode(model_wrap, tok_wrap)

    # 5. 开始批量测试
    win_len = 511 # 对应论文中的 512 上下文截断窗口
    
    for filename in valid_files:
        raw_path = os.path.join(input_dir, filename)
        raw_size = os.path.getsize(raw_path)
        
        if raw_size > 1048576:
            continue

        base_name = filename[:-4] if filename.endswith(".txt") else filename
        slice_name = base_name.split('_')[-1] if '_' in base_name else base_name
        
        print(f"\n{'-'*15} 测试切片: {slice_name} ({raw_size} Bytes) {'-'*15}")

        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        # 生成基础前缀
        comp_prefix = os.path.join(temp_dir, f"{base_name}_LLMzip")
        comp_path = comp_prefix + "_AC.txt"
        decomp_path = os.path.join(temp_dir, f"{base_name}_LLMzip.dec.txt")

        # 将文本转换为原作者需要的 numpy token 数组
        tokens_full = np.array(tok_wrap.encode(raw_text))

        # --- 6. 执行压缩 (调用原作者的 encode_from_tokens) ---
        print(f"  -> 正在进行 LLMzip 算术编码压缩...")
        start_t = time.perf_counter()
        encoder.encode_from_tokens(
            win_size=win_len,
            compression_alg='ArithmeticCoding',
            compressed_file_name=comp_prefix,
            tokens_full=tokens_full,
            batched_encode=False,
            with_context_start=False
        )
        comp_time = time.perf_counter() - start_t
        comp_size = os.path.getsize(comp_path) if os.path.exists(comp_path) else 0

        # 解析生成的 metrics 提取真实的 Token 长度给解码器
        metrics_file = comp_prefix + "_metrics.json"
        total_length = 0
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r', encoding='utf-8') as mf:
                metrics = json.load(mf)
                total_length = metrics['$N_T$'][0]

        # --- 7. 执行解压 (调用原作者的 decode_AC) ---
        print(f"  -> 正在进行 LLMzip 自回归解码...")
        start_t = time.perf_counter()
        # 原作者的解码返回的是解析好的 string
        decoded_text = decoder.decode_AC(
            win_size=win_len,
            starter_tokens=None,
            total_length=total_length,
            compressed_file_name=comp_path
        )
        decomp_time = time.perf_counter() - start_t

        # --- 8. 格式修正：抹平 CRLF ---
        # 直接以二进制形式将字符串 encode 后落盘，防止 Windows 乱加 \r\n
        with open(decomp_path, 'wb') as f:
            f.write(decoded_text.encode('utf-8'))
            
        # --- 9. 无损校验 ---
        is_lossless = False
        if os.path.exists(decomp_path):
            with open(raw_path, 'rb') as f1, open(decomp_path, 'rb') as f2:
                is_lossless = (f1.read() == f2.read())

        bpb = (comp_size * 8) / raw_size if raw_size > 0 else 0
        comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
        decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

        print(f"\n  [结果] BPB={bpb:.4f}, 压时={comp_time:.2f}s, 解时={decomp_time:.2f}s, 校验={'通过' if is_lossless else '失败'}")

        # --- 10. 写入日志 ---
        logger.results.append({
            "Method": "LLMzip (GPT-2)", 
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
        
        # 顺手把模型缓存清理一下，防止连续跑大文件爆显存
        torch.cuda.empty_cache()

    if logger.results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_name = f"llmzip_results_{timestamp}.csv"
        logger.save_to_csv(csv_name)
        print("\n" + "="*60)
        print("LLMzip 批量实验执行完毕！")
        print(f"- 统一数据汇总表已保存至: {os.path.join(out_dir, csv_name)}")
        print("="*60)

if __name__ == "__main__":
    run_llmzip()