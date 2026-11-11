from openai import OpenAI
from core.config import DEEPSEEK_API_KEY, OPENAI_API_KEY

# ========== DeepSeek（优先） ==========
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

def call_deepseek(prompt: str):
    res = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content


# ========== GPT（备用） ==========
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def call_openai(prompt: str):
    res = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content