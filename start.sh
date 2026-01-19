#!/bin/bash

# NFO-XG 本地启动脚本 (macOS)

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 端口配置
PORT=8111

echo -e "${GREEN}=== NFO-XG 本地编辑器 ===${NC}"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 未找到虚拟环境 venv/${NC}"
    echo "请先创建虚拟环境："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}正在激活虚拟环境...${NC}"
source venv/bin/activate

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${RED}错误: 依赖未安装${NC}"
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

echo ""
echo -e "${GREEN}启动服务...${NC}"
echo -e "访问地址: ${GREEN}http://localhost:${PORT}${NC}"
echo ""

# 后台启动服务，然后打开浏览器
# 使用 macOS 的 open 命令打开默认浏览器
(sleep 2 && open "http://localhost:${PORT}") &

# 启动 uvicorn
cd web
python -m uvicorn app:app --host 0.0.0.0 --port $PORT --reload
