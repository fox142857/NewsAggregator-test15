#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from datetime import datetime
import pytz  # 添加pytz库导入

# 导入自定义模块
from crawler.article_main import crawl_article
from converter.article_converter import convert_article

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ArticleAggregatorMain")

def process_article(date=None, output_dir=None, format_type="markdown"):
    """处理文章流程
    
    Args:
        date (str, optional): 指定日期，格式YYYYMMDD
        output_dir (str, optional): 输出目录
        format_type (str): 转换格式，可选值: "markdown", "json", "all"
        
    Returns:
        bool: 处理是否成功
    """
    # 设置默认输出目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
    
    # 使用北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"开始处理文章数据流程 (北京时间: {china_time})")
    
    # 1. 爬取文章
    logger.info("第一步: 爬取人民日报文章")
    crawl_result = crawl_article(date, output_dir)
    
    if not crawl_result['success']:
        logger.error("爬取文章失败，处理终止")
        return False
    
    # 2. 转换为指定格式
    logger.info(f"第二步: 转换文章为{format_type}格式")
    html_path = crawl_result['html_path']
    
    if not html_path or not os.path.exists(html_path):
        logger.error(f"HTML文件不存在: {html_path}")
        return False
    
    # 执行转换
    convert_result = convert_article(html_path, output_dir, format_type)
    
    # 完成时使用北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    
    if convert_result['success']:
        logger.info(f"文章处理成功完成 (北京时间: {china_time})")
        
        # 输出结果文件路径
        if convert_result['markdown_path']:
            logger.info(f"Markdown文件: {convert_result['markdown_path']}")
        if convert_result['json_path']:
            logger.info(f"JSON文件: {convert_result['json_path']}")
        
        return True
    else:
        logger.error(f"文章转换失败 (北京时间: {china_time})")
        return False

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='人民日报文章爬取与转换服务')
    parser.add_argument('-d', '--date', help='指定日期，格式: YYYYMMDD，默认为今天')
    parser.add_argument('-o', '--output_dir', help='输出目录')
    parser.add_argument('-f', '--format', choices=['markdown', 'json', 'all'], default='markdown',
                      help='输出格式 (默认: markdown)')
    args = parser.parse_args()
    
    success = process_article(args.date, args.output_dir, args.format)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 