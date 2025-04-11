#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from datetime import datetime

from converter.formatter import MarkdownFormatter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ConverterMain")

def save_file(content, filepath):
    """保存内容到文件
    
    Args:
        content (str): 文件内容
        filepath (str): 文件路径
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"已保存到: {filepath}")

def convert_to_markdown(input_data, output_path=None):
    """将爬虫数据转换为Markdown
    
    Args:
        input_data (dict): 爬虫数据
        output_path (str, optional): 输出路径
        
    Returns:
        str: 生成的Markdown内容的路径
    """
    formatter = MarkdownFormatter()
    
    # 生成Markdown内容
    versions_data = input_data.get('versions_data', [])
    date_string = input_data.get('date_string', datetime.now().strftime('%Y%m%d'))
    
    markdown_content = formatter.generate_markdown_report(versions_data, date_string)
    
    # 如果指定了输出路径，保存文件
    if output_path:
        save_file(markdown_content, output_path)
        return output_path
    
    return markdown_content

def main(args=None):
    """主程序入口"""
    if args is None:
        parser = argparse.ArgumentParser(description='人民日报转换模块')
        parser.add_argument('--input_file', help='输入的JSON文件路径')
        parser.add_argument('--output_dir', help='输出目录')
        args = parser.parse_args()
    
    logger.info("转换模块启动")
    
    # 此处应该使用传入的数据，目前为简化实现
    # 未来将从JSON文件读取爬虫数据
    
    logger.info("转换完成")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 