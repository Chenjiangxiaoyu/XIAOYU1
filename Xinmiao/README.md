# Xinmiao 多技能 AI 系统

基于 Gradio 的多技能 AI 助手。系统根据用户输入进行意图识别、检索匹配技能、重写提示词，并调用 OpenAI 或 DeepSeek 模型生成回答。界面还提供本地历史记录查询和统计功能。

## 本地运行

需要 Python 3.10 或更新版本。

```powershell
cd Xinmiao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，填入你自己的 `OPENAI_API_KEY` 和/或 `DEEPSEEK_API_KEY`，然后运行：

```powershell
python app.py
```

Gradio 会在终端显示本地访问地址。请勿把真实 API 密钥、`.env` 或包含个人输入的 `history.json` 提交到公开仓库。

## 在线运行说明

本项目依赖 Python 服务进程和模型 API 密钥，不是纯静态网页，不能直接通过 GitHub Pages 运行完整功能。需要部署到支持 Python 的应用托管服务，并将 API 密钥保存在该服务的私密环境变量中。
