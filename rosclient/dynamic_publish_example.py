#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态发布消息内容示例
演示如何使用ROSBridge客户端的动态消息功能
"""

import time
import threading
from lbrosclient import ROSBridgeClient, Logger, LogLevel

# 创建日志器
logger = Logger(name="DynamicPublishExample", min_level=LogLevel.INFO, show_line_info=True)

def main():
    # 创建ROSBridge客户端
    client = ROSBridgeClient(logger=logger)
    
    # 设置远程主机连接
    client.set_host_port('10.10.12.233', 9091)
    
    try:
        # 连接到ROSBridge服务器
        logger.info("正在连接到远程ROS1主机...")
        if not client.connect():
            logger.error("连接失败")
            return
        
        logger.info("连接成功！")
        time.sleep(2)
        
        # 方法1: 使用动态配置更新消息内容
        logger.info("=== 方法1: 动态配置更新 ===")
        
        # 添加发布话题配置
        client.add_publish_topic(
            topic_key='dynamic_topic',
            topic_name='/lb/dynamic_test',
            topic_type='std_msgs/String',
            content='初始消息',
            frequency=1
        )
        
        # 创建发布者并启动自动发布
        client.create_publisher('/lb/dynamic_test', 'std_msgs/String')
        client.start_auto_publish('/lb/dynamic_test', {'data': '初始消息'}, frequency=1.0)
        
        logger.info("已启动动态话题发布，初始内容: '初始消息'")
        
        # 运行5秒后更新消息内容
        def update_content():
            time.sleep(5)
            logger.info("5秒后更新消息内容...")
            client.update_publish_content('dynamic_topic', '更新后的消息')
            
            time.sleep(5)
            logger.info("再次更新消息内容...")
            client.update_publish_content_by_name('/lb/dynamic_test', '第二次更新的消息')
            
            time.sleep(5)
            logger.info("最后一次更新消息内容...")
            client.update_publish_content('dynamic_topic', f'时间戳消息: {time.time()}')
        
        update_thread = threading.Thread(target=update_content, daemon=True)
        update_thread.start()
        
        # 方法2: 使用消息生成器
        logger.info("=== 方法2: 消息生成器 ===")
        
        # 创建时间戳消息生成器
        def timestamp_generator():
            return {'data': f'当前时间: {time.strftime("%Y-%m-%d %H:%M:%S")}'}
        
        # 创建计数器消息生成器
        counter = {'value': 0}
        def counter_generator():
            counter['value'] += 1
            return {'data': f'计数器: {counter["value"]}'}
        
        # 启动时间戳话题
        client.create_publisher('/lb/timestamp', 'std_msgs/String')
        client.start_auto_publish_with_generator('/lb/timestamp', timestamp_generator, 0.5)
        logger.info("已启动时间戳话题发布 (0.5Hz)")
        
        # 启动计数器话题
        client.create_publisher('/lb/counter', 'std_msgs/String')
        client.start_auto_publish_with_generator('/lb/counter', counter_generator, 2.0)
        logger.info("已启动计数器话题发布 (2Hz)")
        
        # 方法3: 复杂消息类型的动态生成
        logger.info("=== 方法3: 复杂消息类型 ===")
        
        def twist_generator():
            # 生成简单的圆周运动命令
            import math
            t = time.time()
            return {
                'linear': {
                    'x': 0.5 * math.sin(t * 0.5),
                    'y': 0.0,
                    'z': 0.0
                },
                'angular': {
                    'x': 0.0,
                    'y': 0.0,
                    'z': 0.3 * math.cos(t * 0.5)
                }
            }
        
        # 启动Twist话题
        client.create_publisher('/lb/cmd_vel', 'geometry_msgs/Twist')
        client.start_auto_publish_with_generator('/lb/cmd_vel', twist_generator, 10.0)
        logger.info("已启动Twist话题发布 (10Hz)")
        
        # 保持运行
        logger.info("客户端运行中，按Ctrl+C退出...")
        logger.info("观察消息内容的动态变化:")
        logger.info("- /lb/dynamic_test: 每5秒更新一次内容")
        logger.info("- /lb/timestamp: 每2秒发布当前时间")
        logger.info("- /lb/counter: 每0.5秒发布递增计数")
        logger.info("- /lb/cmd_vel: 每0.1秒发布圆周运动命令")
        
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