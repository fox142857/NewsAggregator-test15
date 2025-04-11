#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import logging

logger = logging.getLogger("FileProcessor")

class FileProcessor:
    """文件处理器
    
    负责随机选择文件并提取内容
    """
    
    def __init__(self):
        """初始化文件处理器"""
        # 设置日志
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def select_random_file(self, file_list):
        """从文件列表中随机选择一个文件
        
        Args:
            file_list (list): 文件路径列表
            
        Returns:
            str: 选中的文件路径，如果列表为空则返回None
        """
        if not file_list:
            logger.warning("文件列表为空，无法选择")
            return None
        
        selected_file = random.choice(file_list)
        logger.info(f"随机选择的文件: {os.path.basename(selected_file)}")
        return selected_file
    
    def extract_content(self, file_path):
        """提取文件内容
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            dict: 包含文件内容和元数据的字典
        """
        if not file_path or not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        try:
            logger.info(f"正在提取文件内容: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析Markdown前的元数据（frontmatter）
            metadata = {}
            main_content = content
            
            # 检查是否有frontmatter（以---开始和结束的部分）
            if content.startswith('---'):
                end_index = content.find('---', 3)
                if end_index > 0:
                    frontmatter = content[3:end_index].strip()
                    main_content = content[end_index+3:].strip()
                    
                    # 解析frontmatter中的键值对
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
            
            result = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'metadata': metadata,
                'content': main_content
            }
            
            # 在控制台输出文件内容预览
            preview_length = min(500, len(main_content))
            logger.info(f"文件内容预览 ({preview_length}字符):\n{main_content[:preview_length]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"提取文件内容时出错: {str(e)}")
            return None 