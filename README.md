### IT_Exp260416

信息论实验代码库。

### 目录

- [项目结构约定](#项目结构约定)
- [数据集准备](#数据集准备)
- [实验 1 (Exp1)：传统算法基线](./exp1/README.md)
- [实验 2 (Exp2)：LLM 压缩对比](./exp2/README.md)
- [实验 3 (Exp3)：探索实验](#exp3-探索实验)


### 项目结构约定

本项目采用 **环境按需隔离、共享** 策略。`exp1` 与 `exp2` 环境隔离，`exp2` 下的各个模型（如 `gptzip`）均使用 `exp2\.venv` 和 `exp2\requirements.txt` 以节约硬盘。python 使用 `3.12`。相信 `uv`！

#### 数据集准备

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

### exp3: 探索实验
探究上下文窗口长度（Window Length）对 LLM 压缩效率的影响。

前往 `exp2\llmzip\LLMzip.py` 第127行，找到：
```python
win_len = 511
```
分别在窗口长度为 511、256、64 时，运行一次 `LLMzip.py`，数据集使用 `data\enwik8\enwik8_10KB.txt`，观察输出数据并比较。


---