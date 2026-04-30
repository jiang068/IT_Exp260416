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

---