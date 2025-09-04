# 量化交易系统 Docker 容器化方案

## 项目概述

此量化交易系统基于Vue.js 2前端和Python后端，使用Docker容器化技术实现快速部署和开发环境统一。

## 主要功能

1. **历史数据管理** - 查看和管理股票历史数据
2. **数据采集** - 从多种数据源采集股票数据
3. **模拟数据支持** - 内置模拟数据生成功能，无需真实数据源即可演示

## 目录结构

```
├── src/                     # 源代码目录
│   ├── models/              # Python后端模型和服务
│   │   ├── server.py        # Flask后端服务入口
│   ├── views/               # Vue.js前端视图组件
│   └── utils/               # 工具函数
├── data/                    # 数据目录，存放SQLite数据库
│   └── init_db.py           # 数据库初始化脚本
├── Dockerfile.frontend      # 前端Docker构建文件
├── Dockerfile.python        # Python后端Docker构建文件
├── docker-compose.yml       # Docker Compose配置文件
├── nginx.conf               # Nginx配置文件
├── requirements.txt         # Python依赖列表
├── .env                     # 环境变量配置文件
├── DOCKER_GUIDE.md          # Docker使用详细指南
└── README_DOCKER.md         # 本文件
```

## 快速开始

### 前提条件
- 已安装Docker和Docker Compose
- 已安装Node.js（开发环境需要）

### 开发环境启动

1. **启动前端开发服务器**
   ```bash
   npm install
   npm run serve
   ```

2. **启动Python后端服务**
   ```bash
   python src/models/server.py
   ```

### Docker环境启动

1. **使用Docker Compose启动所有服务**
   ```bash
   docker-compose up --build
   ```

2. **访问服务**
   - 前端应用: http://localhost:8080
   - Python后端: http://localhost:5000
   - SQLite数据库查看器: http://localhost:3000

## 关键API端点

- `/health` - 健康检查接口
- `/api/data/load` - 数据加载接口
- `/api/data/collect` - 数据采集接口

## 数据持久化

- 所有数据存储在`data`目录下的SQLite数据库中
- 该目录通过Docker卷挂载，确保数据持久化

## 环境变量配置

在`.env`文件中配置以下环境变量：
- `VUE_APP_API_URL` - 前端API请求的基础URL

## 模拟数据功能

系统内置模拟数据生成功能，即使在没有真实数据源的情况下也能正常展示示例数据。模拟数据包括股票的开盘价、最高价、最低价、收盘价和成交量。

## 注意事项

1. 开发环境中，前端和后端服务分别运行在不同的端口
2. Docker环境中，所有服务通过Docker Compose统一管理
3. 确保data目录有正确的读写权限
4. 首次启动时，系统会自动初始化数据库