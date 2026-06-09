#!/usr/bin/env bash
# 番星 StudyFlow 主启动器：默认网页控制台，--cli 进入命令行模式

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

APP_MAIN="app/main.py"
APP_WEB="app/web_desktop.py"
APP_DESKTOP="app/desktop.py"
CONFIG_TEMPLATE="config/config.ini.example"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
UI_MODE="${SUPERSTAR_UI:-web}"

find_python() {
    if [ -n "${PYTHON_BIN:-}" ]; then
        command -v "$PYTHON_BIN" >/dev/null 2>&1 && return 0
        echo "错误：PYTHON_BIN 指定的 Python 不可用: $PYTHON_BIN"
        return 1
    fi
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
        return 0
    fi
    if command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
        return 0
    fi
    echo "错误：未找到 Python，请先安装 Python 3.8+"
    return 1
}

install_deps() {
    if [ "${SKIP_DEP_INSTALL:-0}" = "1" ]; then
        echo "已跳过依赖检查。"
        return 0
    fi
    echo "检查依赖..."
    "$PYTHON_BIN" -m pip install -r requirements.txt -i "$PIP_INDEX_URL" --prefer-binary -q
}

ensure_cli_config_if_needed() {
    if [ "$#" -eq 0 ] && [ ! -f "config.ini" ]; then
        echo "未找到 config.ini，正在从模板创建..."
        cp "$CONFIG_TEMPLATE" config.ini
        echo "请先编辑 config.ini 填写账号密码，或使用 --cli -u 手机号 -p 密码 直接运行。"
        exit 1
    fi
}

start_tk_or_fallback() {
    TK_CHECK_OUTPUT=$("$PYTHON_BIN" -c 'import tkinter as tk; root = tk.Tk(); root.withdraw(); root.destroy(); print("tk ok")' 2>&1)
    TK_CHECK_STATUS=$?
    if [ "$TK_CHECK_STATUS" -eq 0 ]; then
        echo "启动桌面版..."
        exec "$PYTHON_BIN" "$APP_DESKTOP" "$@"
    fi

    if [ "$UI_MODE" = "tk" ]; then
        echo "桌面版无法在当前 Python/Tk 环境启动。"
        echo "$TK_CHECK_OUTPUT"
        exit 1
    fi

    echo "当前 Python/Tk 无法启动桌面窗口，已自动切换到网页控制台。"
    echo "$TK_CHECK_OUTPUT"
    echo ""
}

find_python || exit 1
echo "使用 Python: $($PYTHON_BIN -c 'import sys; print(sys.executable)')"

if ! install_deps; then
    echo "依赖安装失败，请检查网络或 Python 环境。可设置 SKIP_DEP_INSTALL=1 跳过。"
    exit 1
fi

if [ "${1:-}" = "--cli" ]; then
    shift
    ensure_cli_config_if_needed "$@"
    echo "启动命令行模式..."
    exec "$PYTHON_BIN" -u "$APP_MAIN" "$@"
fi

case "$UI_MODE" in
    web|"")
        ;;
    tk|auto)
        start_tk_or_fallback "$@"
        ;;
    *)
        echo "未知 SUPERSTAR_UI=${UI_MODE}，已使用网页控制台。可选值: web, tk, auto。"
        ;;
esac

echo "启动网页控制台..."
exec "$PYTHON_BIN" "$APP_WEB" "$@"
