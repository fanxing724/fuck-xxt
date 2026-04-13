#!/bin/bash
# 超星学习通自动刷课 - 一键运行

echo "============================================"
echo "  超星学习通自动刷课脚本"
echo "  功能：自动完成视频、文档、阅读任务"
echo "  注意：章节测验需手动完成"
echo "============================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装"
    echo "   下载地址：https://www.python.org/downloads/"
    read -p "按回车键退出..."
    exit 1
fi

echo "✓ Python版本: $(python3 --version)"

# 检查config.ini
if [ ! -f "config.ini" ]; then
    echo ""
    echo "⚠️  未找到config.ini，正在创建..."
    cp config.ini.example config.ini
    echo ""
    echo "❌ 请先编辑 config.ini 填写账号密码！"
    read -p "按回车键退出..."
    exit 1
fi

# 安装依赖
echo ""
echo "📦 检查依赖..."
pip3 install -r requirements.txt -q 2>/dev/null

echo ""
echo "🚀 开始运行..."
echo "============================================"

python3 main.py "$@"

echo ""
echo "============================================"
echo "  程序已退出"
echo "============================================"
read -p "按回车键关闭窗口..."
