@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "UI_MODE=%SUPERSTAR_UI%"
if "%UI_MODE%"=="" set "UI_MODE=web"

set "APP_MAIN=app\main.py"
set "APP_WEB=app\web_desktop.py"
set "APP_DESKTOP=app\desktop.py"
set "CONFIG_TEMPLATE=config\config.ini.example"

:: 检测可用的 Python
set "PYTHON_CMD="
if not "%PYTHON_BIN%"=="" (
    "%PYTHON_BIN%" -c "exit(0)" >nul 2>&1 && set "PYTHON_CMD=%PYTHON_BIN%"
)
if "%PYTHON_CMD%"=="" (
    py -3 -c "exit(0)" >nul 2>&1 && (for /f %%i in ('py -3 -c "import sys; print(sys.executable)"') do set "PYTHON_CMD=%%i")
)
if "%PYTHON_CMD%"=="" (
    python -c "exit(0)" >nul 2>&1 && (for /f %%i in ('python -c "import sys; print(sys.executable)"') do set "PYTHON_CMD=%%i")
)
:: 搜索常见安装路径
if "%PYTHON_CMD%"=="" (
    for %%p in (
        "%LocalAppData%\Python\pythoncore-3.14-64\python.exe"
        "%LocalAppData%\Programs\Python\Python314\python.exe"
        "%ProgramFiles%\Python314\python.exe"
        "%ProgramFiles(x86)%\Python314-64\python.exe"
        "C:\Python314\python.exe"
        "%LocalAppData%\Microsoft\WindowsApps\python3.exe"
    ) do (
        if exist "%%~p" (
            "%%~p" -c "exit(0)" >nul 2>&1 && set "PYTHON_CMD=%%~p" && goto :found_python
        )
    )
)
:found_python
if "%PYTHON_CMD%"="" (
    echo 错误：未找到 Python，请先安装 Python 3.9+ 
    pause
    exit /b 1
)
echo 使用 Python: %PYTHON_CMD%

echo 检查依赖...
%PYTHON_CMD% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary -q
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查网络或 Python 环境
    pause
    exit /b 1
)

if /i "%1"=="--cli" goto cli

if /i "%UI_MODE%"=="web" goto web
if /i not "%UI_MODE%"=="tk" if /i not "%UI_MODE%"=="auto" goto web

%PYTHON_CMD% -c "import tkinter as tk; root = tk.Tk(); root.withdraw(); root.destroy()" >nul 2>"%TEMP%\superstar_tk_error.txt"
if %errorlevel% equ 0 (
    echo 启动桌面版...
    %PYTHON_CMD% "%APP_DESKTOP%"
    exit /b %errorlevel%
)

if /i "%UI_MODE%"=="tk" (
    echo 桌面版无法在当前 Python/Tk 环境启动。
    type "%TEMP%\superstar_tk_error.txt"
    pause
    exit /b 1
)

echo 当前 Python/Tk 无法启动桌面窗口，已自动切换到网页控制台。
type "%TEMP%\superstar_tk_error.txt"
echo.

:web
echo 启动网页控制台...
%PYTHON_CMD% "%APP_WEB%" %*
exit /b %errorlevel%

:cli
shift
if not exist "config.ini" (
    echo 未找到 config.ini，正在从模板创建...
    copy "%CONFIG_TEMPLATE%" config.ini >nul
    echo 请先编辑 config.ini 填写账号密码。
    pause
    exit /b 1
)
%PYTHON_CMD% "%APP_MAIN%" %1 %2 %3 %4 %5 %6 %7 %8 %9
exit /b %errorlevel%
