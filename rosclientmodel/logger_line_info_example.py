#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger行号显示功能使用示例
"""

import sys
import os

# 添加lbrosclient模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lbrosclient'))

from lbrosclient.logger import Logger, LogLevel, info, debug, warning, error, configure_default_logger

def main():
    print("=== Logger行号显示功能示例 ===")
    
    # 1. 创建启用行号显示的日志器
    logger = Logger(
        name="MyApp",
        show_line_info=True,  # 启用行号显示
        min_level=LogLevel.DEBUG
    )
    
    logger.info("这条日志会显示文件名和行号")  # 第23行
    logger.debug("调试信息也会显示行号")      # 第24行
    logger.warning("警告信息")               # 第25行
    logger.error("错误信息")                 # 第26行
    
    print("\n=== 动态启用/禁用行号显示 ===")
    
    # 2. 动态控制行号显示
    logger2 = Logger(name="DynamicApp")
    logger2.info("默认不显示行号")  # 第32行
    
    logger2.enable_line_info(True)  # 启用行号显示
    logger2.info("现在显示行号了")  # 第35行
    
    logger2.enable_line_info(False)  # 禁用行号显示
    logger2.info("又不显示行号了")  # 第38行
    
    print("\n=== 通过配置启用行号显示 ===")
    
    # 3. 通过配置字典启用
    logger3 = Logger(name="ConfigApp")
    logger3.configure({
        'show_line_info': True,
        'min_level': 'DEBUG',
        'show_timestamp': True
    })
    
    logger3.debug("通过配置启用的行号显示")  # 第49行
    
    print("\n=== 默认日志器的行号显示 ===")
    
    # 4. 配置默认日志器启用行号显示
    configure_default_logger({
        'show_line_info': True,
        'min_level': 'DEBUG'
    })
    
    # 使用便捷函数，会显示正确的调用行号
    debug("默认日志器的DEBUG消息")    # 第59行
    info("默认日志器的INFO消息")     # 第60行
    warning("默认日志器的WARNING消息") # 第61行
    error("默认日志器的ERROR消息")   # 第62行
    
    print("\n=== 在函数中使用 ===")
    test_function()
    
    print("\n=== 在类中使用 ===")
    app = MyApplication()
    app.run()

def test_function():
    """测试函数中的日志行号显示"""
    logger = Logger(name="FuncLogger", show_line_info=True)
    logger.info("函数中的日志消息")  # 第74行

class MyApplication:
    """示例应用类"""
    
    def __init__(self):
        self.logger = Logger(
            name="MyApp", 
            show_line_info=True,
            min_level=LogLevel.DEBUG
        )
        self.logger.debug("应用初始化")  # 第85行
    
    def run(self):
        """运行应用"""
        self.logger.info("应用开始运行")     # 第89行
        self.logger.warning("这是一个警告")  # 第90行
        self.logger.info("应用运行完成")     # 第91行

if __name__ == "__main__":
    main()