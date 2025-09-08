# lbrosclient

一个功能强大的ROS和ZMQ客户端库，提供配置化管理和模块化封装。

## 特性

### 🚀 核心功能
- **ROSBridge客户端**: 基于roslibpy的WebSocket客户端，支持话题订阅、发布、服务调用
- **ZMQ客户端**: 基于PyZMQ的消息队列客户端，支持REQ/REP、PUB/SUB、PUSH/PULL等多种通信模式
- **配置管理**: 统一的配置管理系统，支持YAML/JSON配置文件和运行时配置
- **日志系统**: 功能丰富的日志系统，支持颜色输出、时间戳、消息长度限制
- **错误处理**: 完善的错误处理和自动重连机制

### 🛠 技术特点
- **模块化设计**: 各组件独立封装，易于扩展和维护
- **配置驱动**: 支持外部配置文件，无需修改代码即可调整行为
- **类型提示**: 完整的类型注解，提供更好的IDE支持
- **上下文管理**: 支持with语句，自动管理资源
- **线程安全**: 支持多线程环境下的安全使用

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/lbrosclient.git
cd lbrosclient

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install .

# 或者开发模式安装
pip install -e .
```

### 使用pip安装（如果已发布到PyPI）

```bash
pip install lbrosclient

# 离线安装
pip install --upgrade --force-reinstall whl路径
```

### 依赖要求

- Python >= 3.7
- roslibpy >= 1.3.0
- pyzmq >= 24.0.0
- PyYAML >= 6.0
- colorama >= 0.4.4

### 打包
```bash
python setup.py sdist bdist_wheel
```

## 快速开始

### 参数管理器

`ParamManager` 提供了统一的参数管理功能，支持ROSBridge、ZMQ客户端和网络相关的配置参数管理。支持JSON、YAML和INI三种配置文件格式。

#### 支持的配置文件格式

- **JSON格式** (.json): 结构化数据，易于程序处理
- **YAML格式** (.yaml, .yml): 人类可读，支持注释
- **INI格式** (.ini, .cfg, .conf): 传统配置格式，简单易用

```python
from lbrosclient import ParamManager

# 创建参数管理器
param_manager = ParamManager()

# 从不同格式的配置文件加载参数
param_manager.load_from_file("config.json")    # JSON格式
param_manager.load_from_file("config.yaml")    # YAML格式
param_manager.load_from_file("config.ini")     # INI格式

# 获取参数
host = param_manager.get_param('rosbridge', 'host')
port = param_manager.get_param('rosbridge', 'port')

# 设置参数
param_manager.set_param('rosbridge', 'host', '192.168.1.100')
param_manager.set_param('rosbridge', 'port', 9090)

# 批量更新参数
updates = {
    'connection_timeout': 15,
    'verbose': True
}
param_manager.update_rosbridge_config(updates)

# 保存参数到文件（格式由文件扩展名决定）
param_manager.save_to_file()
```

#### 配置文件示例

**JSON格式 (config.json):**
```json
{
  "ROSBridge": {
    "host": "localhost",
    "port": 9091,
    "connection_timeout": 10,
    "verbose": true
  },
  "ZMQ": {
    "host": "localhost",
    "port": 5555,
    "connection_timeout": 10,
    "message_format": "json"
  },
  "Network": {
    "connectivity_check_enabled": true,
    "connectivity_timeout": 5
  }
}
```

**YAML格式 (config.yaml):**
```yaml
ROSBridge:
  host: localhost
  port: 9091
  connection_timeout: 10
  verbose: true

ZMQ:
  host: localhost
  port: 5555
  connection_timeout: 10
  message_format: json

Network:
  connectivity_check_enabled: true
  connectivity_timeout: 5
```

**INI格式 (config.ini):**
```ini
[ROSBridge]
host = localhost
port = 9091
connection_timeout = 10
verbose = True

[ZMQ]
host = localhost
port = 5555
connection_timeout = 10
message_format = json

[Network]
connectivity_check_enabled = True
connectivity_timeout = 5
```

### ROSBridge客户端

```python
from lbrosclient import ROSBridgeClient, ParamManager, Logger

# 创建参数管理器和客户端
param_manager = ParamManager()
client = ROSBridgeClient(param_manager=param_manager)

# 动态配置连接参数（推荐方式）
client.set_host_port('192.168.1.100', 9090)

# 动态添加订阅话题
client.add_subscribe_topic(
    topic_key='odom',
    topic_name='/odom',
    message_type='nav_msgs/Odometry'
)

