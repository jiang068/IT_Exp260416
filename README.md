To setup:  
```bash
uv venv --python 3.12
uv pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple
```

Download dataset:  
```bash
uv run tools/download.py
```

Exp run:  
```bash
uv run exp1/main.py
```
