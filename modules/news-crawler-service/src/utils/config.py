#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理类
    
    负责加载和提供应用配置信息
    """
    
    def __init__(self, config_path=None):
        """初始化配置管理器
        
        Args:
            config_path (str, optional): 配置文件路径. 默认为None，将使用默认路径.
        """
        if config_path is None:
            # 默认配置文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, 'config', 'app_config.json')
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件
        
        Returns:
            dict: 配置数据
        """
        try:
            logger.info(f"加载配置文件: {self.config_path}")
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("配置文件加载成功")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            # 返回空配置，避免程序崩溃
            return {}
    
    def get(self, section, key=None, default=None):
        """获取配置值
        
        Args:
            section (str): 配置节名称
            key (str, optional): 配置项名称. 默认为None，表示获取整个节.
            default: 默认值，当配置项不存在时返回
            
        Returns:
            配置值，或在配置不存在时返回默认值
        """
        if section not in self.config:
            logger.warning(f"配置节不存在: {section}")
            return default
        
        if key is None:
            return self.config[section]
        
        if key not in self.config[section]:
            logger.warning(f"配置项不存在: {section}.{key}")
            return default
        
        return self.config[section][key]
    
    def reload(self):
        """重新加载配置文件"""
        logger.info("重新加载配置文件")
        self.config = self._load_config()
        return self.config

# 创建默认配置管理器实例
config_manager = ConfigManager()

def get_config(section, key=None, default=None):
    """获取配置值的便捷函数
    
    Args:
        section (str): 配置节名称
        key (str, optional): 配置项名称. 默认为None.
        default: 默认值
        
    Returns:
        配置值
    """
    return config_manager.get(section, key, default) 