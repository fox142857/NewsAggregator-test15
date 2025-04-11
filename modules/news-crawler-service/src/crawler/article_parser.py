#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
import os
import pytz

class ArticleParser:
    """
    人民日报文章解析器
    
    负责解析爬取到的文章HTML内容，提取文章标题、作者、正文等信息，
    并生成便于阅读的HTML文件
    """
    
    def __init__(self):
        """初始化解析器"""
        # 配置日志记录器
        self.logger = logging.getLogger("ArticleParser")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def parse_article(self, html_content):
        """
        解析文章HTML内容
        
        Args:
            html_content (str): 文章HTML内容
            
        Returns:
            dict: 解析后的文章信息，包含标题、作者、日期、版面、正文等
        """
        self.logger.info("开始解析文章HTML内容")
        
        if not html_content:
            self.logger.error("输入的HTML内容为空")
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取文章标题
            title_element = None
            title_selectors = [
                "div.article h1",       # 标准选择器
                "h1",                   # 直接查找h1
                "div.article-box h1",   # 备选选择器
                "h2.title",             # 有些可能用h2
                "title"                 # 从title标签提取
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element and title_element.get_text(strip=True):
                    break
            
            title = title_element.get_text(strip=True) if title_element else "无标题"
            
            # 提取作者信息
            author = ""
            author_selectors = [
                "div.article p.sec",   # 常见作者位置
                "p.author",            # 备选
                "span.author"          # 备选
            ]
            
            for selector in author_selectors:
                author_element = soup.select_one(selector)
                if author_element and author_element.get_text(strip=True):
                    author = author_element.get_text(strip=True)
                    break
            
            # 如果上面方法未找到作者，尝试通过meta标签获取
            if not author:
                author_meta = soup.find('meta', {'name': 'author'})
                if author_meta and author_meta.get('content'):
                    author = author_meta.get('content')
            
            # 提取日期
            date = ""
            date_elements = soup.select("span.newstime")
            if date_elements:
                for element in date_elements:
                    text = element.get_text(strip=True)
                    if text:
                        date = text
                        break
            
            # 如果未找到日期，尝试从URL或其他位置提取
            if not date:
                # 尝试从URL中提取日期 (从HTML内容中找)
                date_match = re.search(r'/(\d{6})/(\d{2})/', html_content)
                if date_match:
                    year_month = date_match.group(1)
                    day = date_match.group(2)
                    date = f"{year_month[:4]}年{year_month[4:6]}月{day}日"
            
            # 提取版面信息
            version = ""
            version_elements = soup.select("p.ban")
            if version_elements:
                for element in version_elements:
                    text = element.get_text(strip=True)
                    if text:
                        version = text
                        break
            
            # 尝试其他方式获取版面信息
            if not version:
                version_elements = soup.select("div.date-box p")
                if version_elements and len(version_elements) > 0:
                    version_text = version_elements[0].get_text(strip=True)
                    if "版：" in version_text:
                        version = version_text
            
            # 提取正文内容
            content = ""
            content_selectors = [
                "div#ozoom",           # 人民日报常用ID
                "div.article",         # 常见文章内容容器
                "div.article-content", # 备选
                "div.content"          # 备选
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element and content_element.get_text(strip=True):
                    # 保留HTML格式
                    content = str(content_element)
                    break
            
            # 如果未找到内容，尝试获取所有段落
            if not content:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = '<div class="article-content">'
                    for p in paragraphs:
                        if p.get_text(strip=True) and not p.find_parent('div', class_=["header", "footer"]):
                            content += str(p)
                    content += '</div>'
            
            # 提取原文链接
            original_url = ""
            url_pattern = r'(http://paper\.people\.com\.cn/[^\s"\']+?\.html)'
            url_match = re.search(url_pattern, html_content)
            if url_match:
                original_url = url_match.group(1)
            
            article_info = {
                'title': title,
                'author': author,
                'date': date,
                'version': version,
                'content': content,
                'original_url': original_url
            }
            
            self.logger.info(f"成功解析文章：{title}")
            return article_info
            
        except Exception as e:
            self.logger.error(f"解析文章时出错: {str(e)}")
            return None
    
    def parse_article_content(self, article_content, original_url=""):
        """
        解析已提取的文章内容
        
        Args:
            article_content (str): 已提取的文章内容HTML
            original_url (str): 原始文章URL
            
        Returns:
            dict: 解析后的文章信息，包含标题、正文等
        """
        self.logger.info("开始解析提取的文章内容")
        
        if not article_content:
            self.logger.error("输入的文章内容为空")
            return None
        
        try:
            soup = BeautifulSoup(article_content, 'html.parser')
            
            # 尝试提取标题(可能已经提取出来的内容中没有标题)
            title = "人民日报文章"
            title_elements = soup.find_all(['h1', 'h2', 'h3'])
            if title_elements:
                for elem in title_elements:
                    if elem.get_text(strip=True):
                        title = elem.get_text(strip=True)
                        break
            
            # 尝试从URL提取日期
            date = ""
            date_match = re.search(r'/(\d{6})/(\d{2})/', original_url)
            if date_match:
                year_month = date_match.group(1)
                day = date_match.group(2)
                date = f"{year_month[:4]}年{year_month[4:6]}月{day}日"
            else:
                # 使用当前日期
                date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日')
            
            # 对于剩余字段使用默认值
            article_info = {
                'title': title,
                'author': "人民日报",
                'date': date,
                'version': "01版",
                'content': article_content,
                'original_url': original_url
            }
            
            self.logger.info(f"成功解析文章内容：{title}")
            return article_info
            
        except Exception as e:
            self.logger.error(f"解析文章内容时出错: {str(e)}")
            return None
    
    def generate_readable_html(self, article_info):
        """
        根据解析的文章信息生成可读性更好的HTML
        
        Args:
            article_info (dict): 解析后的文章信息
            
        Returns:
            str: 生成的HTML内容
        """
        if not article_info:
            self.logger.error("无法生成HTML: 文章信息为空")
            return ""
        
        try:
            # 获取当前时间（北京时间）
            now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{article_info['title']} - 人民日报</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: "Microsoft YaHei", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .container {{
            background-color: #fff;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
        .header {{
            border-bottom: 2px solid #c00;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #c00;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .content {{
            font-size: 16px;
            line-height: 1.8;
        }}
        .content p {{
            margin-bottom: 15px;
            text-indent: 2em;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 12px;
        }}
        .source-link {{
            margin-top: 20px;
            font-size: 14px;
        }}
        .source-link a {{
            color: #c00;
            text-decoration: none;
        }}
        .source-link a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">{article_info['title']}</h1>
            <div class="meta">
                <span>作者: {article_info['author']}</span>
                <br>
                <span>日期: {article_info['date']}</span>
                <br>
                <span>版面: {article_info['version']}</span>
            </div>
        </div>
        
        <div class="content">
            {article_info['content']}
        </div>
        
        <div class="source-link">
            <a href="{article_info['original_url']}" target="_blank">查看原文</a>
        </div>
        
        <div class="footer">
            <p>来源: 人民日报</p>
            <p>处理时间: {now} (北京时间)</p>
        </div>
    </div>
</body>
</html>
            """
            
            self.logger.info("成功生成可读性更好的HTML内容")
            return html
            
        except Exception as e:
            self.logger.error(f"生成HTML时出错: {str(e)}")
            return ""
    
    def generate_readable_html_from_content(self, article_content, original_url=""):
        """
        直接从提取的文章内容生成可读性更好的HTML
        
        Args:
            article_content (str): 已提取的文章内容HTML
            original_url (str): 原始文章URL
            
        Returns:
            str: 生成的HTML内容
        """
        # 解析文章内容
        article_info = self.parse_article_content(article_content, original_url)
        if not article_info:
            self.logger.error("文章内容解析失败")
            return None
        
        # 生成HTML
        return self.generate_readable_html(article_info)
    
    def parse_and_save(self, html_content, output_path):
        """
        解析文章并保存为可读性更好的HTML文件
        
        Args:
            html_content (str): 文章HTML内容
            output_path (str): 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        self.logger.info(f"开始解析文章并保存到: {output_path}")
        
        # 解析文章
        article_info = self.parse_article(html_content)
        if not article_info:
            self.logger.error("文章解析失败")
            return False
        
        # 生成HTML
        readable_html = self.generate_readable_html(article_info)
        if not readable_html:
            self.logger.error("生成HTML失败")
            return False
        
        # 保存文件
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(readable_html)
            
            self.logger.info(f"文章已保存到: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存文件时出错: {str(e)}")
            return False

def parse_article_content(html_content, output_path):
    """
    解析文章HTML内容并生成可读性更好的HTML文件
    
    Args:
        html_content (str): 文章HTML内容
        output_path (str): 输出文件路径
        
    Returns:
        bool: 是否成功
    """
    parser = ArticleParser()
    return parser.parse_and_save(html_content, output_path) 