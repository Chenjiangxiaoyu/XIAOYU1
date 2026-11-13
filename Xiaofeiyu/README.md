# 邮件小肥鱼：本地安装与启动

适用系统：Windows 64 位。程序通过 Agent Mail 读取你授权的邮箱，使用 DeepSeek Harness（DSH）分析邮件并提供对话。首次使用还需安装 Node.js、`agently-cli`，并准备本机可用的 DSH runtime。

## 使用安装包

1. 安装 Node.js，在普通 PowerShell 中运行 `npm install -g @tencent-qqmail/agently-cli`。
2. 解压项目根目录下的 `release/Xiaofeiyu-Windows-x64-preview.zip`。
3. 双击解压目录中的 **安装小肥鱼.cmd**。安装完成后，桌面会出现“小肥鱼”快捷方式。
4. 在这台电脑上完成 Agent Mail 的 OAuth 授权，以及 DSH 的账号登录。两项授权都需要使用者自己完成。
5. 双击桌面快捷方式启动。出现悬浮邮件图标后，点击图标打开窗口；点击刷新按钮可立即同步邮件。

如果邮箱显示未连接，在普通 PowerShell 中运行 `agently-cli.cmd auth status` 检查授权。若尚未登录，再运行 `agently-cli.cmd auth login`。智能分析和对话还需要本机已登录且能正常运行的 DSH runtime。

## 从源码运行

先安装 Python 和 Node.js，在项目根目录打开 PowerShell，执行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install -g @tencent-qqmail/agently-cli
agently-cli.cmd auth login
.\.venv\Scripts\python.exe main.py
```

之后可双击项目根目录的 **启动小肥鱼.bat** 启动。首次运行前还需完成 DSH 登录；如果暂时没有可用的 DSH runtime，邮箱窗口可以启动，但智能分析和对话无法使用。

## 卸载

双击解压目录或安装目录中的 **卸载小肥鱼.cmd**，按提示清理本安装器创建的程序目录和本地设置。共享的 Agent Mail／DSH 授权及云端邮件不会被删除。

