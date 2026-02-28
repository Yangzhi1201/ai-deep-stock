# -*- coding: utf-8 -*-
"""
全局配置 —— 通过 pydantic-settings 读取 .env 环境变量
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent   # 项目根目录


class Settings(BaseSettings):
    """所有可配置项，优先读取环境变量 / .env 文件"""

    # --- 服务 ---
    app_name: str = "stock-recommender"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # --- 邮件 ---
    email_smtp_server: str = "smtp.qq.com"
    email_smtp_port: int = 465
    email_sender: str = ""
    email_password: str = ""
    email_receiver: str = ""

    # --- 定时任务 ---
    scheduler_hour: int = 9
    scheduler_minute: int = 0

    # --- 选股 ---
    hot_stock_count: int = 10
    recommend_count: int = 3

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
