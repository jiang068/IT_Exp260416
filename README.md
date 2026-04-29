# IT_Exp260416

信息论实验代码库。

## 目录

- [项目结构约定](#项目结构约定)
- [实验 1 (Exp1)：传统算法基线](#实验-1-exp1)
  - [数据集准备](#数据集准备)
  - [运行实验](#运行实验)
- [实验 2 (Exp2)：LLM 压缩对比](#实验-2-exp2)
  - [GPTzip 运行](#gptzip-运行)

## 项目结构约定

本项目采用**多环境隔离**策略。`exp1` 与 `exp2` 下的各个模型文件夹（如 `gptzip`）均拥有独立的 `.venv` 虚拟环境和 `requirements.txt`。此举旨在彻底解决不同实验间（特别是大语言模型）的依赖与 PyTorch 版本冲突问题。

## 实验 1 (Exp1)

### 数据集准备

请手动下载以下数据集：

| 数据集 | 链接 |
|--------|------|
| enwik8 | [下载](http://mattmahoney.net/dc/enwik8.zip) |
| canterbury | [下载](http://corpus.canterbury.ac.nz/resources/cantrbry.tar.gz) |
| gutenberg (alice_in_wonderland) | [下载](https://www.gutenberg.org/cache/epub/11/pg11.txt) |

将下载的数据集放入 `data/` 目录并解压，确保结构如下：
```text
data/
├── enwik8/
│   └── enwik8             <-- 解压出的纯文本文件
├── canterbury/
│   └── alice29.txt        <-- (及其他文件)
└── gutenberg/
    └── alice_in_wonderland.txt
```


运行实验
```Bash
# 1. 进入 exp1 目录
cd exp1

# 2. 初始化 exp1 的专属轻量级环境
uv venv --python 3.12
uv pip install -r requirements.txt -i [https://mirrors.ustc.edu.cn/pypi/simple](https://mirrors.ustc.edu.cn/pypi/simple)

# 3. 运行实验一主程序
uv run main.py
```

运行结束后，CSV 数据记录与性能图表将生成在 exp1/outputs/ 目录下。

## 实验 2 (Exp2)
### GPTzip 运行
进入 GPTzip 的独立目录并配置专属的深度学习环境：

```bash
# 1. 进入对应模型目录
cd exp2/gptzip

# 2. 初始化 GPTzip 专属环境
uv venv --python 3.12

# 3. 手动安装 PyTorch (请根据你的硬件环境二选一)
# 【NVIDIA GPU 用户】安装 CUDA 12.4 版本（推荐，需提前装好显卡驱动）:
uv pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu124](https://download.pytorch.org/whl/cu124)
# 【无显卡或 AMD 用户】安装 CPU 版本:
uv pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)

# 4. 安装剩余专属依赖 (会自动安装 transformers, modelscope 等)
uv pip install -r requirements.txt -i [https://mirrors.ustc.edu.cn/pypi/simple](https://mirrors.ustc.edu.cn/pypi/simple)

# 5. 运行实验二
uv run GPTzip.py
```


运行结束后，结果将保存在 exp2/gptzip/outputs/ 目录下。


---