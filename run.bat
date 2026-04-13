@echo off
chcp 65001 >nul
echo ============================================
echo   超星学习通自动刷课脚本
echo   功能：自动完成视频、文档、阅读任务
echo   注意：章节测验需手动完成
echo ============================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python已安装

REM 检查config.ini
if not exist "config.ini" (
    echo.
    echo ⚠️  未找到config.ini，正在创建...
    copy config.ini.example config.ini >nul
    echo.
    echo ❌ 请先编辑 config.ini 填写账号密码！
    pause
    exit /b 1
)

REM 安装依赖
echo.
echo 📦 检查依赖...
pip install -r requirements.txt -q 2>nul

echo.
echo 🚀 开始运行...
echo ============================================

python main.py %*

echo.
echo ============================================
echo   程序已退出
echo ============================================
pause
