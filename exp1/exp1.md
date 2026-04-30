
## 实验 1 (Exp1)

运行实验
```Bash
# 1. 进入 exp1 目录
cd exp1

# 2. 初始化 exp1 的专属轻量级环境
uv venv --python 3.12
uv pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple

# 3. 运行实验一主程序
uv run main.py
```

运行结束后，CSV 数据记录与性能图表将生成在 exp1/outputs/ 目录下。
