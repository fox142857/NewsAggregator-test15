#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from datetime import datetime
import pytz

from converter.article_formatter import ArticleFormatter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger("ArticleConverter")

class ArticleConverter:
    """文章转换处理类
    
    负责将HTML文章转换为Markdown或JSON格式
    """
    
    def __init__(self, input_path=None, output_dir=None):
        """初始化转换器
        
        Args:
            input_path (str, optional): 输入文件或目录路径
            output_dir (str, optional): 输出目录路径
        """
        self.input_path = input_path
        
        # 设置输出目录
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建文章格式化器
        self.formatter = ArticleFormatter()
    
    def save_file(self, content, filepath):
        """保存内容到文件
        
        Args:
            content (str): 文件内容
            filepath (str): 文件路径
            
        Returns:
            str: 保存的文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已保存到: {filepath}")
        return filepath
    
    def convert_html_to_markdown(self, html_file_path, output_path=None):
        """将HTML文件转换为Markdown
        
        Args:
            html_file_path (str): HTML文件路径
            output_path (str, optional): 输出文件路径，不含扩展名
            
        Returns:
            str: 生成的Markdown文件路径，或失败时返回None
        """
        # 提取文章信息
        article_info = self.formatter.extract_article_info(html_file_path)
        if not article_info:
            logger.error(f"无法提取文章信息: {html_file_path}")
            return None
        
        # 生成Markdown内容
        md_content = self.formatter.generate_markdown_article(article_info)
        if not md_content:
            logger.error(f"生成Markdown内容失败: {html_file_path}")
            return None
        
        # 确定输出路径
        if output_path is None:
            # 使用原文件路径，仅改变扩展名
            output_path = os.path.splitext(html_file_path)[0]
        
        # 添加.md扩展名
        md_file = f"{output_path}.md"
        
        # 保存文件
        try:
            self.save_file(md_content, md_file)
            logger.info(f"成功转换为Markdown: {md_file}")
            return md_file
        except Exception as e:
            logger.error(f"保存Markdown文件失败: {str(e)}")
            return None
    
    def convert_html_to_json(self, html_file_path, output_path=None):
        """将HTML文件转换为JSON元数据
        
        Args:
            html_file_path (str): HTML文件路径
            output_path (str, optional): 输出文件路径，不含扩展名
            
        Returns:
            str: 生成的JSON文件路径，或失败时返回None
        """
        # 提取文章信息
        article_info = self.formatter.extract_article_info(html_file_path)
        if not article_info:
            logger.error(f"无法提取文章信息: {html_file_path}")
            return None
        
        # 生成JSON内容
        json_content = self.formatter.generate_json_metadata(article_info)
        if not json_content:
            logger.error(f"生成JSON内容失败: {html_file_path}")
            return None
        
        # 确定输出路径
        if output_path is None:
            # 使用原文件路径，仅改变扩展名
            output_path = os.path.splitext(html_file_path)[0]
        
        # 添加.json扩展名
        json_file = f"{output_path}.json"
        
        # 保存文件
        try:
            self.save_file(json_content, json_file)
            logger.info(f"成功转换为JSON: {json_file}")
            return json_file
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            return None
    
    def convert(self, format_type="markdown"):
        """执行转换流程
        
        Args:
            format_type (str): 输出格式，可选值: "markdown", "json", "all"
            
        Returns:
            dict: 包含转换结果的字典
        """
        result = {
            'success': False,
            'markdown_path': None,
            'json_path': None,
            'summary': None
        }
        
        # 检查输入路径
        if not self.input_path:
            logger.error("未指定输入路径")
            return result
        
        # 检查文件是否存在
        if not os.path.exists(self.input_path):
            logger.error(f"输入路径不存在: {self.input_path}")
            return result
        
        # 判断是文件还是目录
        if os.path.isfile(self.input_path):
            # 处理单个文件
            logger.info(f"处理单个文件: {self.input_path}")
            
            # 根据格式类型进行转换
            if format_type in ["markdown", "all"]:
                result['markdown_path'] = self.convert_html_to_markdown(self.input_path)
            
            if format_type in ["json", "all"]:
                result['json_path'] = self.convert_html_to_json(self.input_path)
            
            # 提取摘要
            article_info = self.formatter.extract_article_info(self.input_path)
            if article_info:
                result['summary'] = self.formatter.generate_summary(article_info)
            
            # 检查是否成功
            if result['markdown_path'] or result['json_path']:
                result['success'] = True
        
        elif os.path.isdir(self.input_path):
            # 处理目录中的所有文件
            logger.info(f"处理目录: {self.input_path}")
            
            # 调用处理目录的函数
            from converter.article_formatter import process_articles
            dir_result = process_articles(self.input_path, self.output_dir, format_type)
            
            # 更新结果
            result['success'] = len(dir_result['success']) > 0
            if result['success']:
                # 记录第一个成功的文件路径作为示例
                if dir_result['success']:
                    first_file = os.path.splitext(dir_result['success'][0])[0]
                    if format_type in ["markdown", "all"]:
                        result['markdown_path'] = f"{first_file}.md"
                    if format_type in ["json", "all"]:
                        result['json_path'] = f"{first_file}.json"
            
            # 添加统计信息
            result['stats'] = {
                'total': len(dir_result['success']) + len(dir_result['failed']),
                'success': len(dir_result['success']),
                'failed': len(dir_result['failed'])
            }
        
        return result

def convert_article(input_path, output_dir=None, format_type="markdown"):
    """转换文章的外部接口函数
    
    Args:
        input_path (str): 输入文件或目录路径
        output_dir (str, optional): 输出目录
        format_type (str): 输出格式，可选值: "markdown", "json", "all"
        
    Returns:
        dict: 转换结果
    """
    converter = ArticleConverter(input_path, output_dir)
    return converter.convert(format_type)

def main(args=None):
    """主程序入口"""
    if args is None:
        parser = argparse.ArgumentParser(description='人民日报文章转换工具')
        parser.add_argument('--input', required=True, help='输入的HTML文件或目录路径')
        parser.add_argument('--output', help='输出目录')
        parser.add_argument('--format', choices=['markdown', 'json', 'all'], default='markdown',
                          help='输出格式 (默认: markdown)')
        args = parser.parse_args()
    
    # 获取当前北京时间
    china_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"文章转换工具启动 (北京时间: {china_time})")
    
    # 执行转换
    result = convert_article(args.input, args.output, args.format)
    
    # 输出结果信息
    if result['success']:
        logger.info("文章转换成功")
        if 'stats' in result:
            logger.info(f"共处理 {result['stats']['total']} 个文件，成功 {result['stats']['success']} 个，失败 {result['stats']['failed']} 个")
        else:
            if result['markdown_path']:
                logger.info(f"Markdown文件: {result['markdown_path']}")
            if result['json_path']:
                logger.info(f"JSON文件: {result['json_path']}")
        return 0
    else:
        logger.error("文章转换失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 