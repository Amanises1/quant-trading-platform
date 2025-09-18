import psycopg2
import logging
from typing import Optional, Dict, Any
import os
import psycopg2

class DatabaseConnection:
    """
    数据库连接管理类，负责处理与远程PostgreSQL数据库的连接和操作
    """
    
    _instance = None
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化数据库连接配置"""
        self.logger = logging.getLogger(__name__)
        self.conn = None
        self.cursor = None
        
        # 数据库连接参数
        self.db_params = {
            'host': '10.208.112.57',
            'database': 'quant_db',
            'user': 'quant_user',
            'password': 'quant_pass'
        }
        
        # 自动创建必要的表结构
        self._create_tables_if_not_exists()
    
    def connect(self) -> bool:
        """
        建立数据库连接
        
        返回:
            是否成功连接
        """
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(**self.db_params)
                self.cursor = self.conn.cursor()
                self.logger.info(f"成功连接到数据库: {self.db_params['host']}/{self.db_params['database']}")
                return True
            return True
        except psycopg2.OperationalError as e:
            self.logger.error(f"数据库连接失败: {e}")
            self.conn = None
            self.cursor = None
            return False
        except Exception as e:
            self.logger.error(f"数据库操作异常: {e}")
            self.conn = None
            self.cursor = None
            return False
    
    def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("数据库连接已关闭")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[list]:
        """
        执行SQL查询
        
        参数:
            query: SQL查询语句
            params: 查询参数
        
        返回:
            查询结果列表，如果执行失败则返回None
        """
        if not self.connect():
            return None
        
        try:
            self.cursor.execute(query, params or ())
            
            # 如果是SELECT类型的查询，返回结果
            if query.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in self.cursor.description]
                results = []
                for row in self.cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            
            # 其他类型的查询提交事务
            self.conn.commit()
            return []
            
        except Exception as e:
            self.logger.error(f"执行查询失败: {e}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def _create_tables_if_not_exists(self) -> None:
        """创建交易监控系统所需的表结构"""
        if not self.connect():
            self.logger.error("无法连接到数据库，无法创建表结构")
            return
        
        # 创建positions表
        positions_table_sql = """
        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            quantity INTEGER NOT NULL,
            avg_price NUMERIC(12, 4) NOT NULL,
            current_price NUMERIC(12, 4) NOT NULL,
            market_value NUMERIC(18, 4) NOT NULL,
            profit NUMERIC(18, 4) NOT NULL,
            profit_rate NUMERIC(10, 4) NOT NULL,
            entry_date DATE NOT NULL,
            account_id VARCHAR(20) NOT NULL,
            asset_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (symbol, account_id, asset_type)
        );
        """
        
        # 创建trade_history表
        trade_history_table_sql = """
        CREATE TABLE IF NOT EXISTS trade_history (
            id SERIAL PRIMARY KEY,
            order_id INTEGER,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            price NUMERIC(12, 4) NOT NULL,
            amount NUMERIC(18, 4) NOT NULL,
            fee NUMERIC(10, 4) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            account_id VARCHAR(20) NOT NULL,
            asset_type VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 创建orders表
        orders_table_sql = """
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            filled_quantity INTEGER DEFAULT 0,
            price NUMERIC(12, 4) NOT NULL,
            order_type VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            account_id VARCHAR(20) NOT NULL,
            asset_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 创建alerts表
        alerts_table_sql = """
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            related_id VARCHAR(50),
            related_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 创建indexes
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_positions_account_id ON positions(account_id);",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_trade_history_account_id ON trade_history(account_id);",
            "CREATE INDEX IF NOT EXISTS idx_trade_history_symbol ON trade_history(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_trade_history_timestamp ON trade_history(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_orders_account_id ON orders(account_id);",
            "CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);"
        ]
        
        # 执行建表语句
        for sql in [positions_table_sql, trade_history_table_sql, orders_table_sql, alerts_table_sql] + indexes_sql:
            try:
                self.cursor.execute(sql)
                self.conn.commit()
            except Exception as e:
                self.logger.error(f"创建表或索引失败: {e}")
                self.conn.rollback()
                
        self.logger.info("数据库表结构检查和创建完成")

# 创建全局数据库连接实例
db_conn = DatabaseConnection()