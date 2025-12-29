#!/bin/bash

echo "================================"
echo "104 AI職缺爬蟲 - Mac/Linux版本"
echo "================================"
echo ""

echo "[1/3] 檢查Python環境..."
if command -v python3 &> /dev/null; then
    python3 --version
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    python --version
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "錯誤: 找不到Python! 請先安裝Python 3.8+"
    exit 1
fi
echo ""

echo "[2/3] 檢查Scrapy是否已安裝..."
if ! scrapy version &> /dev/null; then
    echo "Scrapy未安裝,正在安裝..."
    $PIP_CMD install -r requirements.txt
else
    scrapy version
fi
echo ""

echo "[3/3] 開始執行爬蟲..."
echo "這可能需要5-10分鐘,請耐心等待..."
echo ""
scrapy crawl 104_ai_jobs

echo ""
echo "================================"
echo "爬取完成!"
echo "請檢查專案目錄中的CSV檔案"
echo "================================"
