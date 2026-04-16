import sys
import os
from datetime import datetime

class TeeLogger:
    """拦截 sys.stdout，将输出同时发送到终端和日志文件"""
    def __init__(self, log_file):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.terminal = sys.stdout
        self.log = open(log_file, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def setup_console_logger(log_dir="logs", prefix="exp"):
    """初始化日志记录器，按时间戳生成独立日志文件"""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{prefix}_{timestamp}.log")
    
    sys.stdout = TeeLogger(log_file)
    print(f"[Logger] 终端输出已同步记录至: {log_file}")
    return log_file