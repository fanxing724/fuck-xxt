@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0" || exit /b 1

set "APP_MAIN=app\main.py"
set "APP_WEB=app\web_desktop.py"
set "APP_DESKTOP=app\desktop.py"
set "CONFIG_TEMPLATE=config\config.ini.example"

if "%SUPERSTAR_UI%"=="" (
    set "UI_MODE=web"
) else (
    set "UI_MODE=%SUPERSTAR_UI%"
)
if "%PIP_INDEX_URL%"=="" set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"

call :find_python
if errorlevel 1 goto :end

for /f "usebackq delims=" %%i in (`"%PYTHON_CMD%" -c "import sys; print(sys.executable)"`) do set "PYTHON_EXE=%%i"
echo 使用 Python: %PYTHON_EXE%

if /i "%SKIP_DEP_INSTALL%"=="1" (
    echo 已跳过依赖检查。
) else (
    echo 检查依赖...
    "%PYTHON_CMD%" -m pip install -r requirements.txt -i "%PIP_INDEX_URL%" --prefer-binary -q
    if errorlevel 1 (
        echo 依赖安装失败，请检查网络或 Python 环境。可设置 SKIP_DEP_INSTALL=1 跳过。
        pause
        exit /b 1
    )
)

if /i "%~1"=="--cli" goto :cli

if /i "%UI_MODE%"=="web" goto :web
if /i "%UI_MODE%"=="tk" goto :tk
if /i "%UI_MODE%"=="auto" goto :tk

echo 未知 SUPERSTAR_UI=%UI_MODE%，已使用网页控制台。可选值: web, tk, auto。
goto :web

:cli
set "CLI_ARGS=%*"
set "CLI_ARGS=%CLI_ARGS:~5%"
if "%~2"=="" if not exist "config.ini" (
    echo 未找到 config.ini，正在从模板创建...
    copy "%CONFIG_TEMPLATE%" config.ini >nul
    echo 请先编辑 config.ini 填写账号密码，或使用 --cli -u 手机号 -p 密码 直接运行。
    pause
    exit /b 1
)
echo 启动命令行模式...
"%PYTHON_CMD%" -u "%APP_MAIN%" %CLI_ARGS%
exit /b %errorlevel%

:tk
"%PYTHON_CMD%" -c "import tkinter as tk; root = tk.Tk(); root.withdraw(); root.destroy()" >nul 2>"%TEMP%\superstar_tk_error.txt"
if not errorlevel 1 (
    echo 启动桌面版...
    "%PYTHON_CMD%" "%APP_DESKTOP%" %*
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
"%PYTHON_CMD%" "%APP_WEB%" %*
exit /b %errorlevel%

:find_python
set "PYTHON_CMD="
if not "%PYTHON_BIN%"=="" (
    "%PYTHON_BIN%" -c "import sys; raise SystemExit(sys.version_info < (3, 8))" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=%PYTHON_BIN%"
        exit /b 0
    )
    echo 错误：PYTHON_BIN 指定的 Python 不可用: %PYTHON_BIN%
    exit /b 1
)

py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 8))" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)"') do set "PYTHON_CMD=%%i"
    exit /b 0
)

python3 -c "import sys; raise SystemExit(sys.version_info < (3, 8))" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('python3 -c "import sys; print(sys.executable)"') do set "PYTHON_CMD=%%i"
    exit /b 0
)

python -c "import sys; raise SystemExit(sys.version_info < (3, 8))" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set "PYTHON_CMD=%%i"
    exit /b 0
)

for %%p in (
    "%LocalAppData%\Programs\Python\Python314\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%LocalAppData%\Microsoft\WindowsApps\python3.exe"
) do (
    if exist "%%~p" (
        "%%~p" -c "import sys; raise SystemExit(sys.version_info < (3, 8))" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=%%~p"
            exit /b 0
        )
    )
)

echo 错误：未找到 Python，请先安装 Python 3.8+
pause
exit /b 1

:end
exit /b 1
