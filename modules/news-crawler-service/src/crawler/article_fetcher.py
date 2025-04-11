#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import requests
from datetime import datetime, timedelta
import pytz
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 导入文章解析器
from .article_parser import ArticleParser, parse_article_content

class ArticleContentFetcher:
    """
    人民日报文章内容爬取器
    
    专门用于爬取指定版面的文章内容，并保存为HTML文件
    """
    
    def __init__(self, base_url="http://paper.people.com.cn/rmrb/pc/layout", output_dir=None):
        """初始化爬虫
        
        Args:
            base_url (str): 人民日报官网基础URL
            output_dir (str, optional): 输出目录，默认为src/output
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
        # 设置输出目录
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 配置日志记录器
        self.logger = logging.getLogger("ArticleContentFetcher")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 创建文章解析器实例
        self.parser = ArticleParser()
    
    def get_article_url_from_md(self, date_string=None):
        """从markdown文件中获取01版的第一条链接
        
        Args:
            date_string (str, optional): 日期字符串YYYYMMDD. 默认为None，表示当天.
            
        Returns:
            tuple: (文章URL, 日期字符串YYYYMMDD, 版面号, 文章序号)
        """
        # 如果未指定日期，使用当天日期（中国时区）
        if date_string is None:
            today = datetime.now(pytz.timezone('Asia/Shanghai'))
            date_string = today.strftime('%Y%m%d')
        
        # 尝试查找指定日期或前一天的markdown文件
        md_filepath = os.path.join(self.output_dir, f"{date_string}.md")
        
        # 检查指定日期的md文件是否存在
        if not os.path.exists(md_filepath):
            # 计算前一天的日期
            try:
                current_date = datetime.strptime(date_string, '%Y%m%d')
                prev_date = current_date - timedelta(days=1)
                date_string = prev_date.strftime('%Y%m%d')
                md_filepath = os.path.join(self.output_dir, f"{date_string}.md")
                
                # 检查前一天的md文件是否存在
                if not os.path.exists(md_filepath):
                    self.logger.error(f"未找到{date_string}或前一天的markdown文件")
                    return None, date_string, "01", "01"
                else:
                    self.logger.info(f"使用前一天的markdown文件: {md_filepath}")
            except ValueError:
                self.logger.error(f"日期格式无效: {date_string}")
                return None, date_string, "01", "01"
        
        self.logger.info(f"从markdown文件获取链接: {md_filepath}")
        
        try:
            # 读取markdown文件内容
            with open(md_filepath, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 查找01版部分及其链接
            pattern = r'## \[01版：.*?\]\(.*?\)(.*?)##'
            match = re.search(pattern, md_content, re.DOTALL)
            
            # 默认版面号和文章序号
            version_number = "01"
            article_number = "01"
            
            if match:
                section_content = match.group(1)
                
                # 从该部分内容中提取所有链接
                links = re.findall(r'- \[(.*?)\]\((http://.*?)\)', section_content)
                
                if len(links) >= 1:  # 大于等于一个链接时
                    article_url = links[0][1]
                    article_title = links[0][0]
                    self.logger.info(f"找到第一条链接: {article_title}, URL: {article_url}")
                    
                    # 尝试从URL中提取版面和文章编号
                    url_pattern = r'node_(\d+)\.html'
                    version_match = re.search(url_pattern, article_url)
                    if version_match:
                        version_number = version_match.group(1)
                    
                    # 尝试从文章URL中提取文章编号
                    content_pattern = r'content_(\d+)\.html'
                    content_match = re.search(content_pattern, article_url)
                    if content_match:
                        # 如果有文章编号，将其作为序号的一部分
                        article_number = "01"  # 默认为01
                    
                    return article_url, date_string, version_number, article_number
                else:
                    self.logger.error("未在01版找到任何链接")
                    return None, date_string, version_number, article_number
            else:
                self.logger.error("未找到01版部分")
                return None, date_string, version_number, article_number
                
        except Exception as e:
            self.logger.error(f"处理markdown文件时出错: {str(e)}")
            return None, date_string, "01", "01"
    
    def fetch_article_content(self, article_url):
        """获取文章内容
        
        Args:
            article_url (str): 文章URL
            
        Returns:
            str: 文章HTML内容
        """
        self.logger.info(f"获取文章内容: {article_url}")
        
        try:
            response = self.session.get(article_url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取文章内容失败: {str(e)}")
            return None
    
    def extract_article_content(self, html_content):
        """提取文章主体内容
        
        Args:
            html_content (str): 完整的HTML内容
            
        Returns:
            str: 提取后的文章HTML内容
        """
        self.logger.info("提取文章主体内容")
        
        if not html_content:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种选择器查找文章内容
            article_div = None
            article_selectors = [
                "body > div.main.w1000 > div.right.right-main > div.article-box > div.article",  # 原始选择器
                ".article",  # 类名选择器
                "#ozoom",    # ID选择器 (ozoom是一些新闻网站常用的文章内容容器ID)
                ".article-box .article",  # 嵌套选择器
                ".article-content",  # 常见的文章内容类名
                "[id^=articleContent]" # 以articleContent开头的ID
            ]
            
            for selector in article_selectors:
                article_div = soup.select_one(selector)
                if article_div:
                    self.logger.info(f"找到文章内容，使用选择器: {selector}")
                    break
            
            if article_div:
                # 保留原始HTML结构
                self.logger.info("成功提取文章主体内容")
                return str(article_div)
            else:
                # 如果所有选择器都失败，尝试最后的备选方案
                # 查找所有<p>标签，可能是正文段落
                paragraphs = soup.find_all('p')
                if len(paragraphs) > 3:  # 如果至少有几个段落
                    # 将所有段落组合成HTML
                    content = '<div class="extracted-content">\n'
                    for p in paragraphs:
                        content += str(p) + '\n'
                    content += '</div>'
                    self.logger.info("使用段落提取方法找到文章内容")
                    return content
                
                self.logger.warning("未找到文章主体内容")
                return None
        except Exception as e:
            self.logger.error(f"提取文章内容时出错: {str(e)}")
            return None
    
    def save_article_html(self, html_content, date_string, version_number, article_number):
        """保存文章内容为HTML文件
        
        Args:
            html_content (str): 文章HTML内容
            date_string (str): 日期字符串YYYYMMDD
            version_number (str): 版面号
            article_number (str): 文章序号
            
        Returns:
            dict: 包含原始HTML和处理后HTML的文件路径信息
        """
        result = {
            'html_path': None
        }
        
        # 文件名格式：YYYYMMDD-版号序号.html (如: 20250410-0101.html)
        filename = f"{date_string}-{version_number}{article_number}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # 保存HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"文章HTML已保存到: {filepath}")
            result['html_path'] = filepath
            
            return result
        except Exception as e:
            self.logger.error(f"保存文章HTML失败: {str(e)}")
            return result
    
    def fetch_and_save_article(self, date_string=None):
        """获取并保存指定的文章
        
        Args:
            date_string (str, optional): 日期字符串YYYYMMDD. 默认为None，表示当天.
            
        Returns:
            dict: 包含结果信息的字典
        """
        result = {
            'success': False,
            'article_url': None,
            'html_path': None,
            'date_string': None
        }
        
        # 1. 从md文件获取文章URL
        article_url, date_string, version_number, article_number = self.get_article_url_from_md(date_string)
        result['date_string'] = date_string
        
        if not article_url:
            self.logger.error("未能获取文章URL，爬取失败")
            return result
        
        result['article_url'] = article_url
        self.logger.info(f"准备爬取文章，URL: {article_url}")
        
        # 2. 获取文章HTML内容
        html_content = self.fetch_article_content(article_url)
        if not html_content:
            self.logger.error("获取文章HTML内容失败")
            return result
        
        # 3. 提取文章主体内容
        article_content = self.extract_article_content(html_content)
        if not article_content:
            self.logger.error("提取文章内容失败")
            return result
        
        # 4. 将提取的内容传递给解析器生成完整HTML
        readable_html = self.parser.generate_readable_html_from_content(article_content, article_url)
        if not readable_html:
            self.logger.error("生成可读HTML失败")
            return result
        
        # 5. 保存HTML内容
        save_result = self.save_article_html(readable_html, date_string, version_number, article_number)
        result['html_path'] = save_result.get('html_path')
        
        if result['html_path']:
            result['success'] = True
            self.logger.info(f"成功爬取并保存文章HTML到: {result['html_path']}")
        
        return result

def fetch_first_article(date=None, output_dir=None):
    """获取并保存文章的外部接口函数
    
    Args:
        date (str, optional): 日期字符串，格式YYYYMMDD. 默认为None，表示当天日期.
        output_dir (str, optional): 输出目录. 默认为None.
        
    Returns:
        dict: 包含结果信息的字典
    """
    # 实例化爬虫对象
    fetcher = ArticleContentFetcher(output_dir=output_dir)
    
    # 执行获取和保存操作
    return fetcher.fetch_and_save_article(date) 