# 动态添加发布话题
client.add_publish_topic(
    topic_key='cmd_vel',
    topic_name='/cmd_vel',
    message_type='geometry_msgs/Twist',
    frequency=10.0
)

# 或者使用自定义配置
config = {
    'rosbridge': {
        'default': {
            'host': 'localhost',
            'port': 9090
        }
    }
}
client = ROSBridgeClient(config=config)

# 启动客户端
if client.start():
    print("客户端启动成功")
    
    # 订阅话题
    def message_callback(msg, topic_name):
        print(f"收到消息: {msg}")
    
    client.subscribe_topic('/test_topic', 'std_msgs/String', message_callback)
    
    # 创建发布者
    client.create_publisher('/output_topic', 'std_msgs/String')
    
    # 发布消息
    client.publish_message('/output_topic', {'data': 'Hello ROS!'})
    
    # 调用服务
    result = client.call_service('/my_service', 'my_package/MyService', {'input': 'test'})
    
    # 停止客户端
    client.stop()
```

### ZMQ客户端

```python
from lbrosclient import ZMQClient, ParamManager, Logger, LogLevel

# 创建参数管理器和日志器
param_manager = ParamManager()
logger = Logger(name="MyZMQ", min_level=LogLevel.INFO)

# 创建客户端
client = ZMQClient(param_manager=param_manager, logger=logger)

# 连接到远程主机（推荐方式）
success = client.connect_to_remote_host(
    host='192.168.1.100',
    port=5555,
    socket_type='req',  # 支持 'req', 'sub', 'push'
    socket_name='remote_server'
)

if success:
    print("成功连接到远程ZMQ服务器")
    
    # 发送请求并等待响应
    response = client.request_reply(
        'remote_server',
        {'command': 'get_status'},
        timeout=5.0
    )
    print(f"服务器响应: {response}")
    
    # 断开连接
    client.disconnect_from_host('remote_server')
else:
    print("连接远程服务器失败")

# 停止客户端
client.stop()
```

#### 传统方式（本地套接字）

```python
from lbrosclient import ZMQClient

# 使用上下文管理器
with ZMQClient() as client:
    # REQ/REP模式
    client.create_req_client('tcp://localhost:5555')
    response = client.request_reply('req_client', {'message': 'Hello'})
    print(f"收到回复: {response}")
    
    # PUB/SUB模式
    client.create_pub_server('tcp://*:5556')
    client.send_message('pub_server', {'topic': 'news', 'content': '新闻内容'})
```

### 日志系统

```python
from lbrosclient import Logger, LogLevel

# 创建日志器
logger = Logger(name="MyApp", min_level=LogLevel.DEBUG)

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 配置日志器
logger.configure({
    'show_timestamp': True,
    'enable_colors': True,
    'max_message_length': 100
})
```

## 配置文件

### ROSBridge配置示例

```yaml
# rosbridge_config.yaml
rosbridge:
  default:
    host: "10.10.12.233"
    port: 9091
  local:
    host: "localhost"
    port: 9090
  connection:
    timeout: 10
    retry_interval: 0.1
    max_retries: 3

topics:
  subscribe:
    server_time:
      name: "/server_time_now"
      message_type: "std_msgs/String"
      callback_name: "server_time_callback"
  publish:
    test_topic:
      name: "/test"
      message_type: "std_msgs/String"
      content: "test"
      frequency: 1.0

logging:
  verbose: true
  show_timestamp: true
  show_connection_status: true
  show_message_content: true
  max_message_length: 200

error_handling:
  auto_reconnect: true
  reconnect_interval: 5
  max_reconnect_attempts: -1
  continue_on_error: true
```

### ZMQ配置示例

```yaml
# zmq_config.yaml
zmq:
  default:
    host: "localhost"
    port: 5555
  socket:
    linger_time: 1000
    high_water_mark: 1000
    receive_timeout: 5000
    send_timeout: 5000

message:
  format: "json"  # json, string, bytes
  encoding: "utf-8"
  compression:
    enabled: false
    level: 6

patterns:
  req_client:
    enabled: true
    type: "req_client"
    endpoint: "tcp://localhost:5555"
    socket_name: "req_client"
  
  pub_server:
    enabled: true
    type: "pub_server"
    endpoint: "tcp://*:5556"
    socket_name: "pub_server"
```

## 高级用法

### 动态配置管理

```python
from lbrosclient import ROSBridgeClient, ZMQClient, ParamManager

# 创建参数管理器
param_manager = ParamManager()

# 1. 单个配置项更新
client = ROSBridgeClient(param_manager=param_manager)
client.update_config('rosbridge', 'connection_timeout', 15)
client.update_config('rosbridge', 'verbose', False)

