#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import logging
from datetime import datetime, timedelta
import pytz
import argparse

# 导入自定义模块
from crawler.article_fetcher import ArticleContentFetcher
from crawler.article_parser import ArticleParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ArticleMain")

class ArticleContentCrawler:
    """人民日报文章爬虫主程序
    
    负责协调文章获取模块和解析模块，完成单篇文章的爬取、解析和输出流程。
    """
    
    def __init__(self, date_string=None, output_dir=None):
        """初始化爬虫
        
        Args:
            date_string (str, optional): 目标日期，格式为YYYYMMDD
            output_dir (str, optional): 输出目录，默认为模块所在目录下的output文件夹
        """
        # 设置默认日期
        if date_string is None:
            # 使用当天日期（中国时区）
            self.date_string = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d')
        else:
            self.date_string = date_string
        
        # 初始化子模块
        self.fetcher = ArticleContentFetcher(output_dir=output_dir)
        self.parser = ArticleParser()
        
        # 设置输出目录
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
    
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
                - article_url (str): 文章URL
                - html_path (str): HTML文件保存路径
                - date_string (str): 日期字符串
        """
        logger.info(f"开始爬取人民日报 {self.date_string[:4]}年{self.date_string[4:6]}月{self.date_string[6:8]}日 的首篇文章")
        
        # 调用fetch_and_save_article方法获取并保存文章
        result = self.fetcher.fetch_and_save_article(self.date_string)
        
        if result['success']:
            logger.info(f"成功爬取并保存文章：{result['html_path']}")
        else:
            logger.error("文章爬取失败")
        
        return result

def crawl_article(date=None, output_dir=None):
    """爬取人民日报指定日期的单篇文章
    
    Args:
        date (str, optional): 要爬取的日期，格式YYYYMMDD
        output_dir (str, optional): 输出目录
        
    Returns:
        dict: 爬取结果
    """
    # 验证日期格式
    if date:
        try:
            # 简单验证日期格式
            if not re.match(r'^\d{8}$', date):
                raise ValueError("日期格式不正确")
                
            # 创建爬虫实例
            crawler = ArticleContentCrawler(date_string=date, output_dir=output_dir)
        except ValueError as e:
            logger.error(f"错误：{str(e)}，日期格式应为YYYYMMDD，例如：20250408")
            return {'success': False, 'date_string': date}
    else:
        # 使用默认日期（当天）
        crawler = ArticleContentCrawler(output_dir=output_dir)
    
    # 执行爬取
    return crawler.crawl()

def main():
    """文章爬虫主入口函数"""
    parser = argparse.ArgumentParser(description='人民日报单篇文章爬虫工具')
    parser.add_argument('-d', '--date', help='指定日期，格式: YYYYMMDD，默认为今天')
    parser.add_argument('-o', '--output_dir', help='输出目录路径')
    args = parser.parse_args()
    
    # 获取当前北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"人民日报文章爬虫启动 (北京时间: {china_time})")
    
    # 执行爬取过程
    result = crawl_article(args.date, args.output_dir)
    
    # 根据爬取结果输出信息
    if result['success']:
        logger.info(f"文章成功获取并保存到: {result['html_path']}")
        logger.info(f"文章URL: {result['article_url']}")
        return 0
    else:
        logger.error(f"文章获取失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 