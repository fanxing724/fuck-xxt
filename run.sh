#!/bin/bash
# SuperStar 主启动器：默认网页控制台，--cli 进入命令行模式

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PYTHON_BIN="${PYTHON_BIN:-python3}"
UI_MODE="${SUPERSTAR_UI:-web}"
APP_MAIN="app/main.py"
APP_WEB="app/web_desktop.py"
APP_DESKTOP="app/desktop.py"
CONFIG_TEMPLATE="config/config.ini.example"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "错误：未找到 Python3，请先安装"
    exit 1
fi

echo "检查依赖..."
if ! "$PYTHON_BIN" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary -q; then
    echo "依赖安装失败，请检查网络或 Python 环境"
    exit 1
fi

if [ "$1" = "--cli" ]; then
    shift
    if [ ! -f "config.ini" ]; then
        echo "未找到 config.ini，正在从模板创建..."
        cp "$CONFIG_TEMPLATE" config.ini
        echo "请先编辑 config.ini 填写账号密码。"
        exit 1
    fi
    exec "$PYTHON_BIN" "$APP_MAIN" "$@"
fi

if [ "$UI_MODE" = "tk" ] || [ "$UI_MODE" = "auto" ]; then
    TK_CHECK_OUTPUT=$("$PYTHON_BIN" -c 'import tkinter as tk; root = tk.Tk(); root.withdraw(); root.destroy(); print("tk ok")' 2>&1)
    TK_CHECK_STATUS=$?
    if [ "$TK_CHECK_STATUS" -eq 0 ]; then
        echo "启动桌面版..."
        exec "$PYTHON_BIN" "$APP_DESKTOP"
    fi

    if [ "$UI_MODE" = "tk" ]; then
        echo "桌面版无法在当前 Python/Tk 环境启动。"
        echo "$TK_CHECK_OUTPUT"
        exit 1
    fi

    echo "当前 Python/Tk 无法启动桌面窗口，已自动切换到网页控制台。"
    echo "$TK_CHECK_OUTPUT"
    echo ""
fi

echo "启动网页控制台..."
exec "$PYTHON_BIN" "$APP_WEB" "$@"