# 2. 批量配置更新
updates = {
    'connection_timeout': 20,
    'main_loop_sleep': 0.05,
    'show_message_content': True
}
client.batch_update_config('rosbridge', updates)

# 3. 获取配置值
timeout = client.get_config_value('rosbridge', 'connection_timeout')
print(f"当前超时设置: {timeout}秒")

# 4. 动态话题管理
# 添加订阅话题
client.add_subscribe_topic('laser', '/scan', 'sensor_msgs/LaserScan')

# 添加发布话题
client.add_publish_topic('cmd', '/cmd_vel', 'geometry_msgs/Twist', frequency=20)

# 移除话题
client.remove_topic('laser', 'subscribe')
```

### 外部程序集成

```python
def setup_robot_client(robot_config):
    """根据外部配置设置机器人客户端"""
    param_manager = ParamManager()
    client = ROSBridgeClient(param_manager=param_manager)
    
    # 设置连接参数
    client.set_host_port(robot_config['ip'], robot_config['port'])
    
    # 动态添加话题
    for topic in robot_config['subscribe_topics']:
        client.add_subscribe_topic(
            topic_key=topic['key'],
            topic_name=topic['name'],
            message_type=topic['type']
        )
    
    for topic in robot_config['publish_topics']:
        client.add_publish_topic(
            topic_key=topic['key'],
            topic_name=topic['name'],
            message_type=topic['type'],
            frequency=topic.get('frequency', 1.0)
        )
    
    return client

# 使用示例
robot_config = {
    'ip': '192.168.1.100',
    'port': 9090,
    'subscribe_topics': [
        {'key': 'odom', 'name': '/odom', 'type': 'nav_msgs/Odometry'},
        {'key': 'scan', 'name': '/scan', 'type': 'sensor_msgs/LaserScan'}
    ],
    'publish_topics': [
        {'key': 'cmd', 'name': '/cmd_vel', 'type': 'geometry_msgs/Twist', 'frequency': 10}
    ]
}

client = setup_robot_client(robot_config)
client.start()
```

### 自定义回调函数

```python
class MyROSClient(ROSBridgeClient):
    def custom_callback(self, message, topic_name):
        # 自定义消息处理逻辑
        processed_data = self.process_message(message)
        self.logger.info(f"处理后的数据: {processed_data}")
    
    def process_message(self, message):
        # 实现具体的消息处理逻辑
        return message

# 使用自定义客户端
client = MyROSClient()
client.subscribe_topic('/sensor_data', 'sensor_msgs/LaserScan', client.custom_callback)
```

### 多线程使用

```python
import threading
from lbrosclient import ZMQClient

def worker_thread(client, worker_id):
    """工作线程函数"""
    client.create_req_client(f'tcp://localhost:{5555 + worker_id}')
    
    for i in range(10):
        request = {'worker_id': worker_id, 'request_id': i}
        response = client.request_reply('req_client', request)
        print(f"Worker {worker_id} 收到回复: {response}")

# 创建多个工作线程
threads = []
for i in range(3):
    client = ZMQClient()
    thread = threading.Thread(target=worker_thread, args=(client, i))
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()
```

### 配置管理

```python
# ConfigManager已被ParamManager替代，不再使用

# 创建配置管理器
config_manager = ConfigManager()

# 加载配置文件
config = config_manager.load_config('my_config.yaml')

# 验证配置
if config_manager.validate_config(config, 'rosbridge'):
    print("配置验证通过")

# 合并配置
default_config = ConfigManager.get_rosbridge_default_config()
custom_config = {'rosbridge': {'default': {'host': 'localhost'}}}
merged_config = config_manager.merge_configs(default_config, custom_config)

