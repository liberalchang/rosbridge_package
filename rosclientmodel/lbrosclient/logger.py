#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志封装模块
为ROS客户端提供统一的日志输出功能
支持时间戳、日志级别、消息长度限制等功能
"""

import sys
import inspect
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict

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
                 name: str = "LBROSClient",
                 max_message_length: int = 200,
                 show_timestamp: bool = True,
                 timestamp_format: str = "%Y-%m-%d %H:%M:%S.%f",
                 min_level: LogLevel = LogLevel.INFO,
                 show_level: bool = True,
                 show_name: bool = True,
                 enable_colors: bool = True,
                 show_line_info: bool = False):
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
            enable_colors (bool): 是否启用颜色输出
            show_line_info (bool): 是否显示文件名和行号
        """
        self.name = name
        self.max_message_length = max_message_length
        self.show_timestamp = show_timestamp
        self.timestamp_format = timestamp_format
        self.min_level = min_level
        self.show_level = show_level
        self.show_name = show_name
        self.enable_colors = enable_colors
        self.show_line_info = show_line_info
        
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
            if self.enable_colors and sys.stdout.isatty():  # 如果是终端且启用颜色，使用颜色
                color = self.level_colors.get(level, "")
                level_str = f"{color}{level_name}{self.reset_color}"
            else:
                level_str = level_name
            prefix_parts.append(f"[{level_str}]")
        
        # 添加日志器名称
        if self.show_name:
            prefix_parts.append(f"[{self.name}]")
        
        # 添加文件名和行号信息
        if self.show_line_info:
            try:
                # 获取调用栈，跳过当前方法和_log方法，找到实际调用日志的位置
                frame = inspect.currentframe()
                # 跳过: _build_log_prefix -> _log -> debug/info/warning/error/critical
                caller_frame = frame.f_back.f_back.f_back
                if caller_frame:
                    filename = caller_frame.f_code.co_filename
                    lineno = caller_frame.f_lineno
                    # 只显示文件名，不显示完整路径
                    filename = filename.split('/')[-1].split('\\')[-1]
                    prefix_parts.append(f"[{filename}:{lineno}]")
            except (AttributeError, TypeError):
                # 如果获取失败，不添加行号信息
                pass
        
        return " ".join(prefix_parts)
    
    def _build_log_prefix_with_caller(self, level: LogLevel) -> str:
        """
        构建带调用者信息的日志前缀（用于便捷函数）
        
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
            if self.enable_colors and sys.stdout.isatty():  # 如果是终端且启用颜色，使用颜色
                color = self.level_colors.get(level, "")
                level_str = f"{color}{level_name}{self.reset_color}"
            else:
                level_str = level_name
            prefix_parts.append(f"[{level_str}]")
        
        # 添加日志器名称
        if self.show_name:
            prefix_parts.append(f"[{self.name}]")
        
        # 添加文件名和行号信息（针对便捷函数调用）
        if self.show_line_info:
            try:
                # 获取调用栈，跳过当前方法和_log_with_caller_info方法，找到实际调用便捷函数的位置
                frame = inspect.currentframe()
                # 跳过: _build_log_prefix_with_caller -> _log_with_caller_info -> debug/info/warning/error/critical便捷函数
                caller_frame = frame.f_back.f_back.f_back
                if caller_frame:
                    filename = caller_frame.f_code.co_filename
                    lineno = caller_frame.f_lineno
                    # 只显示文件名，不显示完整路径
                    filename = filename.split('/')[-1].split('\\')[-1]
                    prefix_parts.append(f"[{filename}:{lineno}]")
            except (AttributeError, TypeError):
                # 如果获取失败，不添加行号信息
                pass
        
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
    
    def _log_with_caller_info(self, level: LogLevel, message: Any, **kwargs):
        """
        带调用者信息的日志输出方法（用于便捷函数）
        
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
        
        # 构建带调用者信息的日志前缀
        prefix = self._build_log_prefix_with_caller(level)
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
    
    def enable_colors(self, enable: bool = True):
        """启用/禁用颜色输出"""
        self.enable_colors = enable
    
    def enable_line_info(self, enable: bool = True):
        """启用/禁用行号信息显示"""
        self.show_line_info = enable
    
    def configure(self, config: Dict[str, Any]):
        """通过配置字典批量设置参数"""
        if 'max_message_length' in config:
            self.set_max_length(config['max_message_length'])
        if 'show_timestamp' in config:
            self.enable_timestamp(config['show_timestamp'])
        if 'timestamp_format' in config:
            self.set_timestamp_format(config['timestamp_format'])
        if 'min_level' in config:
            if isinstance(config['min_level'], str):
                level_map = {
                    'DEBUG': LogLevel.DEBUG,
                    'INFO': LogLevel.INFO,
                    'WARNING': LogLevel.WARNING,
                    'ERROR': LogLevel.ERROR,
                    'CRITICAL': LogLevel.CRITICAL
                }
                self.set_level(level_map.get(config['min_level'].upper(), LogLevel.INFO))
            else:
                self.set_level(config['min_level'])
        if 'enable_colors' in config:
            self.enable_colors(config['enable_colors'])
        if 'show_level' in config:
            self.show_level = config['show_level']
        if 'show_name' in config:
            self.show_name = config['show_name']
        if 'show_line_info' in config:
            self.enable_line_info(config['show_line_info'])

# 创建默认日志器实例
default_logger = Logger()

# 便捷函数
def debug(message: Any, **kwargs):
    """输出DEBUG级别日志"""
    # 如果启用了行号显示，需要调整调用栈深度
    if default_logger.show_line_info:
        default_logger._log_with_caller_info(LogLevel.DEBUG, message, **kwargs)
    else:
        default_logger.debug(message, **kwargs)

def info(message: Any, **kwargs):
    """输出INFO级别日志"""
    if default_logger.show_line_info:
        default_logger._log_with_caller_info(LogLevel.INFO, message, **kwargs)
    else:
        default_logger.info(message, **kwargs)

def warning(message: Any, **kwargs):
    """输出WARNING级别日志"""
    if default_logger.show_line_info:
        default_logger._log_with_caller_info(LogLevel.WARNING, message, **kwargs)
    else:
        default_logger.warning(message, **kwargs)

def error(message: Any, **kwargs):
    """输出ERROR级别日志"""
    if default_logger.show_line_info:
        default_logger._log_with_caller_info(LogLevel.ERROR, message, **kwargs)
    else:
        default_logger.error(message, **kwargs)

def critical(message: Any, **kwargs):
    """输出CRITICAL级别日志"""
    if default_logger.show_line_info:
        default_logger._log_with_caller_info(LogLevel.CRITICAL, message, **kwargs)
    else:
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

def configure_default_logger(config: Dict[str, Any]):
    """配置默认日志器"""
    default_logger.configure(config)