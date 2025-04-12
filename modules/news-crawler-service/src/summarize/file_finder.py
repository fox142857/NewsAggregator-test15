#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import argparse
import sys
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger("FileFinder")

class FileFinder:
    """文件查找器
    
    在output目录中查找当日或前一日的md文件
    """
    
    def __init__(self, output_dir=None):
        """初始化文件查找器
        
        Args:
            output_dir (str, optional): 输出目录路径，默认为src/output
        """
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
    
    def get_current_date(self):
        """获取当前北京时间的日期字符串
        
        Returns:
            str: 日期字符串，格式为YYYYMMDD
        """
        return datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d')
    
    def get_yesterday_date(self):
        """获取前一天北京时间的日期字符串
        
        Returns:
            str: 日期字符串，格式为YYYYMMDD
        """
        yesterday = datetime.now(pytz.timezone('Asia/Shanghai')) - timedelta(days=1)
        return yesterday.strftime('%Y%m%d')
    
    def find_matching_files(self):
        """查找匹配的文件
        
        查找当天或前一天日期开头的.md文件
        
        Returns:
            list: 匹配文件的路径列表
        """
        # 获取当天日期
        today_date = self.get_current_date()
        
        # 查找当天的匹配文件
        today_pattern = f"^{today_date}-.*\\.md$"
        today_files = self._find_files_by_pattern(today_pattern)
        
        if today_files:
            logger.info(f"找到当天({today_date})的匹配文件: {len(today_files)}个")
            return today_files
        
        # 如果当天没有匹配文件，查找前一天的
        yesterday_date = self.get_yesterday_date()
        yesterday_pattern = f"^{yesterday_date}-.*\\.md$"
        yesterday_files = self._find_files_by_pattern(yesterday_pattern)
        
        if yesterday_files:
            logger.info(f"找到前一天({yesterday_date})的匹配文件: {len(yesterday_files)}个")
            return yesterday_files
        
        # 如果都没有找到
        logger.warning(f"未找到当天({today_date})或前一天({yesterday_date})的匹配文件")
        return []
    
    def _find_files_by_pattern(self, pattern):
        """根据正则表达式模式查找文件
        
        Args:
            pattern (str): 正则表达式模式
            
        Returns:
            list: 匹配文件的路径列表
        """
        matching_files = []
        
        try:
            for filename in os.listdir(self.output_dir):
                # 检查文件是否匹配模式（日期开头）
                if re.match(pattern, filename):
                    # 检查文件是否符合YYYYMMDD-XXXX.md格式
                    # 允许使用格式如20250412-0101.md的文件
                    if re.match(r'^\d{8}-\d{4}\.md$', filename):
                        file_path = os.path.join(self.output_dir, filename)
                        if os.path.isfile(file_path):
                            matching_files.append(file_path)
                            logger.debug(f"找到匹配文件: {filename}")
                    else:
                        # 记录不符合格式的文件，但是使用INFO级别而不是DEBUG级别
                        logger.info(f"文件名格式不符合要求，已排除: {filename}")
        except Exception as e:
            logger.error(f"查找文件时出错: {str(e)}")
        
        return matching_files

if __name__ == "__main__":
    # 配置命令行参数
    parser = argparse.ArgumentParser(description='文件查找工具')
    parser.add_argument('-o', '--output_dir', help='输出目录路径，默认为src/output')
    parser.add_argument('-v', '--verbose', action='store_true', help='输出详细日志')
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建文件查找器实例
        finder = FileFinder(output_dir=args.output_dir)
        
        # 查找匹配的文件
        print(f"正在查找匹配的文件...")
        matching_files = finder.find_matching_files()
        
        # 显示结果
        if matching_files:
            print(f"\n找到 {len(matching_files)} 个匹配的文件:")
            for i, file_path in enumerate(matching_files, 1):
                print(f"{i}. {os.path.basename(file_path)} ({os.path.getsize(file_path)} 字节)")
        else:
            print("未找到匹配的文件。")
        
        # 输出当前和昨天的日期 (用于调试)
        print(f"\n当前日期: {finder.get_current_date()}")
        print(f"昨天日期: {finder.get_yesterday_date()}")
        
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 