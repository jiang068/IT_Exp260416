import os
import urllib.request
import zipfile

def download_enwik8(data_dir="data"):
    os.makedirs(data_dir, exist_ok=True)
    zip_path = os.path.join(data_dir, "enwik8.zip")
    txt_path = os.path.join(data_dir, "enwik8")

    if os.path.exists(txt_path):
        print(f"[Download] {txt_path} 已存在，跳过下载。")
        return txt_path

    # 下载原始 enwik8
    url = "http://mattmahoney.net/dc/enwik8.zip"
    print(f"[Download] 正在从 {url} 下载 enwik8.zip...")
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("[Download] 下载完成，正在解压...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print("[Download] 解压完成！")
    except Exception as e:
        print(f"下载失败: {e}")
        print("建议尝试手动下载并解压到 data/ 目录下。")
        
    return txt_path

if __name__ == "__main__":
    download_enwik8()