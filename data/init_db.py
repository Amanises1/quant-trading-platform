import sqlite3
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 数据库文件路径
db_path = os.path.join(current_dir, 'quant_trading.db')

# 连接到SQLite数据库
# 如果数据库不存在，会自动创建
conn = sqlite3.connect(db_path)

# 创建游标对象
cursor = conn.cursor()

# 创建股票历史数据表
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    ''')
    
    # 创建指数数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS index_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    ''')
    
    # 创建策略表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            parameters TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建交易记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER,
            stock_code TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            price REAL NOT NULL,
            volume INTEGER NOT NULL,
            trade_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id)
        )
    ''')
    
    # 添加索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_history_code_date ON stock_history (code, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_history_code_date ON index_history (code, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades (strategy_id)')
    
    # 提交事务
    conn.commit()
    print(f"数据库初始化成功，文件位置: {db_path}")
    
    # 插入一些示例数据
    try:
        cursor.execute("INSERT INTO stock_history (code, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ('000001', '2023-01-03', 14.50, 14.80, 14.45, 14.65, 12000000))
        cursor.execute("INSERT INTO stock_history (code, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ('000001', '2023-01-04', 14.70, 15.10, 14.60, 14.95, 15000000))
        conn.commit()
        print("已插入示例数据")
    except sqlite3.IntegrityError:
        print("示例数据已存在，跳过插入")
        conn.rollback()
        
except sqlite3.Error as e:
    print(f"数据库初始化错误: {e}")
    conn.rollback()
finally:
    # 关闭数据库连接
    conn.close()