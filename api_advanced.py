#!/usr/bin/env python3
"""
104爬蟲API - 進階版
支援: 非同步任務、認證、流量限制、監控
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from celery import Celery
from functools import wraps
import jwt
import redis
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

# ============================================
# 配置
# ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# CORS設定
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    }
})

# 流量限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery設定
celery = Celery(
    app.name,
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)
celery.conf.update(app.config)

# Redis連線 (用於儲存任務結果)
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# 日誌設定
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Scraper API startup')

# ============================================
# 認證裝飾器
# ============================================

def require_api_key(f):
    """API Key認證"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        valid_api_key = os.getenv('API_KEY')
        
        if not api_key or api_key != valid_api_key:
            app.logger.warning(f'Invalid API key attempt from {request.remote_addr}')
            return jsonify({'error': 'Invalid API Key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_jwt(f):
    """JWT Token認證"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        try:
            # 移除 "Bearer " 前綴
            if token.startswith('Bearer '):
                token = token[7:]
            
            # 驗證token
            data = jwt.decode(
                token, 
                app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            # 將用戶資訊附加到request
            request.user_id = data.get('user_id')
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# 輔助函數
# ============================================

def validate_scrape_params(data):
    """驗證爬蟲參數"""
    errors = []
    
    # 檢查必要欄位
    if 'keywords' not in data:
        errors.append('Missing required field: keywords')
    elif not isinstance(data['keywords'], list) or len(data['keywords']) == 0:
        errors.append('keywords must be a non-empty list')
    
    # 驗證頁數
    if 'pages' in data:
        if not isinstance(data['pages'], int) or data['pages'] < 1 or data['pages'] > 50:
            errors.append('pages must be between 1 and 50')
    
    # 驗證地區代碼
    if 'area_codes' in data:
        if not isinstance(data['area_codes'], list):
            errors.append('area_codes must be a list')
        else:
            for code in data['area_codes']:
                if not isinstance(code, str) or not code.isdigit() or len(code) != 10:
                    errors.append(f'Invalid area code format: {code}')
    
    return errors

def generate_task_id():
    """生成唯一的任務ID"""
    return str(uuid.uuid4())

# ============================================
# Celery任務
# ============================================

@celery.task(bind=True, name='tasks.run_scraper')
def run_scraper_task(self, task_id, keywords, pages=5, area_codes=None):
    """
    背景執行爬蟲任務
    
    Args:
        task_id: 任務ID
        keywords: 搜尋關鍵字列表
        pages: 每個關鍵字爬取的頁數
        area_codes: 地區代碼列表
    """
    try:
        # 更新任務狀態
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting scraper...',
                'progress': 0
            }
        )
        
        # 儲存任務資訊到Redis
        redis_client.hset(
            f'task:{task_id}',
            mapping={
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'keywords': json.dumps(keywords),
                'pages': pages,
                'area_codes': json.dumps(area_codes) if area_codes else ''
            }
        )
        redis_client.expire(f'task:{task_id}', 86400)  # 24小時過期
        
        # 執行爬蟲
        # 這裡需要實際執行Scrapy
        # 方法1: 使用subprocess
        import subprocess
        
        # 建立臨時.env設定
        temp_env = {
            'SEARCH_KEYWORDS': ','.join(keywords),
            'SCRAPY_PAGES_PER_KEYWORD': str(pages),
            'AREA_CODES': ','.join(area_codes) if area_codes else ''
        }
        
        # 執行scrapy
        result = subprocess.run(
            ['scrapy', 'crawl', '104_ai_jobs'],
            cwd=os.path.join(os.path.dirname(__file__), 'scraper'),
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, **temp_env}
        )
        
        if result.returncode != 0:
            raise Exception(f'Scraper failed: {result.stderr}')
        
        # 找到產生的CSV檔案
        import glob
        csv_files = sorted(glob.glob('ai_jobs_*.csv'))
        if not csv_files:
            raise Exception('No CSV file generated')
        
        latest_csv = csv_files[-1]
        
        # 計算職缺數量
        with open(latest_csv, 'r', encoding='utf-8') as f:
            job_count = sum(1 for line in f) - 1  # 扣除標題行
        
        # 更新任務完成狀態
        result_data = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'csv_file': latest_csv,
            'job_count': job_count,
            'keywords': keywords,
            'pages': pages,
            'area_codes': area_codes
        }
        
        redis_client.hset(
            f'task:{task_id}',
            mapping={
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'result': json.dumps(result_data)
            }
        )
        
        return result_data
        
    except Exception as e:
        # 記錄錯誤
        error_data = {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        }
        
        redis_client.hset(
            f'task:{task_id}',
            mapping={
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            }
        )
        
        self.update_state(
            state='FAILURE',
            meta=error_data
        )
        
        raise

# ============================================
# API端點
# ============================================

@app.route('/')
def index():
    """API首頁"""
    return jsonify({
        'service': '104 Job Scraper API',
        'version': '2.0',
        'documentation': '/api/docs',
        'endpoints': {
            'auth': {
                'login': 'POST /api/auth/login',
                'token': 'POST /api/auth/token'
            },
            'scraper': {
                'start': 'POST /api/scrape',
                'status': 'GET /api/tasks/<task_id>',
                'result': 'GET /api/tasks/<task_id>/result',
                'list': 'GET /api/tasks'
            },
            'system': {
                'health': 'GET /health',
                'stats': 'GET /api/stats'
            }
        }
    })

@app.route('/health')
def health_check():
    """健康檢查"""
    checks = {
        'api': 'healthy',
        'redis': 'healthy' if redis_client.ping() else 'unhealthy',
    }
    
    all_healthy = all(v == 'healthy' for v in checks.values())
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }), 200 if all_healthy else 503

@app.route('/api/auth/token', methods=['POST'])
@limiter.limit("10 per hour")
def generate_token():
    """生成JWT Token"""
    data = request.get_json()
    
    # 簡單的驗證 (實際應該查詢數據庫)
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # 這裡應該驗證用戶憑證
    # 為了示範,我們直接生成token
    
    token = jwt.encode({
        'user_id': username,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'expires_in': 604800  # 7天(秒)
    })

@app.route('/api/scrape', methods=['POST'])
@limiter.limit("10 per hour")
@require_api_key  # 或使用 @require_jwt
def start_scrape():
    """
    啟動爬蟲任務
    
    Request Body:
    {
        "keywords": ["AI自動化", "RPA"],
        "pages": 5,
        "area_codes": ["6001001000", "6001002000"],
        "webhook_url": "https://your-domain.com/webhook" (optional)
    }
    
    Response:
    {
        "task_id": "uuid",
        "status": "pending",
        "message": "Task created successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # 驗證參數
        errors = validate_scrape_params(data)
        if errors:
            return jsonify({'errors': errors}), 400
        
        # 提取參數
        keywords = data['keywords']
        pages = data.get('pages', 5)
        area_codes = data.get('area_codes')
        webhook_url = data.get('webhook_url')
        
        # 生成任務ID
        task_id = generate_task_id()
        
        # 記錄請求
        app.logger.info(f'New scrape task: {task_id}, keywords: {keywords}')
        
        # 啟動Celery任務
        task = run_scraper_task.apply_async(
            args=[task_id, keywords, pages, area_codes],
            task_id=task_id
        )
        
        # 儲存webhook URL
        if webhook_url:
            redis_client.hset(f'task:{task_id}', 'webhook_url', webhook_url)
        
        return jsonify({
            'task_id': task_id,
            'status': 'pending',
            'message': 'Task created successfully',
            'check_status_url': f'/api/tasks/{task_id}'
        }), 202
        
    except Exception as e:
        app.logger.error(f'Error creating task: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/tasks/<task_id>', methods=['GET'])
@require_api_key
def get_task_status(task_id):
    """
    查詢任務狀態
    
    Response:
    {
        "task_id": "uuid",
        "status": "pending|running|completed|failed",
        "started_at": "2025-01-01T00:00:00",
        "completed_at": "2025-01-01T00:05:00",
        "progress": 50
    }
    """
    try:
        # 從Redis取得任務資訊
        task_info = redis_client.hgetall(f'task:{task_id}')
        
        if not task_info:
            return jsonify({'error': 'Task not found'}), 404
        
        # 轉換byte為string
        task_data = {k.decode(): v.decode() for k, v in task_info.items()}
        
        response = {
            'task_id': task_id,
            'status': task_data.get('status', 'unknown'),
            'started_at': task_data.get('started_at'),
        }
        
        if task_data.get('status') == 'completed':
            response['completed_at'] = task_data.get('completed_at')
            response['result'] = json.loads(task_data.get('result', '{}'))
        elif task_data.get('status') == 'failed':
            response['error'] = task_data.get('error')
            response['failed_at'] = task_data.get('failed_at')
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f'Error getting task status: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/tasks/<task_id>/result', methods=['GET'])
@require_api_key
def get_task_result(task_id):
    """
    下載任務結果(CSV檔案)
    """
    try:
        task_info = redis_client.hgetall(f'task:{task_id}')
        
        if not task_info:
            return jsonify({'error': 'Task not found'}), 404
        
        task_data = {k.decode(): v.decode() for k, v in task_info.items()}
        
        if task_data.get('status') != 'completed':
            return jsonify({'error': 'Task not completed yet'}), 400
        
        result = json.loads(task_data.get('result', '{}'))
        csv_file = result.get('csv_file')
        
        if not csv_file or not os.path.exists(csv_file):
            return jsonify({'error': 'Result file not found'}), 404
        
        from flask import send_file
        return send_file(
            csv_file,
            as_attachment=True,
            download_name=f'jobs_{task_id}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        app.logger.error(f'Error getting task result: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/tasks', methods=['GET'])
@require_api_key
def list_tasks():
    """列出所有任務"""
    try:
        # 從Redis掃描所有任務
        tasks = []
        for key in redis_client.scan_iter(match='task:*', count=100):
            task_id = key.decode().replace('task:', '')
            task_info = redis_client.hgetall(key)
            task_data = {k.decode(): v.decode() for k, v in task_info.items()}
            
            tasks.append({
                'task_id': task_id,
                'status': task_data.get('status'),
                'started_at': task_data.get('started_at')
            })
        
        # 按時間排序
        tasks.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        
        return jsonify({
            'tasks': tasks,
            'total': len(tasks)
        })
        
    except Exception as e:
        app.logger.error(f'Error listing tasks: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    """取得統計資訊"""
    try:
        # 計算各種狀態的任務數量
        stats = {
            'total': 0,
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0
        }
        
        for key in redis_client.scan_iter(match='task:*'):
            stats['total'] += 1
            status = redis_client.hget(key, 'status')
            if status:
                status = status.decode()
                if status in stats:
                    stats[status] += 1
        
        return jsonify(stats)
        
    except Exception as e:
        app.logger.error(f'Error getting stats: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

# ============================================
# 錯誤處理
# ============================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Something went wrong'
    }), 500

# ============================================
# 啟動
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("104 Scraper API Server")
    print("=" * 60)
    print(f"Environment: {'Production' if not app.debug else 'Development'}")
    print(f"Redis: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    print(f"API Key required: {'Yes' if os.getenv('API_KEY') else 'No (WARNING!)'}")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST /api/scrape - Start scraping task")
    print("  GET  /api/tasks/<id> - Get task status")
    print("  GET  /api/tasks/<id>/result - Download result")
    print("  GET  /api/tasks - List all tasks")
    print("  GET  /health - Health check")
    print("=" * 60)
    
    # 開發環境直接運行Flask
    # 生產環境請使用: gunicorn -w 4 api_advanced:app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )
