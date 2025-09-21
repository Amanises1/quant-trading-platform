#  QTP - Quant Trading Platform  
2025 SEU Summer 基于 Python 与 Docker 的量化交易平台  

---

##  项目简介
QTP 是一个面向研究与教学的 **量化交易选股系统**，支持：  
- 📊 多维特征可视化  
- 📡 实时交易监控  
- 📑 策略回测  
- 🤖 智能信号生成  

系统采用 **Python 后端 + Vue 前端 + PostgreSQL/SQLite 数据库** 架构，支持 Docker 快速部署。  

---

##  功能模块
- **多维特征可视化**：提供股票数据、技术指标、因子分析可视化  
- **实时交易监控**：追踪行情、持仓与风险指标，支持告警推送  
- **交易策略回测**：支持多种经典策略及自定义策略的回测与报告生成  
- **智能信号生成**：集成机器学习模型，输出买卖信号与特征重要性分析  

---

##  项目结构
```bash
quant-trading-platform/
├── code/
│   ├── backend/               # 后端核心逻辑
│   │   ├── app.py              # 后端服务入口
│   │   ├── factors/            # 因子定义与评估
│   │   ├── src/
│   │   │   ├── backtest/       # 策略回测引擎
│   │   │   ├── data_loader/    # 数据加载
│   │   │   ├── models/         # 训练与信号模型
│   │   │   ├── trainers/       # 模型训练脚本
│   │   │   └── utils/          # 工具函数
│   │   ├── train.py            # 模型训练入口
│   │   └── requirements.txt
│   └── frontend/               # 前端界面 (Vue)
│       ├── src/
│       │   ├── components/     # 页面组件
│       │   ├── views/          # 系统功能页面
│       │   ├── models/         # 回测/监控模块
│       │   └── assets/         # 静态资源
│       └── vue.config.js
├── database/                   # 数据库相关
│   ├── docker-compose.yml      # PostgreSQL 启动配置
│   ├── init.sql                # 初始化脚本
│   └── backup.sh               # 数据库备份
├── datasets/                   # 数据集 (原始/处理后)
│   ├── raw/                    # 原始数据
│   └── processed/              # 处理后数据与因子文件
├── docs/                       # 文档 (运维/用户手册)
├── models/                     # 机器学习模型与权重
├── tests/                      # 测试用例
├── docker-compose.yml          # 全局 Docker 配置
├── Dockerfile.python           # Python 服务镜像
├── Dockerfile.frontend         # 前端服务镜像
├── LICENSE
└── README.md
---
