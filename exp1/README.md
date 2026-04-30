### 实验 1 (Exp1)
环境部署：
```Bash
cd exp1
uv venv --python 3.12
uv pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple
```

切片：
```bash
uv run ../tools/divide.py
```

再运行：
```bash
uv run main.py
```

运行结束后，CSV 数据记录与性能图表将生成在 `exp1/outputs/` 目录下。

---