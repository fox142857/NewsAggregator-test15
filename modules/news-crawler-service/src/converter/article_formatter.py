#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import json
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

logger = logging.getLogger("ArticleFormatter")

class ArticleFormatter:
    """文章格式化与内容处理
    
    负责处理从article_fetcher.py和article_parser.py输出的内容
    提供格式化、增强内容展示和内容转换功能
    """
    
    def __init__(self):
        """初始化格式化器"""
        # 配置日志记录器
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def extract_article_info(self, html_file_path):
        """从HTML文件中提取文章信息
        
        Args:
            html_file_path (str): HTML文件路径
            
        Returns:
            dict: 文章信息字典
        """
        logger.info(f"从HTML文件提取文章信息: {html_file_path}")
        
        if not os.path.exists(html_file_path):
            logger.error(f"文件不存在: {html_file_path}")
            return None
        
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = "无标题"
            title_elem = soup.select_one('.title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # 提取元数据
            meta_info = {
                'author': "未知",
                'date': "",
                'version': "",
                'version_number': "",
                'article_number': ""
            }
            
            meta_elems = soup.select('.meta span')
            for elem in meta_elems:
                text = elem.get_text(strip=True)
                if "作者:" in text:
                    meta_info['author'] = text.replace("作者:", "").strip()
                elif "日期:" in text:
                    meta_info['date'] = text.replace("日期:", "").strip()
                elif "版面:" in text:
                    meta_info['version'] = text.replace("版面:", "").strip()
                elif "版面号:" in text and "文章序号:" in text:
                    parts = text.split("，")
                    if len(parts) == 2:
                        meta_info['version_number'] = parts[0].replace("版面号:", "").strip()
                        meta_info['article_number'] = parts[1].replace("文章序号:", "").strip()
            
            # 提取内容
            content = ""
            content_elem = soup.select_one('.content')
            if content_elem:
                content = str(content_elem)
            
            # 提取原文链接
            original_url = ""
            link_elem = soup.select_one('.source-link a')
            if link_elem and link_elem.has_attr('href'):
                original_url = link_elem['href']
            
            # 提取文件名中的日期和编号信息
            file_info = os.path.basename(html_file_path)
            date_match = re.match(r'(\d{8})-(\d{2})(\d{2})\.html', file_info)
            file_date = ""
            file_version = ""
            file_article = ""
            
            if date_match:
                file_date = date_match.group(1)
                file_version = date_match.group(2)
                file_article = date_match.group(3)
            
            # 组合文章信息
            article_info = {
                'title': title,
                'author': meta_info['author'],
                'date': meta_info['date'],
                'version': meta_info['version'],
                'version_number': meta_info['version_number'] or file_version,
                'article_number': meta_info['article_number'] or file_article,
                'content': content,
                'original_url': original_url,
                'file_date': file_date,
                'file_path': html_file_path
            }
            
            logger.info(f"成功提取文章信息: {title}")
            return article_info
            
        except Exception as e:
            logger.error(f"提取文章信息时出错: {str(e)}")
            return None
    
    def generate_json_metadata(self, article_info):
        """生成文章的JSON元数据
        
        Args:
            article_info (dict): 文章信息
            
        Returns:
            str: JSON格式的元数据
        """
        if not article_info:
            return "{}"
        
        # 创建用于JSON的数据结构
        metadata = {
            'title': article_info['title'],
            'author': article_info['author'],
            'date': article_info['date'],
            'version': article_info['version'],
            'version_number': article_info['version_number'],
            'article_number': article_info['article_number'],
            'original_url': article_info['original_url'],
            'processed_time': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 转换为JSON字符串
            json_data = json.dumps(metadata, ensure_ascii=False, indent=2)
            logger.info("成功生成JSON元数据")
            return json_data
        except Exception as e:
            logger.error(f"生成JSON元数据时出错: {str(e)}")
            return "{}"
    
    def generate_markdown_article(self, article_info):
        """从文章信息生成Markdown格式的文章
        
        Args:
            article_info (dict): 文章信息
            
        Returns:
            str: Markdown格式的文章内容
        """
        if not article_info:
            logger.error("文章信息为空，无法生成Markdown")
            return ""
        
        try:
            # 提取纯文本内容
            content_html = article_info['content']
            soup = BeautifulSoup(content_html, 'html.parser')
            
            # 从HTML中提取段落文本
            paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            
            # 生成frontmatter元数据
            frontmatter = "---\n"
            frontmatter += f"title: {article_info['title']}\n"
            frontmatter += f"date: {article_info['date']}\n"
            frontmatter += f"author: {article_info['author']}\n"
            frontmatter += f"version: {article_info['version']}\n"
            frontmatter += f"source: 人民日报\n"
            frontmatter += f"original_url: {article_info['original_url']}\n"
            frontmatter += "---\n\n"
            
            # 生成Markdown内容
            md_content = frontmatter
            md_content += f"# {article_info['title']}\n\n"
            
            # 添加元数据区域
            md_content += f"**作者**: {article_info['author']}  \n"
            md_content += f"**日期**: {article_info['date']}  \n"
            md_content += f"**版面**: {article_info['version']}  \n\n"
            
            # 添加正文内容
            for p in paragraphs:
                md_content += f"{p}\n\n"
            
            # 添加页脚
            md_content += "---\n\n"
            md_content += f"*来源: [人民日报]({article_info['original_url']})*  \n"
            md_content += f"*处理时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')} (北京时间)*\n"
            
            logger.info("成功生成Markdown文章内容")
            return md_content
            
        except Exception as e:
            logger.error(f"生成Markdown文章时出错: {str(e)}")
            return ""
    
    def generate_summary(self, article_info, max_length=200):
        """生成文章摘要
        
        Args:
            article_info (dict): 文章信息
            max_length (int): 摘要最大长度
            
        Returns:
            str: 文章摘要
        """
        if not article_info or 'content' not in article_info:
            return ""
        
        try:
            # 使用BeautifulSoup提取文本
            soup = BeautifulSoup(article_info['content'], 'html.parser')
            text = soup.get_text(strip=True)
            
            # 清理文本
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 截取摘要
            if len(text) > max_length:
                summary = text[:max_length] + "..."
            else:
                summary = text
                
            return summary
            
        except Exception as e:
            logger.error(f"生成摘要时出错: {str(e)}")
            return ""
    
    def process_article_files(self, input_dir, output_dir=None, format_type="markdown"):
        """处理指定目录下的所有文章HTML文件
        
        Args:
            input_dir (str): 输入目录路径
            output_dir (str, optional): 输出目录路径
            format_type (str): 输出格式，可选值: "markdown", "json", "all"
            
        Returns:
            dict: 处理结果，包含成功和失败的文件列表
        """
        if output_dir is None:
            output_dir = input_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        result = {
            'success': [],
            'failed': []
        }
        
        # 查找所有符合命名模式的HTML文件
        pattern = r'\d{8}-\d{4}\.html'
        html_files = []
        
        for file in os.listdir(input_dir):
            if re.match(pattern, file):
                html_files.append(os.path.join(input_dir, file))
        
        logger.info(f"找到 {len(html_files)} 个文章HTML文件")
        
        for html_file in html_files:
            try:
                # 提取文件名 (不含路径和扩展名)
                file_base = os.path.basename(html_file)
                file_name = os.path.splitext(file_base)[0]
                
                # 提取文章信息
                article_info = self.extract_article_info(html_file)
                
                if not article_info:
                    logger.error(f"无法处理文件: {html_file}")
                    result['failed'].append(html_file)
                    continue
                
                # 根据请求的格式生成输出
                if format_type in ["markdown", "all"]:
                    # 生成Markdown文件
                    md_content = self.generate_markdown_article(article_info)
                    md_file = os.path.join(output_dir, f"{file_name}.md")
                    
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(md_content)
                    
                    logger.info(f"生成Markdown文件: {md_file}")
                
                if format_type in ["json", "all"]:
                    # 生成JSON元数据文件
                    json_content = self.generate_json_metadata(article_info)
                    json_file = os.path.join(output_dir, f"{file_name}.json")
                    
                    with open(json_file, 'w', encoding='utf-8') as f:
                        f.write(json_content)
                    
                    logger.info(f"生成JSON元数据文件: {json_file}")
                
                # 记录成功处理的文件
                result['success'].append(html_file)
                
            except Exception as e:
                logger.error(f"处理文件 {html_file} 时出错: {str(e)}")
                result['failed'].append(html_file)
        
        logger.info(f"处理完成. 成功: {len(result['success'])}, 失败: {len(result['failed'])}")
        return result

def process_articles(input_dir=None, output_dir=None, format_type="markdown"):
    """处理文章的外部接口函数
    
    Args:
        input_dir (str, optional): 输入目录. 默认为None，使用默认输出目录
        output_dir (str, optional): 输出目录. 默认为None，与输入目录相同
        format_type (str): 输出格式，可选值: "markdown", "json", "all"
        
    Returns:
        dict: 处理结果
    """
    formatter = ArticleFormatter()
    
    # 使用默认输出目录
    if input_dir is None:
        input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    
    return formatter.process_article_files(input_dir, output_dir, format_type) 