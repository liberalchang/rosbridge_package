# ROS客户端使用说明

## 概述

这个目录包含两个配置化的ROS客户端实现：
- **ZMQ客户端**: 使用ZeroMQ进行直接通信，支持Protobuf优化
- **ROSLibPy客户端**: 使用ROSBridge进行WebSocket通信

两个客户端都支持通过YAML配置文件灵活配置网络参数、话题设置和传输选项，避免硬编码。

## 功能特性

- **配置文件驱动**: 所有参数通过YAML配置文件管理，支持运行时指定配置文件
- **多话题支持**: 可配置多个订阅和发布话题
- **性能优化**: 支持Protobuf传输格式，自动降级到JSON
- **灵活的日志**: 可配置时间戳显示、格式和详细程度
- **错误处理**: 完善的异常处理和自动重试机制
- **命令行接口**: 支持命令行参数指定配置文件

## 文件结构

```
rosclient/
├── zmq_client.py         # 配置化ZMQ客户端
├── roslibpy_client.py    # 配置化ROSLibPy客户端
├── zmq_config.yaml       # ZMQ客户端配置文件
├── roslibpy_config.yaml  # ROSLibPy客户端配置文件
├── requirements.txt      # Python依赖列表
└── README.md            # 使用说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置文件说明

### ZMQ客户端配置 (zmq_config.yaml)

```yaml
# 网络配置
network:
  local:
    ip: "10.10.19.15"     # 本地IP地址
    send_port: 5556       # 本地发送端口
  ros1_server:
    ip: "10.10.16.233"    # ROS1服务器IP
    receive_port: 5555    # 接收端口

# 话题配置
topics:
  subscribe:              # 订阅的话题列表
    - "/server_time_now"
    - "/move_base_node/cross_v2_response"
  publish:
    test_topic:
      name: "/test"        # 发布话题名
      content: "test"      # 消息内容
      frequency: 1.0       # 发布频率(Hz)

# 传输配置
transport:
  prefer_protobuf: true   # 优先使用Protobuf
  zmq:
    receive_timeout: 1000 # 接收超时(ms)
    connection_wait: 2    # 连接等待时间(s)
    retry_interval: 0.1   # 重试间隔(s)

# 日志配置
logging:
  show_timestamp: true
  timestamp_format: "%Y-%m-%d %H:%M:%S.%f"
  show_transport_format: true
  show_connection_details: true

# 性能配置
performance:
  main_loop_sleep: 1.0    # 主循环休眠时间(s)
  send_interval: 1.0      # 发送间隔(s)
```

### ROSLibPy客户端配置 (roslibpy_config.yaml)

```yaml
# ROSBridge连接配置
rosbridge:
  default:
    host: "192.168.1.101"       # 默认ROSBridge服务器
    port: 9090                  # 默认端口
  local:
    host: "localhost"           # 本地服务器
    port: 9090                  # 本地端口
  connection_timeout: 10        # 连接超时(秒)
  retry_interval: 5            # 重试间隔(秒)

# 话题配置
topics:
  subscribe:
    - name: "/server_time"       # 订阅话题
      type: "std_msgs/String"
    - name: "/move_base/result"
      type: "move_base_msgs/MoveBaseActionResult"
  publish:
    name: "/test_topic"          # 发布话题
    type: "std_msgs/String"
    content: "Hello from ROSLibPy!"
    frequency: 1.0              # 发布频率(Hz)

# 网络检查配置
network_check:
  enabled: true               # 启用网络检查
  timeout: 5                  # 检查超时(秒)

# 日志配置
logging:
  show_timestamps: true       # 显示时间戳
  show_connection_status: true # 显示连接状态
  show_message_content: true  # 显示消息内容
  max_message_length: 200     # 最大消息长度

# 性能配置
performance:
  main_loop_sleep: 0.1        # 主循环休眠时间(秒)

# 错误处理配置
error_handling:
  auto_reconnect: true        # 自动重连
  max_reconnect_attempts: 5   # 最大重连次数

