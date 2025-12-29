# API使用範例

## 目錄
1. [快速開始](#快速開始)
2. [認證方式](#認證方式)
3. [API端點說明](#api端點說明)
4. [使用範例](#使用範例)
5. [錯誤處理](#錯誤處理)
6. [Make.com整合](#makecom整合)

---

## 快速開始

### 1. 啟動API服務

```bash
# 方法1: 直接運行 (開發環境)
python api_advanced.py

# 方法2: 使用Gunicorn (生產環境)
gunicorn -w 4 -b 0.0.0.0:5000 api_advanced:app

# 方法3: 使用Docker
docker-compose up -d
```

### 2. 設定環境變數

建立 `.env` 檔案:

```bash
# API設定
SECRET_KEY=your-super-secret-key-change-this
API_KEY=your-api-key-here

# Redis設定
REDIS_URL=redis://localhost:6379/0

# CORS設定
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Debug模式 (生產環境設為false)
DEBUG=false
```

### 3. 啟動Celery Worker

```bash
# 在另一個終端機視窗
celery -A api_advanced.celery worker --loglevel=info
```

---

## 認證方式

### 方法1: API Key認證 (推薦給自動化工具)

在請求header中加入API Key:

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["AI自動化"]}'
```

### 方法2: JWT Token認證 (推薦給前端應用)

#### Step 1: 取得Token

```bash
curl -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
```

回應:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 604800
}
```

#### Step 2: 使用Token呼叫API

```bash
curl -X POST http://localhost:5000/api/scrape \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["AI自動化"]}'
```

---

## API端點說明

### 1. 啟動爬蟲任務

**POST** `/api/scrape`

**請求參數:**
```json
{
  "keywords": ["AI自動化", "AI轉型", "RPA"],
  "pages": 5,
  "area_codes": ["6001001000", "6001002000"],
  "webhook_url": "https://your-domain.com/webhook"
}
```

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| keywords | array | ✅ | 搜尋關鍵字列表 |
| pages | integer | ❌ | 每個關鍵字爬取的頁數(預設5,最大50) |
| area_codes | array | ❌ | 地區代碼列表 |
| webhook_url | string | ❌ | 完成後回調的URL |

**回應:**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "pending",
  "message": "Task created successfully",
  "check_status_url": "/api/tasks/f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**HTTP狀態碼:**
- `202 Accepted` - 任務已建立
- `400 Bad Request` - 參數錯誤
- `401 Unauthorized` - 認證失敗
- `429 Too Many Requests` - 超過流量限制

---

### 2. 查詢任務狀態

**GET** `/api/tasks/{task_id}`

**回應 (pending/running):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "running",
  "started_at": "2025-01-30T10:00:00"
}
```

**回應 (completed):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "started_at": "2025-01-30T10:00:00",
  "completed_at": "2025-01-30T10:05:30",
  "result": {
    "csv_file": "ai_jobs_20250130_100530.csv",
    "job_count": 287,
    "keywords": ["AI自動化", "AI轉型"],
    "pages": 5
  }
}
```

**回應 (failed):**
```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "failed",
  "error": "Connection timeout",
  "failed_at": "2025-01-30T10:03:00"
}
```

---

### 3. 下載結果

**GET** `/api/tasks/{task_id}/result`

**回應:**
- 直接下載CSV檔案
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="jobs_{task_id}.csv"`

---

### 4. 列出所有任務

**GET** `/api/tasks`

**回應:**
```json
{
  "tasks": [
    {
      "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "completed",
      "started_at": "2025-01-30T10:00:00"
    },
    {
      "task_id": "a12bc34d-56ef-7890-gh12-ij34kl567890",
      "status": "running",
      "started_at": "2025-01-30T09:30:00"
    }
  ],
  "total": 2
}
```

---

### 5. 健康檢查

**GET** `/health`

**回應:**
```json
{
  "status": "healthy",
  "checks": {
    "api": "healthy",
    "redis": "healthy"
  },
  "timestamp": "2025-01-30T10:00:00"
}
```

---

### 6. 統計資訊

**GET** `/api/stats`

**回應:**
```json
{
  "total": 150,
  "pending": 2,
  "running": 5,
  "completed": 130,
  "failed": 13
}
```

---

## 使用範例

### Python範例

```python
import requests
import time

# API設定
API_URL = "http://localhost:5000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. 啟動爬蟲
response = requests.post(
    f"{API_URL}/api/scrape",
    headers=headers,
    json={
        "keywords": ["AI自動化", "RPA"],
        "pages": 5,
        "area_codes": ["6001001000", "6001002000"]
    }
)

if response.status_code == 202:
    task_id = response.json()["task_id"]
    print(f"任務已建立: {task_id}")
    
    # 2. 輪詢任務狀態
    while True:
        status_response = requests.get(
            f"{API_URL}/api/tasks/{task_id}",
            headers=headers
        )
        
        status_data = status_response.json()
        print(f"狀態: {status_data['status']}")
        
        if status_data['status'] == 'completed':
            print(f"完成! 找到 {status_data['result']['job_count']} 筆職缺")
            
            # 3. 下載結果
            result_response = requests.get(
                f"{API_URL}/api/tasks/{task_id}/result",
                headers=headers
            )
            
            with open(f"jobs_{task_id}.csv", "wb") as f:
                f.write(result_response.content)
            
            print(f"結果已儲存至 jobs_{task_id}.csv")
            break
            
        elif status_data['status'] == 'failed':
            print(f"失敗: {status_data['error']}")
            break
        
        # 等待10秒後再查詢
        time.sleep(10)
else:
    print(f"錯誤: {response.json()}")
```

---

### JavaScript/Node.js範例

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:5000';
const API_KEY = 'your-api-key-here';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// 1. 啟動爬蟲
async function startScraping() {
  try {
    const response = await axios.post(
      `${API_URL}/api/scrape`,
      {
        keywords: ['AI自動化', 'RPA'],
        pages: 5,
        area_codes: ['6001001000', '6001002000']
      },
      { headers }
    );
    
    const taskId = response.data.task_id;
    console.log(`任務已建立: ${taskId}`);
    
    // 2. 輪詢任務狀態
    return await pollTaskStatus(taskId);
    
  } catch (error) {
    console.error('錯誤:', error.response?.data || error.message);
  }
}

// 輪詢任務狀態
async function pollTaskStatus(taskId) {
  while (true) {
    try {
      const response = await axios.get(
        `${API_URL}/api/tasks/${taskId}`,
        { headers }
      );
      
      const status = response.data.status;
      console.log(`狀態: ${status}`);
      
      if (status === 'completed') {
        console.log(`完成! 找到 ${response.data.result.job_count} 筆職缺`);
        
        // 3. 下載結果
        await downloadResult(taskId);
        break;
        
      } else if (status === 'failed') {
        console.error(`失敗: ${response.data.error}`);
        break;
      }
      
      // 等待10秒
      await new Promise(resolve => setTimeout(resolve, 10000));
      
    } catch (error) {
      console.error('查詢錯誤:', error.message);
      break;
    }
  }
}

// 下載結果
async function downloadResult(taskId) {
  try {
    const response = await axios.get(
      `${API_URL}/api/tasks/${taskId}/result`,
      { 
        headers,
        responseType: 'arraybuffer'
      }
    );
    
    const fs = require('fs');
    fs.writeFileSync(`jobs_${taskId}.csv`, response.data);
    console.log(`結果已儲存至 jobs_${taskId}.csv`);
    
  } catch (error) {
    console.error('下載錯誤:', error.message);
  }
}

// 執行
startScraping();
```

---

### cURL範例

```bash
#!/bin/bash

API_URL="http://localhost:5000"
API_KEY="your-api-key-here"

# 1. 啟動爬蟲
echo "啟動爬蟲..."
RESPONSE=$(curl -s -X POST "$API_URL/api/scrape" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI自動化", "RPA"],
    "pages": 5,
    "area_codes": ["6001001000", "6001002000"]
  }')

TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "任務ID: $TASK_ID"

# 2. 輪詢任務狀態
while true; do
  echo "查詢狀態..."
  STATUS_RESPONSE=$(curl -s -X GET "$API_URL/api/tasks/$TASK_ID" \
    -H "X-API-Key: $API_KEY")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  echo "狀態: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    JOB_COUNT=$(echo $STATUS_RESPONSE | jq -r '.result.job_count')
    echo "完成! 找到 $JOB_COUNT 筆職缺"
    
    # 3. 下載結果
    echo "下載結果..."
    curl -X GET "$API_URL/api/tasks/$TASK_ID/result" \
      -H "X-API-Key: $API_KEY" \
      -o "jobs_$TASK_ID.csv"
    
    echo "結果已儲存至 jobs_$TASK_ID.csv"
    break
    
  elif [ "$STATUS" = "failed" ]; then
    ERROR=$(echo $STATUS_RESPONSE | jq -r '.error')
    echo "失敗: $ERROR"
    break
  fi
  
  sleep 10
done
```

---

## 錯誤處理

### 常見錯誤碼

| 狀態碼 | 說明 | 處理方式 |
|--------|------|----------|
| 400 | 參數錯誤 | 檢查請求參數格式 |
| 401 | 認證失敗 | 檢查API Key或Token |
| 404 | 任務不存在 | 確認task_id正確 |
| 429 | 超過流量限制 | 等待後重試 |
| 500 | 伺服器錯誤 | 聯繫管理員 |
| 503 | 服務不可用 | 檢查服務狀態 |

### 錯誤回應格式

```json
{
  "error": "Bad Request",
  "message": "keywords must be a non-empty list"
}
```

---

## Make.com整合

### Scenario設定

#### 模組1: Schedule
- 觸發時機: 每月1號
- 時區: Asia/Taipei

#### 模組2: HTTP Request - 啟動爬蟲
- URL: `https://your-api.com/api/scrape`
- Method: POST
- Headers:
  ```json
  {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
  }
  ```
- Body:
  ```json
  {
    "keywords": ["AI自動化", "AI轉型"],
    "pages": 5,
    "area_codes": ["6001001000", "6001002000"]
  }
  ```
- 儲存回應中的 `task_id`

#### 模組3: Sleep
- 延遲: 300秒 (5分鐘)

#### 模組4: HTTP Request - 查詢狀態
- URL: `https://your-api.com/api/tasks/{{task_id}}`
- Method: GET
- Headers: (同上)

#### 模組5: Router
- 路徑1: status = "completed" → 下載結果
- 路徑2: status = "running" → 返回模組3繼續等待
- 路徑3: status = "failed" → 發送錯誤通知

#### 模組6: HTTP Request - 下載結果
- URL: `https://your-api.com/api/tasks/{{task_id}}/result`
- Method: GET
- Headers: (同上)
- 儲存回應為檔案

#### 模組7: Google Drive - Upload
- File: 上一步的檔案
- Folder: 選擇目標資料夾

#### 模組8: Gmail - Send Email
- To: 你的Email
- Subject: `104職缺爬蟲完成`
- Body: 
  ```
  爬取完成!
  
  職缺數量: {{job_count}}
  檔案: {{google_drive_link}}
  ```

---

## 最佳實踐

### 1. 錯誤重試

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### 2. 超時設定

```python
response = requests.post(
    url,
    headers=headers,
    json=data,
    timeout=30  # 30秒超時
)
```

### 3. 流量控制

```python
import time

def rate_limited_request(func, min_interval=6):
    """每次請求至少間隔6秒 (10次/分鐘)"""
    last_call = [0]
    
    def wrapper(*args, **kwargs):
        elapsed = time.time() - last_call[0]
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        result = func(*args, **kwargs)
        last_call[0] = time.time()
        return result
    
    return wrapper
```

---

需要更多範例或有其他問題,請隨時詢問!
