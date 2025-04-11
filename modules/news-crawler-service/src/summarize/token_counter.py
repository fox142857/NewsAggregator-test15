#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
import unicodedata

logger = logging.getLogger("TokenCounter")

class TokenCounter:
    """Token计数器
    
    用于计算DeepSeek API的输入token和估算输出token
    参考：https://api-docs.deepseek.com/zh-cn/
    """
    
    def __init__(self):
        """初始化Token计数器"""
        # 设置日志
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def count_tokens(self, text):
        """计算文本的大致token数量
        
        Args:
            text (str): 输入文本
            
        Returns:
            int: 估算的token数量
        """
        if not text:
            return 0
        
        # 初步处理文本
        text = text.strip()
        
        # 中文字符计数 (每个中文字符约为1个token)
        chinese_chars = sum(1 for char in text if self._is_chinese(char))
        
        # 非中文字符的字数 (大约每4个非中文字符为1个token)
        non_chinese_chars = len(text) - chinese_chars
        non_chinese_tokens = non_chinese_chars / 4
        
        # 总token
        total_tokens = chinese_chars + non_chinese_tokens
        
        # 向上取整
        return int(total_tokens + 0.5)
    
    def estimate_input_tokens(self, messages):
        """估算聊天消息的输入token数量
        
        Args:
            messages (list): 消息列表，格式为[{"role": "xxx", "content": "xxx"}, ...]
            
        Returns:
            int: 估算的输入token数量
        """
        if not messages:
            return 0
        
        total_tokens = 0
        
        # 每条消息的固定开销 (角色定义等)
        message_overhead = 4
        
        for message in messages:
            # 计算消息内容的token
            content = message.get('content', '')
            content_tokens = self.count_tokens(content)
            
            # 加上消息固定开销
            total_tokens += content_tokens + message_overhead
        
        # DeepSeek Chat模型的固定开销
        total_tokens += 3
        
        return total_tokens
    
    def estimate_output_tokens(self, word_count, is_chinese=True):
        """根据预期的输出字数估算输出token
        
        Args:
            word_count (int): 预期输出的字数
            is_chinese (bool, optional): 输出是否主要为中文. 默认为True.
            
        Returns:
            int: 估算的输出token数量
        """
        if is_chinese:
            # 中文文本中，1个中文字符约等于1个token
            return word_count
        else:
            # 英文等非中文文本中，约4个字符等于1个token
            return int(word_count / 4 + 0.5)
    
    def estimate_cost(self, input_tokens, output_tokens):
        """估算API调用成本
        
        Args:
            input_tokens (int): 输入token数量
            output_tokens (int): 输出token数量
            
        Returns:
            float: 预估成本（美元）
        """
        # DeepSeek-Chat 模型价格 (参考官方文档)
        input_price_per_1k_tokens = 0.0005   # 输入：每1000 tokens 0.0005美元
        output_price_per_1k_tokens = 0.0025  # 输出：每1000 tokens 0.0025美元
        
        input_cost = (input_tokens / 1000) * input_price_per_1k_tokens
        output_cost = (output_tokens / 1000) * output_price_per_1k_tokens
        
        total_cost = input_cost + output_cost
        return total_cost
    
    def _is_chinese(self, char):
        """判断字符是否为中文字符
        
        Args:
            char (str): 输入字符
            
        Returns:
            bool: 是否为中文字符
        """
        try:
            # 使用Unicode东亚宽度特性判断
            return 'CJK' in unicodedata.name(char)
        except:
            return False 