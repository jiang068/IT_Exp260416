import gzip
import bz2
import lzma
import zstandard as zstd

def gzip_compress(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9)

def gzip_decompress(data: bytes) -> bytes:
    return gzip.decompress(data)

def bzip2_compress(data: bytes) -> bytes:
    return bz2.compress(data, compresslevel=9)

def bzip2_decompress(data: bytes) -> bytes:
    return bz2.decompress(data)

def xz_compress(data: bytes) -> bytes:
    # lzma.FORMAT_XZ 就是通常的 xz 格式
    return lzma.compress(data, format=lzma.FORMAT_XZ, preset=9)

def xz_decompress(data: bytes) -> bytes:
    return lzma.decompress(data, format=lzma.FORMAT_XZ)

def zstd_compress(data: bytes) -> bytes:
    cctx = zstd.ZstdCompressor(level=19) # 使用极高压缩率
    return cctx.compress(data)

def zstd_decompress(data: bytes) -> bytes:
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data)

# 提供一个字典统一调度
TRADITIONAL_COMPRESSORS = {
    "gzip": (gzip_compress, gzip_decompress),
    "bzip2": (bzip2_compress, bzip2_decompress),
    "xz": (xz_compress, xz_decompress),
    "zstd": (zstd_compress, zstd_decompress)
}