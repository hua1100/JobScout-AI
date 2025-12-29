#!/bin/bash

echo "================================"
echo "104 AI職缺爬蟲 - Mac/Linux版本"
echo "================================"
echo ""

# 檢查Python
echo "[1/4] 檢查Python環境..."
if command -v python3 &> /dev/null; then
    python3 --version
    PYTHON_CMD="python3"
else
    echo "錯誤: 找不到Python! 請先安裝Python 3.8+"
    exit 1
fi
echo ""

# 建立虛擬環境
echo "[2/4] 設定虛擬環境..."
if [ ! -d "venv" ]; then
    echo "建立虛擬環境中..."
    $PYTHON_CMD -m venv venv
    echo "✓ 虛擬環境建立完成"
else
    echo "✓ 虛擬環境已存在"
fi
echo ""

# 啟動虛擬環境
echo "[3/4] 啟動虛擬環境並安裝套件..."
source venv/bin/activate

# 安裝套件
if ! python -c "import scrapy" &> /dev/null; then
    echo "正在安裝Scrapy和相關套件..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✓ 套件安裝完成"
else
    echo "✓ Scrapy已安裝"
fi
echo ""

# 執行爬蟲
echo "[4/4] 開始執行爬蟲..."
echo "這可能需要5-10分鐘,請耐心等待..."
echo ""
scrapy crawl 104_ai_jobs

echo ""
echo "================================"
echo "爬取完成!"
echo "請檢查專案目錄中的CSV檔案"
echo "================================"
echo ""
echo "如要關閉虛擬環境,請執行: deactivate"

# 保持虛擬環境啟動狀態
exec $SHELL
