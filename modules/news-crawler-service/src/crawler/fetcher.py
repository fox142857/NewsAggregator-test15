#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

class PeoplesDailyFetcher:
    """人民日报网页获取模块
    
    负责从人民日报网站获取新闻内容，包括版面列表和新闻详情。
    """
    
    def __init__(self, base_url="http://paper.people.com.cn/rmrb/pc/layout"):
        """初始化爬虫配置
        
        Args:
            base_url (str): 人民日报官网基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
        # 配置日志记录器
        self.logger = logging.getLogger("PeoplesDailyFetcher")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def get_latest_edition(self):
        """获取最新一期报纸的首页内容
        
        Returns:
            tuple: (重定向后的URL, HTML内容)
        """
        self.logger.info(f"获取最新一期报纸首页: {self.base_url}")
        try:
            response = self.session.get(self.base_url, headers=self.headers, allow_redirects=True)
            response.raise_for_status()
            response.encoding = 'utf-8'
            self.logger.info(f"成功获取最新一期，URL: {response.url}")
            return response.url, response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取最新一期失败: {str(e)}")
            return None, None
    
    def get_edition_by_date(self, year, month, day, node=1):
        """获取指定日期报纸的特定版面
        
        Args:
            year (int): 年份
            month (int): 月份
            day (int): 日期
            node (int, optional): 版面号. 默认为1.
            
        Returns:
            tuple: (URL, HTML内容)
        """
        date_url = f"{self.base_url}/{year}{month:02d}/{day:02d}/node_{node:02d}.html"
        self.logger.info(f"获取指定日期版面: {date_url}")
        
        try:
            response = self.session.get(date_url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            self.logger.info(f"成功获取指定日期版面: {date_url}")
            return date_url, response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取指定日期版面失败: {date_url}, 错误: {str(e)}")
            return None, None
    
    def extract_versions(self, html_content, base_url):
        """从首页提取报纸版面链接列表
        
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
    
    def get_all_versions(self, date_tuple=None):
        """获取指定日期或最新一期的所有版面内容
        
        Args:
            date_tuple (tuple, optional): (年, 月, 日) 元组. 默认为None，表示获取最新一期.
        
        Returns:
            list: 所有版面数据列表 [{'version_info': 版面信息, 'html_content': 版面HTML内容}, ...]
        """
        if date_tuple:
            year, month, day = date_tuple
            self.logger.info(f"获取 {year}-{month:02d}-{day:02d} 所有版面")
            base_url, main_html = self.get_edition_by_date(year, month, day)
        else:
            self.logger.info("获取最新一期所有版面")
            base_url, main_html = self.get_latest_edition()
        
        if not main_html:
            self.logger.error("获取首页失败，无法提取版面")
            return []
        
        # 提取所有版面链接
        versions = self.extract_versions(main_html, base_url)
        results = []
        
        # 获取每个版面的内容
        for version in versions:
            self.logger.info(f"获取版面: {version['title']} - {version['url']}")
            try:
                response = self.session.get(version['url'], headers=self.headers)
                response.raise_for_status()
                response.encoding = 'utf-8'
                results.append({
                    'version_info': version,
                    'html_content': response.text
                })
                self.logger.info(f"成功获取版面: {version['title']}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"获取版面失败: {version['title']}, 错误: {str(e)}")
            
            # 控制请求速率，避免给服务器造成压力
            time.sleep(0.5)
        
        self.logger.info(f"共获取 {len(results)}/{len(versions)} 个版面内容")
        return results
    
    def extract_news_list(self, html_content, base_url):
        """从版面内容中提取新闻列表
        
        Args:
            html_content (str): 版面HTML内容
            base_url (str): 基础URL，用于转换相对链接
        
        Returns:
            list: 新闻列表 [{'title': '新闻标题', 'url': '新闻URL', 'news_id': '新闻ID'}, ...]
        """
        self.logger.info("提取版面新闻列表")
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = []
        
        # 寻找新闻列表元素
        news_list = soup.select_one("body > div.main.w1000 > div.right.right-main > div.news > ul")
        if news_list:
            news_links = news_list.find_all('a', href=True)
            for link in news_links:
                news_url = urljoin(base_url, link['href'])
                news_id = self._extract_news_id(link['href'])
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
    
    def get_news_content(self, news_url):
        """获取新闻详情页内容
        
        Args:
            news_url (str): 新闻详情页URL
        
        Returns:
            str: 新闻详情页HTML内容，获取失败则返回None
        """
        self.logger.info(f"获取新闻内容: {news_url}")
        try:
            response = self.session.get(news_url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            self.logger.info(f"成功获取新闻内容: {news_url}")
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取新闻内容失败: {news_url}, 错误: {str(e)}")
            return None
    
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
    
    def extract_date_from_url(self, url):
        """从URL中提取日期信息
        
        Args:
            url (str): 包含日期信息的URL
        
        Returns:
            tuple: (年, 月, 日) 元组，提取失败则返回None
        """
        match = re.search(r'/(\d{4})(\d{2})/(\d{2})/', url)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return (year, month, day)
        return None 