# 调试配置
debug:
  enabled: false             # 启用调试模式
```

## 使用方法

### ZMQ客户端

```bash
# 使用默认配置文件 (zmq_config.yaml)
python zmq_client.py

# 指定配置文件
python zmq_client.py --config my_zmq_config.yaml
python zmq_client.py -c my_zmq_config.yaml
```

### ROSLibPy客户端

```bash
# 使用默认配置文件 (roslibpy_config.yaml)
python roslibpy_client.py

# 指定配置文件
python roslibpy_client.py --config my_roslibpy_config.yaml
python roslibpy_client.py -c my_roslibpy_config.yaml

# 使用本地模式 (localhost:9090)
python roslibpy_client.py --local
```

### 命令行参数

- `--config, -c`: 指定配置文件路径 (默认: config.yaml)
- `--help, -h`: 显示帮助信息

### 运行示例

#### ZMQ客户端示例

```bash
$ python zmq_client.py
=== ZMQ客户端用于ROS消息通信 (配置化版本) ===
配置文件: zmq_config.yaml
Protobuf支持: 可用
============================================================
配置文件加载成功: C:\...\rosclient\zmq_config.yaml
ZMQ客户端已初始化 (Windows IP: 10.10.19.15)
从以下地址接收消息: 10.10.16.233:5555
监听话题: /server_time_now, /move_base_node/cross_v2_response
发布/test话题到端口5556
传输格式: Protobuf

当前配置:
  本地IP: 10.10.19.15
  ROS1服务器: 10.10.16.233:5555
  发送端口: 5556
  订阅话题: /server_time_now, /move_base_node/cross_v2_response
  发布话题: /test (1.0Hz)
  传输格式: Protobuf
