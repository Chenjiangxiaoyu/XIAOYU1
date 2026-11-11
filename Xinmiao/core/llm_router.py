import os

# ===== GPT =====
def call_gpt(prompt):
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "⚠️ GPT暂时无法调用（缺少API Key）"

        client = OpenAI(api_key=api_key)

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception as e:
        return "⚠️ GPT暂时无法调用（网络或服务异常）"


# ===== DeepSeek =====
def call_deepseek(prompt):
    try:
        from openai import OpenAI

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "⚠️ DeepSeek暂时无法调用（缺少API Key）"

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception:
        return "⚠️ DeepSeek暂时无法调用（网络或服务异常）"


# ===== 路由器（重点）=====
def call_llm(prompt, model="gpt"):
    if model == "deepseek":
        return call_deepseek(prompt)

    return call_gpt(prompt)