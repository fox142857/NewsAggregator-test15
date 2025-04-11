#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, level=logging.INFO, log_file=None, max_bytes=10485760, backup_count=5):
    """配置日志记录器
    
    Args:
        name (str): 日志记录器名称
        level (int, optional): 日志级别. 默认为logging.INFO.
        log_file (str, optional): 日志文件路径. 默认为None，表示不使用文件日志.
        max_bytes (int, optional): 日志文件最大大小，超过后将自动滚动. 默认为10MB.
        backup_count (int, optional): 保留的备份日志文件数量. 默认为5.
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的处理器，避免重复添加
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 设置格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建滚动文件处理器
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # 添加到日志记录器
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """获取已配置的日志记录器
    
    如果日志记录器已存在，则直接返回；否则创建一个新的日志记录器。
    
    Args:
        name (str): 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name) 