@echo off
chcp 65001
echo ================================
echo 104 AI職缺爬蟲 - Windows版本
echo ================================
echo.

echo [1/3] 檢查Python環境...
python --version
if %errorlevel% neq 0 (
    echo 錯誤: 找不到Python! 請先安裝Python 3.8+
    pause
    exit /b 1
)
echo.

echo [2/3] 檢查Scrapy是否已安裝...
scrapy version
if %errorlevel% neq 0 (
    echo Scrapy未安裝,正在安裝...
    pip install -r requirements.txt
)
echo.

echo [3/3] 開始執行爬蟲...
echo 這可能需要5-10分鐘,請耐心等待...
echo.
scrapy crawl 104_ai_jobs

echo.
echo ================================
echo 爬取完成!
echo 請檢查專案目錄中的CSV檔案
echo ================================
pause
