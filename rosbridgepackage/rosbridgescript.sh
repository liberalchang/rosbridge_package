#!/bin/bash

# ROS Bridges 打包和启动脚本
# 支持多种操作模式：
# -c: 创建 tar.gz 压缩包
# -i: 安装 tar.gz 到 ~/mooe-core/
# -d: 创建 deb 安装包
# -f: 检查和安装功能
# 启动参数: --foxglove, --rosbridge, --zmq

set -e

# 显示帮助信息
show_help() {
    echo "ROS Bridges 打包和启动工具"
    echo "用法:"
    echo "  $0 -c <install路径>                    # 创建 tar.gz 压缩包"
    echo "  $0 -i <tar.gz文件路径>                 # 安装 tar.gz 到 ~/mooe-core/"
    echo "  $0 -d <install路径>                    # 创建 deb 安装包"
    echo "  $0 -f                                  # 检查和安装功能"
    echo "  $0 -k                                  # 结束 rosbridgescript 进程及相关 launch"
    echo "  $0 -h|--help                          # 显示帮助信息"
    echo ""
    echo "启动参数（可任意组合）:"
    echo "  $0 --all                              # 启动所有服务"
    echo "  $0 --foxglove                         # 启动 foxglove bridge"
    echo "  $0 --rosbridge                        # 启动 rosbridge websocket"
    echo "  $0 --zmq                              # 启动 swarm ros bridge"
    echo "  $0 --foxglove --rosbridge             # 启动 foxglove 和 rosbridge"
    echo ""
    echo "示例:"
    echo "  $0 -c ~/mooe-core/install"
    echo "  $0 -i rosbridges.tar.gz"
    echo "  $0 -d ~/mooe-core/install"
    echo "  $0 -f"
    echo "  $0 -k"
    echo "  $0 --all"
    echo "  $0 --foxglove --zmq"
}

