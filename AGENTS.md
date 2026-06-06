# SuperStar 网页控制台版 - AGENTS.md

## 项目概述

- **项目名称**: SuperStar 网页控制台版 (fuck-xxt)
- **项目路径**: `/Users/fanxing/Desktop/fuck-xxt`
- **技术栈**: Python 3
- **代码托管**: GitHub (git@github.com:fanxing724/fuck-xxt.git)
- **GitHub 加速**: https://xingbox.de5.net/fanxing724/fuck-xxt

## 功能说明

- ✅ 自动完成视频任务（支持 2 倍速）
- ✅ 自动完成文档任务
- ✅ 自动完成阅读任务
- ✅ 可选 OpenAI 兼容 AI 答题
- ✅ 本地网页控制台

## 常用命令

```bash
# 默认启动网页控制台
./run.sh
run.bat

# 命令行模式
./run.sh --cli
run.bat --cli
```

## 项目结构

```
├── run.sh                  # macOS/Linux 主启动器
├── run.bat                 # Windows 主启动器
├── app/
│   ├── main.py             # 命令行学习入口
│   ├── web_desktop.py      # 本地网页控制台
│   ├── desktop.py          # 备用 Tk 桌面入口
│   ├── api/                # API 相关
│   ├── resource/           # 字体映射等资源
│   └── static/             # 网页静态资源
├── config/
│   └── config.ini.example  # 配置模板
├── docs/
│   └── superstar-tutorial.html
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

## 配置说明

编辑 `config.ini`：

```ini
[common]
username = 你的手机号
password = 你的密码
speed = 2
```

## 注意事项

1. `config.ini` 包含敏感信息，已加入 `.gitignore`
2. 不要上传真实的配置文件到代码仓库
3. 脚本仅自动播放视频和文档，不自动答题
4. 仅供个人学习使用
5. 根目录只保留 `run.sh` 和 `run.bat` 两个启动入口

## 部署方式

- **本地运行**: 直接执行 `run.sh` 或 `run.bat`
- **Docker 部署**: 使用项目自带的 Dockerfile

## 最近修改记录

- 项目信息初始化
