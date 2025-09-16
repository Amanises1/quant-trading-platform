import sys
import psycopg2
import random
import time
from datetime import datetime, timedelta

# 数据库连接配置
DB_CONFIG = {
    "host": "10.208.112.57",
    "database": "quant_db",
    "user": "quant_user",
    "password": "quant_pass"
}

# 模拟通知类型和内容
NOTIFICATION_TYPES = ["系统通知", "策略提醒", "风险警告", "交易信号", "数据更新"]
NOTIFICATION_CONTENTS = {
    "系统通知": [
        "系统维护将于今晚22:00开始，预计持续2小时",
        "平台已完成升级，新增数据分析功能",
        "服务器负载过高，请合理安排任务执行时间"
    ],
    "策略提醒": [
        "您的策略'均线交叉'今日触发了5次交易信号",
        "策略'动量突破'最近表现优异，胜率达65%",
        "策略'反转指标'参数需要优化，建议调整"
    ],
    "风险警告": [
        "账户可用资金不足，部分策略已暂停",
        "市场波动异常，建议降低杠杆比例",
        "持仓股票'腾讯控股'出现较大跌幅，请关注"
    ],
    "交易信号": [
        "股票'阿里巴巴'出现买入信号，RSI指标超卖",
        "'沪深300'指数MACD金叉，短期看涨",
        "'贵州茅台'成交量异常放大，有资金流入迹象"
    ],
    "数据更新": [
        "A股日线数据已更新至最新交易日",
        "期货市场持仓数据同步完成",
        "期权波动率曲面数据已加载完成"
    ]
}

# 用户ID范围（假设系统中有多个用户）
USER_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("成功连接到数据库")
        return conn
    except psycopg2.OperationalError as e:
        print(f"连接数据库失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


def create_notification_table(conn):
    """创建通知表（如果不存在）"""
    try:
        cur = conn.cursor()
        # 创建通知表的SQL语句
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """
        cur.execute(create_table_sql)
        conn.commit()
        cur.close()
        print("通知表已创建或已存在")
    except Exception as e:
        print(f"创建表时发生错误: {e}")
        conn.rollback()


def generate_mock_notifications(num=10):
    """生成模拟通知数据"""
    notifications = []
    now = datetime.now()
    
    for _ in range(num):
        # 随机选择通知类型
        notification_type = random.choice(NOTIFICATION_TYPES)
        # 随机选择该类型下的内容
        content = random.choice(NOTIFICATION_CONTENTS[notification_type])
        # 随机选择用户ID
        user_id = random.choice(USER_IDS)
        # 随机生成创建时间（过去7天内）
        days_ago = random.randint(0, 6)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        # 随机决定是否已读
        is_read = random.choice([True, False])
        
        notifications.append({
            "user_id": user_id,
            "type": notification_type,
            "content": content,
            "is_read": is_read,
            "created_at": created_at,
            "updated_at": created_at
        })
    
    return notifications


def insert_notifications(conn, notifications):
    """将通知数据插入数据库"""
    try:
        cur = conn.cursor()
        
        # 准备插入语句
        insert_sql = """
        INSERT INTO notifications (user_id, type, content, is_read, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # 准备数据参数
        data_to_insert = [
            (
                n["user_id"],
                n["type"],
                n["content"],
                n["is_read"],
                n["created_at"],
                n["updated_at"]
            )
            for n in notifications
        ]
        
        # 执行批量插入
        cur.executemany(insert_sql, data_to_insert)
        conn.commit()
        cur.close()
        print(f"成功插入 {len(notifications)} 条通知数据")
    except Exception as e:
        print(f"插入数据时发生错误: {e}")
        conn.rollback()


def main():
    """主函数"""
    # 获取数据库连接
    conn = get_db_connection()
    
    # 创建通知表（如果不存在）
    create_notification_table(conn)
    
    # 生成模拟通知数据
    num_notifications = 50  # 生成50条模拟数据
    notifications = generate_mock_notifications(num_notifications)
    
    # 将数据插入数据库
    insert_notifications(conn, notifications)
    
    # 关闭连接
    conn.close()
    print("数据库连接已关闭")


if __name__ == "__main__":
    print("开始生成模拟通知数据并写入数据库...")
    main()
    print("操作完成！")