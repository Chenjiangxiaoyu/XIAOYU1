import os

# 通用请求头
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# AI接口配置
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 请求延迟防封禁
SLEEP_SECOND = 1
