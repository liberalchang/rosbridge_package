#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志封装模块
为ROS客户端提供统一的日志输出功能
支持时间戳、日志级别、消息长度限制等功能
"""

import sys
from datetime import datetime
from enum import Enum
from typing import Optional, Any

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class Logger:
    """统一日志管理器"""
    
    def __init__(self, 
                 name: str = "ROSClient",
                 max_message_length: int = 200,
                 show_timestamp: bool = True,
                 timestamp_format: str = "%Y-%m-%d %H:%M:%S.%f",
                 min_level: LogLevel = LogLevel.INFO,
                 show_level: bool = True,
                 show_name: bool = True):
        """
        初始化日志管理器
        
        Args:
            name (str): 日志器名称
            max_message_length (int): 单条日志最大长度，超过则截断
            show_timestamp (bool): 是否显示时间戳
            timestamp_format (str): 时间戳格式
            min_level (LogLevel): 最小日志级别
            show_level (bool): 是否显示日志级别
            show_name (bool): 是否显示日志器名称
        """
        self.name = name
        self.max_message_length = max_message_length
        self.show_timestamp = show_timestamp
        self.timestamp_format = timestamp_format
        self.min_level = min_level
        self.show_level = show_level
        self.show_name = show_name
        
        # 日志级别颜色映射（ANSI颜色代码）
        self.level_colors = {
            LogLevel.DEBUG: "\033[36m",    # 青色
            LogLevel.INFO: "\033[32m",     # 绿色
            LogLevel.WARNING: "\033[33m",  # 黄色
            LogLevel.ERROR: "\033[31m",    # 红色
            LogLevel.CRITICAL: "\033[35m"  # 紫色
        }
        self.reset_color = "\033[0m"  # 重置颜色
    
    def _format_message(self, message: Any) -> str:
        """
        格式化消息内容
        
        Args:
            message: 要格式化的消息
            
        Returns:
            str: 格式化后的消息字符串
        """
        # 转换为字符串
        if not isinstance(message, str):
            message = str(message)
        
        # 限制消息长度
        if len(message) > self.max_message_length:
            truncated_length = self.max_message_length - 3  # 为"..."预留空间
            message = message[:truncated_length] + "..."
        
        return message
    
    def _build_log_prefix(self, level: LogLevel) -> str:
        """
        构建日志前缀
        
        Args:
            level (LogLevel): 日志级别
            
        Returns:
            str: 日志前缀字符串
        """
        prefix_parts = []
        
        # 添加时间戳
        if self.show_timestamp:
            timestamp = datetime.now().strftime(self.timestamp_format)
            # 截断微秒到3位
            if ".%f" in self.timestamp_format:
                timestamp = timestamp[:-3]
            prefix_parts.append(f"[{timestamp}]")
        
        # 添加日志级别
        if self.show_level:
            level_name = level.name
            if sys.stdout.isatty():  # 如果是终端，使用颜色
                color = self.level_colors.get(level, "")
                level_str = f"{color}{level_name}{self.reset_color}"
            else:
                level_str = level_name
            prefix_parts.append(f"[{level_str}]")
        
        # 添加日志器名称
        if self.show_name:
            prefix_parts.append(f"[{self.name}]")
        
        return " ".join(prefix_parts)
    
    def _log(self, level: LogLevel, message: Any, **kwargs):
        """
        内部日志输出方法
        
        Args:
            level (LogLevel): 日志级别
            message: 日志消息
            **kwargs: 额外参数
        """
        # 检查日志级别
        if level.value < self.min_level.value:
            return
        
        # 格式化消息
        formatted_message = self._format_message(message)
        
        # 构建完整日志
        prefix = self._build_log_prefix(level)
        if prefix:
            full_message = f"{prefix} {formatted_message}"
        else:
            full_message = formatted_message
        
        # 输出日志
        if level.value >= LogLevel.ERROR.value:
            print(full_message, file=sys.stderr, **kwargs)
        else:
            print(full_message, **kwargs)
    
    def debug(self, message: Any, **kwargs):
        """输出DEBUG级别日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: Any, **kwargs):
        """输出INFO级别日志"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: Any, **kwargs):
        """输出WARNING级别日志"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: Any, **kwargs):
        """输出ERROR级别日志"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: Any, **kwargs):
        """输出CRITICAL级别日志"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def log(self, level: LogLevel, message: Any, **kwargs):
        """通用日志输出方法"""
        self._log(level, message, **kwargs)
    
    def set_max_length(self, length: int):
        """设置最大消息长度"""
        self.max_message_length = max(10, length)  # 最小长度为10
    
    def set_level(self, level: LogLevel):
        """设置最小日志级别"""
        self.min_level = level
    
    def enable_timestamp(self, enable: bool = True):
        """启用/禁用时间戳"""
        self.show_timestamp = enable
    
    def set_timestamp_format(self, format_str: str):
        """设置时间戳格式"""
        self.timestamp_format = format_str

# 创建默认日志器实例
default_logger = Logger()

# 便捷函数
def debug(message: Any, **kwargs):
    """输出DEBUG级别日志"""
    default_logger.debug(message, **kwargs)

def info(message: Any, **kwargs):
    """输出INFO级别日志"""
    default_logger.info(message, **kwargs)

def warning(message: Any, **kwargs):
    """输出WARNING级别日志"""
    default_logger.warning(message, **kwargs)

def error(message: Any, **kwargs):
    """输出ERROR级别日志"""
    default_logger.error(message, **kwargs)

def critical(message: Any, **kwargs):
    """输出CRITICAL级别日志"""
    default_logger.critical(message, **kwargs)

def set_max_length(length: int):
    """设置默认日志器的最大消息长度"""
    default_logger.set_max_length(length)

def set_level(level: LogLevel):
    """设置默认日志器的最小日志级别"""
    default_logger.set_level(level)

def create_logger(name: str, **kwargs) -> Logger:
    """创建新的日志器实例"""
    return Logger(name=name, **kwargs)

# 示例用法
if __name__ == "__main__":
    # 测试日志功能
    logger = Logger("TestLogger", max_message_length=50)
    
    logger.debug("这是一条调试消息")
    logger.info("这是一条信息消息")
    logger.warning("这是一条警告消息")
    logger.error("这是一条错误消息")
    logger.critical("这是一条严重错误消息")
    
    # 测试长消息截断
    long_message = "这是一条非常长的消息" * 10
    logger.info(long_message)
    
    # 测试便捷函数
    info("使用便捷函数输出的消息")
    set_max_length(30)
    info("设置新的最大长度后的消息，这条消息会被截断")