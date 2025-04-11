#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from datetime import datetime
import logging
import pytz  # 添加pytz库导入

class PeoplesDailyParser:
    """人民日报HTML解析模块
    
    负责解析人民日报网页内容，提取版面信息、新闻列表和新闻详情。
    """
    
    def __init__(self):
        """初始化解析器"""
        # 配置日志记录器
        self.logger = logging.getLogger("PeoplesDailyParser")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def extract_versions(self, html_content, base_url):
        """提取报纸版面链接列表
        
        Args:
            html_content (str): 首页HTML内容
            base_url (str): 基础URL，用于转换相对链接
            
        Returns:
            list: 版面信息列表 [{'title': '版面标题', 'url': '版面URL', 'version_id': 版面ID}, ...]
        """
        self.logger.info("提取报纸版面链接")
        soup = BeautifulSoup(html_content, 'html.parser')
        versions = []
        
        # 版面导航元素
        swiper = soup.select_one("body > div.main.w1000 > div.right.right-main > div.swiper-box > div")
        if swiper:
            links = swiper.find_all('a', href=True)
            for link in links:
                # 提取版面ID
                version_id = self._extract_version_id(link['href'])
                # 构建完整URL
                full_url = urljoin(base_url, link['href'])
                versions.append({
                    'title': link.get_text(strip=True),
                    'url': full_url,
                    'version_id': version_id
                })
            
            self.logger.info(f"成功提取 {len(versions)} 个版面链接")
        else:
            self.logger.warning("未找到版面导航元素")
        
        return versions
    
    def extract_news_list(self, html_content, base_url):
        """提取版面中的新闻列表
        
        Args:
            html_content (str): 版面HTML内容
            base_url (str): 基础URL，用于转换相对链接
        
        Returns:
            list: 新闻列表 [{'title': '新闻标题', 'url': '新闻URL', 'news_id': '新闻ID'}, ...]
        """
        self.logger.info("提取版面新闻列表")
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = []
        
        # 新闻列表元素
        news_list = soup.select_one("body > div.main.w1000 > div.right.right-main > div.news > ul")
        if news_list:
            news_links = news_list.find_all('a', href=True)
            for link in news_links:
                # 提取新闻原始链接
                href = link['href']
                self.logger.debug(f"原始链接: {href}")
                
                # 如果是相对链接，转换为绝对链接
                news_url = urljoin(base_url, href)
                
                # 如果链接是content类型，需要进行转换
                if '/content/' in news_url:
                    self.logger.debug(f"检测到content类型链接: {news_url}")
                    # 使用原始链接，无需修改
                else:
                    self.logger.debug(f"使用原始相对链接构建URL: {news_url}")
                
                news_id = self._extract_news_id(href)
                news_title = link.get_text(strip=True)
                
                news_items.append({
                    'title': news_title,
                    'url': news_url,
                    'news_id': news_id
                })
            
            self.logger.info(f"成功提取 {len(news_items)} 条新闻")
        else:
            self.logger.warning("未找到新闻列表元素")
        
        return news_items
    
    def extract_news_content(self, html_content):
        """提取新闻详情内容
        
        Args:
            html_content (str): 新闻详情页HTML内容
            
        Returns:
            dict: 新闻内容 {'title': '标题', 'content': '正文内容', 'publish_date': '发布日期', 'source': '来源'}
        """
        self.logger.info("提取新闻详情内容")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 新闻标题通常在h1或h2标签中
        title_element = soup.find(['h1', 'h2', 'h3'])
        # 内容通常在特定class的div中
        content_element = soup.find('div', class_=['article', 'article-content', 'content'])
        
        # 尝试提取发布日期
        publish_date = self._extract_date(soup, html_content)
        
        result = {
            'title': title_element.get_text(strip=True) if title_element else '',
            'content': content_element.get_text('\n', strip=True) if content_element else '',
            'publish_date': publish_date,
            'source': '人民日报'
        }
        
        self.logger.info(f"成功提取新闻内容: {result['title']}")
        return result
    
    def extract_keywords(self, html_content):
        """从新闻内容中提取关键词
        
        Args:
            html_content (str): 新闻详情页HTML内容
            
        Returns:
            list: 关键词列表
        """
        self.logger.info("提取新闻关键词")
        soup = BeautifulSoup(html_content, 'html.parser')
        keywords = []
        
        # 查找meta标签中的keywords
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords.get('content').split(',') if k.strip()]
        
        # 查找可能的关键词标签
        keyword_tags = soup.find('div', class_=['keywords', 'tags', 'article-tags'])
        if keyword_tags:
            tag_links = keyword_tags.find_all('a')
            for tag in tag_links:
                keyword = tag.get_text(strip=True)
                if keyword and keyword not in keywords:
                    keywords.append(keyword)
        
        self.logger.info(f"提取到 {len(keywords)} 个关键词")
        return keywords
    
    def _extract_version_id(self, url):
        """从URL中提取版面ID
        
        Args:
            url (str): 版面URL
        
        Returns:
            int: 版面ID
        """
        match = re.search(r'node_(\d+)\.html', url)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_news_id(self, url):
        """从URL中提取新闻ID
        
        Args:
            url (str): 新闻URL
        
        Returns:
            str: 新闻ID
        """
        match = re.search(r'c(\d+)\.html', url)
        if match:
            return match.group(1)
        return ''
    
    def _extract_date(self, soup, html_content):
        """尝试从页面提取发布日期
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            html_content (str): HTML内容字符串
            
        Returns:
            str: 日期字符串，格式为YYYY-MM-DD
        """
        # 方法1：从URL中提取
        match = re.search(r'layout/(\d{6})/(\d{2})/', html_content)
        if match:
            year_month = match.group(1)
            day = match.group(2)
            return f"{year_month[:4]}-{year_month[4:6]}-{day}"
        
        # 方法2：查找日期元素
        date_element = soup.find('div', class_=['date', 'time', 'publish-time'])
        if date_element:
            date_text = date_element.get_text(strip=True)
            # 尝试解析多种日期格式
            for pattern in [r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'(\d{4})-(\d{1,2})-(\d{1,2})']: 
                date_match = re.search(pattern, date_text)
                if date_match:
                    y, m, d = date_match.groups()
                    return f"{y}-{int(m):02d}-{int(d):02d}"
        
        # 默认使用当天中国日期
        china_tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(china_tz).strftime('%Y-%m-%d')
    
    def generate_html_report(self, versions_data, date_string):
        """生成HTML报告
        
        Args:
            versions_data (list): 版面数据列表，每个元素包含版面信息和新闻列表
            date_string (str): 日期字符串，格式为YYYYMMDD
            
        Returns:
            str: HTML报告内容
        """
        self.logger.info(f"生成HTML报告: {date_string}")
        
        # 格式化日期显示
        display_date = f"{date_string[:4]}年{date_string[4:6]}月{date_string[6:8]}日"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>人民日报 - {display_date} - 全版面新闻汇总</title>
    <style>
        body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: #fff; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
        .version {{ margin-bottom: 40px; }}
        .version-title {{ color: #c00; font-size: 24px; padding-bottom: 10px; border-bottom: 2px solid #c00; margin-bottom: 15px; }}
        .news-list {{ list-style-type: none; padding-left: 0; }}
        .news-item {{ margin-bottom: 15px; padding: 10px; border-bottom: 1px dashed #eee; }}
        .news-item:hover {{ background-color: #f9f9f9; }}
        .news-link {{ color: #333; text-decoration: none; font-size: 16px; }}
        .news-link:hover {{ color: #c00; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>人民日报 - {display_date}</h1>
            <p>全版面新闻汇总</p>
        </div>
        
        <div class="content">
"""
        
        # 添加各版面内容
        for i, version in enumerate(versions_data, 1):
            # 构造版面页面的链接
            # 使用版面序号来构建URL，确保从01开始编号
            version_url = f"http://paper.people.com.cn/rmrb/pc/layout/{date_string[:6]}/{date_string[6:8]}/node_{i:02d}.html"
            
            html_content += f"""
            <div class="version">
                <h2 class="version-title"><a href="{version_url}" target="_blank">{version['title']}</a></h2>
                <ul class="news-list">
"""
            
            # 添加当前版面的新闻列表
            for news in version['news']:
                html_content += f"""
                    <li class="news-item">
                        <a href="{news['url']}" class="news-link" target="_blank">{news['title']}</a>
                    </li>
"""
            
            html_content += """
                </ul>
            </div>
"""
        
        # 添加页脚
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>数据来源: 人民日报 - http://paper.people.com.cn</p>
            <p>爬取时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')} (北京时间)</p>
        </div>
    </div>
</body>
</html>
"""
        
        self.logger.info("HTML报告生成成功")
        return html_content 