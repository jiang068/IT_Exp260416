import os
import subprocess
import sys

def check_nvidia_gpu():
    """检测是否存在 NVIDIA 显卡"""
    try:
        # 如果 nvidia-smi 执行成功，说明有 N 卡及驱动
        subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def main():
    print("="*50)
    print("开始配置 PyTorch 及大模型依赖环境...")
    print("="*50)

    has_gpu = check_nvidia_gpu()

    if has_gpu:
        print("[环境检测] 发现 NVIDIA GPU。将安装 CUDA 版本的 PyTorch。")
        # cu121 适配大多数现代 N 卡
        torch_cmd = ["uv", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu121"]
    else:
        print("[环境检测] 未发现 NVIDIA GPU (或为 AMD 显卡)。将安装 CPU 版本的 PyTorch。")
        torch_cmd = ["uv", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]

    print(f"执行命令: {' '.join(torch_cmd)}")
    subprocess.check_call(torch_cmd)

    print("\n[环境配置] 正在安装其他大模型依赖 (transformers, accelerate, modelscope)...")
    deps_cmd = ["uv", "pip", "install", "transformers", "accelerate", "modelscope"]
    print(f"执行命令: {' '.join(deps_cmd)}")
    subprocess.check_call(deps_cmd)

    print("\n✅ 环境配置完成！您现在可以运行实验二的脚本了。")

if __name__ == "__main__":
    main()