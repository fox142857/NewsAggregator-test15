#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from datetime import datetime
import pytz

from converter.article_formatter import ArticleFormatter, process_articles

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ArticleConverterMain")

def save_file(content, filepath):
    """保存内容到文件
    
    Args:
        content (str): 文件内容
        filepath (str): 文件路径
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"已保存到: {filepath}")

def convert_article(html_file_path, output_path=None, format_type="markdown"):
    """转换单个文章HTML到指定格式
    
    Args:
        html_file_path (str): HTML文件路径
        output_path (str, optional): 输出文件路径，不包含扩展名
        format_type (str): 输出格式，可选值: "markdown", "json", "all"
        
    Returns:
        bool: 是否成功
    """
    formatter = ArticleFormatter()
    
    # 提取文章信息
    article_info = formatter.extract_article_info(html_file_path)
    if not article_info:
        logger.error(f"无法提取文章信息: {html_file_path}")
        return False
    
    success = True
    
    # 如果未指定输出路径，使用原文件路径（更改扩展名）
    if output_path is None:
        base_path = os.path.splitext(html_file_path)[0]
    else:
        base_path = output_path
    
    # 根据请求的格式生成输出
    if format_type in ["markdown", "all"]:
        # 生成Markdown内容
        md_content = formatter.generate_markdown_article(article_info)
        md_file = f"{base_path}.md"
        
        try:
            save_file(md_content, md_file)
            logger.info(f"成功生成Markdown文件: {md_file}")
        except Exception as e:
            logger.error(f"保存Markdown文件失败: {str(e)}")
            success = False
    
    if format_type in ["json", "all"]:
        # 生成JSON元数据
        json_content = formatter.generate_json_metadata(article_info)
        json_file = f"{base_path}.json"
        
        try:
            save_file(json_content, json_file)
            logger.info(f"成功生成JSON文件: {json_file}")
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            success = False
    
    # 生成摘要
    if success:
        summary = formatter.generate_summary(article_info)
        logger.info(f"文章摘要: {summary[:100]}...")
    
    return success

def process_directory(input_dir, output_dir=None, format_type="markdown"):
    """处理目录中的所有HTML文件
    
    Args:
        input_dir (str): 输入目录
        output_dir (str, optional): 输出目录
        format_type (str): 输出格式
        
    Returns:
        dict: 结果统计
    """
    # 调用公共处理函数
    result = process_articles(input_dir, output_dir, format_type)
    
    # 打印结果统计
    logger.info(f"文章处理完成")
    logger.info(f"成功: {len(result['success'])}，失败: {len(result['failed'])}")
    
    if result['failed']:
        logger.warning("失败的文件:")
        for file in result['failed']:
            logger.warning(f" - {file}")
    
    return result

def main(args=None):
    """主程序入口"""
    if args is None:
        parser = argparse.ArgumentParser(description='人民日报文章转换工具')
        parser.add_argument('--input', help='输入的HTML文件路径或目录')
        parser.add_argument('--output', help='输出文件路径或目录')
        parser.add_argument('--format', choices=['markdown', 'json', 'all'], default='markdown',
                          help='输出格式 (默认: markdown)')
        args = parser.parse_args()
    
    # 获取当前北京时间
    now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"文章转换工具启动 (北京时间: {now})")
    
    # 处理输入参数
    input_path = args.input
    output_path = args.output
    format_type = args.format
    
    # 如果未指定输入路径，使用默认输出目录
    if input_path is None:
        input_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        logger.info(f"未指定输入路径，使用默认目录: {input_path}")
    
    # 检查输入路径是文件还是目录
    if os.path.isfile(input_path):
        # 处理单个文件
        logger.info(f"处理单个文件: {input_path}")
        success = convert_article(input_path, output_path, format_type)
        return 0 if success else 1
    elif os.path.isdir(input_path):
        # 处理目录
        logger.info(f"处理目录: {input_path}")
        result = process_directory(input_path, output_path, format_type)
        return 0 if result['failed'] == [] else 1
    else:
        logger.error(f"输入路径不存在: {input_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 