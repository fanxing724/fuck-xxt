# 超星学习通自动刷课脚本 - AGENTS.md

## 项目概述

- **项目名称**: 超星学习通自动刷课脚本 (fuck-xxt)
- **项目路径**: `/Users/fanxing/Desktop/fuck-xxt`
- **技术栈**: Python 3
- **代码托管**: GitHub (git@github.com:fanxing724/fuck-xxt.git)
- **GitHub 加速**: https://xingbox.de5.net/fanxing724/fuck-xxt

## 功能说明

- ✅ 自动完成视频任务（支持 2 倍速）
- ✅ 自动完成文档任务
- ✅ 自动完成阅读任务
- ❌ 不自动答题（章节测验需手动完成）

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 配置账号（复制配置文件）
cp config.ini.example config.ini

# 运行脚本
# Mac/Linux
./run.sh

# Windows
run.bat

# 或直接运行
python main.py
```

## 项目结构

```
├── main.py             # 主程序入口
├── app.py              # 应用逻辑
├── api/                # API 相关
├── config.ini          # 配置文件（git忽略）
├── config.ini.example  # 配置模板
├── requirements.txt    # Python 依赖
├── pyproject.toml      # 项目配置
├── Dockerfile          # Docker 部署
├── run.sh              # Mac/Linux 启动脚本
├── run.bat             # Windows 启动脚本
├── superstar-tutorial.html  # 使用教程页面
├── CNAME               # 自定义域名配置
└── resource/           # 资源文件
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

## 部署方式

- **本地运行**: 直接执行 `run.sh` 或 `run.bat`
- **Docker 部署**: 使用项目自带的 Dockerfile

## 最近修改记录

- 项目信息初始化
