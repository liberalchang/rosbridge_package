#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数管理模块
基于Pydantic的参数管理器，支持ROSBridge和ZMQ客户端配置管理
提供多线程安全的参数存储和访问
"""

import json
import yaml
from pydantic import BaseModel, Field
from configparser import ConfigParser
from threading import RLock
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


class ParamManager:
    """
    参数管理器，管理ROSBridge和ZMQ客户端相关参数并提供多线程安全支持。
    """

    _instance = None
    _lock = RLock()

    class ROSBridgeParameters(BaseModel):
        """
        用于存储ROSBridge相关参数的 Pydantic 数据模型
        """
        # 连接配置
        host: str = Field(default="localhost", description="ROSBridge服务器地址")
        port: int = Field(default=9090, description="ROSBridge服务器端口")
        protocol: str = Field(default="ws", description="连接协议(ws/wss)")
        connection_timeout: float = Field(default=10.0, description="连接超时时间(秒)")
        retry_interval: float = Field(default=1.0, description="重试间隔(秒)")
        max_retries: int = Field(default=3, description="最大重试次数")
        
        # WebSocket配置
        ping_interval: float = Field(default=20.0, description="WebSocket ping间隔(秒)")
        ping_timeout: float = Field(default=10.0, description="WebSocket ping超时(秒)")
        close_timeout: float = Field(default=10.0, description="WebSocket关闭超时(秒)")
        max_size: int = Field(default=1048576, description="WebSocket最大消息大小(字节)")
        
        # 自动重连配置
        auto_reconnect: bool = Field(default=True, description="是否自动重连")
        reconnect_interval: float = Field(default=5.0, description="重连间隔(秒)")
        max_reconnect_attempts: int = Field(default=5, description="最大重连尝试次数")
        
        # 日志配置
        verbose: bool = Field(default=False, description="是否启用详细日志")
        show_connection_status: bool = Field(default=True, description="是否显示连接状态")
        show_message_content: bool = Field(default=False, description="是否显示消息内容")
        max_message_length: int = Field(default=200, description="最大消息显示长度")
        
        # 性能配置
        main_loop_sleep: float = Field(default=0.1, description="主循环休眠时间(秒)")
        message_processing_sleep: float = Field(default=0.01, description="消息处理休眠时间(秒)")
        publish_sleep: float = Field(default=0.01, description="发布休眠时间(秒)")
        
        # 消息配置
        message_format: str = Field(default="json", description="消息格式(json/string/bytes)")
        encoding: str = Field(default="utf-8", description="消息编码")
        compression_enabled: bool = Field(default=False, description="是否启用压缩")
        compression_level: int = Field(default=6, description="压缩级别(1-9)")
        
        class Config:
            populate_by_name = True

    class ZMQParameters(BaseModel):
        """
        用于存储ZMQ相关参数的 Pydantic 数据模型
        """
        # 连接配置
        host: str = Field(default="localhost", description="ZMQ服务器地址")
        port: int = Field(default=5555, description="ZMQ服务器端口")
        connection_timeout: float = Field(default=10.0, description="连接超时时间(秒)")
        retry_interval: float = Field(default=1.0, description="重试间隔(秒)")
        max_retries: int = Field(default=3, description="最大重试次数")
        
        # 套接字配置
        linger_time: int = Field(default=1000, description="套接字关闭等待时间(毫秒)")
        high_water_mark: int = Field(default=1000, description="高水位标记")
        receive_timeout: int = Field(default=5000, description="接收超时时间(毫秒)")
        send_timeout: int = Field(default=5000, description="发送超时时间(毫秒)")
        
        # 自动重连配置
        auto_reconnect: bool = Field(default=True, description="是否自动重连")
        reconnect_interval: float = Field(default=5.0, description="重连间隔(秒)")
        max_reconnect_attempts: int = Field(default=5, description="最大重连尝试次数")
        
        # 日志配置
        verbose: bool = Field(default=False, description="是否启用详细日志")
        show_connection_status: bool = Field(default=True, description="是否显示连接状态")
        show_message_content: bool = Field(default=False, description="是否显示消息内容")
        max_message_length: int = Field(default=200, description="最大消息显示长度")
        
        # 性能配置
        main_loop_sleep: float = Field(default=0.1, description="主循环休眠时间(秒)")
        message_processing_sleep: float = Field(default=0.01, description="消息处理休眠时间(秒)")
        
        # 消息配置
        message_format: str = Field(default="json", description="消息格式(json/string/bytes)")
        encoding: str = Field(default="utf-8", description="消息编码")
        compression_enabled: bool = Field(default=False, description="是否启用压缩")
        compression_level: int = Field(default=6, description="压缩级别(1-9)")
        
        class Config:
            populate_by_name = True

    class NetworkParameters(BaseModel):
        """
        用于存储网络相关参数的 Pydantic 数据模型
        """
        connectivity_check_enabled: bool = Field(default=True, description="是否启用连通性检查")
        connectivity_timeout: float = Field(default=3.0, description="连通性检查超时时间(秒)")
        
        class Config:
            populate_by_name = True

    def __new__(cls, *args, **kwargs):
        """
        单例模式，确保全局只有一个 ParamManager 实例。
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._lock = RLock()
            self.rosbridge_params = self.ROSBridgeParameters()
            self.zmq_params = self.ZMQParameters()
            self.network_params = self.NetworkParameters()
            self.config_file = None
            self._initialized = True

    def load_config(self, config_file: str):
        """
        从配置文件加载参数，并保存配置文件路径以支持写回。
        支持JSON、YAML和INI格式的配置文件。
        :param config_file: 配置文件路径
        """
        self.config_file = config_file
        
        if not os.path.exists(config_file):
            return
            
        file_ext = Path(config_file).suffix.lower()
        
        if file_ext in ['.json']:
            self._load_json_config(config_file)
        elif file_ext in ['.yaml', '.yml']:
            self._load_yaml_config(config_file)
        elif file_ext in ['.ini', '.cfg', '.conf']:
            self._load_ini_config(config_file)
        else:
            # 默认尝试INI格式
            self._load_ini_config(config_file)
    
    def _load_json_config(self, config_file: str):
        """加载JSON格式配置文件"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        if 'ROSBridge' in config_data:
            self._load_rosbridge_from_dict(config_data['ROSBridge'])
        if 'ZMQ' in config_data:
            self._load_zmq_from_dict(config_data['ZMQ'])
        if 'Network' in config_data:
            self._load_network_from_dict(config_data['Network'])
    
    def _load_yaml_config(self, config_file: str):
        """加载YAML格式配置文件"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if config_data:
            if 'ROSBridge' in config_data:
                self._load_rosbridge_from_dict(config_data['ROSBridge'])
            if 'ZMQ' in config_data:
                self._load_zmq_from_dict(config_data['ZMQ'])
            if 'Network' in config_data:
                self._load_network_from_dict(config_data['Network'])
    
    def _load_ini_config(self, config_file: str):
        """加载INI格式配置文件"""
        config = ConfigParser()
        config.read(config_file, encoding='utf-8')

        # 读取 ROSBridge 组
        if config.has_section("ROSBridge"):
            self._load_rosbridge_config(config)
        
        # 读取 ZMQ 组
        if config.has_section("ZMQ"):
            self._load_zmq_config(config)
        
        # 读取 Network 组
        if config.has_section("Network"):
            self._load_network_config(config)
    
    def _load_rosbridge_from_dict(self, config_dict: Dict[str, Any]):
        """从字典加载ROSBridge配置"""
        for key, value in config_dict.items():
            if hasattr(self.rosbridge_params, key):
                setattr(self.rosbridge_params, key, value)
    
    def _load_zmq_from_dict(self, config_dict: Dict[str, Any]):
        """从字典加载ZMQ配置"""
        for key, value in config_dict.items():
            if hasattr(self.zmq_params, key):
                setattr(self.zmq_params, key, value)
    
    def _load_network_from_dict(self, config_dict: Dict[str, Any]):
        """从字典加载Network配置"""
        for key, value in config_dict.items():
            if hasattr(self.network_params, key):
                setattr(self.network_params, key, value)

    def _load_rosbridge_config(self, config: ConfigParser):
        """加载ROSBridge配置"""
        section = "ROSBridge"
        self.rosbridge_params.host = config.get(section, "host", fallback=self.rosbridge_params.host)
        self.rosbridge_params.port = config.getint(section, "port", fallback=self.rosbridge_params.port)
        self.rosbridge_params.connection_timeout = config.getfloat(section, "connection_timeout", fallback=self.rosbridge_params.connection_timeout)
        self.rosbridge_params.retry_interval = config.getfloat(section, "retry_interval", fallback=self.rosbridge_params.retry_interval)
        self.rosbridge_params.max_retries = config.getint(section, "max_retries", fallback=self.rosbridge_params.max_retries)
        self.rosbridge_params.auto_reconnect = config.getboolean(section, "auto_reconnect", fallback=self.rosbridge_params.auto_reconnect)
        self.rosbridge_params.reconnect_interval = config.getfloat(section, "reconnect_interval", fallback=self.rosbridge_params.reconnect_interval)
        self.rosbridge_params.max_reconnect_attempts = config.getint(section, "max_reconnect_attempts", fallback=self.rosbridge_params.max_reconnect_attempts)
        self.rosbridge_params.verbose = config.getboolean(section, "verbose", fallback=self.rosbridge_params.verbose)
        self.rosbridge_params.show_connection_status = config.getboolean(section, "show_connection_status", fallback=self.rosbridge_params.show_connection_status)
        self.rosbridge_params.show_message_content = config.getboolean(section, "show_message_content", fallback=self.rosbridge_params.show_message_content)
        self.rosbridge_params.max_message_length = config.getint(section, "max_message_length", fallback=self.rosbridge_params.max_message_length)
        self.rosbridge_params.main_loop_sleep = config.getfloat(section, "main_loop_sleep", fallback=self.rosbridge_params.main_loop_sleep)
        self.rosbridge_params.publish_sleep = config.getfloat(section, "publish_sleep", fallback=self.rosbridge_params.publish_sleep)

    def _load_zmq_config(self, config: ConfigParser):
        """加载ZMQ配置"""
        section = "ZMQ"
        self.zmq_params.host = config.get(section, "host", fallback=self.zmq_params.host)
        self.zmq_params.port = config.getint(section, "port", fallback=self.zmq_params.port)
        self.zmq_params.connection_timeout = config.getfloat(section, "connection_timeout", fallback=self.zmq_params.connection_timeout)
        self.zmq_params.retry_interval = config.getfloat(section, "retry_interval", fallback=self.zmq_params.retry_interval)
        self.zmq_params.max_retries = config.getint(section, "max_retries", fallback=self.zmq_params.max_retries)
        self.zmq_params.linger_time = config.getint(section, "linger_time", fallback=self.zmq_params.linger_time)
        self.zmq_params.high_water_mark = config.getint(section, "high_water_mark", fallback=self.zmq_params.high_water_mark)
        self.zmq_params.receive_timeout = config.getint(section, "receive_timeout", fallback=self.zmq_params.receive_timeout)
        self.zmq_params.send_timeout = config.getint(section, "send_timeout", fallback=self.zmq_params.send_timeout)
        self.zmq_params.auto_reconnect = config.getboolean(section, "auto_reconnect", fallback=self.zmq_params.auto_reconnect)
        self.zmq_params.reconnect_interval = config.getfloat(section, "reconnect_interval", fallback=self.zmq_params.reconnect_interval)
        self.zmq_params.max_reconnect_attempts = config.getint(section, "max_reconnect_attempts", fallback=self.zmq_params.max_reconnect_attempts)
        self.zmq_params.verbose = config.getboolean(section, "verbose", fallback=self.zmq_params.verbose)
        self.zmq_params.show_connection_status = config.getboolean(section, "show_connection_status", fallback=self.zmq_params.show_connection_status)
        self.zmq_params.show_message_content = config.getboolean(section, "show_message_content", fallback=self.zmq_params.show_message_content)
        self.zmq_params.max_message_length = config.getint(section, "max_message_length", fallback=self.zmq_params.max_message_length)
        self.zmq_params.main_loop_sleep = config.getfloat(section, "main_loop_sleep", fallback=self.zmq_params.main_loop_sleep)
        self.zmq_params.message_processing_sleep = config.getfloat(section, "message_processing_sleep", fallback=self.zmq_params.message_processing_sleep)
        self.zmq_params.message_format = config.get(section, "message_format", fallback=self.zmq_params.message_format)
        self.zmq_params.encoding = config.get(section, "encoding", fallback=self.zmq_params.encoding)
        self.zmq_params.compression_enabled = config.getboolean(section, "compression_enabled", fallback=self.zmq_params.compression_enabled)
        self.zmq_params.compression_level = config.getint(section, "compression_level", fallback=self.zmq_params.compression_level)

    def _load_network_config(self, config: ConfigParser):
        """加载网络配置"""
        section = "Network"
        self.network_params.connectivity_check_enabled = config.getboolean(section, "connectivity_check_enabled", fallback=self.network_params.connectivity_check_enabled)
        self.network_params.connectivity_timeout = config.getfloat(section, "connectivity_timeout", fallback=self.network_params.connectivity_timeout)

    def save_config(self, section_name: str = None):
        """
        将当前参数保存回配置文件。
        支持JSON、YAML和INI格式的配置文件。
        :param section_name: 指定要保存的配置节，如果为 None 则保存所有配置。
        """
        if not self.config_file:
            raise ValueError("未设置配置文件路径，无法保存配置。")

        file_ext = Path(self.config_file).suffix.lower()
        
        if file_ext in ['.json']:
            self._save_json_config(section_name)
        elif file_ext in ['.yaml', '.yml']:
            self._save_yaml_config(section_name)
        elif file_ext in ['.ini', '.cfg', '.conf']:
            self._save_ini_config(section_name)
        else:
            # 默认保存为INI格式
            self._save_ini_config(section_name)
    
    def _save_json_config(self, section_name: str = None):
        """保存为JSON格式配置文件"""
        config_data = {}
        
        # 先读取现有配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                config_data = {}
        
        # 更新配置
        if section_name is None or section_name == "ROSBridge":
            config_data['ROSBridge'] = self.get_rosbridge_config()
        if section_name is None or section_name == "ZMQ":
            config_data['ZMQ'] = self.get_zmq_config()
        if section_name is None or section_name == "Network":
            config_data['Network'] = self.get_network_config()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def _save_yaml_config(self, section_name: str = None):
        """保存为YAML格式配置文件"""
        config_data = {}
        
        # 先读取现有配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, FileNotFoundError):
                config_data = {}
        
        # 更新配置
        if section_name is None or section_name == "ROSBridge":
            config_data['ROSBridge'] = self.get_rosbridge_config()
        if section_name is None or section_name == "ZMQ":
            config_data['ZMQ'] = self.get_zmq_config()
        if section_name is None or section_name == "Network":
            config_data['Network'] = self.get_network_config()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    def _save_ini_config(self, section_name: str = None):
        """保存为INI格式配置文件"""
        config = ConfigParser()

        # 先读取现有的配置文件
        if os.path.exists(self.config_file):
            config.read(self.config_file, encoding='utf-8')

        # 保存ROSBridge配置
        if section_name is None or section_name == "ROSBridge":
            self._save_rosbridge_config(config)
        
        # 保存ZMQ配置
        if section_name is None or section_name == "ZMQ":
            self._save_zmq_config(config)
        
        # 保存Network配置
        if section_name is None or section_name == "Network":
            self._save_network_config(config)

        with open(self.config_file, "w", encoding='utf-8') as configfile:
            config.write(configfile)

    def _save_rosbridge_config(self, config: ConfigParser):
        """保存ROSBridge配置"""
        section = "ROSBridge"
        if not config.has_section(section):
            config.add_section(section)
        
        config.set(section, "host", str(self.rosbridge_params.host))
        config.set(section, "port", str(self.rosbridge_params.port))
        config.set(section, "connection_timeout", str(self.rosbridge_params.connection_timeout))
        config.set(section, "retry_interval", str(self.rosbridge_params.retry_interval))
        config.set(section, "max_retries", str(self.rosbridge_params.max_retries))
        config.set(section, "auto_reconnect", str(self.rosbridge_params.auto_reconnect))
        config.set(section, "reconnect_interval", str(self.rosbridge_params.reconnect_interval))
        config.set(section, "max_reconnect_attempts", str(self.rosbridge_params.max_reconnect_attempts))
        config.set(section, "verbose", str(self.rosbridge_params.verbose))
        config.set(section, "show_connection_status", str(self.rosbridge_params.show_connection_status))
        config.set(section, "show_message_content", str(self.rosbridge_params.show_message_content))
        config.set(section, "max_message_length", str(self.rosbridge_params.max_message_length))
        config.set(section, "main_loop_sleep", str(self.rosbridge_params.main_loop_sleep))
        config.set(section, "publish_sleep", str(self.rosbridge_params.publish_sleep))

    def _save_zmq_config(self, config: ConfigParser):
        """保存ZMQ配置"""
        section = "ZMQ"
        if not config.has_section(section):
            config.add_section(section)
        
        config.set(section, "host", str(self.zmq_params.host))
        config.set(section, "port", str(self.zmq_params.port))
        config.set(section, "connection_timeout", str(self.zmq_params.connection_timeout))
        config.set(section, "retry_interval", str(self.zmq_params.retry_interval))
        config.set(section, "max_retries", str(self.zmq_params.max_retries))
        config.set(section, "linger_time", str(self.zmq_params.linger_time))
        config.set(section, "high_water_mark", str(self.zmq_params.high_water_mark))
        config.set(section, "receive_timeout", str(self.zmq_params.receive_timeout))
        config.set(section, "send_timeout", str(self.zmq_params.send_timeout))
        config.set(section, "auto_reconnect", str(self.zmq_params.auto_reconnect))
        config.set(section, "reconnect_interval", str(self.zmq_params.reconnect_interval))
        config.set(section, "max_reconnect_attempts", str(self.zmq_params.max_reconnect_attempts))
        config.set(section, "verbose", str(self.zmq_params.verbose))
        config.set(section, "show_connection_status", str(self.zmq_params.show_connection_status))
        config.set(section, "show_message_content", str(self.zmq_params.show_message_content))
        config.set(section, "max_message_length", str(self.zmq_params.max_message_length))
        config.set(section, "main_loop_sleep", str(self.zmq_params.main_loop_sleep))
        config.set(section, "message_processing_sleep", str(self.zmq_params.message_processing_sleep))
        config.set(section, "message_format", str(self.zmq_params.message_format))
        config.set(section, "encoding", str(self.zmq_params.encoding))
        config.set(section, "compression_enabled", str(self.zmq_params.compression_enabled))
        config.set(section, "compression_level", str(self.zmq_params.compression_level))

    def _save_network_config(self, config: ConfigParser):
        """保存网络配置"""
        section = "Network"
        if not config.has_section(section):
            config.add_section(section)
        
        config.set(section, "connectivity_check_enabled", str(self.network_params.connectivity_check_enabled))
        config.set(section, "connectivity_timeout", str(self.network_params.connectivity_timeout))

    def get_param(self, param_type: str, key: str, default=None):
        """
        获取参数值。
        :param param_type: 参数类型 ('rosbridge', 'zmq', 'network')
        :param key: 参数名称
        :param default: 默认值
        :return: 参数值
        """
        with self._lock:
            if param_type == 'rosbridge':
                params = self.rosbridge_params
            elif param_type == 'zmq':
                params = self.zmq_params
            elif param_type == 'network':
                params = self.network_params
            else:
                raise ValueError(f"不支持的参数类型: {param_type}")
            
            if key not in params.model_fields:
                if default is not None:
                    return default
                raise KeyError(f"参数 {key} 不存在于 {param_type} 配置中。")
            return getattr(params, key)

    def set_param(self, param_type: str, key: str, value):
        """
        更新参数值。
        :param param_type: 参数类型 ('rosbridge', 'zmq', 'network')
        :param key: 参数名称
        :param value: 新值
        """
        with self._lock:
            if param_type == 'rosbridge':
                params = self.rosbridge_params
            elif param_type == 'zmq':
                params = self.zmq_params
            elif param_type == 'network':
                params = self.network_params
            else:
                raise ValueError(f"不支持的参数类型: {param_type}")
            
            if key in params.model_fields:
                setattr(params, key, value)
            else:
                raise KeyError(f"参数 {key} 不存在于 {param_type} 配置中，无法设置。")

    def get_rosbridge_config(self) -> Dict[str, Any]:
        """
        获取ROSBridge配置信息。
        :return: ROSBridge配置字典
        """
        return self.rosbridge_params.model_dump()

    def get_zmq_config(self) -> Dict[str, Any]:
        """
        获取ZMQ配置信息。
        :return: ZMQ配置字典
        """
        return self.zmq_params.model_dump()

    def get_network_config(self) -> Dict[str, Any]:
        """
        获取网络配置信息。
        :return: 网络配置字典
        """
        return self.network_params.model_dump()

    def update_rosbridge_config(self, config_dict: Dict[str, Any]):
        """
        批量更新ROSBridge配置。
        :param config_dict: 配置字典
        """
        with self._lock:
            for key, value in config_dict.items():
                if key in self.rosbridge_params.model_fields:
                    setattr(self.rosbridge_params, key, value)

    def update_zmq_config(self, config_dict: Dict[str, Any]):
        """
        批量更新ZMQ配置。
        :param config_dict: 配置字典
        """
        with self._lock:
            for key, value in config_dict.items():
                if key in self.zmq_params.model_fields:
                    setattr(self.zmq_params, key, value)

    def update_network_config(self, config_dict: Dict[str, Any]):
        """
        批量更新网络配置。
        :param config_dict: 配置字典
        """
        with self._lock:
            for key, value in config_dict.items():
                if key in self.network_params.model_fields:
                    setattr(self.network_params, key, value)

    def reset_to_defaults(self, param_type: str = None):
        """
        重置参数为默认值。
        :param param_type: 参数类型，如果为None则重置所有参数
        """
        with self._lock:
            if param_type is None or param_type == 'rosbridge':
                self.rosbridge_params = self.ROSBridgeParameters()
            if param_type is None or param_type == 'zmq':
                self.zmq_params = self.ZMQParameters()
            if param_type is None or param_type == 'network':
                self.network_params = self.NetworkParameters()

    def export_config_to_dict(self) -> Dict[str, Any]:
        """
        导出所有配置为字典格式。
        :return: 包含所有配置的字典
        """
        return {
            'rosbridge': self.get_rosbridge_config(),
            'zmq': self.get_zmq_config(),
            'network': self.get_network_config()
        }

    def import_config_from_dict(self, config_dict: Dict[str, Any]):
        """
        从字典导入配置。
        :param config_dict: 配置字典
        """
        if 'rosbridge' in config_dict:
            self.update_rosbridge_config(config_dict['rosbridge'])
        if 'zmq' in config_dict:
            self.update_zmq_config(config_dict['zmq'])
        if 'network' in config_dict:
            self.update_network_config(config_dict['network'])