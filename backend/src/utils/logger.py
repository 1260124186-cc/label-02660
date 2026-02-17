"""
日志配置模块
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    配置全局日志
    Args:
        log_dir: 日志目录
        level: 日志级别
    Returns:
        根日志记录器
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_path / f"cert_ocr_{timestamp}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件处理器
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 避免重复添加
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    logging.getLogger("ppocr").setLevel(logging.WARNING)
    logging.getLogger("paddle").setLevel(logging.WARNING)

    return root_logger
