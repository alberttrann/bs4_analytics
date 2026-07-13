"""
config/logging.py
Owner: Duong (D)
Task : Logging config — colored console in dev, JSON in prod
"""
import sys
import logging
import json
from datetime import datetime
from config.settings import settings

# Định nghĩa cấu trúc formatter cho môi trường Production (Định dạng JSON)
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line_no": record.lineno
        }
        # Nếu có thông tin lỗi Exception thì kèm vào log JSON luôn
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

# Hàm cấu hình hệ thống log chính
def setup_logging():
    # Lấy level log từ file settings cấu hình sẵn
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Xóa bỏ các handler cũ nếu có để tránh bị lặp log
    if logger.handlers:
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    
    if settings.ENV.lower() == "prod":
        # Môi trường Production: Sử dụng JSON Formatter
        handler.setFormatter(JsonFormatter())
    else:
        # Môi trường Development: Sử dụng màu sắc mã ANSI để console rực rỡ
        # \033[36m: Xanh lam (DEBUG), \033[32m: Xanh lá (INFO), \033[33m: Vàng (WARNING), \033[31m: Đỏ (ERROR)
        COLOR_FORMAT = (
            "\033[90m%(asctime)s\033[0m | "
            "%(levelname)s: "
            "\033[36m%(message)s\033[0m "
            "\033[94m(%(filename)s:%(lineno)d)\033[0m"
        )
        handler.setFormatter(logging.Formatter(COLOR_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))

    logger.addHandler(handler)
    
    # In một dòng thông báo trạng thái log đã sẵn sàng
    logging.info(f" Hệ thống Logging đã kích hoạt thành công trên môi trường: [{settings.ENV.upper()}]")

# Tự động chạy cấu hình log ngay khi module này được import
setup_logging()