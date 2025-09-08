#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROSLibPy客户端示例
使用lbrosclient模块连接远程ROS1主机
"""

import time
import threading
from lbrosclient import ROSBridgeClient, Logger, LogLevel
# 创建日志器
logger = Logger(name="ROSLibPyClient", min_level=LogLevel.INFO,show_line_info=True)

def server_time_callback(message, topic_name):
    """服务器时间回调函数"""
    logger.info(f"[{topic_name}] 收到时间消息: {message}")

def cmd_vel_callback(message, topic_name):
    """cmd_vel话题回调函数"""
    logger.info(f"[{topic_name}] 收到速度命令: {message}")

def main():
    
    # 创建ROSBridge客户端
    client = ROSBridgeClient(logger=logger)
    
    # 设置远程主机连接
    client.set_host_port('10.10.17.235', 9091)
    
    try:
        # 连接到ROSBridge服务器
        logger.info("正在连接到远程ROS1主机...")
        if not client.connect():
            logger.error("连接失败")
            return
        
        logger.info("连接成功！")
        
        # 等待连接稳定
        time.sleep(2)
        
        # 查询并打印rostopic list
        logger.info("正在查询话题列表...")
        try:
            result = client.call_service('/rosapi/topics', 'rosapi/Topics', {}, timeout=10.0)
            if result and 'topics' in result:
                topics = result['topics']
                logger.info(f"找到 {len(topics)} 个话题:")
                for i, topic in enumerate(topics, 1):
                    print(f"  {i:2d}. {topic}")
            else:
                logger.warning("无法获取话题列表")
        except Exception as e:
            logger.error(f"查询话题列表失败: {e}")
        
        # 订阅/server_time_now话题
        logger.info("订阅/server_time_now话题...")
        success = client.subscribe_topic(
            '/server_time_now', 
            'std_msgs/String',  # 假设是字符串类型，可根据实际情况调整
            server_time_callback
        )
        
        if success:
            logger.info("成功订阅/server_time_now话题")
        else:
            logger.error("订阅/server_time_now话题失败")
        
        # 订阅/move_tracker/cmd_vel话题，频率限制为1Hz
        logger.info("订阅/move_tracker/cmd_vel话题...")
        cmd_vel_success = client.subscribe_topic(
            '/move_tracker/cmd_vel',
            'geometry_msgs/Twist',  # cmd_vel通常是Twist类型
            cmd_vel_callback,
            target_hz=1.0  # 设置频率为1Hz
        )
        
        if cmd_vel_success:
            logger.info("成功订阅/move_tracker/cmd_vel话题 (1Hz)")
        else:
            logger.error("订阅/move_tracker/cmd_vel话题失败")
        
        # 使用动态发布功能添加/lb/rosbridge话题
        logger.info("添加/lb/rosbridge话题动态发布配置...")
        client.add_publish_topic(
            topic_key='rosbridge_topic',
            topic_name='/lb/rosbridge',
            topic_type='std_msgs/String',
            content='roslibpy',
            frequency=1
        )
        
        # 设置running状态以启用自动发布
        client.running = True
        
        # 创建发布者并启动自动发布
        success = client.create_publisher('/lb/rosbridge', 'std_msgs/String')
        if success:
            logger.info("成功创建/lb/rosbridge话题发布者")
            
            # 启动自动发布，使用配置中的频率
            configured_frequency = client.publish_topics['rosbridge_topic']['frequency']
            
            # 使用消息生成器，每次发布时生成带有时间戳的消息
            def message_generator():
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"发送消息'data': f'{timestamp}-roslibpy'")
                return {'data': f'{timestamp}-roslibpy'}
            
            auto_publish_success = client.start_auto_publish_with_generator(
                '/lb/rosbridge', 
                message_generator, 
                frequency=configured_frequency
            )
            
            if auto_publish_success:
                logger.info(f"成功启动/lb/rosbridge话题自动发布 ({configured_frequency}Hz)，消息内容将包含时间戳")
                
                # 演示5秒后更新消息内容
                def update_content_later():
                    time.sleep(5)
                    logger.info("5秒后更新话题内容...")
                    client.update_publish_content('rosbridge_topic', '已更新的消息内容')
                    logger.info("话题内容已更新，将在下一次发布时生效")
                
                # 启动延时更新线程
                update_thread = threading.Thread(target=update_content_later, daemon=True)
                update_thread.start()
            else:
                logger.error("启动自动发布失败")
        else:
            logger.error("创建/lb/rosbridge话题发布者失败")
        
        # 保持运行
        logger.info("客户端运行中，按Ctrl+C退出...")
        try:
            while client.is_connected():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到退出信号")
    
    except Exception as e:
        logger.error(f"运行时错误: {e}")
    
    finally:
        # 清理资源
        logger.info("正在断开连接...")
        client.disconnect()
        logger.info("客户端已退出")

if __name__ == '__main__':
    main()