============================================================
正在启动ZMQ客户端...
所有线程已启动。按Ctrl+C停止。
等待连接建立...
[2024-01-15 10:30:15.123] 发送/test: test (格式: Protobuf)
[2024-01-15 10:30:16.124] 接收到/server_time_now: {...}
```

#### ROSLibPy客户端示例

```bash
$ python roslibpy_client.py
=== ROSLibPy客户端用于ROS消息通信 (配置化版本) ===
配置文件: roslibpy_config.yaml
连接目标: 192.168.1.101:9090
订阅话题: ['/server_time', '/move_base/result']
发布话题: /test_topic (1.0 Hz)
日志详细程度: 高
自动重连: 启用 (最多5次)
============================================================
[2024-01-15 10:30:15] 网络连通性检查通过
[2024-01-15 10:30:15] 正在连接到ROSBridge服务器...
[2024-01-15 10:30:15] 成功连接到ROSBridge
[2024-01-15 10:30:16] 收到消息 [/server_time]: 2024-01-15 10:30:16
[2024-01-15 10:30:17] 发布消息 [/test_topic]: Hello from ROSLibPy!
```

## 配置参数详解

### ZMQ客户端参数

#### 网络配置 (network)
- `local.ip`: 本地Windows客户端IP地址
- `local.send_port`: 本地发送消息的端口
- `ros1_server.ip`: ROS1服务器IP地址
- `ros1_server.receive_port`: 从ROS1服务器接收消息的端口

#### 话题配置 (topics)
- `subscribe`: 要订阅的话题列表
- `publish.test_topic.name`: 发布的话题名称
- `publish.test_topic.content`: 发布的消息内容
- `publish.test_topic.frequency`: 发布频率(Hz)

#### 传输配置 (transport)
- `prefer_protobuf`: 是否优先使用Protobuf格式
- `zmq.receive_timeout`: ZMQ接收超时时间(毫秒)
- `zmq.connection_wait`: 连接建立等待时间(秒)
- `zmq.retry_interval`: 错误重试间隔(秒)

#### 日志配置 (logging)
- `show_timestamp`: 是否显示时间戳
- `timestamp_format`: 时间戳格式
- `show_transport_format`: 是否显示传输格式信息
- `show_connection_details`: 是否显示详细连接信息

#### 性能配置 (performance)
- `main_loop_sleep`: 主循环休眠时间(秒)
- `send_interval`: 发送消息间隔(秒)

### ROSLibPy客户端参数

#### ROSBridge连接配置 (rosbridge)
- `default.host`: 默认ROSBridge服务器地址
- `default.port`: 默认ROSBridge服务器端口
- `local.host`: 本地ROSBridge服务器地址
- `local.port`: 本地ROSBridge服务器端口
- `connection_timeout`: 连接超时时间(秒)
- `retry_interval`: 重试间隔时间(秒)

#### 话题配置 (topics)
- `subscribe`: 订阅话题列表，包含name和type
- `publish.name`: 发布话题名称
- `publish.type`: 发布话题消息类型
- `publish.content`: 发布消息内容
- `publish.frequency`: 发布频率(Hz)

#### 网络检查配置 (network_check)
- `enabled`: 是否启用网络连通性检查
- `timeout`: 网络检查超时时间(秒)

#### 日志配置 (logging)
- `show_timestamps`: 是否显示时间戳
- `show_connection_status`: 是否显示连接状态
- `show_message_content`: 是否显示消息内容
- `max_message_length`: 最大消息显示长度

#### 性能配置 (performance)
- `main_loop_sleep`: 主循环休眠时间(秒)

#### 错误处理配置 (error_handling)
- `auto_reconnect`: 是否启用自动重连
- `max_reconnect_attempts`: 最大重连尝试次数

#### 调试配置 (debug)
- `enabled`: 是否启用调试模式

## 故障排除

### ZMQ客户端常见问题

1. **配置文件未找到**
   - 确保配置文件存在于指定路径
   - 使用绝对路径或相对于脚本的路径

2. **连接失败**
   - 检查网络配置中的IP地址和端口
   - 确保ROS1服务器正在运行
   - 检查防火墙设置

3. **Protobuf不可用**
   - 安装protobuf: `pip install protobuf>=4.21.0`
   - 系统会自动降级到JSON格式

4. **YAML解析错误**
   - 检查YAML语法是否正确
   - 确保缩进使用空格而非制表符

### ROSLibPy客户端常见问题

1. **ROSBridge连接失败**
   - 确认ROSBridge服务器是否运行
   - 检查WebSocket端口(默认9090)是否开放
   - 验证网络连通性

2. **话题订阅失败**
   - 检查话题名称是否正确
   - 确认消息类型是否匹配
   - 验证ROS节点是否发布该话题

3. **自动重连问题**
   - 检查`auto_reconnect`配置
   - 调整`max_reconnect_attempts`参数
   - 确认网络稳定性

4. **配置文件错误**
   - 验证YAML语法
   - 检查roslibpy_config.yaml路径
   - 确认所有必需参数存在

### 调试技巧

#### ZMQ客户端调试

1. **启用详细日志**
   ```yaml
   logging:
     show_timestamp: true
     show_transport_format: true
     show_connection_details: true
   ```

2. **调整超时设置**
   ```yaml
   transport:
     zmq:
       receive_timeout: 5000  # 增加超时时间
       connection_wait: 5     # 增加连接等待时间
   ```

3. **测试网络连接**
   ```bash
   # 测试端口连通性
   telnet 10.10.16.233 5555
   ```

#### ROSLibPy客户端调试

1. **启用调试模式**
   ```yaml
   debug:
     enabled: true
   logging:
     show_timestamps: true
     show_connection_status: true
     show_message_content: true
   ```

2. **测试ROSBridge连接**
   ```bash
   # 测试WebSocket连接
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://192.168.1.101:9090
   ```

3. **网络连通性检查**
   ```yaml
   network_check:
     enabled: true
     timeout: 5
   ```

4. **调整重连参数**
   ```yaml
   error_handling:
     auto_reconnect: true
     max_reconnect_attempts: 10
   rosbridge:
     retry_interval: 3
   ```

## 扩展配置示例

### ZMQ客户端扩展配置

#### 添加新的订阅话题

```yaml
topics:
  subscribe:
    - "/server_time_now"
    - "/move_base_node/cross_v2_response"
    - "/new_topic"  # 添加新话题
