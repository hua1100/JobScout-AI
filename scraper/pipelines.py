# 簡化版 Pipeline - 不需要 Elasticsearch

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class CsvPipeline:
    """簡單的去重處理,重複的職缺會被跳過"""
    
    def __init__(self):
        self.seen_jobs = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 使用 jobLink 作為唯一識別
        job_link = adapter.get('jobLink')
        
        if job_link in self.seen_jobs:
            raise DropItem(f"重複職缺: {adapter.get('jobName')}")
        else:
            self.seen_jobs.add(job_link)
            return item