# 创建 tar.gz 压缩包
create_tarball() {
    local install_path="$1"

    if [ ! -d "$install_path" ]; then
        echo "错误: 安装路径 '$install_path' 不存在"
        exit 1
    fi

    # 检查必要的目录是否存在
    for dir in include lib share; do
        if [ ! -d "$install_path/$dir" ]; then
            echo "警告: 目录 '$install_path/$dir' 不存在，跳过"
        fi
    done

    local work_dir="$(pwd)"
    local tarball_name="rosbridges$(date +%Y%m%d).tar.gz"
    local tarball_path="$work_dir/$tarball_name"

    echo "正在创建压缩包: $tarball_name"
    echo "源路径: $install_path"
    echo "保存路径: $tarball_path"

    cd "$install_path"

    # 只打包存在的目录
    local dirs_to_pack=()
    for dir in include lib share; do
        if [ -d "$dir" ]; then
            dirs_to_pack+=("$dir/")
        fi
    done

    if [ ${#dirs_to_pack[@]} -eq 0 ]; then
        echo "错误: 没有找到 include、lib 或 share 目录"
        exit 1
    fi

    tar -czvf "$tarball_path" "${dirs_to_pack[@]}"

    echo "压缩包创建成功: $tarball_path"
    echo "文件大小: $(du -h "$tarball_path" | cut -f1)"
}

# 安装 tar.gz 到 ~/mooe-core/
install_tarball() {
    local tarball_path="$1"

    # 转换为绝对路径
    if [[ "$tarball_path" != /* ]]; then
        tarball_path="$(pwd)/$tarball_path"
    fi

    if [ ! -f "$tarball_path" ]; then
        echo "错误: 压缩包文件 '$tarball_path' 不存在"
        echo "当前工作目录: $(pwd)"
        echo "请检查文件路径是否正确"
        exit 1
    fi

    local target_dir="$HOME/mooe-core"

    echo "正在安装压缩包: $tarball_path"
    echo "目标路径: $target_dir"

    # 创建目标目录
    mkdir -p "$target_dir"

    # 解压到目标目录
    cd "$target_dir"
    tar -xzvf "$tarball_path"

    echo "安装完成！"
    echo "文件已解压到: $target_dir"

    # 显示安装的内容
    echo ""
    echo "安装的内容:"
    for dir in include lib share; do
        if [ -d "$target_dir/$dir" ]; then
            echo "  $dir/: $(find "$target_dir/$dir" -type f | wc -l) 个文件"
        fi
    done
}

# 检查和安装功能
check_and_install() {
    echo "正在检查 ROS Bridges 组件..."
    
    # 定义需要检查的文件
    local foxglove_launch="/home/muyi/mooe-core/share/foxglove_bridge/launch/foxglove_bridge.launch"
    local rosbridge_launch="/home/muyi/mooe-core/share/rosbridge_server/launch/rosbridge_websocket.launch"
    local swarm_launch="/home/muyi/mooe-core/share/swarm_ros_bridge/launch/swarm_ros_bridge.launch"
    
    local missing_files=()
    
    # 检查文件是否存在
    if [ ! -f "$foxglove_launch" ]; then
        echo "缺失: $foxglove_launch"
        missing_files+=("foxglove_bridge")
    else
        echo "存在: $foxglove_launch"
    fi
    
    if [ ! -f "$rosbridge_launch" ]; then
        echo "缺失: $rosbridge_launch"
        missing_files+=("rosbridge_server")
    else
        echo "存在: $rosbridge_launch"
    fi
    
    if [ ! -f "$swarm_launch" ]; then
        echo "缺失: $swarm_launch"
        missing_files+=("swarm_ros_bridge")
    else
        echo "存在: $swarm_launch"
    fi
    
    # 如果所有文件都存在，跳过安装
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "所有组件都已存在，跳过安装"
        return 0
    fi
    
    echo "发现 ${#missing_files[@]} 个缺失组件: ${missing_files[*]}"
    
    # 查找 deb 包
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local deb_file=$(find "$script_dir" -name "rosbridges*_amd64.deb" | head -1)
    
    if [ -z "$deb_file" ]; then
        echo "错误: 在脚本目录中未找到 rosbridges.*_amd64.deb 文件"
        echo "脚本目录: $script_dir"
        echo "请确保 deb 包存在于脚本同一目录下"
        exit 1
    fi
    
    echo "找到 deb 包: $deb_file"
    echo "正在安装依赖包..."
    
    # 先安装依赖包
    echo "安装 libzmq3-dev 和 libzmqpp-dev..."
    if ! sudo apt-get update && sudo apt-get install -y libzmq3-dev libzmqpp-dev; then
        echo "警告: 依赖包安装可能失败，继续尝试安装 deb 包"
    fi
    
    echo "正在覆盖安装..."
    
    # 覆盖安装 deb 包
    if sudo dpkg -i --force-overwrite "$deb_file"; then
        echo "deb 包安装成功"
        # 解决可能的依赖问题
        sudo apt-get install -f -y 2>/dev/null || true
        echo "安装完成！"
    else
        echo "错误: deb 包安装失败，尝试修复依赖后重新安装..."
        # 尝试修复依赖问题
        sudo apt-get install -f -y
        # 重新尝试安装
        if sudo dpkg -i --force-overwrite "$deb_file"; then
            echo "deb 包重新安装成功"
            echo "安装完成！"
        else
            echo "错误: deb 包安装最终失败"
            exit 1
        fi
    fi
}

# 创建 deb 安装包
create_deb() {
    local install_path="$1"

    if [ ! -d "$install_path" ]; then
        echo "错误: 安装路径 '$install_path' 不存在"
        exit 1
    fi

    local work_dir="$(pwd)"
    local deb_dir="$work_dir/rosbridges-deb"
    local version="0.1.0"
    local arch="amd64"
    local deps_dir="$deb_dir/var/cache/apt/archives"

    echo "正在创建 deb 包..."
    echo "源路径: $install_path"

    # 清理并创建打包目录
    rm -rf "$deb_dir"
    mkdir -p "$deb_dir/DEBIAN"
    mkdir -p "$deb_dir/home/muyi/mooe-core"
    mkdir -p "$deps_dir"

    # 下载依赖包到本地
    echo "正在下载依赖包..."
    local temp_deps_dir="$(mktemp -d)"
    cd "$temp_deps_dir"
    
    # 更新包列表并下载依赖包
    if apt-get update >/dev/null 2>&1; then
        echo "下载 libzmq3-dev 及其依赖..."
        apt-get download libzmq3-dev $(apt-cache depends --recurse --no-recommends --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances libzmq3-dev | grep "^\w" | sort -u) 2>/dev/null || true
        
        echo "下载 libzmqpp-dev 及其依赖..."
        apt-get download libzmqpp-dev $(apt-cache depends --recurse --no-recommends --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances libzmqpp-dev | grep "^\w" | sort -u) 2>/dev/null || true
        
        # 复制下载的deb包到打包目录
        if ls *.deb >/dev/null 2>&1; then
            cp *.deb "$deps_dir/"
            echo "已下载 $(ls *.deb | wc -l) 个依赖包"
        else
            echo "警告: 未能下载到依赖包，将使用在线安装方式"
        fi
    else
        echo "警告: 无法更新包列表，跳过依赖包下载"
    fi
    
    cd "$work_dir"
    rm -rf "$temp_deps_dir"

    # 复制文件
    for dir in include lib share; do
        if [ -d "$install_path/$dir" ]; then
            echo "复制 $dir/ ..."
            cp -r "$install_path/$dir" "$deb_dir/home/muyi/mooe-core/"
        else
            echo "警告: 目录 '$install_path/$dir' 不存在，跳过"
        fi
    done

    # 创建 control 文件
    cat > "$deb_dir/DEBIAN/control" << EOF
Package: rosbridges
Version: $version
Section: misc
Priority: optional
Architecture: $arch
Conflicts: rosbridges
Replaces: rosbridges
Provides: rosbridges
Maintainer: liber <libercxl@gmail.com>
Description: ROS Bridges Package
 This package provides bridges for ROS communication including rosbridge_suite,
 roslibpy, swarm_ros_bridge and rosbridges components.
 Includes headers, libraries, and configuration files.
 Replaces the previous rosbridges package.
 Includes bundled dependencies: libzmq3-dev, libzmqpp-dev
EOF

    # 创建 preinst 脚本（解包前处理冲突）
    cat > "$deb_dir/DEBIAN/preinst" << 'EOF'
#!/bin/bash
set -e

# 检查并处理冲突包
if dpkg -l foxglove-bridge 2>/dev/null | grep -q "^ii"; then
    echo "检测到冲突包 foxglove-bridge，正在移除..."
    dpkg --remove --force-remove-reinstreq foxglove-bridge 2>/dev/null || true
    dpkg --purge foxglove-bridge 2>/dev/null || true
fi

# 清理可能的残留文件
if [ -d "/home/muyi/mooe-core" ]; then
    echo "清理可能的冲突文件..."
    find /home/muyi/mooe-core -name "*foxglove*" -type f -delete 2>/dev/null || true
fi
EOF

    # 创建 prerm 脚本（卸载时清理）
    cat > "$deb_dir/DEBIAN/prerm" << 'EOF'
#!/bin/bash
# 卸载时的清理工作
echo "正在准备卸载 rosbridges..."
EOF

    # 创建 postinst 脚本
    cat > "$deb_dir/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# 检查并安装依赖包
echo "检查依赖包..."

# 本地依赖包目录
DEPS_DIR="/var/cache/apt/archives"

# 安装本地依赖包函数
install_local_deps() {
    if [ -d "$DEPS_DIR" ] && [ "$(ls -A $DEPS_DIR/*.deb 2>/dev/null | wc -l)" -gt 0 ]; then
        echo "发现本地依赖包，正在安装..."
        # 先安装所有依赖包
        dpkg -i "$DEPS_DIR"/*.deb 2>/dev/null || true
        # 修复可能的依赖问题
        apt-get install -f -y 2>/dev/null || true
        return 0
    fi
    return 1
}

# 检查 libzmq3-dev
if ! dpkg -l | grep -q "^ii.*libzmq3-dev"; then
    echo "安装 libzmq3-dev..."
    if ! install_local_deps; then
        echo "使用在线方式安装 libzmq3-dev..."
        if ! apt-get update && apt-get install -y libzmq3-dev; then
            echo "警告: libzmq3-dev 安装失败，请手动安装"
        fi
    fi
else
    echo "libzmq3-dev 已安装"
fi

# 检查 libzmqpp-dev
if ! dpkg -l | grep -q "^ii.*libzmqpp-dev"; then
    echo "安装 libzmqpp-dev..."
    if ! install_local_deps; then
        echo "使用在线方式安装 libzmqpp-dev..."
        if ! apt-get update && apt-get install -y libzmqpp-dev; then
            echo "警告: libzmqpp-dev 安装失败，请手动安装"
        fi
    fi
else
    echo "libzmqpp-dev 已安装"
fi

# 确保用户目录存在
mkdir -p "/home/muyi/mooe-core/"

# 修复权限
if id "muyi" >/dev/null 2>&1; then
    chown -R "muyi:muyi" "/home/muyi/mooe-core/"
fi

# 添加环境变量到用户的 .bashrc
if [ -f "/home/muyi/.bashrc" ]; then
    if ! grep -q "mooe-core.*setup.bash" "/home/muyi/.bashrc"; then
        echo "# ROS Bridges environment" >> "/home/muyi/.bashrc"
        echo "if [ -f \"\$HOME/mooe-core/setup.bash\" ]; then" >> "/home/muyi/.bashrc"
        echo "    source \"\$HOME/mooe-core/setup.bash\"" >> "/home/muyi/.bashrc"
        echo "fi" >> "/home/muyi/.bashrc"
    fi
fi
EOF

    # 添加执行权限
    chmod +x "$deb_dir/DEBIAN/preinst"
    chmod +x "$deb_dir/DEBIAN/prerm"
    chmod +x "$deb_dir/DEBIAN/postinst"

    # 计算 md5sums
    cd "$deb_dir"
    find . -type f ! -path './DEBIAN/*' -exec md5sum {} + > DEBIAN/md5sums
    cd "$work_dir"

    # 构建 deb 包
    local deb_name="rosbridges_${version}_${arch}.deb"
    dpkg-deb --build "$deb_dir" "$deb_name"

    # 清理临时目录
    rm -rf "$deb_dir"

    echo "deb 包创建成功: $(pwd)/$deb_name"
    echo "文件大小: $(du -h "$deb_name" | cut -f1)"
    echo ""
    echo "安装说明:"
    echo "此 deb 包已包含所需依赖包 (libzmq3-dev, libzmqpp-dev)，支持离线安装。"
    echo ""
    echo "1. 直接安装 deb 包 (推荐):"
    echo "   sudo dpkg -i $deb_name"
    echo "   # 安装过程会自动处理依赖包"
    echo ""
    echo "2. 使用 apt 安装:"
    echo "   sudo apt install ./$deb_name"
    echo ""
    echo "3. 如果在无网络环境下安装失败，可手动安装依赖:"
    echo "   # 依赖包已打包在 deb 中，通常会自动安装"
    echo "   # 如有问题可运行: sudo apt-get install -f"
    echo ""
    echo "4. 或使用脚本自动安装:"
    echo "   $0 -f"
}

# 结束 rosbridgescript 进程及相关 launch
kill_processes() {
    echo "正在查找并结束 rosbridgescript 相关进程..."
    
    # 查找并结束 rosbridgescript.sh 进程（排除当前进程）
    local script_pids=$(pgrep -f "rosbridgescript.sh" | grep -v $$)
    if [ -n "$script_pids" ]; then
        echo "找到 rosbridgescript.sh 进程: $script_pids"
        kill $script_pids 2>/dev/null || true
        sleep 1
        # 强制结束仍在运行的进程
        kill -9 $script_pids 2>/dev/null || true
    else
        echo "未找到运行中的 rosbridgescript.sh 进程"
    fi
    
    # 查找并结束相关的 roslaunch 进程
    local launch_processes=("foxglove_bridge" "rosbridge_server" "swarm_ros_bridge")
    for process in "${launch_processes[@]}"; do
        local pids=$(pgrep -f "$process")
        if [ -n "$pids" ]; then
            echo "找到 $process 进程: $pids"
            kill $pids 2>/dev/null || true
            sleep 1
            # 强制结束仍在运行的进程
            kill -9 $pids 2>/dev/null || true
        fi
    done
    
    echo "进程清理完成"
    echo
}

# 启动 ROS Bridges 服务
launch_ros_bridges() {
    local foxglove=0
    local rosbridge=0
    local zmq=0
    
    # 解析启动参数
    for arg in "$@"; do
        case "$arg" in
            --all)
                foxglove=1
                rosbridge=1
                zmq=1
                echo "启动所有 ROS Bridges 服务..."
                ;;
            --foxglove)
                foxglove=1
                ;;
            --rosbridge)
                rosbridge=1
                ;;
            --zmq)
                zmq=1
                ;;
            *)
                echo "错误: 未知启动参数 '$arg'"
                echo "支持的参数: --all, --foxglove, --rosbridge, --zmq"
                exit 1
                ;;
        esac
    done
    
    # 检查 ROS 环境
    if ! command -v roslaunch &> /dev/null; then
        echo "错误: 未找到 roslaunch 命令，请确保 ROS 环境已正确设置"
        exit 1
    fi
    
    # 启动服务（并行启动）
    local pids=()
    
    if [ $foxglove -eq 1 ]; then
        echo "启动 foxglove_bridge..."
        roslaunch foxglove_bridge foxglove_bridge.launch &
        pids+=($!)
        sleep 2
    fi
    
    if [ $rosbridge -eq 1 ]; then
        echo "启动 rosbridge_server..."
        roslaunch rosbridge_server rosbridge_websocket.launch &
        pids+=($!)
        sleep 2
    fi
    
    if [ $zmq -eq 1 ]; then
        echo "启动 swarm_ros_bridge..."
        roslaunch swarm_ros_bridge swarm_ros_bridge.launch &
        pids+=($!)
        sleep 2
    fi
    
    if [ ${#pids[@]} -eq 0 ]; then
        echo "错误: 没有指定要启动的服务"
        exit 1
    fi
    
    echo "所有服务已启动，进程 ID: ${pids[*]}"
    echo "按 Ctrl+C 停止所有服务"
    
    # 等待所有进程
    trap 'echo "正在停止所有服务..."; kill ${pids[*]} 2>/dev/null; exit 0' INT TERM
    wait
}

# 主程序
main() {
    case "$1" in
        -c)
            if [ -z "$2" ]; then
                echo "错误: 请指定 install 路径"
                echo "用法: $0 -c <install路径>"
                exit 1
            fi
            create_tarball "$2"
            ;;
        -i)
            if [ -z "$2" ]; then
                echo "错误: 请指定 tar.gz 文件路径"
                echo "用法: $0 -i <tar.gz文件路径>"
                exit 1
            fi
            install_tarball "$2"
            ;;
        -d)
            if [ -z "$2" ]; then
                echo "错误: 请指定 install 路径"
                echo "用法: $0 -d <install路径>"
                exit 1
            fi
            create_deb "$2"
            ;;
        -f)
            check_and_install
            ;;
        -k)
            kill_processes
            ;;
        -h|--help)
            show_help
            ;;
        --all|--foxglove|--rosbridge|--zmq)
            launch_ros_bridges "$@"
            ;;
        *)
            echo "错误: 未知选项 '$1'"
            show_help
            exit 1
            ;;
    esac
}

# 检查参数并执行相应功能
if [ $# -eq 0 ]; then
    # 无参数时显示帮助信息
    show_help
else
    # 检查是否全部为启动参数
    all_launch_params=true
    for arg in "$@"; do
        case "$arg" in
            --all|--foxglove|--rosbridge|--zmq)
                ;;
            *)
                all_launch_params=false
                break
                ;;
        esac
    done
    
    if [ "$all_launch_params" = true ]; then
        # 全部为启动参数，直接启动
        launch_ros_bridges "$@"
    else
        # 包含其他参数，调用主程序
        main "$@"
    fi
fi
