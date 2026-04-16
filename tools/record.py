import os
import time
import pandas as pd

class ExperimentLogger:
    def __init__(self, out_dir="outputs"): 
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self.results = []

    def record_and_verify(self, method_name, slice_name, raw_path, compress_func, decompress_func):
        # 1. 读取原文
        with open(raw_path, 'rb') as f:
            raw_data = f.read()
        raw_size = len(raw_data)

        # 2. 压缩与计时
        start_t = time.perf_counter()
        comp_data = compress_func(raw_data)
        comp_time = time.perf_counter() - start_t
        comp_size = len(comp_data)

        # 3. 解压与计时
        start_t = time.perf_counter()
        decomp_data = decompress_func(comp_data)
        decomp_time = time.perf_counter() - start_t

        # 4. 无损校验
        is_lossless = (raw_data == decomp_data)

        # 5. 计算指标
        bpb = (comp_size * 8) / raw_size
        # 吞吐量 MB/s (按原始数据大小计算)
        comp_throughput = (raw_size / 1024 / 1024) / comp_time if comp_time > 0 else 0
        decomp_throughput = (raw_size / 1024 / 1024) / decomp_time if decomp_time > 0 else 0

        # 打印日志
        print(f"[{method_name}] {slice_name}: BPB={bpb:.4f}, 压缩时间={comp_time:.4f}s, 校验={'通过' if is_lossless else '失败'}")

        self.results.append({
            "Method": method_name,
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

    def save_to_csv(self, filename="results.csv"):
        df = pd.DataFrame(self.results)
        save_path = os.path.join(self.out_dir, filename)
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"\n[Record] 实验结果已保存至: {save_path}")
        return df