import scrapy
from scrapy.http import FormRequest
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# 載入.env設定檔
load_dotenv()


class A104Spider(scrapy.Spider):
    name = "104_ai_jobs"
    allowed_domains = ["www.104.com.tw"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-TW",
            "origin": "https://www.104.com.tw/",
            "referer": "https://www.104.com.tw/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
            "Content-Type": "application/json",
        }
    }

    start_url = "https://www.104.com.tw/jobs/search/list"
    
    def __init__(self, *args, **kwargs):
        super(A104Spider, self).__init__(*args, **kwargs)
        
        # 1. 處理關鍵字: 優先使用 CLI 參數 (scrapy crawl -a keywords="A,B")
        if hasattr(self, 'keywords') and self.keywords:
            if isinstance(self.keywords, str):
                self.keywords = [k.strip() for k in self.keywords.split(",")]
        else:
            # Fallback: 從.env讀取搜尋關鍵字
            keywords_str = os.getenv("SEARCH_KEYWORDS", "AI自動化,AI轉型,數位轉型,流程自動化,RPA,AI工程師")
            self.keywords = [k.strip() for k in keywords_str.split(",")]
        
        # 2. 處理地區代碼: 優先使用 CLI 參數
        if hasattr(self, 'area_codes') and self.area_codes:
             if isinstance(self.area_codes, str):
                self.area_codes = [a.strip() for a in self.area_codes.split(",")]
             self.logger.info(f"地區篩選(CLI): {', '.join(self.area_codes)}")
        else:
            # Fallback: 從.env讀取地區代碼
            area_codes_str = os.getenv("AREA_CODES", "")
            if area_codes_str:
                self.area_codes = [a.strip() for a in area_codes_str.split(",")]
                self.logger.info(f"地區篩選(ENV): {', '.join(self.area_codes)}")
            else:
                self.area_codes = []
                self.logger.info("地區篩選: 不限地區(全台灣)")
        
        # 3. 處理頁數: 優先使用 CLI 參數
        try:
            if hasattr(self, 'pages'):
                 self.pages_per_keyword = int(self.pages)
            else:
                 self.pages_per_keyword = int(os.getenv("SCRAPY_PAGES_PER_KEYWORD", "5"))

            if not 1 <= self.pages_per_keyword <= 50:
                self.logger.warning(f"頁數設定異常,使用預設值5頁")
                self.pages_per_keyword = 5
        except:
            self.logger.warning("無法讀取頁數設定,使用預設值5頁")
            self.pages_per_keyword = 5

        # 4. 處理遠端工作模式: 優先使用 CLI 參數
        # full: 完全遠端, partial: 部分遠端, both: 兩者皆可
        self.remote_mode = getattr(self, 'remote_mode', None)
        if self.remote_mode:
            self.logger.info(f"遠端工作篩選: {self.remote_mode}")
        
        self.logger.info(f"搜尋關鍵字: {', '.join(self.keywords)}")
        self.logger.info(f"每個關鍵字爬取: {self.pages_per_keyword} 頁")

    def start_requests(self):
        for keyword in self.keywords:
            self.logger.info(f'開始搜尋關鍵字: {keyword}')
            for i in range(self.pages_per_keyword):
                # 建立URL參數
                url_params = f"?page={i+1}&keyword={keyword}"
                
                # 如果有設定地區代碼,加入area參數
                if self.area_codes:
                    area_param = "&area=" + ",".join(self.area_codes)
                    url_params += area_param

                # 處理遠端工作參數
                if self.remote_mode:
                    if self.remote_mode == 'full':
                        url_params += "&remoteWork=1"
                    elif self.remote_mode == 'partial':
                        url_params += "&remoteWork=2"
                    elif self.remote_mode == 'both':
                        url_params += "&remoteWork=1,2"
                
                yield FormRequest(
                    url=self.start_url + url_params,
                    method="GET",
                    callback=self.parse,
                    meta={'keyword': keyword, 'page': i+1}
                )

    def parse(self, response):
        try:
            body = json.loads(response.body)
            jobs = body["data"]["list"]
            keyword = response.meta.get('keyword', '')
            page = response.meta.get('page', 1)
            
            self.logger.info(f'關鍵字 "{keyword}" 第{page}頁: 找到 {len(jobs)} 筆職缺')
            
            for job in jobs:
                yield {
                    'search_keyword': keyword,  # 記錄是用哪個關鍵字找到的
                    'jobName': job.get('jobName', ''),
                    'jobRole': self._get_job_role_text(job.get('jobRole', '')),
                    'jobAddrNoDesc': job.get('jobAddrNoDesc', ''),
                    'jobAddress': job.get('jobAddress', ''),
                    'description': job.get('description', ''),
                    'optionEdu': job.get('optionEdu', ''),
                    'periodDesc': job.get('periodDesc', ''),
                    'applyCnt': job.get('applyCnt', 0),
                    'custName': job.get('custName', ''),
                    'coIndustryDesc': job.get('coIndustryDesc', ''),
                    'salaryLow': job.get('salaryLow', 0),
                    'salaryHigh': job.get('salaryHigh', 0),
                    'appearDate': datetime.strptime(job['appearDate'], "%Y%m%d").strftime("%Y-%m-%d") if job.get('appearDate') else '',
                    'jobLink': "https:" + job["link"]["job"].split("?")[0] if job.get('link') and job['link'].get('job') else '',
                    'remoteWorkType': self._get_remote_work_text(job.get('remoteWorkType', 0)),
                    'major': ','.join(job.get('major', [])) if job.get('major') else '',
                    'salaryType': self._get_salary_type_text(job.get('salaryType', '')),
                }
        except Exception as e:
            self.logger.error(f'解析錯誤: {e}')
    
    def _get_job_role_text(self, role):
        """將工作型態代碼轉為文字"""
        role_map = {1: '正職', 2: '兼職', 3: '高階'}
        return role_map.get(role, '未知')
    
    def _get_remote_work_text(self, remote_type):
        """將遠端工作代碼轉為文字"""
        remote_map = {0: '不可遠端', 1: '完全遠端', 2: '部分遠端'}
        return remote_map.get(remote_type, '未知')
    
    def _get_salary_type_text(self, salary_type):
        """將薪資型態代碼轉為文字"""
        salary_map = {'H': '時薪', 'M': '月薪', 'Y': '年薪', '': '面議'}
        return salary_map.get(salary_type, salary_type)
