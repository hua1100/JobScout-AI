#!/bin/bash

echo "================================"
echo "104 AI職缺爬蟲 - uv 版本"
echo "================================"
echo ""

# 檢查 uv 是否安裝
if ! command -v uv &> /dev/null; then
    echo "錯誤: 找不到 uv! 請先安裝 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 建立虛擬環境 (如果不存在)
if [ ! -d ".venv" ]; then
    echo "正在使用 uv 建立虛擬環境..."
    uv venv
else
    echo "✓ 虛擬環境已存在 (.venv)"
fi

# 安裝依賴
echo "正在檢查並安裝依賴..."
uv pip install -r requirements.txt

# 執行爬蟲
echo ""
echo "開始執行爬蟲..."
echo "這可能需要5-10分鐘,請耐心等待..."
echo ""

# 使用 uv run 執行命令，它會自動使用 .venv 中的環境
uv run scrapy crawl 104_ai_jobs

echo ""
echo "================================"
echo "爬取完成!"
echo "請檢查專案目錄中的CSV檔案"
echo "================================"
