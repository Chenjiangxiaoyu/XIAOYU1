# 追星行程规划系统

一个基于 FastAPI 的追星出行规划网页，包含演出、火车、航班和酒店数据抓取模块，并调用 DeepSeek API 生成行程建议。

## 本地启动

需要 Python 3.9 或更高版本。在本目录运行：

```bash
python -m pip install -r requirements.txt
```

设置 DeepSeek API 密钥（不要把真实密钥提交到 GitHub）：

PowerShell：
```powershell
$env:AI_API_KEY="你的密钥"
```

macOS/Linux：
```bash
export AI_API_KEY="你的密钥"
```

启动网页：
```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000 。

## 说明

首页由 FastAPI 提供，单独打开 HTML 文件或 GitHub 文件页不会调用后端接口。生成行程需要后端运行、有效的 DeepSeek API 密钥和外网访问。抓取模块依赖第三方网站的接口/页面结构，网站规则变化、反爬限制或 Chrome/ChromeDriver 环境不匹配都可能导致实时数据抓取失败。此仓库只保存源码，不会自动部署成在线网站。
