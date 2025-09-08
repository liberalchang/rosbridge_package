# 示例配置文件

本目录包含了 `lbrosclient` 模块的示例配置文件，支持 JSON、YAML 和 INI 三种格式。

## 文件说明

### ROSBridge 客户端配置
- `rosbridge_config.json` - JSON 格式的 ROSBridge 配置文件
- `rosbridge_config.yaml` - YAML 格式的 ROSBridge 配置文件（推荐，支持注释）
- `rosbridge_config.ini` - INI 格式的 ROSBridge 配置文件

### ZMQ 客户端配置
- `zmq_config.json` - JSON 格式的 ZMQ 配置文件
- `zmq_config.yaml` - YAML 格式的 ZMQ 配置文件（推荐，支持注释）
- `zmq_config.ini` - INI 格式的 ZMQ 配置文件

## 使用方法

### 1. 使用 ParamManager 加载配置

```python
from lbrosclient import ParamManager

# 创建参数管理器实例
param_manager = ParamManager()

# 加载 ROSBridge 配置
param_manager.load_from_file('example_configs/rosbridge_config.yaml')

# 加载 ZMQ 配置
param_manager.load_from_file('example_configs/zmq_config.yaml')
```

### 2. 直接在客户端中使用

```python
from lbrosclient import ROSBridgeClient, ZMQClient, ParamManager

# 使用 ROSBridge 客户端
param_manager = ParamManager()
param_manager.load_from_file('example_configs/rosbridge_config.yaml')
ros_client = ROSBridgeClient(param_manager=param_manager)

# 使用 ZMQ 客户端
param_manager = ParamManager()
param_manager.load_from_file('example_configs/zmq_config.yaml')
zmq_client = ZMQClient(param_manager=param_manager)
```

## 配置参数说明

### ROSBridge 配置参数

#### 连接配置
- `host`: ROSBridge 服务器地址（默认: localhost）
- `port`: ROSBridge 服务器端口（默认: 9091）
- `protocol`: 协议类型，ws 或 wss（默认: ws）
- `connection_timeout`: 连接超时时间，单位秒（默认: 10）
- `retry_interval`: 重试间隔，单位秒（默认: 0.1）
- `max_retries`: 最大重试次数（默认: 3）

#### WebSocket 配置
- `ping_interval`: ping 间隔，单位秒（默认: 30）
- `ping_timeout`: ping 超时，单位秒（默认: 10）
- `close_timeout`: 关闭超时，单位秒（默认: 10）
- `max_size`: 最大消息大小，单位字节（默认: 1048576）

#### 重连配置
- `auto_reconnect`: 是否自动重连（默认: true）
- `reconnect_interval`: 重连间隔，单位秒（默认: 5）
- `max_reconnect_attempts`: 最大重连次数，-1 表示无限制（默认: -1）

### ZMQ 配置参数

#### 端口配置
- `pub_port`: 发布端口（默认: 5555）
- `sub_port`: 订阅端口（默认: 5556）
- `req_port`: 请求端口（默认: 5557）
- `rep_port`: 响应端口（默认: 5558）
- `host`: ZMQ 服务器地址（默认: localhost）

#### Socket 配置
- `socket_timeout`: Socket 超时时间，单位毫秒（默认: 5000）
- `linger_time`: Socket 关闭等待时间，单位毫秒（默认: 1000）
- `high_water_mark`: 高水位标记，消息队列大小（默认: 1000）

#### 安全配置
- `security_enabled`: 是否启用安全认证（默认: false）
- `security_mechanism`: 安全机制，PLAIN/CURVE/GSSAPI（默认: PLAIN）
- `username`: 用户名（默认: 空）
- `password`: 密码（默认: 空）

### 通用配置参数

#### 日志配置
- `verbose`: 详细日志（默认: true）
- `show_connection_status`: 显示连接状态（默认: true）
- `show_message_content`: 显示消息内容（默认: true）
- `max_message_length`: 最大消息显示长度（默认: 200）

#### 性能配置
- `main_loop_sleep`: 主循环休眠时间，单位秒（默认: 0.1）
- `publish_sleep`: 发布休眠时间，单位秒（默认: 1.0）
- `message_processing_sleep`: 消息处理休眠时间，单位秒（默认: 0.01）

#### 消息配置
- `message_format`: 消息格式，json/string/bytes（默认: json）
- `encoding`: 编码格式（默认: utf-8）
- `compression_enabled`: 是否启用压缩（默认: false）
- `compression_level`: 压缩级别，1-9（默认: 6）

#### 网络配置
- `connectivity_check_enabled`: 是否启用连通性检查（默认: true）
- `connectivity_timeout`: 连通性检查超时，单位秒（默认: 5）

## 格式选择建议

- **YAML 格式**：推荐使用，支持注释，结构清晰，易于维护
- **JSON 格式**：适合程序化生成和解析，无注释支持
- **INI 格式**：传统配置格式，简单易用，适合简单配置

## 自定义配置

您可以基于这些示例文件创建自己的配置文件，只需修改相应的参数值即可。建议：

1. 复制示例文件到您的项目目录
2. 根据实际需求修改参数值
3. 使用 `ParamManager.load_from_file()` 加载配置
4. 通过 `ParamManager.save_to_file()` 保存修改后的配置