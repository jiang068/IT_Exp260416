### 实验 2 (Exp2)
三个实验：
GPTzip
FineZip
LLMzip

三个实验环境可以共用，不需要分开部署：
```
# 1. 进入 exp2 目录
cd exp2

# 2. 初始化 exp2 专属环境
uv venv --python 3.12

# 3. 手动安装 PyTorch (请根据你的硬件环境二选一)
# 【NVIDIA GPU 用户】安装 CUDA 12.4 版本（推荐，需提前装好显卡驱动）:
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
# 【无显卡或 AMD 用户】安装 CPU 版本:
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. 安装剩余专属依赖 (会自动安装 transformers, modelscope 等)
uv pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple
```
先把待处理文件放入 `exp2\*zip\inputs`。  
不要放超过 `1MB` 的文件，除非你有足够时间。  

#### GPTzip
```bash
cd gptzip
uv run GPTzip.py
```

#### FineZip
```bash
cd finezip
uv run FineZip.py
```

#### LLMzip
```bash
cd llmzip
uv run LLMzip.py
```
默认会以AC模式调用。如果想换成RZ模式只要把157行的：
```python
compression_alg='ArithmeticCoding',
```

换成：RankZip 或 both。

输出均在 `exp2\*zip\outputs` 目录里。  
实验报告将会基于各实验的 `output` 书写。