# 保存配置
config_manager.save_config(merged_config, 'output_config.yaml')
```

## API参考

### ROSBridgeClient

#### 主要方法

- `connect() -> bool`: 连接到ROSBridge服务器
- `disconnect()`: 断开连接
- `subscribe_topic(topic_name, message_type, callback) -> bool`: 订阅话题
- `unsubscribe_topic(topic_name) -> bool`: 取消订阅话题
- `create_publisher(topic_name, message_type) -> bool`: 创建发布者
- `publish_message(topic_name, message_data) -> bool`: 发布消息
- `call_service(service_name, service_type, request_data, timeout) -> dict`: 调用服务
- `start() -> bool`: 启动客户端
- `stop()`: 停止客户端

### ZMQClient

#### 主要方法

- `connect_to_remote_host(host, port, socket_type, socket_name) -> bool`: 连接到远程主机
- `disconnect_from_host(socket_name) -> bool`: 断开远程主机连接
- `create_socket(socket_type, socket_name) -> zmq.Socket`: 创建套接字
- `create_req_client(endpoint, socket_name) -> bool`: 创建REQ客户端
- `create_rep_server(endpoint, socket_name) -> bool`: 创建REP服务器
- `create_pub_server(endpoint, socket_name) -> bool`: 创建PUB发布者
- `create_sub_client(endpoint, socket_name, topics) -> bool`: 创建SUB订阅者
- `send_message(socket_name, data) -> bool`: 发送消息
- `receive_message(socket_name) -> Any`: 接收消息
- `request_reply(socket_name, request_data, timeout) -> Any`: 请求-回复
- `start() -> bool`: 启动客户端
- `stop()`: 停止客户端

### Logger

#### 主要方法

- `debug(message)`: 记录调试信息
- `info(message)`: 记录普通信息
- `warning(message)`: 记录警告信息
- `error(message)`: 记录错误信息
- `critical(message)`: 记录严重错误信息
- `configure(config)`: 配置日志器

### ConfigManager

#### 主要方法

- `load_config(config_path, default_config) -> dict`: 加载配置文件
- `save_config(config, config_path)`: 保存配置文件
- `validate_config(config, config_type) -> bool`: 验证配置
- `merge_configs(base_config, override_config) -> dict`: 合并配置
- `get_rosbridge_default_config() -> dict`: 获取ROSBridge默认配置
- `get_zmq_default_config() -> dict`: 获取ZMQ默认配置

## 示例项目

查看 `examples.py` 文件获取更多使用示例，包括：

- 基本用法示例
- 配置管理示例
- 错误处理示例
- 多线程使用示例
- 不同通信模式示例

## 开发

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/liberalchang/rosbridge_package.git
cd lbrosclient

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=lbrosclient --cov-report=html

# 运行特定测试
pytest tests/test_logger.py
```

### 代码格式化

```bash
# 格式化代码
black lbrosclient/

# 检查代码风格
flake8 lbrosclient/

# 类型检查
mypy lbrosclient/
```

### 构建文档

```bash
# 构建文档
cd docs
make html

# 查看文档
open _build/html/index.html
```

## 构建和发布

### 构建wheel包

```bash
# 安装构建工具
pip install build

# 构建包
python -m build

# 生成的文件在dist/目录下
ls dist/
# lbrosclient-1.0.0-py3-none-any.whl
# lbrosclient-1.0.0.tar.gz
```

### 安装本地构建的包

```bash
# 安装wheel包
pip install dist/lbrosclient-1.0.0-py3-none-any.whl

# 或者安装tar.gz包
pip install dist/lbrosclient-1.0.0.tar.gz
```

### 发布到PyPI（可选）

```bash
# 安装发布工具
pip install twine

# 检查包
twine check dist/*

# 发布到测试PyPI
twine upload --repository testpypi dist/*

# 发布到正式PyPI
twine upload dist/*
```

## 故障排除

### 常见问题

1. **连接失败**
   - 检查ROSBridge/ZMQ服务器是否运行
   - 验证主机地址和端口配置
   - 检查防火墙设置

2. **导入错误**
   - 确保已安装所有依赖
   - 检查Python版本兼容性
   - 验证包安装是否成功

3. **配置问题**
   - 检查配置文件格式
   - 验证配置文件路径
   - 使用默认配置进行测试

### 调试技巧

```python
# 启用详细日志
from lbrosclient import Logger, LogLevel

logger = Logger(name="Debug", min_level=LogLevel.DEBUG)
logger.configure({'verbose': True})

# 在客户端中使用调试日志器
client = ROSBridgeClient(logger=logger)
```

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 贡献指南

- 遵循现有代码风格
- 添加适当的测试
- 更新文档
- 确保所有测试通过

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0 (2024-01-XX)

- 初始版本发布
- ROSBridge客户端功能
- ZMQ客户端功能
- 配置管理系统
- 日志系统
- 完整的文档和示例

## 联系方式

- 作者: liber
- 邮箱: liberalcxl@gmail.com
- 项目链接: https://github.com/liberalchang/rosbridge_package.git

## 致谢

- [roslibpy](https://github.com/gramaziokohler/roslibpy) - ROS WebSocket通信
- [PyZMQ](https://github.com/zeromq/pyzmq) - ZeroMQ Python绑定
- [PyYAML](https://github.com/yaml/pyyaml) - YAML解析
- [colorama](https://github.com/tartley/colorama) - 跨平台彩色