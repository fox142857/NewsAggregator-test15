#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
from datetime import datetime
import pytz
import requests
import re

# 导入Token计数器
from src.summarize.token_counter import TokenCounter

# 尝试导入OpenAI模块，如果不存在则使用替代方案
try:
    from openai import OpenAI
    has_openai = True
except ImportError:
    has_openai = False
    logging.warning("未安装openai模块，将使用requests替代。建议运行 'pip install openai' 安装更稳定的官方SDK。")

logger = logging.getLogger("AISummarizer")

class AISummarizer:
    """AI内容总结器
    
    使用DeepSeek API对内容进行总结
    """
    
    def __init__(self, api_key=None, output_dir=None, use_mock=False):
        """初始化AI总结器
        
        Args:
            api_key (str, optional): DeepSeek API密钥，如未提供则尝试从环境变量获取
            output_dir (str, optional): 输出目录路径，默认为src/output
            use_mock (bool, optional): 是否使用模拟模式，在没有API密钥的情况下返回模拟结果
        """
        # 设置API密钥
        self.api_key = api_key
        if self.api_key is None:
            # 尝试从环境变量获取API密钥
            self.api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not self.api_key:
                logger.warning("未提供DeepSeek API密钥，请设置DEEPSEEK_API_KEY环境变量或在初始化时提供")
        
        # 设置模拟模式
        self.use_mock = use_mock or not self.api_key
                
        # 设置API客户端
        self.has_openai = has_openai
        if self.has_openai and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        
        # 创建Token计数器
        self.token_counter = TokenCounter()
        
        # 设置输出目录
        if output_dir is None:
            # 使用默认输出目录
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        else:
            self.output_dir = output_dir
            
        # 设置日志
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def summarize(self, content_data):
        """使用DeepSeek API对内容进行总结
        
        Args:
            content_data (dict): 包含文件内容和元数据的字典
            
        Returns:
            dict: 总结结果，包含原始内容和总结内容
        """
        if not content_data or 'content' not in content_data:
            logger.error("内容数据无效，无法进行总结")
            return None
        
        if not self.api_key and not self.use_mock:
            logger.error("未设置API密钥，无法调用DeepSeek API")
            return None
            
        try:
            logger.info("正在准备进行内容总结...")
            
            # 准备提示词
            prompt = self._generate_fixed_prompt(content_data)
            
            # 准备消息
            messages = [
                {"role": "system", "content": "你是一个专业的新闻摘要助手，擅长提取新闻文章的关键信息，并按照模板生成简洁明了的总结。"},
                {"role": "user", "content": prompt}
            ]
            
            # 计算输入tokens
            input_tokens = self.token_counter.estimate_input_tokens(messages)
            # 估算输出tokens (基于200字的中文输出)
            output_tokens = self.token_counter.estimate_output_tokens(200)
            # 估算成本
            estimated_cost = self.token_counter.estimate_cost(input_tokens, output_tokens)
            
            logger.info(f"估算输入tokens: {input_tokens}")
            logger.info(f"估算输出tokens: {output_tokens}")
            logger.info(f"估算API调用成本: ${estimated_cost:.6f}")
            
            # 如果是模拟模式，返回模拟结果
            if self.use_mock:
                logger.info("使用模拟模式，生成模拟总结内容")
                summary = self._generate_mock_summary(content_data)
            else:
                logger.info("正在调用DeepSeek API进行内容总结...")
                # 调用API
                if self.has_openai:
                    # 使用OpenAI SDK
                    response = self.client.chat.completions.create(
                        model="deepseek-chat",  # 使用DeepSeek-V3模型
                        messages=messages,
                        temperature=0.3,  # 较低的温度使输出更加确定性
                        stream=False
                    )
                    
                    # 提取总结内容
                    summary = response.choices[0].message.content
                else:
                    # 使用requests替代
                    response = requests.post(
                        "https://api.deepseek.com/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": messages,
                            "temperature": 0.3,
                            "stream": False
                        }
                    )
                    
                    # 检查响应
                    response.raise_for_status()
                    data = response.json()
                    
                    # 提取总结内容
                    summary = data['choices'][0]['message']['content']
            
            logger.info("内容总结完成")
            logger.info(f"总结内容预览:\n{summary[:200]}...")
            
            # 准备结果
            result = {
                'original_content': content_data,
                'summary': summary,
                'timestamp': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
                'tokens': {
                    'input': input_tokens,
                    'output': len(summary),  # 实际输出字符数
                    'estimated_cost': estimated_cost
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"内容总结出错: {str(e)}")
            return None
    
    def save_summary(self, summary_data):
        """保存总结内容到文件
        
        Args:
            summary_data (dict): 总结结果
            
        Returns:
            str: 保存的文件路径，失败则返回None
        """
        if not summary_data or 'summary' not in summary_data or 'original_content' not in summary_data:
            logger.error("总结数据无效，无法保存")
            return None
            
        try:
            # 获取原始文件名
            original_file = summary_data['original_content']['file_name']
            
            # 创建新文件名
            base_name = os.path.splitext(original_file)[0]
            summary_file = f"{base_name}-ai-summarize.md"
            output_path = os.path.join(self.output_dir, summary_file)
            
            # 提取原始元数据
            original_metadata = summary_data['original_content'].get('metadata', {})
            
            # 创建总结内容
            content = "---\n"
            content += f"title: AI总结: {original_metadata.get('title', '未知标题')}\n"
            content += f"original_title: {original_metadata.get('title', '未知标题')}\n"
            content += f"date: {original_metadata.get('date', datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d'))}\n"
            content += f"source: {original_metadata.get('source', '人民日报')}\n"
            content += f"summarized_at: {summary_data['timestamp']}\n"
            
            # 添加token使用情况
            if 'tokens' in summary_data:
                tokens_info = summary_data['tokens']
                content += f"input_tokens: {tokens_info.get('input', 0)}\n"
                content += f"output_chars: {tokens_info.get('output', 0)}\n"
                content += f"estimated_cost: ${tokens_info.get('estimated_cost', 0):.6f}\n"
            
            content += "---\n\n"
            
            # 添加总结内容
            content += f"# AI总结: {original_metadata.get('title', '未知标题')}\n\n"
            content += summary_data['summary'] + "\n\n"
            
            # 添加原文链接
            content += "---\n\n"
            content += f"*原文: [{original_file}]({original_file})*\n"
            
            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"总结内容已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"保存总结内容时出错: {str(e)}")
            return None
    
    def _generate_fixed_prompt(self, content_data):
        """生成固定格式的提示词
        
        Args:
            content_data (dict): 包含文件内容和元数据的字典
            
        Returns:
            str: 总结提示词
        """
        content = content_data.get('content', '')
        
        # 使用固定格式的提示词
        prompt = f"""
[文章内容]
{content}
```
帮我总结以上新闻内容，字数控制在200左右，结果以以下模板输出：
```
时间：
地点：
人物：
事件：
起因：
结果：
```
直接输出结果，不要有任何多余的内容。
"""
        return prompt
    
    def _generate_mock_summary(self, content_data):
        """生成模拟的总结内容，用于没有API密钥的情况
        
        Args:
            content_data (dict): 包含文件内容和元数据的字典
            
        Returns:
            str: 模拟的总结内容
        """
        metadata = content_data.get('metadata', {})
        title = metadata.get('title', '未知标题')
        date = metadata.get('date', datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d'))
        
        # 分析内容找出一些关键信息
        content = content_data.get('content', '')
        # 简单识别一些时间、地点、人物
        time_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日)'
        times = re.findall(time_pattern, content)
        time_str = times[0] if times else date
        
        # 从内容中提取前200个字符作为事件描述
        event_desc = content[:200].strip() if len(content) > 0 else "无法提取事件描述"
        
        # 生成模拟总结
        mock_summary = f"""时间：{time_str}
地点：模拟地点
人物：模拟人物
事件：{title}
起因：这是一个模拟总结，由于未提供API密钥，系统生成了这个示例。
结果：为了完整展示功能，系统提供了这个模板化的总结。实际使用时，请提供有效的DeepSeek API密钥。"""
        
        return mock_summary 