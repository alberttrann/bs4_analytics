"""
config/settings.py
Owner: Duong (D)
Task : Pydantic BaseSettings — API port, log level, env vars from .env
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API Port và Host
    API_PORT: int = Field(default=8000, description="Cổng chạy ứng dụng API")
    API_HOST: str = Field(default="127.0.0.1", description="Địa chỉ host API")
    
    # Môi trường chạy dự án: "dev" (phát triển) hoặc "prod" (sản xuất)
    ENV: str = Field(default="dev", description="Môi trường chạy ứng dụng")
    
    # Mức độ log hệ thống: DEBUG, INFO, WARNING, ERROR
    LOG_LEVEL: str = Field(default="INFO", description="Mức độ logging hệ thống")

    class Config:
        # Tự động load biến môi trường từ file .env ở thư mục gốc nếu có
        env_file = ".env"
        env_file_encoding = "utf-8"

# Khởi tạo một đối tượng settings dùng chung cho toàn dự án
settings = Settings()
