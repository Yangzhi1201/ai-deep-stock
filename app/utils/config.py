import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 邮箱配置（支持新旧两种环境变量名）
EMAIL_CONFIG = {
    "smtp_server": os.getenv("EMAIL_SMTP_SERVER") or os.getenv("SMTP_SERVER", "smtp.qq.com"),
    "smtp_port": int(os.getenv("EMAIL_SMTP_PORT") or os.getenv("SMTP_PORT", 465)),
    "sender": os.getenv("EMAIL_SENDER") or os.getenv("SENDER", "505557473@qq.com"),
    "password": os.getenv("EMAIL_PASSWORD") or os.getenv("PASSWORD", "你的QQ邮箱授权码"),
    "receiver": [email.strip() for email in (os.getenv("EMAIL_RECEIVER") or os.getenv("RECEIVER", "505557473@qq.com")).split(",")],
}

# 股票分析配置
HOT_STOCK_COUNT = int(os.getenv("HOT_STOCK_COUNT", 10))
RECOMMEND_COUNT = int(os.getenv("RECOMMEND_COUNT", 3))