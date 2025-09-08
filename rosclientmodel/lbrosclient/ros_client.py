#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROSBridge客户端模块
基于roslibpy的WebSocket客户端，支持配置化管理
提供ROS话题订阅、发布、服务调用等功能
"""

import roslibpy
import time
import threading
import socket
import inspect
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

from .logger import Logger, LogLevel
from .param_manager import ParamManager

class FrequencyController:
    """频率控制器，用于限制回调函数的执行频率"""
    
    def __init__(self, target_hz: float = 1.0):
        """
        初始化频率控制器
        
        Args:
            target_hz (float): 目标频率（Hz），默认1Hz
        """
        self.target_hz = target_hz
        self.interval = 1.0 / target_hz if target_hz > 0 else 0
        self.last_time = 0
    
    def should_process(self) -> bool:
        """
        检查是否应该处理当前消息
        
        Returns:
            bool: True表示应该处理，False表示跳过
        """
        if self.interval <= 0:  # 如果频率为0或负数，不限制
            return True
            
        current_time = time.time()
        if current_time - self.last_time >= self.interval:
            self.last_time = current_time
            return True
        return False
    
    def reset(self):
        """重置时间戳"""
        self.last_time = 0
    
    def set_frequency(self, target_hz: float):
        """
        设置新的目标频率
        
        Args:
            target_hz (float): 新的目标频率（Hz）
        """
        self.target_hz = target_hz
        self.interval = 1.0 / target_hz if target_hz > 0 else 0
        self.reset()

class ROSBridgeClient:
    """ROSBridge WebSocket客户端"""
    
    def __init__(self, config_path: Optional[str] = None, 
                 param_manager: Optional[ParamManager] = None,
                 logger: Optional[Logger] = None):
        """
        初始化ROSBridge客户端
        
        Args:
            config_path (Optional[str]): 配置文件路径
            param_manager (Optional[ParamManager]): 参数管理器实例
            logger (Optional[Logger]): 日志器实例
        """
        # 初始化日志器
        self.logger = logger or Logger(name="ROSBridge", min_level=LogLevel.INFO)
        
        # 初始化参数管理器
        self.param_manager = param_manager or ParamManager()
        
        # 加载配置文件（如果提供）
        if config_path:
            self.param_manager.load_config(config_path)
        
        # 应用配置
        self._apply_config()
        
        # 运行时变量
        self.client = None
        self.publishers = {}
        self.subscribers = {}
        self.services = {}
        self.running = False
        self.reconnect_count = 0
        self._publish_threads = []
    
    def _apply_config(self):
        """应用配置参数"""
        # 获取ROSBridge配置
        rosbridge_config = self.param_manager.get_rosbridge_config()
        network_config = self.param_manager.get_network_config()
        
        # ROSBridge连接配置
        self.host = rosbridge_config['host']
        self.port = rosbridge_config['port']
        self.protocol = rosbridge_config['protocol']
        self.connection_timeout = rosbridge_config['connection_timeout']
        self.retry_interval = rosbridge_config['retry_interval']
        self.max_retries = rosbridge_config['max_retries']
        
        # WebSocket配置
        self.ping_interval = rosbridge_config['ping_interval']
        self.ping_timeout = rosbridge_config['ping_timeout']
        self.close_timeout = rosbridge_config['close_timeout']
        self.max_size = rosbridge_config['max_size']
        
        # 网络检查配置
        self.connectivity_check_enabled = network_config['connectivity_check_enabled']
        self.connectivity_timeout = network_config['connectivity_timeout']
        
        # 日志配置
        self.verbose = rosbridge_config['verbose']
        self.show_connection_status = rosbridge_config['show_connection_status']
        self.show_message_content = rosbridge_config['show_message_content']
        self.max_message_length = rosbridge_config['max_message_length']
        
        # 配置日志器
        self.logger.configure({
            'max_message_length': self.max_message_length,
            'show_timestamp': True,
            'timestamp_format': '%Y-%m-%d %H:%M:%S',
            'min_level': LogLevel.DEBUG if self.verbose else LogLevel.INFO
        })
        
        # 性能配置
        self.main_loop_sleep = rosbridge_config['main_loop_sleep']
        self.message_processing_sleep = rosbridge_config['message_processing_sleep']
        
        # 消息配置
        self.message_format = rosbridge_config['message_format']
        self.encoding = rosbridge_config['encoding']
        self.compression_enabled = rosbridge_config['compression_enabled']
        self.compression_level = rosbridge_config['compression_level']
        
        # 话题配置（初始化为空，可以动态添加）
        self.subscribe_topics = {}
        self.publish_topics = {}
        
        # 错误处理配置
        self.auto_reconnect = rosbridge_config['auto_reconnect']
        self.reconnect_interval = rosbridge_config['reconnect_interval']
        self.max_reconnect_attempts = rosbridge_config['max_reconnect_attempts']
        self.continue_on_error = True  # 默认继续处理错误
        
        # ROS系统信息查询配置（可以根据需要扩展）
        self.ros_info_config = {}
    
    def set_host_port(self, host: str, port: int):
        """设置连接地址和端口"""
        self.host = host
        self.port = port
        # 同时更新参数管理器
        self.param_manager.set_param('rosbridge', 'host', host)
        self.param_manager.set_param('rosbridge', 'port', port)
        self.logger.debug(f"连接地址已更新: {host}:{port}")
    
    def update_config(self, param_type: str, key: str, value: Any):
        """动态更新单个配置项"""
        self.param_manager.set_param(param_type, key, value)
        self._apply_config()  # 重新应用配置
        self.logger.debug(f"配置项 {param_type}.{key} 已更新为: {value}")
    
    def batch_update_config(self, param_type: str, updates: Dict[str, Any]):
        """批量更新配置项"""
        if param_type == 'rosbridge':
            self.param_manager.update_rosbridge_config(updates)
        elif param_type == 'network':
            self.param_manager.update_network_config(updates)
        else:
            raise ValueError(f"不支持的参数类型: {param_type}")
        self._apply_config()  # 重新应用配置
        self.logger.debug(f"批量更新了 {len(updates)} 个 {param_type} 配置项")
    
    def add_subscribe_topic(self, topic: str, topic_type: str = 'std_msgs/String'):
        """动态添加订阅话题"""
        # 这里可以扩展为使用参数管理器存储话题配置
        if not hasattr(self, 'subscribe_topics'):
            self.subscribe_topics = {}
        self.subscribe_topics[topic] = {'type': topic_type}
        self.logger.debug(f"已添加订阅话题: {topic} ({topic_type})")
    
    def add_publish_topic(self, topic_key: str, topic_name: str, 
                         topic_type: str = 'std_msgs/String',
                         content: str = 'test', frequency: float = 1.0):
        """动态添加发布话题"""
        # 这里可以扩展为使用参数管理器存储话题配置
        if not hasattr(self, 'publish_topics'):
            self.publish_topics = {}
        topic_config = {
            'name': topic_name,
            'type': topic_type,
            'content': content,
            'frequency': frequency
        }
        self.publish_topics[topic_key] = topic_config
        self.logger.debug(f"已添加发布话题: {topic_key} -> {topic_name} ({topic_type})")
    
    def remove_subscribe_topic(self, topic: str):
        """移除订阅话题"""
        if hasattr(self, 'subscribe_topics') and topic in self.subscribe_topics:
            del self.subscribe_topics[topic]
            self.logger.debug(f"已移除订阅话题: {topic}")
    
    def remove_publish_topic(self, topic_key: str):
        """移除发布话题"""
        if hasattr(self, 'publish_topics') and topic_key in self.publish_topics:
            del self.publish_topics[topic_key]
            self.logger.debug(f"已移除发布话题: {topic_key}")
    
    def get_config_value(self, param_type: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.param_manager.get_param(param_type, key, default)
    
    def use_local_config(self):
        """使用本地配置"""
        self.set_host_port('localhost', 9090)
    
    def check_network_connectivity(self) -> bool:
        """检查网络连通性"""
        if not self.connectivity_check_enabled:
            return True
            
        try:
            self.logger.debug(f"检查网络连通性: {self.host}:{self.port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connectivity_timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                self.logger.debug(f"网络连接正常: {self.host}:{self.port}")
                return True
            else:
                self.logger.warning(f"无法连接到 {self.host}:{self.port} (错误代码: {result})")
                return False
        except Exception as e:
            self.logger.error(f"网络连接检查失败: {e}")
            return False
    
    def connect(self) -> bool:
        """连接到ROSBridge服务器"""
        try:
            self.logger.debug(f"正在尝试连接到ROSBridge服务器: {self.host}:{self.port}")
            self.client = roslibpy.Ros(host=self.host, port=self.port)
            
            # 添加连接事件监听
            if self.show_connection_status:
                self.client.on('connection', lambda: self.logger.debug("WebSocket连接已建立"))
                self.client.on('close', lambda proto: self.logger.debug("WebSocket连接已关闭"))
                self.client.on('error', lambda error: self.logger.error(f"WebSocket错误: {error}"))
            
            self.client.run()
            
            # 等待连接建立
            start_time = time.time()
            while not self.client.is_connected and (time.time() - start_time) < self.connection_timeout:
                time.sleep(self.retry_interval)
            
            if self.client.is_connected:
                self.logger.debug(f"成功连接到ROSBridge服务器: {self.host}:{self.port}")
                self.reconnect_count = 0  # 重置重连计数
                return True
            else:
                self.logger.error(f"连接超时: 无法在{self.connection_timeout}秒内连接到服务器")
                return False
                
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            # 取消所有订阅
            for topic_name in list(self.subscribers.keys()):
                self.unsubscribe_topic(topic_name)
            
            # 清理所有频率控制器
            if hasattr(self, '_freq_controllers'):
                self._freq_controllers.clear()
                self.logger.debug("已清理所有频率控制器")
            
            # 关闭所有发布者
            for publisher in self.publishers.values():
                publisher.unadvertise()
            self.publishers.clear()
            
            if self.client:
                self.client.terminate()
                self.client = None
                self.logger.debug("已断开ROSBridge连接")
            
        except Exception as e:
            self.logger.error(f"断开连接时发生错误: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.client is not None and self.client.is_connected
    
    def subscribe_topic(self, topic_name: str, message_type: str, 
                       callback: Callable, queue_size: int = 1, 
                       include_topic_name: bool = True,
                       target_hz: float = None) -> bool:
        """订阅话题
        
        Args:
            topic_name (str): 话题名称
            message_type (str): 消息类型
            callback (Callable): 回调函数
            queue_size (int): 队列大小
            include_topic_name (bool): 是否在回调函数中包含话题名称
                                     True: callback(message, topic_name)
                                     False: callback(message)
            target_hz (float): 目标频率（Hz），如果设置则会限制回调频率
                              例如：原话题是10Hz，设置target_hz=1.0，则只会以1Hz的频率处理消息
                              如果不设置或设置为None，则不限制频率
        """
        try:
            if not self.is_connected():
                self.logger.error("客户端未连接，无法订阅话题")
                return False
            
            subscriber = roslibpy.Topic(
                self.client,
                topic_name,
                message_type,
                queue_size=queue_size
            )
            
            # 创建频率控制器（如果需要）
            freq_controller = None
            if target_hz is not None and target_hz > 0:
                freq_controller = FrequencyController(target_hz)
                self.logger.debug(f"已为话题 {topic_name} 设置频率限制: {target_hz}Hz")
            
            # 根据参数决定是否包装回调函数
            if include_topic_name:
                # 检查回调函数的参数数量
                sig = inspect.signature(callback)
                param_count = len(sig.parameters)
                
                if param_count >= 2:
                    # 回调函数已经支持两个参数，直接传递话题名称
                    if freq_controller:
                        # 添加频率控制
                        original_callback = lambda msg: callback(msg, topic_name)
                        wrapped_callback = lambda msg: (
                            original_callback(msg) if freq_controller.should_process() else None
                        )
                    else:
                        wrapped_callback = lambda msg: callback(msg, topic_name)
                else:
                    # 回调函数只支持一个参数，使用原始回调
                    if freq_controller:
                        # 添加频率控制
                        wrapped_callback = lambda msg: (
                            callback(msg) if freq_controller.should_process() else None
                        )
                    else:
                        wrapped_callback = callback
                    self.logger.warning(f"回调函数只接受一个参数，无法传递话题名称: {topic_name}")
            else:
                # 不包含话题名称，直接使用原始回调
                if freq_controller:
                    # 添加频率控制
                    wrapped_callback = lambda msg: (
                        callback(msg) if freq_controller.should_process() else None
                    )
                else:
                    wrapped_callback = callback
            
            subscriber.subscribe(wrapped_callback)
            self.subscribers[topic_name] = subscriber
            
            # 保存频率控制器（如果有）
            if freq_controller:
                if not hasattr(self, '_freq_controllers'):
                    self._freq_controllers = {}
                self._freq_controllers[topic_name] = freq_controller
            
            self.logger.debug(f"已订阅话题: {topic_name} ({message_type})" + 
                             (f", 频率限制: {target_hz}Hz" if target_hz else ""))
            return True
            
        except Exception as e:
            self.logger.error(f"订阅话题失败 {topic_name}: {e}")
            return False
    
    def subscribe_topic_with_name(self, topic_name: str, message_type: str, 
                                 callback: Callable[[Dict[str, Any], str], None], 
                                 queue_size: int = 1) -> bool:
        """订阅话题并在回调中包含话题名称
        
        这是一个便捷方法，专门用于需要在回调函数中获取话题名称的场景。
        回调函数签名: callback(message: Dict[str, Any], topic_name: str)
        
        Args:
            topic_name (str): 话题名称
            message_type (str): 消息类型
            callback (Callable): 回调函数，必须接受两个参数 (message, topic_name)
            queue_size (int): 队列大小
        
        Returns:
            bool: 订阅是否成功
        """
        return self.subscribe_topic(topic_name, message_type, callback, queue_size, include_topic_name=True)
    
    def subscribe_topic_simple(self, topic_name: str, message_type: str, 
                              callback: Callable[[Dict[str, Any]], None], 
                              queue_size: int = 1) -> bool:
        """简单订阅话题（仅传递消息数据）
        
        这是一个便捷方法，用于只需要消息数据的场景。
        回调函数签名: callback(message: Dict[str, Any])
        
        Args:
            topic_name (str): 话题名称
            message_type (str): 消息类型
            callback (Callable): 回调函数，只接受一个参数 (message)
            queue_size (int): 队列大小
        
        Returns:
            bool: 订阅是否成功
        """
        return self.subscribe_topic(topic_name, message_type, callback, queue_size, include_topic_name=False)
    
    def unsubscribe_topic(self, topic_name: str) -> bool:
        """取消订阅话题"""
        try:
            if topic_name in self.subscribers:
                self.subscribers[topic_name].unsubscribe()
                del self.subscribers[topic_name]
                
                # 清理频率控制器（如果有）
                if hasattr(self, '_freq_controllers') and topic_name in self._freq_controllers:
                    del self._freq_controllers[topic_name]
                    self.logger.debug(f"已清理话题 {topic_name} 的频率控制器")
                
                self.logger.debug(f"已取消订阅话题: {topic_name}")
                return True
            else:
                self.logger.warning(f"话题未订阅: {topic_name}")
                return False
        except Exception as e:
            self.logger.error(f"取消订阅话题失败 {topic_name}: {e}")
            return False
    
    def create_publisher(self, topic_name: str, message_type: str, 
                        queue_size: int = 1) -> bool:
        """创建发布者"""
        try:
            if not self.is_connected():
                self.logger.error("客户端未连接，无法创建发布者")
                return False
            
            publisher = roslibpy.Topic(
                self.client,
                topic_name,
                message_type,
                queue_size=queue_size
            )
            
            self.publishers[topic_name] = publisher
            self.logger.debug(f"已创建发布者: {topic_name} ({message_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"创建发布者失败 {topic_name}: {e}")
            return False
    
    def publish_message(self, topic_name: str, message_data: Dict[str, Any]) -> bool:
        """发布消息"""
        try:
            if topic_name not in self.publishers:
                self.logger.error(f"发布者不存在: {topic_name}")
                return False
            
            message = roslibpy.Message(message_data)
            self.publishers[topic_name].publish(message)
            
            if self.show_message_content:
                msg_str = str(message_data)
                if len(msg_str) > self.max_message_length:
                    msg_str = msg_str[:self.max_message_length] + "..."
                self.logger.debug(f"[{topic_name}] 发布消息: {msg_str}")
            else:
                self.logger.debug(f"[{topic_name}] 发布消息")
            
            return True
            
        except Exception as e:
            self.logger.error(f"发布消息失败 {topic_name}: {e}")
            return False
    
    def call_service(self, service_name: str, service_type: str, 
                    request_data: Dict[str, Any], timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """调用服务"""
        try:
            if not self.is_connected():
                self.logger.error("客户端未连接，无法调用服务")
                return None
            
            service = roslibpy.Service(self.client, service_name, service_type)
            request = roslibpy.ServiceRequest(request_data)
            
            self.logger.debug(f"调用服务: {service_name}")
            result = service.call(request, timeout=timeout)
            
            self.logger.debug(f"服务调用成功: {service_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"服务调用失败 {service_name}: {e}")
            return None
    
    def setup_configured_topics(self):
        """根据配置设置话题订阅和发布"""
        # 设置订阅者
        for topic_key, topic_config in self.subscribe_topics.items():
            topic_name = topic_config['name']
            message_type = topic_config['message_type']
            callback_name = topic_config.get('callback_name', 'default_callback')
            
            # 获取回调函数
            callback_func = getattr(self, callback_name, self.default_callback)
            
            # 使用新的订阅方法，自动传递话题名称
            self.subscribe_topic_with_name(topic_name, message_type, callback_func)
        
        # 设置发布者
        for topic_key, topic_config in self.publish_topics.items():
            topic_name = topic_config['name']
            message_type = topic_config['message_type']
            self.create_publisher(topic_name, message_type)
    
    def setup_topic_dynamically(self, topic_key: str, topic_type: str = 'subscribe'):
        """动态设置单个话题"""
        if topic_type == 'subscribe' and topic_key in self.subscribe_topics:
            topic_config = self.subscribe_topics[topic_key]
            topic_name = topic_config['name']
            message_type = topic_config['message_type']
            callback_name = topic_config.get('callback_name', 'default_callback')
            
            callback_func = getattr(self, callback_name, self.default_callback)
            
            # 使用新的订阅方法，自动传递话题名称
            self.subscribe_topic_with_name(topic_name, message_type, callback_func)
        elif topic_type == 'publish' and topic_key in self.publish_topics:
            topic_config = self.publish_topics[topic_key]
            topic_name = topic_config['name']
            message_type = topic_config['message_type']
            self.create_publisher(topic_name, message_type)
    
    def default_callback(self, message: Dict[str, Any], topic_name: str):
        """默认回调函数"""
        if self.show_message_content:
            msg_str = str(message)
            if len(msg_str) > self.max_message_length:
                msg_str = msg_str[:self.max_message_length] + "..."
            self.logger.debug(f"[{topic_name}] 收到消息: {msg_str}")
        else:
            self.logger.debug(f"[{topic_name}] 收到消息")
    
    def server_time_callback(self, message: Dict[str, Any], topic_name: str):
        """服务器时间回调函数"""
        self.default_callback(message, topic_name)
    
    def move_base_callback(self, message: Dict[str, Any], topic_name: str):
        """移动基座回调函数"""
        self.default_callback(message, topic_name)
    
    def start_auto_publish(self, topic_name: str, message_data: Dict[str, Any] = None, 
                          frequency: float = 1.0, message_generator: Callable = None) -> bool:
        """启动自动发布
        
        Args:
            topic_name (str): 话题名称
            message_data (Dict[str, Any], optional): 静态消息数据，如果提供message_generator则忽略此参数
            frequency (float): 发布频率（Hz）
            message_generator (Callable, optional): 消息生成器函数，每次发布时调用以获取新的消息内容
                                                   函数签名: () -> Dict[str, Any]
        
        Returns:
            bool: 启动是否成功
        
        注意:
            - 如果同时提供message_data和message_generator，优先使用message_generator
            - message_generator函数应该返回符合话题消息类型的字典
            - 可以通过修改publish_topics配置来动态更新消息内容
        """
        try:
            if topic_name not in self.publishers:
                self.logger.error(f"发布者不存在: {topic_name}")
                return False
            
            def publish_loop():
                sleep_time = 1.0 / frequency if frequency > 0 else 1.0
                while self.running:
                    if self.is_connected():
                        # 优先使用消息生成器
                        if message_generator and callable(message_generator):
                            try:
                                current_message = message_generator()
                                self.publish_message(topic_name, current_message)
                            except Exception as e:
                                self.logger.error(f"消息生成器执行失败: {e}")
                        else:
                            # 检查是否有动态配置的消息内容
                            current_message = self._get_dynamic_message_data(topic_name, message_data)
                            self.publish_message(topic_name, current_message)
                    time.sleep(sleep_time)
            
            thread = threading.Thread(target=publish_loop, daemon=True)
            thread.start()
            self._publish_threads.append(thread)
            
            self.logger.debug(f"已启动自动发布: {topic_name} ({frequency}Hz)")
            return True
            
        except Exception as e:
            self.logger.error(f"启动自动发布失败 {topic_name}: {e}")
            return False
    
    def _get_dynamic_message_data(self, topic_name: str, default_message: Dict[str, Any]) -> Dict[str, Any]:
        """获取动态消息数据
        
        检查publish_topics配置中是否有更新的消息内容，如果有则使用最新的，否则使用默认消息
        
        Args:
            topic_name (str): 话题名称
            default_message (Dict[str, Any]): 默认消息数据
        
        Returns:
            Dict[str, Any]: 要发布的消息数据
        """
        # 查找对应的话题配置
        for topic_key, topic_config in self.publish_topics.items():
            if topic_config.get('name') == topic_name:
                # 使用配置中的最新内容
                content = topic_config.get('content', 'test')
                # 根据消息类型构造消息数据
                if 'std_msgs/String' in topic_config.get('type', ''):
                    return {'data': content}
                elif 'geometry_msgs/Twist' in topic_config.get('type', ''):
                    # 如果是Twist消息，content应该是包含linear和angular的字典
                    if isinstance(content, dict):
                        return content
                    else:
                        # 如果content是字符串，构造一个简单的Twist消息
                        return {
                            'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                            'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}
                        }
                else:
                    # 对于其他消息类型，尝试直接使用content
                    if isinstance(content, dict):
                        return content
                    else:
                        return {'data': content}
        
        # 如果没有找到配置，使用默认消息
        return default_message or {'data': 'test'}
    
    def update_publish_content(self, topic_key: str, new_content: Any) -> bool:
        """动态更新发布话题的消息内容
        
        Args:
            topic_key (str): 话题配置键名
            new_content (Any): 新的消息内容
        
        Returns:
            bool: 更新是否成功
        """
        if topic_key in self.publish_topics:
            self.publish_topics[topic_key]['content'] = new_content
            self.logger.debug(f"已更新话题 {topic_key} 的消息内容: {new_content}")
            return True
        else:
            self.logger.error(f"话题配置不存在: {topic_key}")
            return False
    
    def update_publish_content_by_name(self, topic_name: str, new_content: Any) -> bool:
        """根据话题名称动态更新发布话题的消息内容
        
        Args:
            topic_name (str): 话题名称
            new_content (Any): 新的消息内容
        
        Returns:
            bool: 更新是否成功
        """
        for topic_key, topic_config in self.publish_topics.items():
            if topic_config.get('name') == topic_name:
                topic_config['content'] = new_content
                self.logger.debug(f"已更新话题 {topic_name} 的消息内容: {new_content}")
                return True
        
        self.logger.error(f"未找到话题: {topic_name}")
        return False
    
    def get_publish_content(self, topic_key: str) -> Any:
        """获取发布话题的当前消息内容
        
        Args:
            topic_key (str): 话题配置键名
        
        Returns:
            Any: 当前消息内容，如果话题不存在则返回None
        """
        if topic_key in self.publish_topics:
            return self.publish_topics[topic_key].get('content')
        return None
    
    def start_auto_publish_with_generator(self, topic_name: str, message_generator: Callable, 
                                        frequency: float = 1.0) -> bool:
        """使用消息生成器启动自动发布
        
        这是一个便捷方法，专门用于需要动态生成消息内容的场景
        
        Args:
            topic_name (str): 话题名称
            message_generator (Callable): 消息生成器函数，签名: () -> Dict[str, Any]
            frequency (float): 发布频率（Hz）
        
        Returns:
            bool: 启动是否成功
        
        Example:
            # 发布当前时间戳
            def time_generator():
                return {'data': f'current_time: {time.time()}'}
            
            client.start_auto_publish_with_generator('/time_topic', time_generator, 1.0)
        """
        return self.start_auto_publish(topic_name, None, frequency, message_generator)
    
    def query_ros_system_info(self):
        """查询ROS系统信息"""
        if not self.ros_info_config.get('query_on_startup', False):
            return
        
        self.logger.debug("开始查询ROS系统信息...")
        
        if self.ros_info_config.get('query_nodes', False):
            self._query_ros_nodes()
        
        if self.ros_info_config.get('query_topics', False):
            self._query_ros_topics()
        
        if self.ros_info_config.get('query_services', False):
            self._query_ros_services()
        
        if self.ros_info_config.get('query_params', False):
            self._query_ros_params()
    
    def _query_ros_nodes(self):
        """查询ROS节点列表"""
        try:
            result = self.call_service('/rosapi/nodes', 'rosapi/Nodes', {}, 
                                     timeout=self.ros_info_config.get('query_timeout', 10))
            if result and 'nodes' in result:
                nodes = result['nodes']
                self.logger.debug(f"找到 {len(nodes)} 个ROS节点")
                if self.ros_info_config.get('show_details', False):
                    for i, node in enumerate(nodes, 1):
                        self.logger.debug(f"  {i:2d}. {node}")
        except Exception as e:
            self.logger.error(f"查询节点列表失败: {e}")
    
    def _query_ros_topics(self):
        """查询ROS话题列表"""
        try:
            result = self.call_service('/rosapi/topics', 'rosapi/Topics', {}, 
                                     timeout=self.ros_info_config.get('query_timeout', 10))
            if result and 'topics' in result:
                topics = result['topics']
                self.logger.debug(f"找到 {len(topics)} 个ROS话题")
                if self.ros_info_config.get('show_details', False):
                    for i, topic in enumerate(topics, 1):
                        self.logger.debug(f"  {i:2d}. {topic}")
        except Exception as e:
            self.logger.error(f"查询话题列表失败: {e}")
    
    def _query_ros_services(self):
        """查询ROS服务列表"""
        try:
            result = self.call_service('/rosapi/services', 'rosapi/Services', {}, 
                                     timeout=self.ros_info_config.get('query_timeout', 10))
            if result and 'services' in result:
                services = result['services']
                self.logger.debug(f"找到 {len(services)} 个ROS服务")
                if self.ros_info_config.get('show_details', False):
                    for i, service in enumerate(services, 1):
                        self.logger.debug(f"  {i:2d}. {service}")
        except Exception as e:
            self.logger.error(f"查询服务列表失败: {e}")
    
    def _query_ros_params(self):
        """查询ROS参数列表"""
        try:
            result = self.call_service('/rosapi/params', 'rosapi/Params', {}, 
                                     timeout=self.ros_info_config.get('query_timeout', 10))
            if result and 'params' in result:
                params = result['params']
                self.logger.debug(f"找到 {len(params)} 个ROS参数")
                if self.ros_info_config.get('show_details', False):
                    for i, param in enumerate(params, 1):
                        self.logger.debug(f"  {i:2d}. {param}")
        except Exception as e:
            self.logger.error(f"查询参数列表失败: {e}")
    
    def start(self) -> bool:
        """启动客户端"""
        # 检查网络连通性
        if not self.check_network_connectivity():
            self.logger.error("网络连接失败，请检查ROSBridge服务器状态")
            return False
        
        # 连接到服务器
        if not self.connect():
            if self.auto_reconnect and self.reconnect_count < self.max_reconnect_attempts:
                self.logger.debug(f"将在{self.reconnect_interval}秒后尝试重连...")
                time.sleep(self.reconnect_interval)
                self.reconnect_count += 1
                return self.start()  # 递归重连
            return False
        
        # 等待连接稳定
        time.sleep(1)
        
        # 查询ROS系统信息
        self.query_ros_system_info()
        
        # 设置话题
        self.setup_configured_topics()
        
        # 启动自动发布
        self.running = True
        for topic_key, topic_config in self.publish_topics.items():
            topic_name = topic_config['name']
            content = topic_config.get('content', 'test')
            frequency = topic_config.get('frequency', 1.0)
            
            message_data = {'data': content}
            self.start_auto_publish(topic_name, message_data, frequency)
        
        self.logger.debug("ROSBridge客户端已启动")
        return True
    
    def stop(self):
        """停止客户端"""
        self.running = False
        
        # 取消所有订阅
        for topic_name in list(self.subscribers.keys()):
            self.unsubscribe_topic(topic_name)
        
        # 清理发布者
        self.publishers.clear()
        
        # 断开连接
        self.disconnect()
        
        self.logger.debug("ROSBridge客户端已停止")
    
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