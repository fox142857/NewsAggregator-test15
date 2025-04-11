#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import pytz  # 添加pytz库导入

logger = logging.getLogger("MarkdownFormatter")

class MarkdownFormatter:
    """Markdown格式化与元数据处理
    
    负责处理Markdown格式并添加必要的元数据
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
    
    def generate_markdown_report(self, versions_data, date_string):
        """生成Markdown报告
        
        Args:
            versions_data (list): 版面数据列表，每个元素包含版面信息和新闻列表
            date_string (str): 日期字符串，格式为YYYYMMDD
            
        Returns:
            str: Markdown报告内容
        """
        logger.info(f"生成Markdown报告: {date_string}")
        
        # 格式化日期显示
        display_date = f"{date_string[:4]}年{date_string[4:6]}月{date_string[6:8]}日"
        
        # 开始生成Markdown内容
        md_content = self.add_frontmatter({
            'title': f"人民日报 - {display_date}",
            'description': "全版面新闻汇总",
            'sidebar': "auto"
        })
        
        md_content += f"\n# 人民日报 - {display_date}\n\n全版面新闻汇总\n\n"
        
        # 添加各版面内容
        for i, version in enumerate(versions_data, 1):
            # 构造版面页面的链接
            version_url = f"http://paper.people.com.cn/rmrb/pc/layout/{date_string[:6]}/{date_string[6:8]}/node_{i:02d}.html"
            
            md_content += f"## [{version['title']}]({version_url})\n\n"
            
            # 添加当前版面的新闻列表
            for news in version['news']:
                md_content += f"- [{news['title']}]({news['url']})\n"
            
            md_content += "\n"
        
        # 添加页脚
        md_content += f"---\n\n"
        md_content += f"数据来源: 人民日报 - [http://paper.people.com.cn](http://paper.people.com.cn)  \n"
        md_content += f"爬取时间: {datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n"
        
        logger.info("Markdown报告生成成功")
        return md_content
    
    def add_frontmatter(self, metadata):
        """添加frontmatter元数据
        
        Args:
            metadata (dict): 元数据字典
            
        Returns:
            str: 包含frontmatter的markdown文本
        """
        frontmatter = "---\n"
        
        for key, value in metadata.items():
            if isinstance(value, str):
                frontmatter += f"{key}: {value}\n"
            else:
                frontmatter += f"{key}: {str(value)}\n"
                
        frontmatter += "---\n"
        return frontmatter
    
    def organize_today_files(self, files, output_dir):
        """组织当天文件结构
        
        Args:
            files (list): 文件列表
            output_dir (str): 输出目录
            
        Returns:
            bool: 操作是否成功
        """
        # 此函数将在未来扩展，目前为占位符
        logger.info(f"正在组织文件到: {output_dir}")
        return True 