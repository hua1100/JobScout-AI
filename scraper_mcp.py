from mcp.server.fastmcp import FastMCP
import subprocess
import glob
import os
import sys
import pandas as pd
import json

# 初始化 MCP Server
mcp = FastMCP("104-Jobs-Scraper")

@mcp.tool()
def run_scraper(keywords: str, pages: int = 1) -> str:
    """
    執行 104 職缺爬蟲。
    
    Args:
        keywords: 搜尋關鍵字，多個關鍵字用逗號分隔 (例如: "AI工程師,Python")
        pages: 每個關鍵字要爬取的頁數 (預設 1 頁，建議不超過 5 頁以免太久)
    """
    print(f"正在執行爬蟲: keywords={keywords}, pages={pages}")
    
    # 確保參數型別正確
    pages = int(pages)
    
    # 建構指令
    # 使用 sys.executable 確保使用當前環境的 Python (即 uv venv)
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "104_ai_jobs",
        "-a", f"keywords={keywords}",
        "-a", f"pages={pages}"
    ]
    
    try:
        # 執行爬蟲，並捕獲輸出
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # 尋找最新產生的 CSV 檔案
        list_of_files = glob.glob('ai_jobs_*.csv') 
        if not list_of_files:
            return "爬蟲執行完成，但找不到產出的 CSV 檔案。請檢查 logs。"
            
        latest_file = max(list_of_files, key=os.path.getctime)
        return f"爬蟲執行成功！\n已產出檔案: {latest_file}\n搜尋條件: {keywords}\n爬取頁數: {pages}"
        
    except subprocess.CalledProcessError as e:
        return f"爬蟲執行失敗:\nError: {e.stderr}"

@mcp.tool()
def get_latest_job_data(limit: int = 10) -> str:
    """
    讀取最新爬取得的職缺資料 (CSV)，返回 JSON 格式供分析。
    
    Args:
        limit: 要返回的資料筆數 (預設 10 筆，避免 context window 爆掉)
    """
    list_of_files = glob.glob('ai_jobs_*.csv')
    if not list_of_files:
        return "尚未找到任何職缺資料檔案 (ai_jobs_*.csv)。請先執行爬蟲。"
        
    latest_file = max(list_of_files, key=os.path.getctime)
    
    try:
        # 讀取 CSV
        df = pd.read_csv(latest_file)
        
        # 簡單清理或選取重要欄位 (可選)
        # 假設我們只回傳前 N 筆
        data = df.head(limit).to_dict(orient='records')
        
        info = {
            "filename": latest_file,
            "total_rows": len(df),
            "preview_limit": limit,
            "data": data
        }
        
        return json.dumps(info, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"讀取檔案失敗 ({latest_file}): {str(e)}"

if __name__ == "__main__":
    # 使用 uv run scraper_mcp.py 執行時，FastMCP 會自動處理 stdio 連線
    print("Starting 104 Scraper MCP Server...", file=sys.stderr)
    mcp.run()
