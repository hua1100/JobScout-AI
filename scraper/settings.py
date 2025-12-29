# Scrapy settings for scraper project (支援.env設定)

import os
from dotenv import load_dotenv

# 載入.env設定檔
load_dotenv()

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Log設定 - 從.env讀取
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_STDOUT = True

# Obey robots.txt rules - 從.env讀取
ROBOTSTXT_OBEY = os.getenv("ROBOTSTXT_OBEY", "false").lower() == "true"

# Configure maximum concurrent requests - 從.env讀取
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "16"))

# Download delay - 從.env讀取
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", "0.5"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "60"))
RANDOMIZE_DOWNLOAD_DELAY = os.getenv("RANDOMIZE_DOWNLOAD_DELAY", "true").lower() == "true"

CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv("CONCURRENT_REQUESTS", "16"))

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.CsvPipeline": 300,
}

# Feed exports - 從.env讀取輸出設定
output_filename = os.getenv("OUTPUT_FILENAME", "ai_jobs")
output_format = os.getenv("OUTPUT_FORMAT", "csv")
csv_encoding = os.getenv("CSV_ENCODING", "utf-8-sig")

FEEDS = {
    f'{output_filename}_%(time)s.{output_format}': {
        'format': output_format,
        'encoding': csv_encoding,
        'overwrite': False,
        'fields': [
            'search_keyword',
            'jobName',
            'custName',
            'coIndustryDesc',
            'jobRole',
            'salaryLow',
            'salaryHigh',
            'salaryType',
            'jobAddrNoDesc',
            'jobAddress',
            'remoteWorkType',
            'optionEdu',
            'periodDesc',
            'major',
            'applyCnt',
            'appearDate',
            'description',
            'jobLink',
        ]
    }
}

# AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 8
AUTOTHROTTLE_DEBUG = False

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
