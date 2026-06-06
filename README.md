# SuperStar 网页控制台版

[![Build and Release](https://github.com/fanxing724/fuck-xxt/actions/workflows/build.yml/badge.svg)](https://github.com/fanxing724/fuck-xxt/actions/workflows/build.yml)

超星学习通自动学习脚本，提供本地网页控制台。默认启动浏览器界面，可填写账号、课程、倍速和 AI 答题配置，并实时查看运行日志。

## 下载

从 [Releases](https://github.com/fanxing724/fuck-xxt/releases) 下载对应平台的预编译包：

| 平台 | 文件 |
|------|------|
| Windows 7+ | `fuck-xxt-windows.zip` (单文件 exe) |
| macOS 10.13+ | `fuck-xxt-macos.tar.gz` |
| Linux | `fuck-xxt-linux.tar.gz` |

下载解压后直接运行即可，无需安装 Python。

## 功能

- 自动完成视频、文档、阅读任务
- 支持课程 ID 留空时学习全部课程
- 支持 OpenAI 兼容接口作为 AI 题库
- 支持自动获取模型列表
- 支持 Windows 7+、macOS 10.13+、Linux

## 快速开始

### macOS / Linux

```bash
cd /Users/fanxing/Desktop/fuck-xxt
./run.sh
```

### Windows

```cmd
cd /d 路径\到\fuck-xxt
run.bat
```

启动后会自动打开浏览器。如果没有自动打开，访问终端里显示的地址，默认是：

```text
http://127.0.0.1:8765/
```

## 网页控制台

网页界面使用 `app/static/background.jpeg` 作为背景图。当前背景图来自本项目的本地静态资源。

网页中可配置：

- 手机号和密码
- 课程 ID，留空表示全部课程
- 视频播放倍速
- AI 答题开关
- OpenAI 兼容 Endpoint、API Key、模型
- 是否直接提交答案
- 是否保存配置

填写 `Endpoint` 和 `API Key` 后，点击“刷新模型”，或开启 AI 答题后自动获取模型列表。

## 命令行模式

根目录仍只使用同一个启动器。需要直接跑命令行任务时：

```bash
./run.sh --cli
```

Windows:

```cmd
run.bat --cli
```

首次命令行运行如果没有 `config.ini`，启动器会从 `config/config.ini.example` 创建一份。

## 配置文件

默认配置文件在项目根目录：

```text
config.ini
```

配置模板在：

```text
config/config.ini.example
```

AI 题库示例：

```ini
[tiku]
provider = AI
submit = false
endpoint = https://api.openai.com/v1
key = your_api_key
model = gpt-4o-mini
http_proxy =
min_interval_seconds = 3
cover_rate = 0.8
true_list = 正确,对,√,是
false_list = 错误,错,×,否,不对,不正确
```

`provider` 留空时禁用 AI 答题。

## 目录结构

```text
.
├── run.sh                    # macOS / Linux 主启动器
├── run.bat                   # Windows 主启动器
├── app/
│   ├── main.py               # 命令行学习入口
│   ├── web_desktop.py        # 本地网页控制台
│   ├── desktop.py            # 备用 Tk 桌面入口
│   ├── api/                  # 核心接口和学习逻辑
│   ├── resource/             # 字体映射等资源
│   └── static/               # 网页静态资源
├── config/
│   └── config.ini.example    # 配置模板
├── docs/
│   └── superstar-tutorial.html
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

## 备用桌面模式

默认启动网页控制台。若需要尝试旧 Tk 桌面界面：

```bash
SUPERSTAR_UI=tk ./run.sh
```

如果只想在 Tk 可用时自动使用桌面、不可用时回退网页：

```bash
SUPERSTAR_UI=auto ./run.sh
```

Windows:

```cmd
set SUPERSTAR_UI=auto
run.bat
```

## 常见问题

### 依赖安装失败

检查网络和 Python 环境。启动器会使用：

```bash
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary
```

### 模型列表获取失败

确认：

- Endpoint 是 OpenAI 兼容接口地址，例如 `https://api.openai.com/v1`
- API Key 可用
- 服务商支持 `GET /models`

如果提示 Cloudflare 403 / 1010，说明服务商拦截了模型列表请求。模型列表只是辅助功能，可以直接在模型输入框手动填写模型名后运行。

如果服务商不支持模型列表接口，可以直接手动输入模型名。

## 免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用本项目造成的任何后果由使用者自行承担。
