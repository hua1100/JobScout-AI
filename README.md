# 104 AI職缺爬蟲 🚀

自動爬取104人力銀行的AI相關職缺,包含:AI自動化、AI轉型、數位轉型、流程自動化、RPA等。

## ⚡ 快速開始 (3步驟)

### Windows用戶
1. 解壓縮此檔案
2. 雙擊 `run_scraper.bat`
3. 完成!查看產生的CSV檔案

### Mac/Linux用戶
1. 解壓縮此檔案
2. 開啟終端機,執行:
   ```bash
   cd 解壓縮的資料夾
   chmod +x run_scraper.sh
   ./run_scraper.sh
   ```
3. 完成!查看產生的CSV檔案

### 手動執行
```bash
# 1. 安裝套件
pip install -r requirements.txt

# 2. 執行爬蟲
scrapy crawl 104_ai_jobs
```

## 📁 檔案說明

```
104-scraper-package/
├── .env                      # ⭐ 設定檔(可修改關鍵字、頁數等)
├── requirements.txt          # Python套件清單
├── scrapy.cfg               # Scrapy配置
├── run_scraper.bat          # Windows一鍵執行
├── run_scraper.sh           # Mac/Linux一鍵執行
├── 完整安裝指南.md          # 📖 詳細說明文件
├── 本機執行指南.md          # 📖 快速入門
└── scraper/
    ├── settings.py          # Scrapy設定
    ├── pipelines.py         # 資料處理管道
    └── spiders/
        └── a104.py          # 爬蟲主程式
```

## ⚙️ 自訂設定

編輯 `.env` 檔案:

```bash
# 修改搜尋關鍵字
SEARCH_KEYWORDS="AI自動化,機器學習,深度學習"

# 🆕 設定地區 (只搜尋雙北地區)
AREA_CODES="6001001000,6001002000"

# 修改每個關鍵字爬取頁數(建議1-10)
SCRAPY_PAGES_PER_KEYWORD=5

# 修改延遲時間(被封鎖時增加)
DOWNLOAD_DELAY=0.5
```

### 常用地區代碼
- 台北市: `6001001000`
- 新北市: `6001002000`
- 桃園市: `6001004000`
- 台中市: `6001008000`
- 台南市: `6001013000`
- 高雄市: `6001016000`

**更多地區代碼請參考「地區代碼對照表.md」**

## 📊 輸出結果

執行完成後會產生:
- **ai_jobs_YYYYMMDD_HHMMSS.csv**
- 包含 200-600 筆 AI相關職缺
- 欄位:職缺名稱、公司、薪資、地點、描述、連結等

## 🔧 環境需求

- Python 3.8+ (建議3.11或3.12)
- pip
- 網路連線

如果沒有Python:
- Windows: https://www.python.org/downloads/
- Mac: `brew install python3`
- Linux: `sudo apt install python3`

## 📚 詳細文件

請參考:
- **完整安裝指南.md** - 詳細的安裝和設定說明
- **本機執行指南.md** - 快速入門教學

## ⚠️ 注意事項

- ✅ 個人求職使用
- ✅ 學習研究用途
- ❌ 商業轉售資料
- ❌ 過度頻繁爬取

請合理使用,尊重104網站服務條款。

## 🐛 常見問題

### Q: 執行時出現 "No module named 'scrapy'"
A: 執行 `pip install scrapy`

### Q: 中文亂碼
A: Excel開啟時選擇「UTF-8」編碼

### Q: 爬不到資料
A: 增加 `.env` 中的 `DOWNLOAD_DELAY` 到 1.0 或 2.0

更多問題請參考「完整安裝指南.md」

## 📧 問題回報

如有問題,請檢查:
1. Python版本是否 3.8+
2. 是否已安裝所有套件
3. 網路連線是否正常
4. `.env` 設定是否正確

---

**祝求職順利!** 🎉
