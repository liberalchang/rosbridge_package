#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向ROS发布Pose消息示例
"""

import time
import threading
from lbrosclient import ROSBridgeClient, Logger, LogLevel

# 创建日志器
logger = Logger(name="PosePublisher", min_level=LogLevel.INFO, show_line_info=True)

def create_pose_message(x, y, z, ox, oy, oz, ow):
    """
    创建geometry_msgs/Pose类型的消息
    """
    return {
        "position": {
            "x": x,
            "y": y,
            "z": z
        },
        "orientation": {
            "x": ox,
            "y": oy,
            "z": oz,
            "w": ow
        }
    }

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
        
        # 创建发布者
        topic_name = '/baselink_tf'
        topic_type = 'geometry_msgs/Pose'
        
        logger.info(f"创建{topic_name}话题发布者...")
        success = client.create_publisher(topic_name, topic_type)
        
        if not success:
            logger.error(f"创建{topic_name}话题发布者失败")
            return
            
        logger.info(f"成功创建{topic_name}话题发布者")
        
        # 定义消息内容
        pose_message = create_pose_message(1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # 添加到自动发布配置中，频率为10Hz
        client.add_publish_topic(
            topic_key='baselink_tf_topic',
            topic_name=topic_name,
            topic_type=topic_type,
            content=pose_message,
            frequency=10
        )
        
        # 设置running状态以启用自动发布
        client.running = True
        
        # 启动自动发布
        auto_publish_success = client.start_auto_publish(topic_name, frequency=10)
        
        if auto_publish_success:
            logger.info(f"成功启动{topic_name}话题自动发布 (10Hz)")
        else:
            logger.error("启动自动发布失败")
            return
        
        # 保持运行
        logger.info("话题发布中，按Ctrl+C退出...")
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