```

#### 修改发布频率

```yaml
topics:
  publish:
    test_topic:
      frequency: 10.0  # 改为10Hz
```

#### 自定义消息内容

```yaml
topics:
  publish:
    test_topic:
      content: "custom_message"  # 自定义内容
```

#### 多话题订阅配置

```yaml
topics:
  subscribe:
    - "/robot/pose"
    - "/robot/velocity"
    - "/sensor/laser"
    - "/camera/image"
  publish:
    test_topic:
      name: "/robot/cmd_vel"
      content: "move_command"
      frequency: 10.0
```

#### 高性能配置

```yaml
transport:
  prefer_protobuf: true
  zmq:
    receive_timeout: 1000
    retry_interval: 0.01

performance:
  main_loop_sleep: 0.01
  send_interval: 0.1

logging:
  show_timestamp: false
  show_transport_format: false
```

### ROSLibPy客户端扩展配置

#### 多话题订阅配置

```yaml
topics:
  subscribe:
    - name: "/robot/pose"
      type: "geometry_msgs/PoseStamped"
    - name: "/robot/velocity"
      type: "geometry_msgs/Twist"
    - name: "/sensor/laser"
      type: "sensor_msgs/LaserScan"
    - name: "/camera/image"
      type: "sensor_msgs/Image"
  publish:
    name: "/robot/cmd_vel"
    type: "geometry_msgs/Twist"
    content: '{"linear": {"x": 0.5, "y": 0, "z": 0}, "angular": {"x": 0, "y": 0, "z": 0.1}}'
    frequency: 10.0
```

#### 生产环境配置

```yaml
rosbridge:
  default:
    host: "production-server.local"
    port: 9090
  connection_timeout: 30
  retry_interval: 10

network_check:
  enabled: true
  timeout: 10

logging:
  show_timestamps: true
  show_connection_status: true
  show_message_content: false
  max_message_length: 100

performance:
  main_loop_sleep: 0.05

error_handling:
  auto_reconnect: true
  max_reconnect_attempts: 20

debug:
  enabled: false
```

#### 开发调试配置

```yaml
rosbridge:
  local:
    host: "localhost"
    port: 9090
  connection_timeout: 5
  retry_interval: 2

logging:
  show_timestamps: true
  show_connection_status: true
  show_message_content: true
  max_message_length: 500

performance:
  main_loop_sleep: 0.1

error_handling:
  auto_reconnect: true
  max_reconnect_attempts: 3

debug:
  enabled: true
```

## 技术特性

### 共同特性

- **配置化设计**: 所有参数通过YAML文件配置，支持运行时指定
- **错误处理**: 完善的异常处理和重试机制
- **日志系统**: 可配置的日志输出，支持时间戳
- **跨平台**: 支持Windows/Linux/macOS
- **扩展性**: 易于添加新的话题和功能
- **性能优化**: 可调节的循环间隔和超时参数

### ZMQ客户端特性

- **Protobuf优化**: 支持Protobuf序列化，提升传输效率
- **直接通信**: 使用ZeroMQ进行点对点通信
- **低延迟**: 适合实时性要求高的应用
- **自定义协议**: 支持自定义消息格式
- **线程安全**: 使用独立线程处理接收和发送
- **优雅关闭**: 支持Ctrl+C安全停止
- **资源管理**: 自动清理ZMQ资源

### ROSLibPy客户端特性

- **标准兼容**: 完全兼容ROS标准消息类型
- **WebSocket通信**: 使用ROSBridge进行WebSocket通信
- **动态话题**: 支持运行时动态订阅和发布话题
- **网络检查**: 内置网络连通性检查功能
- **自动重连**: 智能重连机制，提高连接稳定性
- **消息类型验证**: 自动验证ROS消息类型
- **调试模式**: 丰富的调试信息输出
- **配置验证**: 自动加载默认配置作为备用