#!/bin/bash
# 超星学习通自动刷课脚本 - 一键运行脚本

echo "=========================================="
echo "  超星学习通自动刷课脚本"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "Python版本: $(python3 --version)"

# 检查依赖是否已安装
echo ""
echo "检查依赖..."
pip3 install -r requirements.txt -q

echo ""
echo "开始运行刷课脚本..."
echo "=========================================="

# 运行主程序
python3 main.py "$@"

echo ""
echo "=========================================="
echo "  程序已退出"
echo "=========================================="
