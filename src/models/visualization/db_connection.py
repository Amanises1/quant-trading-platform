import psycopg2
import pandas as pd
import logging
import psycopg2
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class DatabaseConnection:
    """
    数据库连接类，用于连接到远程PostgreSQL数据库并获取股票数据
    """
    
    def __init__(self, host: str = "10.208.112.57", 
                 database: str = "quant_db", 
                 user: str = "quant_user", 
                 password: str = "quant_pass"):
        """
        初始化数据库连接
        
        参数:
            host: 数据库主机地址
            database: 数据库名称
            user: 用户名
            password: 密码
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        建立数据库连接
        
        返回:
            bool: 连接是否成功
        """
        try:
            if not self.conn or self.conn.closed:
                self.conn = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
            self.logger.info("成功连接到数据库")
            return True
        except psycopg2.OperationalError as e:
            self.logger.error(f"连接数据库失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发生错误: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        关闭数据库连接
        """
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.logger.info("已关闭数据库连接")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Dict]]:
        """
        执行SQL查询并返回结果
        
        参数:
            query: SQL查询语句
            params: 查询参数
        
        返回:
            List[Dict]: 查询结果列表
        """
        try:
            if not self.connect():
                return None
            
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                
                # 获取列名
                columns = [desc[0] for desc in cur.description]
                
                # 获取结果
                result = []
                for row in cur.fetchall():
                    result.append(dict(zip(columns, row)))
                
                return result
        except Exception as e:
            self.logger.error(f"执行查询失败: {e}")
            return None
    
    def get_stock_data(self, stock_name: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取指定股票在指定日期范围内的OHLCV数据
        
        参数:
            stock_name: 股票名称
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'
            
        返回:
            pd.DataFrame: 包含OHLCV数据的DataFrame，或None如果失败
        """
        try:
            # 确保连接是打开的
            if not self.connect():
                return None
                
            # 打印调试信息
            self.logger.info(f"查询股票数据: name={stock_name}, start_date={start_date}, end_date={end_date}")
            
            # 先检查股票名称是否存在
            check_query = """
            SELECT COUNT(*) AS count FROM stock_data_daily WHERE name = %s
            """
            check_result = self.execute_query(check_query, (stock_name,))
            if check_result and len(check_result) > 0:
                count = check_result[0]['count']
                self.logger.info(f"股票 {stock_name} 的记录数量: {count}")
            
            # 使用stock_data_daily表，列名使用name
            query = """
            SELECT 
                date, 
                open, 
                high, 
                low, 
                close, 
                volume
            FROM stock_data_daily
            WHERE 
                name = %s AND
                date >= %s AND
                date <= %s
            ORDER BY date ASC
            """
            
            params = (stock_name, start_date, end_date)
            result = self.execute_query(query, params)
            
            # 如果没有数据，尝试获取任何日期的数据
            if not result or len(result) == 0:
                self.logger.info(f"指定日期范围内没有数据，尝试获取最新数据")
                query = """
                SELECT 
                    date, 
                    open, 
                    high, 
                    low, 
                    close, 
                    volume
                FROM stock_data_daily
                WHERE 
                    name = %s
                ORDER BY date DESC LIMIT 100
                """
                result = self.execute_query(query, (stock_name,))
            
            if result and len(result) > 0:
                df = pd.DataFrame(result)
                self.logger.info(f"查询到 {len(df)} 条数据")
                
                # 确保列名正确并转换数据类型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    
                return df
            else:
                self.logger.warning(f"没有找到股票 {stock_name} 的数据")
                return None
        except Exception as e:
            self.logger.error(f"获取股票数据失败: {e}")
            return None
    
    def get_multi_stock_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        获取多只股票的数据
        
        参数:
            symbols: 股票名称列表
            start_date: 开始日期
            end_date: 结束日期
        
        返回:
            Dict[str, pd.DataFrame]: 股票名称到数据的映射
        """
        result = {}
        for symbol in symbols:
            df = self.get_stock_data(symbol, start_date, end_date)
            if df is not None:
                result[symbol] = df
        return result
    
    def get_realtime_data(self, symbols: List[str]) -> Optional[List[Dict]]:
        """
        获取实时股票数据
        
        参数:
            symbols: 股票名称列表
        
        返回:
            List[Dict]: 实时数据列表
        """
        try:
            # 从stock_data_daily表获取最新数据
            query = """
            SELECT 
                name as symbol,
                close as price,
                volume,
                date as timestamp
            FROM stock_data_daily
            WHERE 
                name = ANY(%s) AND
                date = (SELECT MAX(date) FROM stock_data_daily)
            """
            
            params = (symbols,)
            result = self.execute_query(query, params)
            
            if result:
                # 处理结果
                realtime_data = []
                for row in result:
                    # 计算变化和涨跌幅（从数据库获取前一日收盘价）
                    prev_close = self._get_previous_close(row['symbol'], row['timestamp'])
                    if prev_close and prev_close > 0:
                        change = row['price'] - prev_close
                        change_percent = (change / prev_close) * 100
                    else:
                        change = 0.0
                        change_percent = 0.0
                    
                    realtime_data.append({
                        'symbol': row['symbol'],
                        'lastPrice': row['price'],
                        'change': change,
                        'changePercent': change_percent,
                        'volume': row['volume'],
                        'timestamp': row['timestamp'].timestamp() if isinstance(row['timestamp'], datetime) else row['timestamp']
                    })
                return realtime_data
            return None
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
            return None
    
    def _get_previous_close(self, symbol: str, date: datetime) -> Optional[float]:
        """
        获取股票在前一交易日的收盘价
        
        参数:
            symbol: 股票名称
            date: 当前日期
        
        返回:
            float: 前一交易日的收盘价
        """
        try:
            # 确保date是datetime对象
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d')
            
            query = """
            SELECT close
            FROM stock_data_daily
            WHERE 
                name = %s AND
                date < %s
            ORDER BY date DESC
            LIMIT 1
            """
            
            params = (symbol, date)
            result = self.execute_query(query, params)
            
            if result and len(result) > 0:
                return float(result[0]['close'])
            return None
        except Exception as e:
            self.logger.error(f"获取前收盘价失败: {e}")
            return None
    
    def get_available_stocks(self, limit: int = 100) -> List[str]:
        """
        获取数据库中可用的股票名称列表
        
        参数:
            limit: 返回的股票名称数量限制
        
        返回:
            List[str]: 股票名称列表
        """
        try:
            query = """
            SELECT DISTINCT name
            FROM stock_data_daily
            ORDER BY name
            LIMIT %s
            """
            
            params = (limit,)
            result = self.execute_query(query, params)
            
            if result:
                return [row['name'] for row in result]
            return []
        except Exception as e:
            self.logger.error(f"获取可用股票列表失败: {e}")
            return []
    
    def get_supported_chart_types(self) -> Dict[str, str]:
        """
        获取当前数据库支持的图表类型
        
        返回:
            Dict[str, str]: 图表类型到描述的映射
        """
        # 基于stock_data_daily表的结构，我们支持以下图表类型
        supported_charts = {
            'price_chart': '价格走势图',
            'candlestick_chart': 'K线图',
            'volume_chart': '成交量图'
        }
        
        return supported_charts

# 创建全局数据库连接实例
db_conn = DatabaseConnection()