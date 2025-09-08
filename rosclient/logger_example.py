#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块使用示例
演示如何在ROS客户端项目中使用统一的日志封装模块
"""

from logger import Logger, LogLevel, create_logger
from logger import debug, info, warning, error, critical, set_max_length, set_level

def demo_basic_usage():
    """演示基本用法"""
    print("=== 基本日志功能演示 ===")
    
    # 使用便捷函数
    debug("这是一条调试消息")
    info("这是一条信息消息")
    warning("这是一条警告消息")
    error("这是一条错误消息")
    critical("这是一条严重错误消息")
    
    print("\n")

def demo_custom_logger():
    """演示自定义日志器"""
    print("=== 自定义日志器演示 ===")
    
    # 创建自定义日志器
    custom_logger = create_logger(
        name="CustomLogger",
        max_message_length=50,
        show_timestamp=True,
        min_level=LogLevel.DEBUG
    )
    
    custom_logger.debug("自定义日志器的调试消息")
    custom_logger.info("自定义日志器的信息消息")
    custom_logger.warning("自定义日志器的警告消息")
    
    print("\n")

def demo_message_truncation():
    """演示消息截断功能"""
    print("=== 消息截断功能演示 ===")
    
    # 设置较短的最大长度
    set_max_length(30)
    
    long_message = "这是一条非常长的消息，" * 10
    info(f"原始消息长度: {len(long_message)} 字符")
    info(long_message)
    
    # 恢复默认长度
    set_max_length(200)
    
    print("\n")

def demo_log_levels():
    """演示日志级别控制"""
    print("=== 日志级别控制演示 ===")
    
    # 设置为WARNING级别，DEBUG和INFO将不显示
    set_level(LogLevel.WARNING)
    
    debug("这条DEBUG消息不会显示")
    info("这条INFO消息不会显示")
    warning("这条WARNING消息会显示")
    error("这条ERROR消息会显示")
    
    # 恢复为INFO级别
    set_level(LogLevel.INFO)
    
    print("\n")

def demo_ros_client_integration():
    """演示在ROS客户端中的集成使用"""
    print("=== ROS客户端集成演示 ===")
    
    # 模拟ROS客户端日志器
    ros_logger = create_logger(
        name="ROSClient",
        max_message_length=100,
        show_timestamp=True,
        timestamp_format="%H:%M:%S.%f",
        min_level=LogLevel.INFO
    )
    
    # 模拟连接过程
    ros_logger.info("正在连接到ROS服务器...")
    ros_logger.info("连接成功")
    
    # 模拟消息收发
    ros_logger.info("发送话题: /test, 消息: Hello ROS")
    ros_logger.info("接收话题: /response, 消息: ACK")
    
    # 模拟错误情况
    ros_logger.error("连接丢失，正在重试...")
    ros_logger.warning("网络延迟较高")
    
    print("\n")

def demo_zmq_client_integration():
    """演示在ZMQ客户端中的集成使用"""
    print("=== ZMQ客户端集成演示 ===")
    
    # 模拟ZMQ客户端日志器
    zmq_logger = create_logger(
        name="ZMQClient",
        max_message_length=150,
        show_timestamp=True,
        min_level=LogLevel.DEBUG
    )
    
    # 模拟ZMQ操作
    zmq_logger.debug("初始化ZMQ上下文")
    zmq_logger.info("连接到 tcp://192.168.1.100:5555")
    zmq_logger.info("发送多帧消息 - 话题: /test, 类型: std_msgs/String, 长度: 42字节")
    zmq_logger.info("接收消息 - 话题: /response, 类型: std_msgs/String, 长度: 15字节")
    
    # 模拟序列化过程
    zmq_logger.debug("创建消息: 话题=/test, 内容=Hello ZMQ, 消息类型=std_msgs/String, 序列化后长度=42字节")
    
    print("\n")

if __name__ == "__main__":
    print("日志封装模块使用示例\n")
    
    demo_basic_usage()
    demo_custom_logger()
    demo_message_truncation()
    demo_log_levels()
    demo_ros_client_integration()
    demo_zmq_client_integration()
    
    print("=== 演示完成 ===")
    print("\n使用说明:")
    print("1. 导入: from logger import Logger, LogLevel, create_logger")
    print("2. 创建日志器: logger = create_logger('MyLogger', max_message_length=100)")
    print("3. 输出日志: logger.info('消息内容')")
    print("4. 设置级别: logger.set_level(LogLevel.WARNING)")
    print("5. 设置长度: logger.set_max_length(50)")