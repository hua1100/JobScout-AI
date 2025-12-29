#!/usr/bin/env python3
"""
104爬蟲API - 供Make.com或其他服務呼叫
"""

from flask import Flask, jsonify, request
import subprocess
import os
import glob
from datetime import datetime
import json

app = Flask(__name__)

# 設定爬蟲專案路徑
SCRAPER_PATH = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """API首頁"""
    return jsonify({
        'service': '104 Job Scraper API',
        'version': '1.0',
        'endpoints': {
            'trigger': '/trigger-scraper (POST)',
            'status': '/status (GET)',
            'latest': '/latest-file (GET)'
        }
    })

@app.route('/trigger-scraper', methods=['POST'])
def trigger_scraper():
    """觸發爬蟲執行"""
    try:
        print(f"[{datetime.now()}] 收到爬蟲觸發請求")
        
        # 執行爬蟲
        result = subprocess.run(
            ['scrapy', 'crawl', '104_ai_jobs'],
            cwd=SCRAPER_PATH,
            capture_output=True,
            text=True,
            timeout=600  # 10分鐘超時
        )
        
        # 檢查執行結果
        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': '爬蟲執行失敗',
                'error': result.stderr
            }), 500
        
        # 找到最新的CSV檔案
        csv_files = sorted(glob.glob(os.path.join(SCRAPER_PATH, 'ai_jobs_*.csv')))
        
        if not csv_files:
            return jsonify({
                'status': 'error',
                'message': '找不到輸出的CSV檔案'
            }), 500
        
        latest_csv = os.path.basename(csv_files[-1])
        
        # 計算職缺數量
        with open(csv_files[-1], 'r', encoding='utf-8') as f:
            job_count = sum(1 for line in f) - 1  # 扣除標題行
        
        print(f"[{datetime.now()}] 爬蟲執行成功,產生檔案: {latest_csv}")
        
        return jsonify({
            'status': 'success',
            'message': '爬蟲執行完成',
            'csv_file': latest_csv,
            'full_path': csv_files[-1],
            'job_count': job_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': '爬蟲執行超時(>10分鐘)'
        }), 500
        
    except Exception as e:
        print(f"[{datetime.now()}] 錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'執行錯誤: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """取得API狀態"""
    csv_files = glob.glob(os.path.join(SCRAPER_PATH, 'ai_jobs_*.csv'))
    
    if csv_files:
        latest_file = max(csv_files, key=os.path.getctime)
        file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
        
        return jsonify({
            'status': 'online',
            'last_scrape': file_time.isoformat(),
            'latest_file': os.path.basename(latest_file),
            'total_files': len(csv_files)
        })
    else:
        return jsonify({
            'status': 'online',
            'last_scrape': None,
            'message': '尚未執行過爬蟲'
        })

@app.route('/latest-file', methods=['GET'])
def get_latest_file():
    """取得最新CSV檔案資訊"""
    csv_files = glob.glob(os.path.join(SCRAPER_PATH, 'ai_jobs_*.csv'))
    
    if not csv_files:
        return jsonify({
            'status': 'error',
            'message': '找不到CSV檔案'
        }), 404
    
    latest_file = max(csv_files, key=os.path.getctime)
    file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
    
    # 讀取前5筆資料作為預覽
    preview_data = []
    with open(latest_file, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            preview_data.append(row)
    
    return jsonify({
        'status': 'success',
        'filename': os.path.basename(latest_file),
        'full_path': latest_file,
        'created_at': file_time.isoformat(),
        'file_size': os.path.getsize(latest_file),
        'preview': preview_data
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 50)
    print("104爬蟲API伺服器啟動中...")
    print("=" * 50)
    print(f"專案路徑: {SCRAPER_PATH}")
    print(f"API端點:")
    print(f"  - http://localhost:5000/")
    print(f"  - http://localhost:5000/trigger-scraper (POST)")
    print(f"  - http://localhost:5000/status (GET)")
    print(f"  - http://localhost:5000/latest-file (GET)")
    print("=" * 50)
    
    # 啟動Flask伺服器
    app.run(
        host='0.0.0.0',  # 允許外部存取
        port=5000,
        debug=False
    )
