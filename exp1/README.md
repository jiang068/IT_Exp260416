### 实验 1 (Exp1)

运行实验
```Bash
cd exp1

uv venv --python 3.12
uv pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple

uv run main.py
```

运行结束后，CSV 数据记录与性能图表将生成在 `exp1/outputs/` 目录下。
