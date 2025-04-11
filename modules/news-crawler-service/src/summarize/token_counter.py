#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
import unicodedata
import argparse
import sys

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

if __name__ == "__main__":
    # 配置命令行参数
    parser = argparse.ArgumentParser(description='Token计数器工具')
    parser.add_argument('text', nargs='?', help='要计算token的文本。如不提供则从标准输入读取')
    parser.add_argument('-f', '--file', help='要计算token的文件路径')
    parser.add_argument('-c', '--chinese', action='store_true', help='输出是否主要为中文')
    parser.add_argument('-e', '--estimate', type=int, help='估算指定字数的token数量')
    parser.add_argument('-v', '--verbose', action='store_true', help='输出详细日志')
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建Token计数器实例
        counter = TokenCounter()
        
        if args.estimate:
            # 估算指定字数的token数量
            tokens = counter.estimate_output_tokens(args.estimate, args.chinese)
            print(f"估算 {args.estimate} 字的输出约为 {tokens} tokens")
            # 计算成本
            cost = counter.estimate_cost(0, tokens)
            print(f"估算成本: ${cost:.6f}")
            sys.exit(0)
        
        # 获取要计算token的文本
        text = None
        if args.file:
            # 从文件读取
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"已读取文件: {args.file}, 字符数: {len(text)}")
        elif args.text:
            # 使用命令行参数
            text = args.text
        else:
            # 从标准输入读取
            print("请输入要计算token的文本 (Ctrl+D结束输入):")
            text = sys.stdin.read()
        
        if not text:
            print("错误: 未提供文本")
            sys.exit(1)
        
        # 计算token数量
        tokens = counter.count_tokens(text)
        
        # 创建模拟消息以估算输入token
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": text}
        ]
        input_tokens = counter.estimate_input_tokens(messages)
        
        # 计算成本
        # 假设输出token是输入的一半
        output_tokens = tokens // 2
        cost = counter.estimate_cost(input_tokens, output_tokens)
        
        print(f"\n文本统计:")
        print(f"- 字符数: {len(text)}")
        print(f"- 预估token数: {tokens}")
        print(f"- 作为API输入的token数: {input_tokens}")
        print(f"- 假设输出token数: {output_tokens}")
        print(f"- 预估API调用成本: ${cost:.6f}")
        
        # 字符类型统计
        chinese_chars = sum(1 for char in text if counter._is_chinese(char))
        print(f"\n字符类型分布:")
        print(f"- 中文字符: {chinese_chars} ({chinese_chars/len(text)*100:.1f}%)")
        print(f"- 非中文字符: {len(text) - chinese_chars} ({(len(text) - chinese_chars)/len(text)*100:.1f}%)")
        
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 