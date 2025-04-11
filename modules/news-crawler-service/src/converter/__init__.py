#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人民日报转换模块

用于将爬取的新闻内容转换为各种格式
"""

__version__ = '0.2.0'

from .formatter import MarkdownFormatter
from .article_formatter import ArticleFormatter, process_articles 