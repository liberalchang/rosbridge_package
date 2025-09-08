#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZMQ客户端模块
基于PyZMQ的消息队列客户端，支持配置化管理
提供REQ/REP、PUB/SUB、PUSH/PULL等多种通信模式
"""

import zmq
import time
import json
import threading
import socket
from typing import Dict, Any, Optional, Callable, List, Union
from pathlib import Path

from .logger import Logger, LogLevel
from .param_manager import ParamManager

class ZMQClient:
    """ZMQ消息队列客户端"""
    
    def __init__(self, config_path: Optional[str] = None, 
                 param_manager: Optional[ParamManager] = None,
                 logger: Optional[Logger] = None):
        """
        初始化ZMQ客户端
        
        Args:
            config_path (Optional[str]): 配置文件路径
            param_manager (Optional[ParamManager]): 参数管理器实例
            logger (Optional[Logger]): 日志器实例
        """
        # 初始化日志器
        self.logger = logger or Logger(name="ZMQ", min_level=LogLevel.INFO)
        
        # 初始化参数管理器
        self.param_manager = param_manager or ParamManager()
        
        # 加载配置文件（如果提供）
        if config_path:
            self.param_manager.load_config(config_path)
        
        # 应用配置
        self._apply_config()
        
        # ZMQ上下文和套接字
        self.context = zmq.Context()
        self.sockets = {}
        self.running = False
        self.threads = []
        
        # 连接状态
        self.connected_endpoints = set()
        self.reconnect_count = 0
    
    def _apply_config(self):
        """应用配置参数"""
        # 获取ZMQ配置
        zmq_config = self.param_manager.get_zmq_config()
        network_config = self.param_manager.get_network_config()
        
        # ZMQ连接配置
        self.default_host = zmq_config['host']
        self.default_port = zmq_config['port']
        self.connection_timeout = zmq_config['connection_timeout']
        self.retry_interval = zmq_config['retry_interval']
        self.max_retries = zmq_config['max_retries']
        
        # 套接字配置
        self.socket_options = {}  # 可以根据需要扩展
        self.linger_time = zmq_config['linger_time']
        self.high_water_mark = zmq_config['high_water_mark']
        self.receive_timeout = zmq_config['receive_timeout']
        self.send_timeout = zmq_config['send_timeout']
        
        # 网络检查配置
        self.connectivity_check_enabled = network_config['connectivity_check_enabled']
        self.connectivity_timeout = network_config['connectivity_timeout']
        
        # 日志配置
        self.verbose = zmq_config['verbose']
        self.show_connection_status = zmq_config['show_connection_status']
        self.show_message_content = zmq_config['show_message_content']
        self.max_message_length = zmq_config['max_message_length']
        
        # 配置日志器
        self.logger.configure({
            'max_message_length': self.max_message_length,
            'show_timestamp': True,
            'timestamp_format': '%Y-%m-%d %H:%M:%S',
            'min_level': LogLevel.DEBUG if self.verbose else LogLevel.INFO
        })
        
        # 性能配置
        self.main_loop_sleep = zmq_config['main_loop_sleep']
        self.message_processing_sleep = zmq_config['message_processing_sleep']
        
        # 消息配置
        self.message_format = zmq_config['message_format']
        self.encoding = zmq_config['encoding']
        self.compression_enabled = zmq_config['compression_enabled']
        self.compression_level = zmq_config['compression_level']
        
        # 错误处理配置
        self.auto_reconnect = zmq_config['auto_reconnect']
        self.reconnect_interval = zmq_config['reconnect_interval']
        self.max_reconnect_attempts = zmq_config['max_reconnect_attempts']
        self.continue_on_error = True  # 默认继续处理错误
        
        # 通信模式配置（可以根据需要扩展）
        self.patterns_config = {}
    
    def set_host_port(self, host: str, port: int):
        """设置连接地址和端口"""
        self.default_host = host
        self.default_port = port
        # 同时更新参数管理器
        self.param_manager.set_param('zmq', 'host', host)
        self.param_manager.set_param('zmq', 'port', port)
        self.logger.debug(f"连接地址已更新: {host}:{port}")
    
    def update_config(self, param_type: str, key: str, value: Any):
        """动态更新单个配置项"""
        self.param_manager.set_param(param_type, key, value)
        self._apply_config()  # 重新应用配置
        self.logger.debug(f"配置项 {param_type}.{key} 已更新为: {value}")
    
    def batch_update_config(self, param_type: str, updates: Dict[str, Any]):
        """批量更新配置项"""
        if param_type == 'zmq':
            self.param_manager.update_zmq_config(updates)
        elif param_type == 'network':
            self.param_manager.update_network_config(updates)
        else:
            raise ValueError(f"不支持的参数类型: {param_type}")
        self._apply_config()  # 重新应用配置
        self.logger.debug(f"批量更新了 {len(updates)} 个 {param_type} 配置项")
    
    def add_subscribe_topic(self, topic: str):
        """动态添加订阅话题"""
        # 这里可以扩展为使用参数管理器存储话题配置
        if not hasattr(self, 'subscribe_topics'):
            self.subscribe_topics = []
        if topic not in self.subscribe_topics:
            self.subscribe_topics.append(topic)
            self.logger.debug(f"已添加订阅话题: {topic}")
    
    def add_publish_topic(self, topic_key: str, topic_name: str, 
                         content: str = 'test', frequency: float = 1.0):
        """动态添加发布话题"""
        # 这里可以扩展为使用参数管理器存储话题配置
        if not hasattr(self, 'publish_topics'):
            self.publish_topics = {}
        topic_config = {
            'name': topic_name,
            'content': content,
            'frequency': frequency
        }
        self.publish_topics[topic_key] = topic_config
        self.logger.debug(f"已添加发布话题: {topic_key} -> {topic_name}")
    
    def remove_subscribe_topic(self, topic: str):
        """移除订阅话题"""
        if hasattr(self, 'subscribe_topics') and topic in self.subscribe_topics:
            self.subscribe_topics.remove(topic)
            self.logger.debug(f"已移除订阅话题: {topic}")
    
    def remove_publish_topic(self, topic_key: str):
        """移除发布话题"""
        if hasattr(self, 'publish_topics') and topic_key in self.publish_topics:
            del self.publish_topics[topic_key]
            self.logger.debug(f"已移除发布话题: {topic_key}")
    
    def enable_pattern(self, pattern_name: str, endpoint: str = None, topics: List[str] = None):
        """启用通信模式"""
        if pattern_name in self.patterns_config:
            self.patterns_config[pattern_name]['enabled'] = True
            if endpoint:
                self.patterns_config[pattern_name]['endpoint'] = endpoint
            if topics and 'topics' in self.patterns_config[pattern_name]:
                self.patterns_config[pattern_name]['topics'] = topics
            self.logger.debug(f"已启用通信模式: {pattern_name}")
    
    def disable_pattern(self, pattern_name: str):
        """禁用通信模式"""
        if pattern_name in self.patterns_config:
            self.patterns_config[pattern_name]['enabled'] = False
            self.logger.debug(f"已禁用通信模式: {pattern_name}")
    
    def get_config_value(self, param_type: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.param_manager.get_param(param_type, key, default)
    
    def use_local_config(self):
        """使用本地配置"""
        # 使用localhost作为本地配置
        self.set_host_port('localhost', self.default_port)
    
    def connect_to_remote_host(self, host: str, port: int, 
                              socket_type: str = 'req', 
                              socket_name: str = None,
                              topics: List[str] = None,
                              auto_start_loop: bool = True) -> bool:
        """连接到远程主机
        
        Args:
            host (str): 远程主机地址
            port (int): 远程主机端口
            socket_type (str): 套接字类型 ('req', 'sub', 'push')
            socket_name (str): 套接字名称，默认为 socket_type + '_remote'
            topics (List[str]): 订阅话题列表（仅用于SUB类型）
            auto_start_loop (bool): 是否自动启动消息循环（仅用于SUB类型）
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 设置连接参数
            self.set_host_port(host, port)
            
            # 检查网络连通性
            if not self.check_network_connectivity(host, port):
                self.logger.warning(f"无法连接到远程主机 {host}:{port}，但继续尝试创建套接字")
            
            # 设置默认套接字名称
            if socket_name is None:
                socket_name = f"{socket_type}_remote"
            
            endpoint = f"tcp://{host}:{port}"
            
            # 根据套接字类型创建连接
            if socket_type.lower() == 'req':
                success = self.create_req_client(endpoint, socket_name)
                if success:
                    self.logger.debug(f"成功连接到远程REQ服务器: {host}:{port}")
                return success
                
            elif socket_type.lower() == 'sub':
                success = self.create_sub_client(endpoint, socket_name, topics)
                if success:
                    self.logger.debug(f"成功连接到远程PUB服务器: {host}:{port}")
                    # 自动启动订阅循环
                    if auto_start_loop:
                        self.start_subscriber_loop(socket_name, self.default_callback)
                return success
                
            elif socket_type.lower() == 'push':
                success = self.create_push_client(endpoint, socket_name)
                if success:
                    self.logger.debug(f"成功连接到远程PULL服务器: {host}:{port}")
                return success
                
            else:
                self.logger.error(f"不支持的套接字类型: {socket_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"连接远程主机失败 {host}:{port}: {e}")
            return False
    
    def connect_to_multiple_hosts(self, hosts_config: List[Dict[str, Any]]) -> Dict[str, bool]:
        """连接到多个远程主机
        
        Args:
            hosts_config (List[Dict]): 主机配置列表，每个配置包含:
                - host: 主机地址
                - port: 端口
                - socket_type: 套接字类型
                - socket_name: 套接字名称（可选）
                - topics: 订阅话题（可选，仅用于SUB）
                - auto_start_loop: 是否自动启动循环（可选）
                
        Returns:
            Dict[str, bool]: 每个主机的连接结果
        """
        results = {}
        
        for config in hosts_config:
            host = config.get('host')
            port = config.get('port')
            socket_type = config.get('socket_type', 'req')
            socket_name = config.get('socket_name')
            topics = config.get('topics')
            auto_start_loop = config.get('auto_start_loop', True)
            
            if not host or not port:
                self.logger.error(f"主机配置缺少必要参数: {config}")
                results[f"{host}:{port}"] = False
                continue
            
            success = self.connect_to_remote_host(
                host=host,
                port=port,
                socket_type=socket_type,
                socket_name=socket_name,
                topics=topics,
                auto_start_loop=auto_start_loop
            )
            
            results[f"{host}:{port}"] = success
        
        return results
    
    def disconnect_from_host(self, socket_name: str) -> bool:
        """断开与指定主机的连接
        
        Args:
            socket_name (str): 要断开的套接字名称
            
        Returns:
            bool: 断开是否成功
        """
        return self.close_socket(socket_name)
    
    def check_network_connectivity(self, host: str = None, port: int = None) -> bool:
        """检查网络连通性"""
        if not self.connectivity_check_enabled:
            return True
        
        host = host or self.default_host
        port = port or self.default_port
        
        try:
            self.logger.debug(f"检查网络连通性: {host}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connectivity_timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.logger.debug(f"网络连接正常: {host}:{port}")
                return True
            else:
                self.logger.warning(f"无法连接到 {host}:{port} (错误代码: {result})")
                return False
        except Exception as e:
            self.logger.error(f"网络连接检查失败: {e}")
            return False
    
    def _configure_socket(self, socket_obj: zmq.Socket):
        """配置套接字选项"""
        try:
            # 设置基本选项
            socket_obj.setsockopt(zmq.LINGER, self.linger_time)
            socket_obj.setsockopt(zmq.SNDHWM, self.high_water_mark)
            socket_obj.setsockopt(zmq.RCVHWM, self.high_water_mark)
            
            if self.receive_timeout > 0:
                socket_obj.setsockopt(zmq.RCVTIMEO, self.receive_timeout)
            if self.send_timeout > 0:
                socket_obj.setsockopt(zmq.SNDTIMEO, self.send_timeout)
            
            # 应用自定义选项
            for option_name, option_value in self.socket_options.items():
                if hasattr(zmq, option_name):
                    option_const = getattr(zmq, option_name)
                    socket_obj.setsockopt(option_const, option_value)
                    self.logger.debug(f"设置套接字选项: {option_name} = {option_value}")
                else:
                    self.logger.warning(f"未知的套接字选项: {option_name}")
        
        except Exception as e:
            self.logger.error(f"配置套接字选项失败: {e}")
    
    def create_socket(self, socket_type: int, socket_name: str = None) -> zmq.Socket:
        """创建套接字"""
        try:
            socket_obj = self.context.socket(socket_type)
            self._configure_socket(socket_obj)
            
            if socket_name:
                self.sockets[socket_name] = socket_obj
                self.logger.debug(f"创建套接字: {socket_name} (类型: {socket_type})")
            
            return socket_obj
        
        except Exception as e:
            self.logger.error(f"创建套接字失败: {e}")
            return None
    
    def connect_socket(self, socket_obj: zmq.Socket, endpoint: str) -> bool:
        """连接套接字到端点"""
        try:
            socket_obj.connect(endpoint)
            self.connected_endpoints.add(endpoint)
            
            if self.show_connection_status:
                self.logger.debug(f"套接字已连接到: {endpoint}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"连接套接字失败 {endpoint}: {e}")
            return False
    
    def bind_socket(self, socket_obj: zmq.Socket, endpoint: str) -> bool:
        """绑定套接字到端点"""
        try:
            socket_obj.bind(endpoint)
            
            if self.show_connection_status:
                self.logger.debug(f"套接字已绑定到: {endpoint}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"绑定套接字失败 {endpoint}: {e}")
            return False
    
    def close_socket(self, socket_name: str) -> bool:
        """关闭套接字"""
        try:
            if socket_name in self.sockets:
                self.sockets[socket_name].close()
                del self.sockets[socket_name]
                self.logger.debug(f"套接字已关闭: {socket_name}")
                return True
            else:
                self.logger.warning(f"套接字不存在: {socket_name}")
                return False
        
        except Exception as e:
            self.logger.error(f"关闭套接字失败 {socket_name}: {e}")
            return False
    
    def _serialize_message(self, data: Any) -> bytes:
        """序列化消息"""
        try:
            if self.message_format == 'json':
                json_str = json.dumps(data, ensure_ascii=False)
                return json_str.encode(self.encoding)
            elif self.message_format == 'string':
                if isinstance(data, str):
                    return data.encode(self.encoding)
                else:
                    return str(data).encode(self.encoding)
            elif self.message_format == 'bytes':
                if isinstance(data, bytes):
                    return data
                else:
                    return str(data).encode(self.encoding)
            else:
                # 默认使用JSON
                json_str = json.dumps(data, ensure_ascii=False)
                return json_str.encode(self.encoding)
        
        except Exception as e:
            self.logger.error(f"消息序列化失败: {e}")
            return b''
    
    def _deserialize_message(self, data: bytes) -> Any:
        """反序列化消息"""
        try:
            if self.message_format == 'json':
                json_str = data.decode(self.encoding)
                return json.loads(json_str)
            elif self.message_format == 'string':
                return data.decode(self.encoding)
            elif self.message_format == 'bytes':
                return data
            else:
                # 默认尝试JSON，失败则返回字符串
                try:
                    json_str = data.decode(self.encoding)
                    return json.loads(json_str)
                except:
                    return data.decode(self.encoding)
        
        except Exception as e:
            self.logger.error(f"消息反序列化失败: {e}")
            return None
    
    def send_message(self, socket_name: str, data: Any, flags: int = 0) -> bool:
        """发送消息"""
        try:
            if socket_name not in self.sockets:
                self.logger.error(f"套接字不存在: {socket_name}")
                return False
            
            message_bytes = self._serialize_message(data)
            if not message_bytes:
                return False
            
            self.sockets[socket_name].send(message_bytes, flags)
            
            if self.show_message_content:
                msg_str = str(data)
                if len(msg_str) > self.max_message_length:
                    msg_str = msg_str[:self.max_message_length] + "..."
                self.logger.debug(f"[{socket_name}] 发送消息: {msg_str}")
            else:
                self.logger.debug(f"[{socket_name}] 发送消息")
            
            return True
        
        except Exception as e:
            self.logger.error(f"发送消息失败 {socket_name}: {e}")
            return False
    
    def receive_message(self, socket_name: str, flags: int = 0) -> Any:
        """接收消息"""
        try:
            if socket_name not in self.sockets:
                self.logger.error(f"套接字不存在: {socket_name}")
                return None
            
            message_bytes = self.sockets[socket_name].recv(flags)
            data = self._deserialize_message(message_bytes)
            
            if self.show_message_content:
                msg_str = str(data)
                if len(msg_str) > self.max_message_length:
                    msg_str = msg_str[:self.max_message_length] + "..."
                self.logger.debug(f"[{socket_name}] 接收消息: {msg_str}")
            else:
                self.logger.debug(f"[{socket_name}] 接收消息")
            
            return data
        
        except zmq.Again:
            # 超时或非阻塞模式下无消息
            return None
        except Exception as e:
            self.logger.error(f"接收消息失败 {socket_name}: {e}")
            return None
    
    def send_multipart_message(self, socket_name: str, parts: List[Any], flags: int = 0) -> bool:
        """发送多部分消息"""
        try:
            if socket_name not in self.sockets:
                self.logger.error(f"套接字不存在: {socket_name}")
                return False
            
            message_parts = []
            for part in parts:
                if isinstance(part, bytes):
                    message_parts.append(part)
                else:
                    message_parts.append(self._serialize_message(part))
            
            self.sockets[socket_name].send_multipart(message_parts, flags)
            
            if self.show_message_content:
                parts_str = [str(part) for part in parts]
                msg_str = ' | '.join(parts_str)
                if len(msg_str) > self.max_message_length:
                    msg_str = msg_str[:self.max_message_length] + "..."
                self.logger.debug(f"[{socket_name}] 发送多部分消息: {msg_str}")
            else:
                self.logger.debug(f"[{socket_name}] 发送多部分消息 ({len(parts)}部分)")
            
            return True
        
        except Exception as e:
            self.logger.error(f"发送多部分消息失败 {socket_name}: {e}")
            return False
    
    def receive_multipart_message(self, socket_name: str, flags: int = 0) -> List[Any]:
        """接收多部分消息"""
        try:
            if socket_name not in self.sockets:
                self.logger.error(f"套接字不存在: {socket_name}")
                return []
            
            message_parts = self.sockets[socket_name].recv_multipart(flags)
            data_parts = []
            
            for part in message_parts:
                data = self._deserialize_message(part)
                data_parts.append(data)
            
            if self.show_message_content:
                parts_str = [str(part) for part in data_parts]
                msg_str = ' | '.join(parts_str)
                if len(msg_str) > self.max_message_length:
                    msg_str = msg_str[:self.max_message_length] + "..."
                self.logger.debug(f"[{socket_name}] 接收多部分消息: {msg_str}")
            else:
                self.logger.debug(f"[{socket_name}] 接收多部分消息 ({len(data_parts)}部分)")
            
            return data_parts
        
        except zmq.Again:
            # 超时或非阻塞模式下无消息
            return []
        except Exception as e:
            self.logger.error(f"接收多部分消息失败 {socket_name}: {e}")
            return []
    
    def create_req_client(self, endpoint: str = None, socket_name: str = "req_client") -> bool:
        """创建REQ客户端"""
        try:
            endpoint = endpoint or f"tcp://{self.default_host}:{self.default_port}"
            
            socket_obj = self.create_socket(zmq.REQ, socket_name)
            if not socket_obj:
                return False
            
            return self.connect_socket(socket_obj, endpoint)
        
        except Exception as e:
            self.logger.error(f"创建REQ客户端失败: {e}")
            return False
    
    def create_rep_server(self, endpoint: str = None, socket_name: str = "rep_server") -> bool:
        """创建REP服务器"""
        try:
            endpoint = endpoint or f"tcp://*:{self.default_port}"
            
            socket_obj = self.create_socket(zmq.REP, socket_name)
            if not socket_obj:
                return False
            
            return self.bind_socket(socket_obj, endpoint)
        
        except Exception as e:
            self.logger.error(f"创建REP服务器失败: {e}")
            return False
    
    def create_pub_server(self, endpoint: str = None, socket_name: str = "pub_server") -> bool:
        """创建PUB发布者"""
        try:
            endpoint = endpoint or f"tcp://*:{self.default_port}"
            
            socket_obj = self.create_socket(zmq.PUB, socket_name)
            if not socket_obj:
                return False
            
            return self.bind_socket(socket_obj, endpoint)
        
        except Exception as e:
            self.logger.error(f"创建PUB发布者失败: {e}")
            return False
    
    def create_sub_client(self, endpoint: str = None, socket_name: str = "sub_client", 
                         topics: List[str] = None) -> bool:
        """创建SUB订阅者"""
        try:
            endpoint = endpoint or f"tcp://{self.default_host}:{self.default_port}"
            
            socket_obj = self.create_socket(zmq.SUB, socket_name)
            if not socket_obj:
                return False
            
            # 设置订阅主题
            if topics:
                for topic in topics:
                    socket_obj.setsockopt_string(zmq.SUBSCRIBE, topic)
                    self.logger.debug(f"订阅主题: {topic}")
            else:
                # 订阅所有消息
                socket_obj.setsockopt(zmq.SUBSCRIBE, b"")
                self.logger.debug("订阅所有消息")
            
            return self.connect_socket(socket_obj, endpoint)
        
        except Exception as e:
            self.logger.error(f"创建SUB订阅者失败: {e}")
            return False
    
    def create_push_client(self, endpoint: str = None, socket_name: str = "push_client") -> bool:
        """创建PUSH客户端"""
        try:
            endpoint = endpoint or f"tcp://{self.default_host}:{self.default_port}"
            
            socket_obj = self.create_socket(zmq.PUSH, socket_name)
            if not socket_obj:
                return False
            
            return self.connect_socket(socket_obj, endpoint)
        
        except Exception as e:
            self.logger.error(f"创建PUSH客户端失败: {e}")
            return False
    
    def create_pull_server(self, endpoint: str = None, socket_name: str = "pull_server") -> bool:
        """创建PULL服务器"""
        try:
            endpoint = endpoint or f"tcp://*:{self.default_port}"
            
            socket_obj = self.create_socket(zmq.PULL, socket_name)
            if not socket_obj:
                return False
            
            return self.bind_socket(socket_obj, endpoint)
        
        except Exception as e:
            self.logger.error(f"创建PULL服务器失败: {e}")
            return False
    
    def request_reply(self, socket_name: str, request_data: Any, timeout: float = 10.0) -> Any:
        """发送请求并等待回复（REQ/REP模式）"""
        try:
            if not self.send_message(socket_name, request_data):
                return None
            
            # 设置接收超时
            if socket_name in self.sockets:
                original_timeout = self.sockets[socket_name].getsockopt(zmq.RCVTIMEO)
                self.sockets[socket_name].setsockopt(zmq.RCVTIMEO, int(timeout * 1000))
                
                try:
                    response = self.receive_message(socket_name)
                    return response
                finally:
                    # 恢复原始超时设置
                    self.sockets[socket_name].setsockopt(zmq.RCVTIMEO, original_timeout)
            
            return None
        
        except Exception as e:
            self.logger.error(f"请求-回复操作失败 {socket_name}: {e}")
            return None
    
    def start_subscriber_loop(self, socket_name: str, callback: Callable[[Any], None]):
        """启动订阅者循环（SUB模式）"""
        def subscriber_loop():
            self.logger.debug(f"启动订阅者循环: {socket_name}")
            
            while self.running:
                try:
                    # SUB套接字通常接收多部分消息：[话题, 消息内容, ...]
                    message_parts = self.receive_multipart_message(socket_name, zmq.NOBLOCK)
                    if message_parts:
                        if len(message_parts) >= 2:
                            # 第一部分是话题，第二部分是消息内容
                            topic = message_parts[0]
                            content = message_parts[1]
                            
                            # 如果有第三部分，可能包含额外信息，将其合并
                            if len(message_parts) >= 3:
                                # 对于3部分消息，通常第三部分是实际内容
                                actual_content = message_parts[2]
                                # 如果第三部分不为空，使用第三部分作为内容
                                if actual_content and (not isinstance(actual_content, bytes) or len(actual_content) > 0):
                                    content = actual_content
                            
                            # 只有当内容不为空时才调用回调函数
                            if content is not None and (not isinstance(content, bytes) or len(content) > 0):
                                callback(content)  # 传递消息内容给回调函数
                        elif len(message_parts) == 1:
                            # 只有一部分，可能是简单消息
                            if message_parts[0] is not None:
                                callback(message_parts[0])
                    else:
                        time.sleep(self.message_processing_sleep)
                
                except Exception as e:
                    if self.continue_on_error:
                        self.logger.error(f"订阅者循环错误 {socket_name}: {e}")
                        time.sleep(self.message_processing_sleep)
                    else:
                        self.logger.error(f"订阅者循环致命错误 {socket_name}: {e}")
                        break
            
            self.logger.debug(f"订阅者循环已停止: {socket_name}")
        
        thread = threading.Thread(target=subscriber_loop, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def start_server_loop(self, socket_name: str, handler: Callable[[Any], Any]):
        """启动服务器循环（REP/PULL模式）"""
        def server_loop():
            self.logger.debug(f"启动服务器循环: {socket_name}")
            
            while self.running:
                try:
                    request = self.receive_message(socket_name, zmq.NOBLOCK)
                    if request is not None:
                        response = handler(request)
                        
                        # 如果是REP模式，需要发送回复
                        if socket_name in self.sockets:
                            socket_type = self.sockets[socket_name].socket_type
                            if socket_type == zmq.REP and response is not None:
                                self.send_message(socket_name, response)
                    else:
                        time.sleep(self.message_processing_sleep)
                
                except Exception as e:
                    if self.continue_on_error:
                        self.logger.error(f"服务器循环错误 {socket_name}: {e}")
                        time.sleep(self.message_processing_sleep)
                    else:
                        self.logger.error(f"服务器循环致命错误 {socket_name}: {e}")
                        break
            
            self.logger.debug(f"服务器循环已停止: {socket_name}")
        
        thread = threading.Thread(target=server_loop, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def setup_configured_patterns(self):
        """根据配置设置通信模式"""
        for pattern_name, pattern_config in self.patterns_config.items():
            if not pattern_config.get('enabled', False):
                continue
            
            pattern_type = pattern_config.get('type', '')
            endpoint = pattern_config.get('endpoint', '')
            socket_name = pattern_config.get('socket_name', pattern_name)
            
            self.logger.debug(f"设置通信模式: {pattern_name} ({pattern_type})")
            
            if pattern_type == 'req_client':
                self.create_req_client(endpoint, socket_name)
            elif pattern_type == 'rep_server':
                self.create_rep_server(endpoint, socket_name)
                # 启动服务器循环
                handler_name = pattern_config.get('handler', 'default_handler')
                handler_func = getattr(self, handler_name, self.default_handler)
                self.start_server_loop(socket_name, handler_func)
            elif pattern_type == 'pub_server':
                self.create_pub_server(endpoint, socket_name)
            elif pattern_type == 'sub_client':
                topics = pattern_config.get('topics', [])
                self.create_sub_client(endpoint, socket_name, topics)
                # 启动订阅者循环
                callback_name = pattern_config.get('callback', 'default_callback')
                callback_func = getattr(self, callback_name, self.default_callback)
                self.start_subscriber_loop(socket_name, callback_func)
            elif pattern_type == 'push_client':
                self.create_push_client(endpoint, socket_name)
            elif pattern_type == 'pull_server':
                self.create_pull_server(endpoint, socket_name)
                # 启动服务器循环
                handler_name = pattern_config.get('handler', 'default_handler')
                handler_func = getattr(self, handler_name, self.default_handler)
                self.start_server_loop(socket_name, handler_func)
    
    def default_callback(self, message: Any):
        """默认回调函数"""
        self.logger.debug(f"收到消息: {message}")
    
    def default_handler(self, request: Any) -> Any:
        """默认处理函数"""
        self.logger.debug(f"处理请求: {request}")
        return {"status": "ok", "echo": request}
    
    def start(self) -> bool:
        """启动客户端"""
        try:
            self.logger.debug("启动ZMQ客户端...")
            
            # 检查网络连通性
            if not self.check_network_connectivity():
                self.logger.warning("网络连接检查失败，但继续启动")
            
            # 设置通信模式
            self.setup_configured_patterns()
            
            # 启动运行标志
            self.running = True
            
            self.logger.debug("ZMQ客户端已启动")
            return True
        
        except Exception as e:
            self.logger.error(f"启动ZMQ客户端失败: {e}")
            return False
    
    def stop(self):
        """停止客户端"""
        try:
            self.logger.debug("停止ZMQ客户端...")
            
            # 停止运行标志
            self.running = False
            
            # 等待线程结束
            for thread in self.threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)
            
            # 关闭所有套接字
            for socket_name in list(self.sockets.keys()):
                self.close_socket(socket_name)
            
            # 终止上下文
            self.context.term()
            
            self.logger.debug("ZMQ客户端已停止")
        
        except Exception as e:
            self.logger.error(f"停止ZMQ客户端失败: {e}")
    
    def run(self):
        """运行客户端（阻塞模式）"""
        if not self.start():
            return
        
        try:
            while True:
                time.sleep(self.main_loop_sleep)
        except KeyboardInterrupt:
            self.logger.debug("收到中断信号，正在停止客户端...")
        finally:
            self.stop()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()