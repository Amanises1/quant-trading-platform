# 量化交易系统 Docker 使用指南

本指南详细介绍如何使用Docker容器化部署量化交易系统，实现开发环境统一、数据库协作和云服务器部署。

## 目录结构

```
├── Dockerfile.frontend       # 前端应用Dockerfile
├── Dockerfile.python         # Python服务Dockerfile
├── docker-compose.yml        # Docker Compose配置文件
├── nginx.conf                # Nginx配置文件
├── requirements.txt          # Python依赖文件
├── .env                      # 环境变量配置
└── data/                     # 数据目录（存放SQLite数据库）
```

## 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)
- 基本的Docker和容器化知识

## 本地开发环境设置

### 1. 初始化数据库

首次使用时，需要初始化SQLite数据库：

```bash
# 运行数据库初始化脚本
python data/init_db.py
```

这将在`data`目录下创建`quant_trading.db`数据库文件，并创建必要的表结构和示例数据。

### 2. 使用Docker Compose启动服务

```bash
# 构建并启动所有服务
docker-compose up --build
```

此命令将：
- 构建前端应用镜像并启动容器（映射到主机8080端口）
- 构建Python服务镜像并启动容器（映射到主机5000端口）
- 启动SQLite浏览器容器（映射到主机3000端口）

### 3. 访问服务

- **前端应用**：http://localhost:8080
- **Python API**：http://localhost:5000/health
- **SQLite浏览器**：http://localhost:3000

## 数据库协作说明

### 共享数据库文件

所有团队成员共享同一个数据库文件，位于`data/quant_trading.db`。通过Docker卷映射，该文件在容器和主机之间共享。

### 使用SQLite浏览器

可以通过http://localhost:3000访问SQLite浏览器，直接查看和编辑数据库内容。

### 数据迁移

项目中已有的`data_migrator.py`可以用于CSV数据导入导出：

```bash
# 在Python容器中运行数据迁移
# 首先进入容器
# docker exec -it quant-trading-python bash
# 然后运行迁移命令
# python -m models.migration.data_migrator
```

## 开发流程

### 前端开发

前端开发可以使用两种方式：

1. **使用Docker开发**：修改代码后，运行`docker-compose up --build frontend`重新构建前端
2. **本地开发**：直接运行`npm run serve`，使用本地开发服务器

### 后端开发

后端开发时，可以通过修改`src/models`目录下的Python代码，然后重新启动Python服务容器：

```bash
docker-compose restart python-service
```

## 环境变量配置

项目使用`.env`文件进行环境变量配置，主要配置项：

- `VUE_APP_API_URL`：API服务地址，默认为http://localhost:5000

## 云服务器部署

### 1. 在云服务器上安装Docker

以Ubuntu为例：

```bash
# 更新软件包
sudo apt-get update

# 安装Docker
sudo apt-get install -y docker.io docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. 部署项目

```bash
# 克隆代码仓库
# git clone <your-repository-url>
cd quant-trading-platform

# 初始化数据库
python data/init_db.py

# 构建并启动服务（生产环境）
docker-compose up --build -d
```

### 3. 配置安全组

确保云服务器安全组开放以下端口：
- 8080（前端应用）
- 3000（可选，SQLite浏览器，生产环境建议关闭）

### 4. 数据备份

定期备份`data/quant_trading.db`文件，以防止数据丢失。

## Docker命令参考

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看容器日志
docker-compose logs <service-name>

# 进入容器
docker exec -it <container-name> bash

# 构建特定服务
docker-compose build <service-name>

# 重启特定服务
docker-compose restart <service-name>
```

## 注意事项

1. 生产环境中，建议关闭Python服务的debug模式
2. 定期备份数据库文件，防止数据丢失
3. 云服务器部署时，考虑使用HTTPS协议
4. 大规模部署时，可以考虑使用Kubernetes进行容器编排
5. 如需修改数据库结构，请更新`data/init_db.py`脚本并重新初始化数据库

## 常见问题解决

### 端口冲突

如果本地8080、5000或3000端口已被占用，可以修改`docker-compose.yml`文件中的端口映射：

```yaml
ports:
  - "新端口:80"  # 前端端口映射
```

### 数据库连接问题

如果前端无法连接到后端API，请检查：
1. Python服务是否正常运行
2. `.env`文件中的`VUE_APP_API_URL`配置是否正确
3. 防火墙设置是否阻止了端口访问

### 容器启动失败

查看容器日志以获取详细错误信息：

```bash
docker-compose logs <service-name>
```

如有其他问题，请联系系统管理员或技术支持。