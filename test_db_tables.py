import psycopg2
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_stock_data_tables():
    """
    检查数据库中的股票数据表结构，特别是stock_data_daily表
    """
    try:
        # 使用与db_connection.py相同的连接参数
        conn = psycopg2.connect(
            host="10.208.112.57",
            database="quant_db",
            user="quant_user",
            password="quant_pass"
        )
        logger.info("成功连接到数据库")
        
        # 创建游标
        cursor = conn.cursor()
        
        # 重点检查的股票数据表
        stock_tables = [
            'stock_data_daily',    # 每日股票数据
        ]
        
        for table_name in stock_tables:
            try:
                # 检查表是否存在
                cursor.execute(f"""SELECT EXISTS (
                                  SELECT FROM information_schema.tables 
                                  WHERE table_schema = 'public'
                                  AND table_name = '{table_name}'
                                  )""")
                exists = cursor.fetchone()[0]
                
                if exists:
                    logger.info(f"\n表 '{table_name}' 存在")
                    
                    # 查询表中的数据行数
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    logger.info(f"表中数据行数: {count}")
                    
                    # 如果表中有数据，查询其包含的股票名称
                    if count > 0:
                        # 使用正确的列名'name'而不是'code'
                        cursor.execute("SELECT DISTINCT name FROM stock_data_daily LIMIT 10")
                        names = cursor.fetchall()
                        if names:
                            logger.info(f"找到 {len(names)} 个股票名称:")
                            for name in names:
                                logger.info(f"- {name[0]}")
                        
                        # 获取一个股票的样本数据，使用正确的列名
                        if names:
                            sample_stock = names[0][0]
                            cursor.execute(f"SELECT name, date, open, high, low, close, volume FROM stock_data_daily WHERE name = %s ORDER BY date DESC LIMIT 10", (sample_stock,))
                            sample_data = cursor.fetchall()
                            logger.info(f"\n股票 '{sample_stock}' 的最新10条数据:")
                            # 打印表头
                            logger.info(f"{'日期':<20} {'开盘价':<10} {'最高价':<10} {'最低价':<10} {'收盘价':<10} {'成交量':<15}")
                            logger.info("-" * 85)
                            # 打印数据
                            for row in sample_data:
                                date_str = str(row[1])[:10] if row[1] else 'None'
                                open_price = f"{row[2]:.2f}" if row[2] else 'None'
                                high_price = f"{row[3]:.2f}" if row[3] else 'None'
                                low_price = f"{row[4]:.2f}" if row[4] else 'None'
                                close_price = f"{row[5]:.2f}" if row[5] else 'None'
                                volume = f"{row[6]:,}" if row[6] else 'None'
                                logger.info(f"{date_str:<20} {open_price:<10} {high_price:<10} {low_price:<10} {close_price:<10} {volume:<15}")
                else:
                    logger.info(f"\n表 '{table_name}' 不存在")
            except Exception as e:
                logger.error(f"查询表 '{table_name}' 时出错: {e}")
        
        # 关闭游标和连接
        cursor.close()
        conn.close()
        logger.info("\n已关闭数据库连接")
        
    except psycopg2.OperationalError as e:
        logger.error(f"连接数据库失败: {e}")
    except Exception as e:
        logger.error(f"发生错误: {e}")

if __name__ == "__main__":
    check_stock_data_tables()