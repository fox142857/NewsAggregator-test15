#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import re
import sys
import logging
import argparse
from datetime import datetime
from urllib.parse import urljoin
import pytz  # 添加pytz库导入

# 导入自定义模块
from crawler.fetcher import PeoplesDailyFetcher
from crawler.parser import PeoplesDailyParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("CrawlerMain")

class PeoplesDailyCrawler:
    """人民日报爬虫主程序
    
    负责协调网页获取模块和解析模块，完成爬取、解析和输出流程。
    """
    
    def __init__(self, target_url=None, output_dir=None):
        """初始化爬虫
        
        Args:
            target_url (str, optional): 目标URL，默认为人民日报当天的版面
            output_dir (str, optional): 输出目录，默认为模块所在目录下的output文件夹
        """
        # 设置默认目标URL
        if target_url is None:
            # 使用当天日期构造URL（使用中国时区）
            today = datetime.now(pytz.timezone('Asia/Shanghai'))
            target_url = f"http://paper.people.com.cn/rmrb/pc/layout/{today.strftime('%Y%m')}/{today.strftime('%d')}/node_01.html"
        
        self.target_url = target_url
        
        # 初始化子模块
        self.fetcher = PeoplesDailyFetcher()
        self.parser = PeoplesDailyParser()
        
        # 设置输出目录
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 从URL中提取日期
        date_match = re.search(r'/(\d{6})/(\d{2})/', self.target_url)
        if date_match:
            self.date_string = date_match.group(1) + date_match.group(2)
        else:
            # 使用中国时区的当前日期
            self.date_string = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d')
    
    def save_to_file(self, content, filename):
        """保存内容到文件
        
        Args:
            content (str): 文件内容
            filename (str): 文件名
            
        Returns:
            str: 保存的文件路径
        """
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已保存到: {filepath}")
        return filepath
    
    def crawl(self):
        """执行爬取流程
        
        Returns:
            dict: 包含爬取结果的字典，keys包括:
                - success (bool): 爬取是否成功
                - versions_data (list): 版面数据列表
                - date_string (str): 日期字符串
                - html_path (str): HTML报告路径
        """
        logger.info(f"开始爬取人民日报 {self.date_string[:4]}年{self.date_string[4:6]}月{self.date_string[6:8]}日 的所有版面新闻")
        
        result = {
            'success': False,
            'versions_data': [],
            'date_string': self.date_string,
            'html_path': ''
        }
        
        # 1. 获取首页内容
        base_url, main_html = self.fetcher.get_edition_by_date(
            int(self.date_string[:4]), 
            int(self.date_string[4:6]), 
            int(self.date_string[6:8])
        )
        
        if not main_html:
            logger.error("获取首页失败，退出爬取")
            return result
        
        # 2. 提取所有版面链接
        versions = self.parser.extract_versions(main_html, base_url)
        if not versions:
            logger.error("未找到版面链接，退出爬取")
            return result
        
        logger.info(f"找到 {len(versions)} 个版面，开始爬取每个版面的新闻...")
        
        # 3. 提取每个版面的新闻
        all_versions_data = []
        
        for version in versions:
            # 控制请求速率
            time.sleep(0.5)
            
            # 获取版面内容
            version_html = self.fetcher.get_news_content(version['url'])
            if not version_html:
                logger.warning(f"获取版面 {version['title']} 失败，跳过")
                continue
            
            # 提取版面中的新闻列表
            news_items = self.parser.extract_news_list(version_html, version['url'])
            
            # 添加版面数据
            version_data = {
                'title': version['title'],
                'url': version['url'],
                'news': news_items
            }
            all_versions_data.append(version_data)
            
            logger.info(f"已爬取 {version['title']} 版面，发现 {len(news_items)} 条新闻")
        
        # 4. 生成HTML报告
        logger.info("正在生成HTML报告...")
        html_content = self.parser.generate_html_report(all_versions_data, self.date_string)
        
        # 5. 保存HTML结果
        output_filename = f"{self.date_string}.html"
        html_path = self.save_to_file(html_content, output_filename)
        
        # 6. 更新结果
        result['success'] = True
        result['versions_data'] = all_versions_data
        result['html_path'] = html_path
        
        logger.info(f"爬取完成! 共爬取 {len(all_versions_data)} 个版面")
        return result

def crawl_peoples_daily(date=None, output_dir=None):
    """爬取人民日报指定日期的内容
    
    Args:
        date (str, optional): 要爬取的日期，格式YYYYMMDD
        output_dir (str, optional): 输出目录
        
    Returns:
        dict: 爬取结果
    """
    # 如果指定了日期，构造URL
    if date:
        # 解析日期
        try:
            year = date[:4]
            month = date[4:6]
            day = date[6:8]
            
            url = f"http://paper.people.com.cn/rmrb/pc/layout/{year}{month}/{day}/node_01.html"
            crawler = PeoplesDailyCrawler(target_url=url, output_dir=output_dir)
        except (ValueError, IndexError):
            logger.error(f"错误：日期格式无效，应为YYYYMMDD，例如：20250408")
            return {'success': False}
    else:
        # 使用默认URL（当天日期）
        crawler = PeoplesDailyCrawler(output_dir=output_dir)
    
    # 执行爬取
    return crawler.crawl()

def main(args=None):
    """主程序入口"""
    if args is None:
        parser = argparse.ArgumentParser(description='人民日报爬虫模块')
        parser.add_argument('-d', '--date', help='指定日期，格式: YYYYMMDD，默认为今天')
        parser.add_argument('-o', '--output_dir', help='输出目录')
        args = parser.parse_args()
    
    logger.info("爬虫模块启动")
    
    result = crawl_peoples_daily(args.date, args.output_dir)
    
    if result['success']:
        logger.info("爬取成功完成")
        return 0
    else:
        logger.error("爬取失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 