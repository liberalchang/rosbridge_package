#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZMQ客户端示例
使用lbrosclient模块实现ZMQ通信
订阅远程主机话题并发布本地话题
"""

import sys
import time
import threading
import struct

try:
    from lbrosclient import ZMQClient, Logger, LogLevel
    print("成功导入lbrosclient模块")
except ImportError as e:
    print(f"导入lbrosclient模块失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"导入过程中发生错误: {e}")
    sys.exit(1)

# 创建日志器
logger = Logger(name="ZMQClient", min_level=LogLevel.INFO, show_line_info=True)

def create_enhanced_callback(remote_host, remote_port, subscribe_topic):
    """
    创建增强的消息回调函数，包含远程主机信息和话题名称
    
    Args:
        remote_host (str): 远程主机IP地址
        remote_port (int): 远程主机端口
        subscribe_topic (str): 订阅的话题名称
    
    Returns:
        function: 消息回调函数
    """
    def message_callback(message):
        """
        消息回调函数
        
        Args:
            message (Any): 接收到的消息
        """
        # 处理原始消息数据
        if isinstance(message, (bytes, bytearray)):
            try:
                # 尝试解码为字符串
                decoded_message = message.decode('utf-8')
                logger.info(f"[订阅] 远程主机: {remote_host}:{remote_port} | 话题: {subscribe_topic} | 消息: {decoded_message}")
            except UnicodeDecodeError:
                logger.info(f"[订阅] 远程主机: {remote_host}:{remote_port} | 话题: {subscribe_topic} | 二进制消息: {len(message)} 字节")
        else:
            logger.info(f"[订阅] 远程主机: {remote_host}:{remote_port} | 话题: {subscribe_topic} | 消息: {message}")
    
    return message_callback

def create_ros_message(topic_name, content):
    """
    创建符合ROS标准的ZMQ多帧消息格式: [话题名帧][数据长度帧][消息数据帧]
    
    Args:
        topic_name (str): 话题名称
        content (str): 消息内容
    
    Returns:
        list: 多帧消息列表
    """
    try:
        # 编码话题名作为第一帧
        topic_frame = topic_name.encode('utf-8')
        
        # 创建符合ROS std_msgs/String格式的序列化数据
        # std_msgs/String消息格式: [字符串长度(4字节)] + [字符串数据]
        content_bytes = content.encode('utf-8')
        content_length = len(content_bytes)
        
        # 按照ROS序列化格式构造消息数据
        # 格式: [字符串长度(4字节小端序)] + [字符串数据]
        message_data = struct.pack('<I', content_length) + content_bytes
        
        # 数据长度作为第二帧（4字节整数）
        data_length = len(message_data)
        data_length_frame = struct.pack('I', data_length)
        
        # 返回多帧消息列表: [话题名帧, 数据长度帧, 消息数据帧]
        return [topic_frame, data_length_frame, message_data]
    except Exception as e:
        logger.error(f"创建ROS消息时出错: {e}")
        return None

def publish_messages(client, socket_name, topic, content, frequency):
    """
    定时发布消息的函数
    
    Args:
        client: ZMQ客户端实例
        socket_name (str): 套接字名称
        topic (str): 话题名称
        content (str): 消息内容
        frequency (float): 发布频率(Hz)
    """
    interval = 1.0 / frequency
    message_count = 0
    
    while True:
        try:
            # 创建符合ROS标准的三帧消息格式
            message_content = f"{content}_{message_count}"
            message_frames = create_ros_message(topic, message_content)
            
            if message_frames:
                # 发送多帧消息
                success = client.send_multipart_message(socket_name, message_frames)
                if success:
                    logger.info(f"[发布] 话题: {topic}, 消息: {message_content}, 计数: {message_count}, 帧数: {len(message_frames)}")
                    message_count += 1
                else:
                    logger.info(f"[发布失败] 话题: {topic}")
            else:
                logger.error(f"创建消息失败: {topic}")
            
            time.sleep(interval)
        except Exception as e:
            logger.info(f"发布消息时发生错误: {e}")
            break

def main():
    """
    主函数
    """
    
    # 创建ZMQ客户端，设置消息格式为bytes以避免JSON反序列化
    client = ZMQClient(logger=logger)
    # 设置消息格式为bytes，避免自动JSON反序列化
    client.message_format = 'bytes'
    
    try:
        # 设置运行标志
        client.running = True
        
        # 1. 连接到远程主机订阅话题
        remote_host = "10.10.12.233"
        remote_port = 5555
        subscribe_topics = ["/server_time_now", "/move_tracker/cmd_vel"]  # 订阅多个话题
        
        logger.info(f"正在连接到远程主机 {remote_host}:{remote_port} 订阅话题 {subscribe_topics}...")
        
        # 创建订阅客户端 - 订阅指定话题列表
        remote_endpoint = f"tcp://{remote_host}:{remote_port}"
        success = client.create_sub_client(remote_endpoint, "remote_sub", subscribe_topics)  # 订阅多个话题
        
        if success:
            logger.info(f"成功连接到远程主机 {remote_host}:{remote_port}")
            # 创建增强的消息回调函数（支持多话题）
            enhanced_callback = create_enhanced_callback(remote_host, remote_port, "多话题")
            # 启动订阅循环
            client.start_subscriber_loop("remote_sub", enhanced_callback)
            logger.info(f"已启动订阅循环，等待接收话题 {subscribe_topics} 的消息...")
        else:
            logger.info(f"连接远程主机失败: {remote_host}:{remote_port}")
            return
        
        # 2. 在本地主机发布话题
        local_host = "10.10.19.252"
        local_port = 5556
        publish_topic = "/lb/rosbridge"  # ROS话题名称必须以'/'开头
        publish_content = "zmq"
        publish_frequency = 1.0  # 1Hz
        
        logger.info(f"正在本地主机 {local_host}:{local_port} 发布话题 {publish_topic}...")
        
        # 创建发布服务器
        local_endpoint = f"tcp://{local_host}:{local_port}"
        success = client.create_pub_server(local_endpoint, "local_pub")
        
        if success:
            logger.info(f"成功在本地主机 {local_host}:{local_port} 创建发布服务器")
            # 启动发布线程
            publish_thread = threading.Thread(
                target=publish_messages, 
                args=(client, "local_pub", publish_topic, publish_content, publish_frequency),
                daemon=True
            )
            publish_thread.start()
        else:
            logger.info(f"创建本地发布服务器失败: {local_host}:{local_port}")
            return
        
        logger.info("ZMQ客户端已启动，按 Ctrl+C 退出...")
        logger.info(f"订阅: {remote_host}:{remote_port} -> {subscribe_topics}")
        logger.info(f"发布: {local_host}:{local_port} -> {publish_topic} (频率: {publish_frequency}Hz)")
        
        # 保持程序运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n正在停止ZMQ客户端...")
        
    except Exception as e:
        logger.error(f"运行过程中发生错误: {e}")
    
    finally:
        # 清理资源
        logger.info("正在清理资源...")
        client.stop()
        logger.info("ZMQ客户端已停止")

if __name__ == "__main__":
    main()