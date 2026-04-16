To setup:  
```bash
uv venv --python 3.12
uv pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple
```

Exp1 run:  
```bash
uv run tools/download.py  # to download dataset
uv run exp1/main.py
```

Exp2 run:
```bash
uv run pytorchsetup.py  # to setup pytorch env
uv run GPTzip.py  # run GPTzip

```
