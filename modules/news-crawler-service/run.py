#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人民日报爬虫服务启动脚本

此脚本是项目的主入口，用于启动人民日报爬虫服务
"""

import os
import sys
import argparse
from datetime import datetime
import pytz  # 添加pytz库导入

# 将src目录添加到模块搜索路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# 现在可以导入我们的模块
from src.main import process_news
from src.crawler.article_fetcher import fetch_first_article
from src.converter.article_formatter import process_articles
from src.article_main import process_article
from src.summarize import run_summarize

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='人民日报新闻爬虫服务')
    
    # 子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 爬取命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取新闻')
    crawl_parser.add_argument('-d', '--date', help='指定日期，格式: YYYYMMDD，默认为今天')
    crawl_parser.add_argument('-o', '--output_dir', help='输出目录路径')
    crawl_parser.add_argument('--only-article', action='store_true', help='只爬取文章详情，跳过版面爬取')
    
    # 单篇文章爬取与处理命令
    article_parser = subparsers.add_parser('get-article', help='爬取并处理单篇文章')
    article_parser.add_argument('-d', '--date', help='指定日期，格式: YYYYMMDD，默认为今天')
    article_parser.add_argument('-o', '--output_dir', help='输出目录路径')
    article_parser.add_argument('-f', '--format', choices=['markdown', 'json', 'all'], 
                              default='markdown', help='输出格式 (默认: markdown)')
    
    # AI总结命令
    summarize_parser = subparsers.add_parser('ai-summarize', help='使用AI总结文章内容')
    summarize_parser.add_argument('api_key', nargs='?', help='DeepSeek API密钥，如未提供则使用DEEPSEEK_API_KEY环境变量')
    summarize_parser.add_argument('-o', '--output_dir', help='输出目录路径')
    summarize_parser.add_argument('-m', '--mock', action='store_true', help='使用模拟模式，不调用实际API')
    summarize_parser.add_argument('-v', '--verbose', action='store_true', help='输出详细日志')
    
    # 版本命令
    version_parser = subparsers.add_parser('version', help='显示版本信息')
    
    return parser.parse_args()

def main():
    """主程序入口"""
    args = parse_args()
    
    if args.command == 'crawl':
        # 使用中国时间作为日志记录
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] 开始爬取人民日报新闻...")
        
        success = True
        # 如果不是只爬取文章，则先执行版面爬取
        if not args.only_article:
            # 执行新闻处理流程
            success = process_news(date=args.date, output_dir=args.output_dir)
        
        # 无论上一步是否成功，都尝试爬取文章详情
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] 开始爬取第一版面指定新闻的详细内容...")
        
        # 爬取文章
        article_result = fetch_first_article(date=args.date, output_dir=args.output_dir)
        
        if article_result['success']:
            print(f"文章爬取成功! 保存至: {article_result['html_path']}")
        else:
            print("文章爬取失败")
            success = False
        
        # 结束时间
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] 爬取任务{'成功' if success else '失败'}")
        
        return 0 if success else 1
    
    elif args.command == 'get-article':
        # 使用中国时间作为日志记录
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] 开始爬取并处理单篇文章...")
        
        # 调用article_main.py中的process_article函数
        success = process_article(
            date=args.date,
            output_dir=args.output_dir,
            format_type=args.format
        )
        
        # 结束时间
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] 文章处理任务{'成功' if success else '失败'}")
        
        return 0 if success else 1
    
    elif args.command == 'ai-summarize':
        # 使用中国时间作为日志记录
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] 开始进行文章AI总结...")
        
        # 设置日志级别
        if hasattr(args, 'verbose') and args.verbose:
            import logging
            logging.basicConfig(level=logging.INFO)
        
        # 调用summarize模块中的run_summarize函数
        success = run_summarize(
            api_key=args.api_key,
            output_dir=args.output_dir,
            use_mock=args.mock if hasattr(args, 'mock') else False
        )
        
        # 结束时间
        china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{china_time}] AI总结任务{'成功' if success else '失败'}")
        
        return 0 if success else 1
        
    elif args.command == 'version':
        # 显示版本信息
        from src.crawler import __version__ as crawler_version
        from src.converter import __version__ as converter_version
        from src.summarize import __version__ as summarize_version
        print(f"人民日报爬虫服务 v{crawler_version}")
        print(f"人民日报转换服务 v{converter_version}")
        print(f"人民日报AI总结服务 v{summarize_version}")
        return 0
    
    else:
        # 如果没有指定子命令，显示帮助信息
        print("请指定子命令。使用 --help 查看帮助信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 