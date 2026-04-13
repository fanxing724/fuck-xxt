@echo off
chcp 65001 >nul
echo ==========================================
echo   超星学习通自动刷课脚本
echo ==========================================

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo Python版本: 
python --version

REM 检查依赖是否已安装
echo.
echo 检查依赖...
pip install -r requirements.txt -q

echo.
echo 开始运行刷课脚本...
echo ==========================================

REM 运行主程序
python main.py %*

echo.
echo ==========================================
echo   程序已退出
echo ==========================================
pause
