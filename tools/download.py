import os
import urllib.request
import zipfile
import tarfile
import requests

def download_enwik8(data_dir="data/enwik8"):
    """下载并解压 enwik8 数据集"""
    os.makedirs(data_dir, exist_ok=True)
    zip_path = os.path.join(data_dir, "enwik8.zip")
    txt_path = os.path.join(data_dir, "enwik8")

    if os.path.exists(txt_path):
        print(f"[Download] enwik8 已存在: {txt_path}，跳过。")
        return txt_path

    url = "http://mattmahoney.net/dc/enwik8.zip"
    print(f"[Download] 正在从 {url} 下载 enwik8.zip...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("[Download] enwik8 下载完成，正在解压...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print("[Download] enwik8 解压完成！")
    except Exception as e:
        print(f"[Error] enwik8 下载失败: {e}")
        
    return txt_path

def download_canterbury(data_dir="data/canterbury"):
    """下载并解压 Canterbury Corpus 数据集"""
    os.makedirs(data_dir, exist_ok=True)
    tar_path = os.path.join(data_dir, "cantrbry.tar.gz")
    
    # 检查是否已经解压过（以 alice29.txt 为代表）
    if os.path.exists(os.path.join(data_dir, "alice29.txt")):
        print(f"[Download] Canterbury Corpus 已存在于 {data_dir}，跳过。")
        return data_dir

    url = "http://corpus.canterbury.ac.nz/resources/cantrbry.tar.gz"
    print(f"[Download] 正在从 {url} 下载 Canterbury Corpus...")
    try:
        urllib.request.urlretrieve(url, tar_path)
        print("[Download] Canterbury Corpus 下载完成，正在解压...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=data_dir)
        print("[Download] Canterbury Corpus 解压完成！")
    except Exception as e:
        print(f"[Error] Canterbury Corpus 下载失败: {e}")
        
    return data_dir

def download_gutenberg(data_dir="data/gutenberg"):
    """
    下载 Project Gutenberg 的代表性书籍片段
    由于全站太大，这里精选 3 本不同风格的名著纯文本：
    1. Alice's Adventures in Wonderland (童话/小说)
    2. Pride and Prejudice (古典文学)
    3. Frankenstein (科幻/恐怖小说)
    """
    os.makedirs(data_dir, exist_ok=True)
    
    books = {
        "alice_in_wonderland.txt": "https://www.gutenberg.org/cache/epub/11/pg11.txt",
        "pride_and_prejudice.txt": "https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
        "frankenstein.txt": "https://www.gutenberg.org/cache/epub/84/pg84.txt"
    }

    # 伪装成浏览器请求，防止被古腾堡服务器拦截
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    downloaded_paths = []

    for filename, url in books.items():
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            print(f"[Download] 古腾堡书籍已存在: {filename}，跳过。")
            downloaded_paths.append(file_path)
            continue

        print(f"[Download] 正在获取古腾堡书籍: {filename} ...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # 检查HTTP状态码
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"[Download] {filename} 保存成功！")
            downloaded_paths.append(file_path)
        except Exception as e:
            print(f"[Error] 获取 {filename} 失败: {e}")

    return downloaded_paths

if __name__ == "__main__":
    print("="*50)
    print("开始下载实验所需的所有数据集...")
    print("="*50)
    
    download_enwik8()
    download_canterbury()
    download_gutenberg()
    
    print("\n所有数据集下载流程执行完毕！请检查 data/ 目录。")