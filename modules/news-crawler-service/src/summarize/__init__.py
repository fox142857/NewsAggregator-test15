#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人民日报文章AI总结模块

基于DeepSeek API对人民日报文章进行智能总结
"""

__version__ = '0.1.0'

from src.summarize.main import run_summarize

__all__ = ['run_summarize'] 