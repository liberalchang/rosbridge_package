#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例文件
展示如何使用lbrosclient模块的各种功能
"""

import time
import json
from pathlib import Path

# 导入模块
from . import Logger, LogLevel, ROSBridgeClient, ZMQClient
from .param_manager import ParamManager

def example_logger():
    """日志器使用示例"""
    print("\n=== 日志器使用示例 ===")
    
    # 创建日志器
    logger = Logger(name="Example", min_level=LogLevel.DEBUG)
    
    # 测试不同级别的日志
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")
    
    # 配置日志器
    logger.configure({
        'show_timestamp': True,
        'timestamp_format': '%H:%M:%S',
        'max_message_length': 50,
        'enable_colors': True
    })
    
    logger.info("配置后的日志输出")
    logger.info("这是一条很长的日志消息，用于测试消息长度限制功能是否正常工作")

def example_config_manager():
    """配置管理器使用示例"""
    print("\n=== 配置管理器使用示例 ===")
    
    # 创建配置管理器
    logger = Logger(name="ConfigExample")
    config_manager = ConfigManager(logger)
    
    # 获取默认配置
    ros_config = ConfigManager.get_rosbridge_default_config()
    zmq_config = ConfigManager.get_zmq_default_config()
    
    print(f"ROSBridge默认主机: {ros_config['rosbridge']['default']['host']}")
    print(f"ZMQ默认主机: {zmq_config['zmq']['default']['host']}")
    
    # 验证配置
    is_valid = config_manager.validate_config(ros_config, 'rosbridge')
    print(f"ROSBridge配置验证结果: {is_valid}")
    
    # 合并配置
    custom_config = {
        'rosbridge': {
            'default': {
                'host': 'localhost',
                'port': 9090
            }
        }
    }
    
    merged_config = config_manager.merge_configs(ros_config, custom_config)
    print(f"合并后的主机: {merged_config['rosbridge']['default']['host']}")

def example_rosbridge_client():
    """ROSBridge客户端使用示例"""
    print("\n=== ROSBridge客户端使用示例 ===")
    
    # 创建自定义配置
    custom_config = {
        'rosbridge': {
            'default': {
                'host': 'localhost',
                'port': 9090
            },
            'connection': {
                'timeout': 5,
                'retry_interval': 0.5,
                'max_retries': 3
            }
        },
        'logging': {
            'verbose': True,
            'show_connection_status': True,
            'show_message_content': True,
            'max_message_length': 100
        },
        'topics': {
            'subscribe': {
                'test_sub': {
                    'name': '/test_topic',
                    'message_type': 'std_msgs/String',
                    'callback_name': 'test_callback'
                }
            },
            'publish': {
                'test_pub': {
                    'name': '/test_publish',
                    'message_type': 'std_msgs/String',
                    'content': 'Hello ROS!',
                    'frequency': 1.0
                }
            }
        },
        'network': {
            'connectivity_check': {
                'enabled': False  # 禁用网络检查用于示例
            }
        }
    }
    
    # 创建客户端
    logger = Logger(name="ROSExample")
    client = ROSBridgeClient(config=custom_config, logger=logger)
    
    # 添加自定义回调函数
    def test_callback(message, topic_name):
        logger.info(f"收到来自 {topic_name} 的消息: {message}")
    
    # 将回调函数绑定到客户端
    client.test_callback = test_callback
    
    print("ROSBridge客户端已创建")
    print(f"目标地址: {client.host}:{client.port}")
    print("注意: 此示例需要ROSBridge服务器运行才能正常工作")
    
    # 演示API使用（不实际连接）
    print("\n可用的API方法:")
    print("- client.connect(): 连接到服务器")
    print("- client.subscribe_topic(name, type, callback): 订阅话题")
    print("- client.create_publisher(name, type): 创建发布者")
    print("- client.publish_message(name, data): 发布消息")
    print("- client.call_service(name, type, data): 调用服务")
    print("- client.start(): 启动客户端")
    print("- client.stop(): 停止客户端")

def example_zmq_client():
    """ZMQ客户端使用示例"""
    print("\n=== ZMQ客户端使用示例 ===")
    
    # 创建自定义配置
    custom_config = {
        'zmq': {
            'default': {
                'host': 'localhost',
                'port': 5555
            },
            'connection': {
                'timeout': 5,
                'retry_interval': 0.5,
                'max_retries': 3
            },
            'socket': {
                'linger_time': 1000,
                'high_water_mark': 1000,
                'receive_timeout': 5000,
                'send_timeout': 5000,
                'options': {}
            }
        },
        'message': {
            'format': 'json',
            'encoding': 'utf-8',
            'compression': {
                'enabled': False,
                'level': 6
            }
        },
        'logging': {
            'verbose': True,
            'show_connection_status': True,
            'show_message_content': True,
            'max_message_length': 100
        },
        'patterns': {
            'req_client': {
                'enabled': False,  # 禁用自动设置用于示例
                'type': 'req_client',
                'endpoint': 'tcp://localhost:5555',
                'socket_name': 'req_client'
            },
            'pub_server': {
                'enabled': False,
                'type': 'pub_server',
                'endpoint': 'tcp://*:5556',
                'socket_name': 'pub_server'
            }
        },
        'network': {
            'connectivity_check': {
                'enabled': False  # 禁用网络检查用于示例
            }
        }
    }
    
    # 创建客户端
    logger = Logger(name="ZMQExample")
    client = ZMQClient(config=custom_config, logger=logger)
    
    print("ZMQ客户端已创建")
    print(f"默认地址: {client.default_host}:{client.default_port}")
    print(f"消息格式: {client.message_format}")
    
    # 演示API使用（不实际连接）
    print("\n可用的API方法:")
    print("- client.create_req_client(endpoint): 创建REQ客户端")
    print("- client.create_rep_server(endpoint): 创建REP服务器")
    print("- client.create_pub_server(endpoint): 创建PUB发布者")
    print("- client.create_sub_client(endpoint, topics): 创建SUB订阅者")
    print("- client.send_message(socket_name, data): 发送消息")
    print("- client.receive_message(socket_name): 接收消息")
    print("- client.request_reply(socket_name, data): 请求-回复")
    print("- client.start(): 启动客户端")
    print("- client.stop(): 停止客户端")

def example_zmq_req_rep_pattern():
    """ZMQ请求-回复模式示例"""
    print("\n=== ZMQ请求-回复模式示例 ===")
    
    # 创建简单配置
    config = ConfigManager.get_zmq_default_config()
    config['network']['connectivity_check']['enabled'] = False
    
    logger = Logger(name="ZMQReqRep")
    
    # 创建客户端和服务器
    server = ZMQClient(config=config, logger=logger)
    client = ZMQClient(config=config, logger=logger)
    
    print("演示REQ/REP模式的使用方法:")
    print("")
    print("# 服务器端代码")
    print("server.create_rep_server('tcp://*:5555')")
    print("")
    print("def handle_request(request):")
    print("    return {'response': f'处理了请求: {request}'}")
    print("")
    print("server.start_server_loop('rep_server', handle_request)")
    print("")
    print("# 客户端代码")
    print("client.create_req_client('tcp://localhost:5555')")
    print("response = client.request_reply('req_client', {'message': 'Hello'})")
    print("print(f'收到回复: {response}')")

def example_zmq_pub_sub_pattern():
    """ZMQ发布-订阅模式示例"""
    print("\n=== ZMQ发布-订阅模式示例 ===")
    
    print("演示PUB/SUB模式的使用方法:")
    print("")
    print("# 发布者代码")
    print("publisher.create_pub_server('tcp://*:5556')")
    print("publisher.send_message('pub_server', {'topic': 'news', 'content': '新闻内容'})")
    print("")
    print("# 订阅者代码")
    print("subscriber.create_sub_client('tcp://localhost:5556', ['news'])")
    print("")
    print("def message_callback(message):")
    print("    print(f'收到消息: {message}')")
    print("")
    print("subscriber.start_subscriber_loop('sub_client', message_callback)")

def example_context_manager():
    """上下文管理器使用示例"""
    print("\n=== 上下文管理器使用示例 ===")
    
    config = ConfigManager.get_zmq_default_config()
    config['network']['connectivity_check']['enabled'] = False
    
    print("使用with语句自动管理资源:")
    print("")
    print("with ZMQClient(config=config) as client:")
    print("    client.create_req_client('tcp://localhost:5555')")
    print("    response = client.request_reply('req_client', {'test': 'data'})")
    print("    # 退出with块时自动调用client.stop()")

def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    # 创建配置，启用错误处理
    config = ConfigManager.get_rosbridge_default_config()
    config['error_handling']['continue_on_error'] = True
    config['error_handling']['auto_reconnect'] = True
    config['error_handling']['max_reconnect_attempts'] = 3
    config['network']['connectivity_check']['enabled'] = False
    
    logger = Logger(name="ErrorExample")
    client = ROSBridgeClient(config=config, logger=logger)
    
    print("错误处理配置:")
    print(f"- 遇到错误时继续运行: {client.continue_on_error}")
    print(f"- 自动重连: {client.auto_reconnect}")
    print(f"- 最大重连次数: {client.max_reconnect_attempts}")
    print(f"- 重连间隔: {client.reconnect_interval}秒")
    
    print("\n客户端会在连接失败时自动重试，并在遇到错误时继续运行")

def dynamic_config_example():
    """动态配置功能示例"""
    print("\n=== 动态配置功能示例 ===")
    
    # 创建参数管理器
    param_manager = ParamManager()
    
    # 1. ROSBridge客户端动态配置示例
    print("\n--- ROSBridge动态配置 ---")
    ros_client = ROSBridgeClient(param_manager=param_manager)
    
    # 动态设置连接参数
    ros_client.set_host_port('192.168.1.100', 9090)
    
    # 动态添加订阅话题
    ros_client.add_subscribe_topic(
        topic_key='sensor_data',
        topic_name='/sensor/data',
        message_type='sensor_msgs/LaserScan',
        callback_name='default_callback'
    )
    
    # 动态添加发布话题
    ros_client.add_publish_topic(
        topic_key='cmd_vel',
        topic_name='/cmd_vel',
        message_type='geometry_msgs/Twist',
        content='move_command',
        frequency=10.0
    )
    
    # 批量更新配置
    updates = {
        'connection_timeout': 15,
        'verbose': False,
        'main_loop_sleep': 0.05
    }
    ros_client.batch_update_config('rosbridge', updates)
    
    # 获取配置值
    timeout = ros_client.get_config_value('rosbridge', 'connection_timeout')
    print(f"当前连接超时: {timeout}秒")
    
    # 2. ZMQ客户端动态配置示例
    print("\n--- ZMQ动态配置 ---")
    zmq_client = ZMQClient(param_manager=param_manager)
    
    # 动态设置连接参数
    zmq_client.set_host_port('192.168.1.200', 5555)
    
    # 动态添加订阅话题
    zmq_client.add_subscribe_topic('/robot/status')
    zmq_client.add_subscribe_topic('/robot/sensors')
    
    # 动态添加发布话题
    zmq_client.add_publish_topic(
        topic_key='control_cmd',
        topic_name='/robot/control',
        content='control_data',
        frequency=20.0
    )
    
    # 启用通信模式
    zmq_client.enable_pattern('req_rep', endpoint='tcp://localhost:5556')
    zmq_client.enable_pattern('pub_sub', topics=['/status', '/data'])
    
    # 单个配置更新
    zmq_client.update_config('zmq', 'message_format', 'json')
    zmq_client.update_config('zmq', 'receive_timeout', 2000)
    
    print("动态配置示例完成")

def external_program_integration_example():
    """外部程序集成示例"""
    print("\n=== 外部程序集成示例 ===")
    
    # 创建参数管理器
    param_manager = ParamManager()
    
    # 模拟外部程序传递的配置
    external_config = {
        'robot_ip': '192.168.1.50',
        'robot_port': 9090,
        'topics_to_subscribe': [
            {'key': 'odom', 'name': '/odom', 'type': 'nav_msgs/Odometry'},
            {'key': 'scan', 'name': '/scan', 'type': 'sensor_msgs/LaserScan'}
        ],
        'topics_to_publish': [
            {'key': 'cmd', 'name': '/cmd_vel', 'type': 'geometry_msgs/Twist', 'freq': 10}
        ]
    }
    
    # 创建客户端（使用空的默认配置）
    client = ROSBridgeClient(param_manager=param_manager)
    
    # 根据外部配置动态设置
    client.set_host_port(external_config['robot_ip'], external_config['robot_port'])
    
    # 动态添加订阅话题
    for topic in external_config['topics_to_subscribe']:
        client.add_subscribe_topic(
            topic_key=topic['key'],
            topic_name=topic['name'],
            message_type=topic['type']
        )
    
    # 动态添加发布话题
    for topic in external_config['topics_to_publish']:
        client.add_publish_topic(
            topic_key=topic['key'],
            topic_name=topic['name'],
            message_type=topic['type'],
            frequency=topic['freq']
        )
    
    print(f"已配置连接到: {external_config['robot_ip']}:{external_config['robot_port']}")
    print(f"订阅话题数量: {len(external_config['topics_to_subscribe'])}")
    print(f"发布话题数量: {len(external_config['topics_to_publish'])}")
    
    # 在实际应用中，这里会调用 client.start() 启动客户端
    print("外部程序集成配置完成")

def zmq_remote_connection_example():
    """ZMQ远程连接示例"""
    print("\n=== ZMQ远程连接示例 ===")
    
    from .zmq_client import ZMQClient
    from .logger import Logger, LogLevel
    
    # 创建参数管理器和ZMQ客户端
    param_manager = ParamManager()
    logger = Logger(name="ZMQRemote", min_level=LogLevel.INFO)
    client = ZMQClient(param_manager=param_manager, logger=logger)
    
    # 1. 连接单个远程主机
    print("\n1. 连接单个远程主机")
    success = client.connect_to_remote_host(
        host='192.168.1.100',
        port=5555,
        socket_type='req',
        socket_name='remote_server'
    )
    print(f"连接结果: {'成功' if success else '失败'}")
    
    # 2. 连接订阅服务器
    print("\n2. 连接远程订阅服务器")
    success = client.connect_to_remote_host(
        host='192.168.1.101',
        port=5556,
        socket_type='sub',
        socket_name='remote_publisher',
        topics=['topic1', 'topic2'],
        auto_start_loop=True
    )
    print(f"订阅连接结果: {'成功' if success else '失败'}")
    
    # 3. 连接多个远程主机
    print("\n3. 连接多个远程主机")
    hosts_config = [
        {
            'host': '192.168.1.102',
            'port': 5557,
            'socket_type': 'req',
            'socket_name': 'server1'
        },
        {
            'host': '192.168.1.103',
            'port': 5558,
            'socket_type': 'push',
            'socket_name': 'push_server'
        },
        {
            'host': '192.168.1.104',
            'port': 5559,
            'socket_type': 'sub',
            'socket_name': 'data_stream',
            'topics': ['sensor_data', 'status'],
            'auto_start_loop': True
        }
    ]
    
    results = client.connect_to_multiple_hosts(hosts_config)
    print("多主机连接结果:")
    for host, success in results.items():
        print(f"  {host}: {'成功' if success else '失败'}")
    
    # 4. 发送请求消息
    if 'remote_server' in client.sockets:
        print("\n4. 发送请求消息")
        response = client.request_reply(
            'remote_server', 
            {'command': 'get_status', 'timestamp': time.time()},
            timeout=5.0
        )
        print(f"服务器响应: {response}")
    
    # 5. 推送消息
    if 'push_server' in client.sockets:
        print("\n5. 推送消息")
        success = client.send_message(
            'push_server',
            {'data': 'test_data', 'id': 12345}
        )
        print(f"推送结果: {'成功' if success else '失败'}")
    
    # 6. 断开连接
    print("\n6. 断开连接")
    client.disconnect_from_host('remote_server')
    client.disconnect_from_host('push_server')
    print("已断开指定连接")
    
    # 停止客户端
    client.stop()
    print("ZMQ远程连接示例完成")

def zmq_advanced_remote_example():
    """ZMQ高级远程连接示例"""
    print("\n=== ZMQ高级远程连接示例 ===")
    
    from .zmq_client import ZMQClient
    from .logger import Logger, LogLevel
    import threading
    
    # 创建参数管理器和ZMQ客户端
    param_manager = ParamManager()
    logger = Logger(name="ZMQAdvanced", min_level=LogLevel.INFO)
    client = ZMQClient(param_manager=param_manager, logger=logger)
    
    # 自定义消息处理回调
    def custom_message_handler(message):
        print(f"收到自定义消息: {message}")
        # 这里可以添加自定义的消息处理逻辑
    
    # 连接到数据流服务器
    print("连接到数据流服务器...")
    success = client.connect_to_remote_host(
        host='192.168.1.200',
        port=6000,
        socket_type='sub',
        socket_name='data_stream',
        topics=['sensor/*', 'robot/status'],
        auto_start_loop=False  # 手动控制循环
    )
    
    if success:
        # 手动启动订阅循环，使用自定义回调
        client.start_subscriber_loop('data_stream', custom_message_handler)
        print("数据流订阅已启动")
    
    # 连接到控制服务器
    print("连接到控制服务器...")
    control_success = client.connect_to_remote_host(
        host='192.168.1.201',
        port=6001,
        socket_type='req',
        socket_name='control_server'
    )
    
    if control_success:
        # 发送控制命令
        commands = [
            {'action': 'start', 'params': {'speed': 1.0}},
            {'action': 'move', 'params': {'x': 10, 'y': 5}},
            {'action': 'stop', 'params': {}}
        ]
        
        for cmd in commands:
            print(f"发送命令: {cmd}")
            response = client.request_reply('control_server', cmd, timeout=3.0)
            print(f"命令响应: {response}")
            time.sleep(1)
    
    # 运行一段时间后停止
    print("运行10秒后停止...")
    time.sleep(10)
    
    client.stop()
    print("高级远程连接示例完成")

def main():
    """运行所有示例"""
    print("lbrosclient模块使用示例")
    print("=" * 50)
    
    # 运行各个示例
    example_logger()
    example_config_manager()
    example_rosbridge_client()
    example_zmq_client()
    example_zmq_req_rep_pattern()
    example_zmq_pub_sub_pattern()
    example_context_manager()
    example_error_handling()
    dynamic_config_example()
    external_program_integration_example()
    zmq_remote_connection_example()
    zmq_advanced_remote_example()
    
    print("\n=== 示例运行完成 ===")
    print("\n注意事项:")
    print("1. ROSBridge示例需要ROSBridge服务器运行")
    print("2. ZMQ示例需要对应的服务器端运行")
    print("3. 实际使用时请根据需要修改配置")
    print("4. 更多详细用法请参考各模块的文档字符串")
    print("5. 动态配置功能允许在运行时灵活调整客户端配置")

if __name__ == '__main__':
    main()