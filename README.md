# 超星学习通自动刷课脚本

> 小白友好版：配置简单，安全可靠

## 功能说明

- ✅ 自动完成**视频任务**（支持2倍速）
- ✅ 自动完成**文档任务**
- ✅ 自动完成**阅读任务**
- ❌ **章节测验需要手动完成**（安全起见，不自动答题）

## 快速开始

### 第一步：安装依赖

```bash
pip install -r requirements.txt
```

### 第二步：配置账号

复制并编辑配置文件：

```bash
cp config.ini.example config.ini
```

编辑 `config.ini`，填写你的手机号和密码：

```ini
[common]
username = 你的手机号
password = 你的密码
speed = 2
```

### 第三步：运行脚本

**Mac/Linux:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

## 常见问题

### Q: 如何只学习某几门课程？

在 `config.ini` 中填写课程ID：

```ini
course_list = 255200448,123456789
```

课程ID会在首次运行时显示出来。

### Q: 视频播放太慢怎么办？

修改 `speed` 参数，最大支持2倍速：

```ini
speed = 2
```

### Q: 章节测验能自动完成吗？

**不能。** 为了账号安全，章节测验需要手动完成。脚本会自动跳过测验任务。

### Q: 运行出错怎么办？

1. 检查手机号和密码是否正确
2. 检查网络连接
3. 使用 `-v` 参数查看详细错误信息：

```bash
python3 main.py -v
```

## 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-u` | 手机号 | `python3 main.py -u 13800138000` |
| `-p` | 密码 | `python3 main.py -p yourpassword` |
| `-l` | 课程ID列表 | `python3 main.py -l 123456,789012` |
| `-s` | 播放倍速 | `python3 main.py -s 2` |
| `-c` | 配置文件 | `python3 main.py -c myconfig.ini` |
| `-v` | 调试模式 | `python3 main.py -v` |

## 免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用本项目造成的任何后果由使用者自行承担。
