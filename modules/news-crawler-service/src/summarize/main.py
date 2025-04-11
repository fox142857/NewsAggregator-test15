#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from datetime import datetime
import pytz
import random

from src.summarize.file_finder import FileFinder
from src.summarize.file_processor import FileProcessor
from src.summarize.ai_summarizer import AISummarizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("AISummarizeMain")

def run_summarize(api_key=None, output_dir=None, use_mock=False):
    """运行AI总结流程
    
    Args:
        api_key (str, optional): DeepSeek API密钥
        output_dir (str, optional): 输出目录路径
        use_mock (bool, optional): 是否使用模拟模式，不调用实际API
        
    Returns:
        bool: 操作是否成功
    """
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"AI内容总结流程开始 (北京时间: {china_time})")
    
    # 如果使用模拟模式，输出提示
    if use_mock:
        logger.info("使用模拟模式，将不会调用真实的DeepSeek API")
    
    # 1. 查找匹配的文件
    logger.info("第一步: 查找匹配的文件")
    file_finder = FileFinder(output_dir=output_dir)
    matching_files = file_finder.find_matching_files()
    
    if not matching_files:
        logger.error("未找到匹配的文件，结束流程")
        return False
    
    # 列出所有匹配的文件
    logger.info(f"找到 {len(matching_files)} 个匹配的文件:")
    for i, file_path in enumerate(matching_files, 1):
        logger.info(f"{i}. {os.path.basename(file_path)}")
    
    # 2. 随机选择文件并提取内容
    logger.info("第二步: 随机选择文件并提取内容")
    file_processor = FileProcessor()
    selected_file = file_processor.select_random_file(matching_files)
    
    if not selected_file:
        logger.error("选择文件失败，结束流程")
        return False
    
    content_data = file_processor.extract_content(selected_file)
    
    if not content_data:
        logger.error("提取文件内容失败，结束流程")
        return False
    
    # 3. 调用DeepSeek API进行内容总结
    logger.info("第三步: 调用DeepSeek API进行内容总结")
    summarizer = AISummarizer(api_key=api_key, output_dir=output_dir, use_mock=use_mock)
    
    summary_data = summarizer.summarize(content_data)
    
    if not summary_data:
        logger.error("内容总结失败，结束流程")
        return False
    
    # 4. 保存总结结果
    logger.info("第四步: 保存总结结果")
    summary_file = summarizer.save_summary(summary_data)
    
    if not summary_file:
        logger.error("保存总结结果失败，结束流程")
        return False
    
    # 完成时使用北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"AI内容总结流程完成 (北京时间: {china_time})")
    logger.info(f"总结文件已保存到: {summary_file}")
    
    return True

def main(args=None):
    """主程序入口"""
    if args is None:
        parser = argparse.ArgumentParser(description='人民日报文章AI总结工具')
        parser.add_argument('-k', '--api_key', help='DeepSeek API密钥，如未提供则使用DEEPSEEK_API_KEY环境变量')
        parser.add_argument('-o', '--output_dir', help='输出目录路径')
        parser.add_argument('-m', '--mock', action='store_true', help='使用模拟模式，不调用实际API')
        parser.add_argument('-v', '--verbose', action='store_true', help='输出详细日志')
        args = parser.parse_args()
        
        # 设置日志级别
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
    
    # 执行总结流程
    success = run_summarize(
        api_key=args.api_key, 
        output_dir=args.output_dir,
        use_mock=args.mock if hasattr(args, 'mock') else False
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 