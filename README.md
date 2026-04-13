# 超星学习通自动刷课脚本

## 使用方法

### Linux/Mac

```bash
# 一键运行
./run.sh

# 或者直接使用命令行参数
python3 main.py -u 手机号 -p 密码 -c config.ini
```

### Windows

```cmd
REM 一键运行
run.bat

REM 或者直接使用命令行参数
python main.py -u 手机号 -p 密码 -c config.ini
```

## 配置

编辑 `config.ini` 文件，填写你的账号信息：

```ini
[common]
username = 你的手机号
password = 你的密码
course_list = 课程ID（可选，逗号分隔）
speed = 2  # 播放倍速

[tiku]
provider = TikuYanxi
tokens = 你的题库Token
submit = false  # 是否自动提交答题
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-u, --username` | 手机号账号 |
| `-p, --password` | 登录密码 |
| `-c, --config` | 配置文件路径 |
| `-l, --list` | 要学习的课程ID列表，以 `, 分隔 |
| `-s, --speed` | 视频播放倍速（默认1.0，最大2） |
| `-v, --verbose` | 启用调试模式 |
| `-a, --notopen-action` | 遇到关闭任务点时的行为：retry/ask/continue |

## 依赖

```bash
pip install -r requirements.txt
```

## 免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用本项目造成的任何后果由使用者自行承担。
