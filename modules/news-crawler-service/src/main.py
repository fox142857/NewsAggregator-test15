#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from datetime import datetime
import pytz  # 添加pytz库导入

# 导入自定义模块
from crawler.main import crawl_peoples_daily
from converter.main import convert_to_markdown

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("NewsAggregatorMain")

def process_news(date=None, output_dir=None):
    """处理新闻流程
    
    Args:
        date (str, optional): 指定日期，格式YYYYMMDD
        output_dir (str, optional): 输出目录
        
    Returns:
        bool: 处理是否成功
    """
    # 设置默认输出目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
    
    # 使用北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"开始处理新闻数据流程 (北京时间: {china_time})")
    
    # 1. 爬取数据
    logger.info("第一步: 爬取人民日报数据")
    crawl_result = crawl_peoples_daily(date, output_dir)
    
    if not crawl_result['success']:
        logger.error("爬取数据失败，处理终止")
        return False
    
    # 2. 转换为Markdown
    logger.info("第二步: 转换数据为Markdown格式")
    
    # 构建输入数据
    input_data = {
        'versions_data': crawl_result['versions_data'],
        'date_string': crawl_result['date_string']
    }
    
    # 构建输出路径
    md_output_path = os.path.join(output_dir, f"{crawl_result['date_string']}.md")
    
    # 执行转换
    convert_to_markdown(input_data, md_output_path)
    
    # 完成时使用北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"数据处理完成 (北京时间: {china_time})")
    return True

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='人民日报新闻爬虫与转换服务')
    parser.add_argument('-d', '--date', help='指定日期，格式: YYYYMMDD，默认为今天')
    parser.add_argument('-o', '--output_dir', help='输出目录')
    args = parser.parse_args()
    
    success = process_news(args.date, args.output_dir)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 