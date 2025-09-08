#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py for lbrosclient package
用于将lbrosclient打包成Python wheel标准模块
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = """
# lbrosclient

一个功能强大的ROS和ZMQ客户端库，提供配置化管理和模块化封装。

## 主要功能

- **ROSBridge客户端**: 基于roslibpy的WebSocket客户端，支持话题订阅、发布、服务调用
- **ZMQ客户端**: 基于PyZMQ的消息队列客户端，支持多种通信模式
- **配置管理**: 统一的配置管理系统，支持YAML/JSON配置文件
- **日志系统**: 功能丰富的日志系统，支持颜色输出、时间戳、消息长度限制
- **错误处理**: 完善的错误处理和自动重连机制

## 快速开始

```python
from lbrosclient import ROSBridgeClient, ZMQClient, Logger

# 创建ROSBridge客户端
ros_client = ROSBridgeClient()
ros_client.start()

# 创建ZMQ客户端
zmq_client = ZMQClient()
zmq_client.start()
```

更多使用示例请参考examples.py文件。
"""

# 读取版本信息
version = "1.0.0"
try:
    # 尝试从__init__.py读取版本
    init_file = this_directory / "lbrosclient" / "__init__.py"
    if init_file.exists():
        with open(init_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    version = line.split('=')[1].strip().strip('"\'')
                    break
except Exception:
    pass

# 读取依赖
requirements = [
    "roslibpy>=1.3.0",
    "pyzmq>=24.0.0",
    "PyYAML>=6.0",
    "colorama>=0.4.4",
]

# 开发依赖
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
    "sphinx>=5.0.0",
    "sphinx-rtd-theme>=1.0.0",
]

# 额外依赖组
extra_requirements = {
    "dev": dev_requirements,
    "test": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
    ],
    "docs": [
        "sphinx>=5.0.0",
        "sphinx-rtd-theme>=1.0.0",
    ],
    "all": dev_requirements,
}

setup(
    # 基本信息
    name="lbrosclient",
    version=version,
    description="一个功能强大的ROS和ZMQ客户端库，提供配置化管理和模块化封装",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # 作者信息
    author="liber",
    author_email="liberalcxl@gmail.com",
    maintainer="liber",
    maintainer_email="liberalcxl@gmail.com",
    
    # 项目信息
    url="https://github.com/yourusername/lbrosclient",
    download_url="https://github.com/yourusername/lbrosclient/archive/v{}.tar.gz".format(version),
    
    # 许可证
    license="MIT",
    
    # 包信息
    packages=find_packages(),
    package_dir={"": "."},
    
    # 包含的文件
    package_data={
        "lbrosclient": [
            "*.py",
            "*.yaml",
            "*.yml",
            "*.json",
            "*.md",
            "*.txt",
        ],
    },
    include_package_data=True,
    
    # 依赖
    install_requires=requirements,
    extras_require=extra_requirements,
    
    # Python版本要求
    python_requires=">=3.7",
    
    # 分类信息
    classifiers=[
        # 开发状态
        "Development Status :: 4 - Beta",
        
        # 目标用户
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        
        # 主题
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        
        # 许可证
        "License :: OSI Approved :: MIT License",
        
        # 支持的Python版本
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        
        # 操作系统
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    
    # 关键词
    keywords=[
        "ros", "rosbridge", "zmq", "zeromq", "messaging", "robotics", 
        "communication", "client", "websocket", "configuration", "logging"
    ],
    
    # 项目URL
    project_urls={
        "Bug Reports": "https://github.com/yourusername/lbrosclient/issues",
        "Source": "https://github.com/yourusername/lbrosclient",
        "Documentation": "https://lbrosclient.readthedocs.io/",
    },
    
    # 命令行工具（如果有的话）
    entry_points={
        "console_scripts": [
            # "lbrosclient=lbrosclient.cli:main",
        ],
    },
    
    # 其他选项
    zip_safe=False,
    platforms=["any"],
    
    # 测试套件
    test_suite="tests",
    
    # 构建选项
    options={
        "build_py": {
            "compile": True,
            "optimize": 1,
        },
        "bdist_wheel": {
            "universal": False,
        },
    },
)