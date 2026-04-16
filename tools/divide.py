import os

def slice_dataset(input_file, out_dir="data"):
    sizes = {
        "1KB": 1024,
        "10KB": 10240,
        "100KB": 102400,
        "1MB": 1048576
    }
    
    os.makedirs(out_dir, exist_ok=True)
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"找不到文件: {input_file}。请先运行 download.py")

    slices_paths = {}
    with open(input_file, 'rb') as f:
        content = f.read(max(sizes.values())) # 一次性最多读1MB即可
        
        for name, size in sizes.items():
            out_path = os.path.join(out_dir, f"enwik8_{name}.txt")
            with open(out_path, 'wb') as out_f:
                out_f.write(content[:size])
            print(f"[Divide] 成功生成切片: {out_path} ({size} Bytes)")
            slices_paths[name] = out_path
            
    return slices_paths
