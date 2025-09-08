#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LBROS Client - 模块化ROS客户端库

提供ROSBridge和ZMQ客户端的统一接口，支持配置化管理和日志功能。
适用于ROS1/ROS2系统的跨平台通信。

主要组件:
- ROSBridgeClient: 基于roslibpy的WebSocket客户端
- ZMQClient: 基于ZeroMQ的高性能客户端  
- Logger: 统一日志管理
- ConfigManager: 配置文件管理

使用示例:
    from lbrosclient import ROSBridgeClient, ZMQClient, Logger
    
    # 创建ROSBridge客户端
    ros_client = ROSBridgeClient('config.yaml')
    ros_client.start()
    
    # 创建ZMQ客户端
    zmq_client = ZMQClient('zmq_config.yaml')
    zmq_client.start()
"""

__version__ = '1.0.0'
__author__ = 'LBROS Team'
__email__ = 'support@lbros.com'

# 导入主要类
from .logger import Logger, LogLevel
from .param_manager import ParamManager
from .ros_client import ROSBridgeClient
from .zmq_client import ZMQClient

# 导出的公共接口
__all__ = [
    'Logger',
    'LogLevel', 
    'ParamManager',
    'ROSBridgeClient',
    'ZMQClient'
]

# 版本信息
version_info = (1, 0, 0)