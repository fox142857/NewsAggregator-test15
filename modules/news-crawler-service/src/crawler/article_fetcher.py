#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import requests
from datetime import datetime
import pytz
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 导入文章解析器
from .article_parser import ArticleParser, parse_article_content

class ArticleContentFetcher:
    """
    人民日报文章内容爬取器
    
    专门用于爬取第一版面第一篇文章的内容，并保存为HTML文件
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
    
    def get_first_article_url(self, date_tuple=None):
        """获取指定日期第一版面的第一篇文章URL
        
        Args:
            date_tuple (tuple, optional): (年, 月, 日)元组. 默认为None，表示获取当天日期.
            
        Returns:
            tuple: (文章URL, 日期字符串YYYYMMDD)
        """
        # 如果未指定日期，使用当天日期（中国时区）
        if date_tuple is None:
            today = datetime.now(pytz.timezone('Asia/Shanghai'))
            year, month, day = today.year, today.month, today.day
            date_string = today.strftime('%Y%m%d')
        else:
            year, month, day = date_tuple
            date_string = f"{year:04d}{month:02d}{day:02d}"
        
        # 构建第一版面URL
        version_url = f"{self.base_url}/{year:04d}{month:02d}/{day:02d}/node_01.html"
        self.logger.info(f"获取第一版面: {version_url}")
        
        try:
            # 请求第一版面
            response = self.session.get(version_url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种选择器查找新闻列表
            news_list = None
            news_selectors = [
                "body > div.main.w1000 > div.left.paper-box > div.news > ul",  # 原始选择器
                ".news-list",  # 类名选择器
                ".news ul",    # 嵌套选择器
                "ul.news-list"  # 标签+类名选择器
            ]
            
            for selector in news_selectors:
                news_list = soup.select_one(selector)
                if news_list:
                    self.logger.info(f"找到新闻列表，使用选择器: {selector}")
                    break
            
            # 如果找到了新闻列表，尝试获取第一篇文章的链接
            if news_list:
                # 尝试从第一个li元素中获取链接
                first_news = news_list.find('a', href=True)
                if first_news:
                    article_url = urljoin(version_url, first_news['href'])
                    self.logger.info(f"找到第一篇文章: {first_news.get_text(strip=True)}, URL: {article_url}")
                    return article_url, date_string
            
            # 如果上面的方法失败，直接在页面上查找所有新闻链接
            self.logger.info("未能通过新闻列表找到文章，尝试直接在页面查找链接...")
            
            # 尝试查找所有内容页面链接
            content_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # 查找形如 content_*.html 的链接
                if 'content_' in href and href.endswith('.html'):
                    content_links.append((link, urljoin(version_url, href)))
            
            if content_links:
                # 取第一个内容链接
                first_link, article_url = content_links[0]
                self.logger.info(f"通过直接搜索找到第一篇文章: {first_link.get_text(strip=True) if first_link.get_text(strip=True) else '(无标题)'}, URL: {article_url}")
                return article_url, date_string
            
            self.logger.error("未找到任何文章链接")
            return None, date_string
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取第一版面失败: {str(e)}")
            return None, date_string
    
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
    
    def save_article_html(self, html_content, date_string):
        """保存文章内容为HTML文件
        
        Args:
            html_content (str): 文章HTML内容
            date_string (str): 日期字符串YYYYMMDD
            
        Returns:
            dict: 包含原始HTML和处理后HTML的文件路径信息
        """
        result = {
            'original_html_path': None,
            'readable_html_path': None
        }
        
        # 保存原始HTML
        # 文件名格式：YYYYMMDD-0101.html
        original_filename = f"{date_string}-0101.html"
        original_filepath = os.path.join(self.output_dir, original_filename)
        
        # 处理后的HTML文件名格式：YYYYMMDD-0101-readable.html
        readable_filename = f"{date_string}-0101-readable.html"
        readable_filepath = os.path.join(self.output_dir, readable_filename)
        
        try:
            # 保存原始HTML
            with open(original_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"原始文章HTML已保存到: {original_filepath}")
            result['original_html_path'] = original_filepath
            
            # 使用解析器处理并保存可读性更好的HTML
            if self.parser.parse_and_save(html_content, readable_filepath):
                self.logger.info(f"可读性HTML已保存到: {readable_filepath}")
                result['readable_html_path'] = readable_filepath
            else:
                self.logger.warning("生成可读性HTML失败")
            
            return result
        except Exception as e:
            self.logger.error(f"保存文章HTML失败: {str(e)}")
            return result
    
    def fetch_and_save_first_article(self, date_tuple=None):
        """获取并保存第一版面第一篇文章
        
        Args:
            date_tuple (tuple, optional): (年, 月, 日)元组. 默认为None，表示获取当天日期.
            
        Returns:
            dict: 包含结果信息的字典
        """
        result = {
            'success': False,
            'article_url': None,
            'original_html_path': None,
            'readable_html_path': None,
            'date_string': None
        }
        
        # 1. 获取第一篇文章的URL
        article_url, date_string = self.get_first_article_url(date_tuple)
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
        
        # 3. 保存原始HTML内容和处理后的HTML
        save_result = self.save_article_html(html_content, date_string)
        result['original_html_path'] = save_result.get('original_html_path')
        result['readable_html_path'] = save_result.get('readable_html_path')
        
        if result['original_html_path']:
            result['success'] = True
            self.logger.info(f"成功爬取并保存文章HTML")
            
            if result['readable_html_path']:
                self.logger.info(f"同时生成了可读性更好的HTML版本")
        
        return result

def fetch_first_article(date=None, output_dir=None):
    """获取并保存第一版面第一篇文章的外部接口函数
    
    Args:
        date (str, optional): 日期字符串，格式YYYYMMDD. 默认为None，表示当天日期.
        output_dir (str, optional): 输出目录. 默认为None.
        
    Returns:
        dict: 包含结果信息的字典
    """
    # 实例化爬虫对象
    fetcher = ArticleContentFetcher(output_dir=output_dir)
    
    # 如果指定了日期，解析日期
    date_tuple = None
    if date:
        try:
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:8])
            date_tuple = (year, month, day)
        except (ValueError, IndexError):
            logging.error(f"日期格式无效: {date}，应为YYYYMMDD")
            return {'success': False, 'error': '日期格式无效'}
    
    # 执行获取和保存操作
    return fetcher.fetch_and_save_first_article(date_tuple) 