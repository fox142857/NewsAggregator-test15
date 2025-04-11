#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import logging
import argparse
import sys

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

if __name__ == "__main__":
    # 配置命令行参数
    parser = argparse.ArgumentParser(description='文件处理工具')
    parser.add_argument('file', nargs='?', help='要处理的文件路径，如不提供则需要提供目录和文件数量')
    parser.add_argument('-d', '--directory', help='要处理的目录，会从中随机选择文件')
    parser.add_argument('-n', '--num_files', type=int, default=5, help='随机选择的文件数量，默认为5')
    parser.add_argument('-v', '--verbose', action='store_true', help='输出详细日志')
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建文件处理器实例
        processor = FileProcessor()
        
        if args.file:
            # 处理单个指定文件
            print(f"正在处理文件: {args.file}")
            content_data = processor.extract_content(args.file)
            
            if content_data:
                print(f"\n文件元数据:")
                for key, value in content_data['metadata'].items():
                    print(f"- {key}: {value}")
                
                content_preview = content_data['content'][:500]
                print(f"\n内容预览 (前500字符):\n{content_preview}...")
            else:
                print(f"无法提取文件内容: {args.file}")
        
        elif args.directory:
            # 从目录中随机选择文件
            if not os.path.isdir(args.directory):
                print(f"错误: 指定的目录不存在: {args.directory}")
                sys.exit(1)
                
            # 获取目录中的所有 .md 文件
            md_files = [os.path.join(args.directory, f) for f in os.listdir(args.directory) 
                       if f.endswith('.md') and os.path.isfile(os.path.join(args.directory, f))]
            
            if not md_files:
                print(f"目录中未找到.md文件: {args.directory}")
                sys.exit(1)
                
            # 选择要处理的文件数量
            num_files = min(args.num_files, len(md_files))
            selected_files = []
            
            for _ in range(num_files):
                if not md_files:
                    break
                selected_file = processor.select_random_file(md_files)
                md_files.remove(selected_file)  # 确保不重复选择
                selected_files.append(selected_file)
            
            # 处理选中的文件
            print(f"\n已选择 {len(selected_files)} 个文件进行处理:")
            for i, file_path in enumerate(selected_files, 1):
                print(f"\n--- 处理文件 {i}/{len(selected_files)}: {os.path.basename(file_path)} ---")
                content_data = processor.extract_content(file_path)
                
                if content_data:
                    print(f"元数据:")
                    for key, value in content_data['metadata'].items():
                        print(f"- {key}: {value}")
                    
                    print(f"内容长度: {len(content_data['content'])} 字符")
                else:
                    print(f"无法提取文件内容")
                
                print("---")
        
        else:
            print("错误: 必须提供文件路径或目录")
            parser.print_help()
            sys.exit(1)
            
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 