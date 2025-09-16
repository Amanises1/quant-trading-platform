import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable
from datetime import datetime, timedelta
import threading
import time
import json

from .database_connection import db_conn

class MarketMonitor:
    """
    市场监控类，用于实时监控市场数据和指标
    支持价格异常检测、波动率监控和流动性监控
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化市场监控器
        
        参数:
            config: 配置信息，包含监控参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('price_alert_threshold', 0.05)  # 价格异常阈值（百分比）
        self.config.setdefault('volatility_alert_threshold', 0.03)  # 波动率异常阈值
        self.config.setdefault('volume_alert_threshold', 3.0)  # 成交量异常阈值（倍数）
        self.config.setdefault('monitoring_interval', 60)  # 监控间隔（秒）
        self.config.setdefault('max_history_points', 100)  # 每个交易品种保留的历史数据点数
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 监控数据（内存缓存）
        self.market_data = {}
        self.alerts = []
        self.last_update_time = None
        
        # 初始化数据库表
        self._init_database()
    
    def _init_database(self) -> None:
        """
        初始化数据库表结构
        """
        try:
            # 创建market_data表用于存储市场数据
            create_market_data_table = """
            CREATE TABLE IF NOT EXISTS market_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                volume DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
            db_conn.execute_query(create_market_data_table)
            
            # 创建market_alerts表用于存储市场警报
            create_market_alerts_table = """
            CREATE TABLE IF NOT EXISTS market_alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(20) NOT NULL,
                data JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
            db_conn.execute_query(create_market_alerts_table)
            
            # 创建market_monitor_config表用于存储监控配置
            create_monitor_config_table = """
            CREATE TABLE IF NOT EXISTS market_monitor_config (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL UNIQUE,
                is_monitored BOOLEAN DEFAULT true,
                price_alert_threshold DOUBLE PRECISION,
                volatility_alert_threshold DOUBLE PRECISION,
                volume_alert_threshold DOUBLE PRECISION,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
            db_conn.execute_query(create_monitor_config_table)
            
            # 创建索引以提高查询性能
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data (symbol, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_market_alerts_timestamp ON market_alerts (timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_market_alerts_symbol ON market_alerts (symbol)",
                "CREATE INDEX IF NOT EXISTS idx_market_alerts_type ON market_alerts (type)"
            ]
            
            for idx in create_indexes:
                db_conn.execute_query(idx)
            
            self.logger.info("市场监控数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化市场监控数据库表失败: {e}")
    
    def start_monitoring(self, data_source: Callable, symbols: List[str]) -> bool:
        """
        启动市场监控
        
        参数:
            data_source: 数据源函数，用于获取实时市场数据
            symbols: 要监控的交易品种列表
            
        返回:
            是否成功启动监控
        """
        if self.is_monitoring:
            self.logger.warning("市场监控已经在运行中")
            return False
        
        self.is_monitoring = True
        self.data_source = data_source
        self.symbols = symbols
        
        # 初始化监控配置
        self._init_monitor_config(symbols)
        
        # 初始化市场数据（从数据库加载历史数据）
        self._load_historical_data(symbols)
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"已启动市场监控，监控{len(symbols)}个交易品种，间隔{self.config['monitoring_interval']}秒")
        
        return True
    
    def _init_monitor_config(self, symbols: List[str]) -> None:
        """
        初始化监控配置到数据库
        
        参数:
            symbols: 交易品种列表
        """
        try:
            for symbol in symbols:
                query = """
                INSERT INTO market_monitor_config (symbol, is_monitored, 
                                                  price_alert_threshold, 
                                                  volatility_alert_threshold, 
                                                  volume_alert_threshold)
                VALUES (%s, true, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE
                SET is_monitored = true,
                    updated_at = NOW()
                """
                params = (
                    symbol,
                    self.config['price_alert_threshold'],
                    self.config['volatility_alert_threshold'],
                    self.config['volume_alert_threshold']
                )
                db_conn.execute_query(query, params)
            
            self.logger.info(f"已初始化{len(symbols)}个交易品种的监控配置")
        except Exception as e:
            self.logger.error(f"初始化监控配置失败: {e}")
    
    def _load_historical_data(self, symbols: List[str]) -> None:
        """
        从数据库加载历史市场数据
        
        参数:
            symbols: 交易品种列表
        """
        try:
            for symbol in symbols:
                # 初始化符号数据结构
                self.market_data[symbol] = {
                    'price_history': [],
                    'volume_history': [],
                    'volatility': 0.0,
                    'avg_volume': 0.0,
                    'last_price': 0.0,
                    'last_volume': 0.0
                }
                
                # 加载历史数据
                query = """
                SELECT price, volume
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """
                params = (symbol, self.config['max_history_points'])
                result = db_conn.execute_query(query, params)
                
                if result:
                    # 将结果反向添加，因为我们按降序查询，但希望历史数据按升序排列
                    for row in reversed(result):
                        self.market_data[symbol]['price_history'].append(row['price'])
                        self.market_data[symbol]['volume_history'].append(row['volume'])
                    
                    # 更新最新价格和成交量
                    if self.market_data[symbol]['price_history']:
                        self.market_data[symbol]['last_price'] = self.market_data[symbol]['price_history'][-1]
                        self.market_data[symbol]['last_volume'] = self.market_data[symbol]['volume_history'][-1]
                    
                    # 计算波动率和平均成交量
                    if len(self.market_data[symbol]['price_history']) >= 20:
                        price_returns = np.diff(np.log(self.market_data[symbol]['price_history'][-20:]))
                        self.market_data[symbol]['volatility'] = np.std(price_returns) * np.sqrt(252)
                        self.market_data[symbol]['avg_volume'] = np.mean(self.market_data[symbol]['volume_history'][-20:])
            
            self.logger.info(f"已加载{len(symbols)}个交易品种的历史数据")
        except Exception as e:
            self.logger.error(f"加载历史市场数据失败: {e}")
    
    def stop_monitoring(self) -> bool:
        """
        停止市场监控
        
        返回:
            是否成功停止监控
        """
        if not self.is_monitoring:
            self.logger.warning("市场监控未在运行")
            return False
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            self.monitor_thread = None
        
        # 更新数据库中的监控状态
        try:
            query = """
            UPDATE market_monitor_config
            SET is_monitored = false,
                updated_at = NOW()
            WHERE symbol IN %s
            """
            params = (tuple(self.symbols),)
            db_conn.execute_query(query, params)
            self.logger.info(f"已更新{len(self.symbols)}个交易品种的监控状态为未监控")
        except Exception as e:
            self.logger.error(f"更新监控状态失败: {e}")
        
        self.logger.info("已停止市场监控")
        
        return True
    
    def _monitoring_loop(self) -> None:
        """
        监控循环，定期获取市场数据并进行分析
        """
        while self.is_monitoring:
            try:
                # 获取最新市场数据
                self._update_market_data()
                
                # 分析市场数据
                self._analyze_market_data()
                
                # 更新最后更新时间
                self.last_update_time = datetime.now()
                
                # 等待下一次监控
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"市场监控出错: {e}")
                time.sleep(5)  # 出错后短暂等待再重试
    
    def _update_market_data(self) -> None:
        """
        更新市场数据
        """
        current_time = datetime.now()
        
        for symbol in self.symbols:
            try:
                # 调用数据源函数获取最新数据
                data = self.data_source(symbol)
                
                if data is None or not isinstance(data, dict):
                    self.logger.warning(f"获取{symbol}的市场数据失败")
                    continue
                
                # 提取价格和成交量
                price = data.get('price', 0.0)
                volume = data.get('volume', 0.0)
                
                if price <= 0 or volume < 0:
                    self.logger.warning(f"{symbol}的价格或成交量数据无效")
                    continue
                
                # 保存到数据库
                try:
                    query = """
                    INSERT INTO market_data (timestamp, symbol, price, volume)
                    VALUES (%s, %s, %s, %s)
                    """
                    params = (current_time, symbol, price, volume)
                    db_conn.execute_query(query, params)
                except Exception as e:
                    self.logger.error(f"保存{symbol}的市场数据到数据库失败: {e}")
                
                # 更新内存中的历史数据
                self.market_data[symbol]['price_history'].append(price)
                self.market_data[symbol]['volume_history'].append(volume)
                
                # 限制历史数据长度
                max_history = self.config['max_history_points']
                if len(self.market_data[symbol]['price_history']) > max_history:
                    self.market_data[symbol]['price_history'] = self.market_data[symbol]['price_history'][-max_history:]
                    self.market_data[symbol]['volume_history'] = self.market_data[symbol]['volume_history'][-max_history:]
                
                # 更新最新价格和成交量
                self.market_data[symbol]['last_price'] = price
                self.market_data[symbol]['last_volume'] = volume
                
                # 计算波动率和平均成交量
                if len(self.market_data[symbol]['price_history']) >= 20:
                    price_returns = np.diff(np.log(self.market_data[symbol]['price_history'][-20:]))
                    self.market_data[symbol]['volatility'] = np.std(price_returns) * np.sqrt(252)
                    self.market_data[symbol]['avg_volume'] = np.mean(self.market_data[symbol]['volume_history'][-20:])
                
            except Exception as e:
                self.logger.error(f"更新{symbol}的市场数据出错: {e}")
    
    def _analyze_market_data(self) -> None:
        """
        分析市场数据，检测异常情况
        """
        for symbol in self.symbols:
            try:
                # 获取当前数据
                data = self.market_data[symbol]
                
                if len(data['price_history']) < 2:
                    continue  # 数据不足，跳过分析
                
                # 检测价格异常
                last_price = data['last_price']
                prev_price = data['price_history'][-2]
                price_change = abs(last_price / prev_price - 1)
                
                if price_change > self.config['price_alert_threshold']:
                    alert = {
                        'timestamp': datetime.now(),
                        'symbol': symbol,
                        'type': 'price_alert',
                        'message': f"{symbol}价格异常波动: {price_change:.2%}",
                        'severity': 'high' if price_change > 2 * self.config['price_alert_threshold'] else 'medium',
                        'data': {
                            'last_price': last_price,
                            'prev_price': prev_price,
                            'change': price_change
                        }
                    }
                    self.alerts.append(alert)
                    
                    # 保存到数据库
                    try:
                        query = """
                        INSERT INTO market_alerts (timestamp, symbol, type, message, severity, data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        params = (
                            alert['timestamp'],
                            alert['symbol'],
                            alert['type'],
                            alert['message'],
                            alert['severity'],
                            json.dumps(alert['data'])
                        )
                        db_conn.execute_query(query, params)
                    except Exception as e:
                        self.logger.error(f"保存{symbol}的价格警报到数据库失败: {e}")
                    
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
                
                # 检测波动率异常
                if data['volatility'] > self.config['volatility_alert_threshold']:
                    alert = {
                        'timestamp': datetime.now(),
                        'symbol': symbol,
                        'type': 'volatility_alert',
                        'message': f"{symbol}波动率异常: {data['volatility']:.2%}",
                        'severity': 'high' if data['volatility'] > 2 * self.config['volatility_alert_threshold'] else 'medium',
                        'data': {
                            'volatility': data['volatility'],
                            'threshold': self.config['volatility_alert_threshold']
                        }
                    }
                    self.alerts.append(alert)
                    
                    # 保存到数据库
                    try:
                        query = """
                        INSERT INTO market_alerts (timestamp, symbol, type, message, severity, data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        params = (
                            alert['timestamp'],
                            alert['symbol'],
                            alert['type'],
                            alert['message'],
                            alert['severity'],
                            json.dumps(alert['data'])
                        )
                        db_conn.execute_query(query, params)
                    except Exception as e:
                        self.logger.error(f"保存{symbol}的波动率警报到数据库失败: {e}")
                    
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
                
                # 检测成交量异常
                if data['avg_volume'] > 0 and data['last_volume'] > data['avg_volume'] * self.config['volume_alert_threshold']:
                    alert = {
                        'timestamp': datetime.now(),
                        'symbol': symbol,
                        'type': 'volume_alert',
                        'message': f"{symbol}成交量异常: 当前{data['last_volume']:.0f}，平均{data['avg_volume']:.0f}",
                        'severity': 'medium',
                        'data': {
                            'last_volume': data['last_volume'],
                            'avg_volume': data['avg_volume'],
                            'ratio': data['last_volume'] / data['avg_volume']
                        }
                    }
                    self.alerts.append(alert)
                    
                    # 保存到数据库
                    try:
                        query = """
                        INSERT INTO market_alerts (timestamp, symbol, type, message, severity, data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        params = (
                            alert['timestamp'],
                            alert['symbol'],
                            alert['type'],
                            alert['message'],
                            alert['severity'],
                            json.dumps(alert['data'])
                        )
                        db_conn.execute_query(query, params)
                    except Exception as e:
                        self.logger.error(f"保存{symbol}的成交量警报到数据库失败: {e}")
                    
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
                
            except Exception as e:
                self.logger.error(f"分析{symbol}的市场数据出错: {e}")
    
    def get_alerts(self, start_time: Optional[datetime] = None, 
                  alert_types: Optional[List[str]] = None, 
                  min_severity: Optional[str] = None) -> List[Dict]:
        """
        获取警报列表
        
        参数:
            start_time: 开始时间，只返回该时间之后的警报
            alert_types: 警报类型列表，只返回指定类型的警报
            min_severity: 最低严重程度，只返回不低于该严重程度的警报
            
        返回:
            警报列表
        """
        try:
            # 构建查询语句
            query_parts = ["SELECT id, timestamp, symbol, type, message, severity, data FROM market_alerts WHERE 1=1"]
            params = []
            
            # 按时间过滤
            if start_time:
                query_parts.append("AND timestamp >= %s")
                params.append(start_time)
            
            # 按类型过滤
            if alert_types:
                placeholders = ",".join(["%s"] * len(alert_types))
                query_parts.append(f"AND type IN ({placeholders})")
                params.extend(alert_types)
            
            # 按严重程度过滤
            if min_severity:
                severity_levels = {'low': 0, 'medium': 1, 'high': 2}
                min_level = severity_levels.get(min_severity.lower(), 0)
                
                # 构建严重程度过滤条件
                if min_level == 0:
                    # 返回所有严重程度
                    pass
                elif min_level == 1:
                    # 返回medium和high
                    query_parts.append("AND severity IN ('medium', 'high')")
                elif min_level == 2:
                    # 只返回high
                    query_parts.append("AND severity = 'high'")
            
            # 添加排序
            query_parts.append("ORDER BY timestamp DESC")
            
            # 组合完整查询
            query = " ".join(query_parts)
            
            # 执行查询
            result = db_conn.execute_query(query, tuple(params))
            
            # 转换结果格式
            alerts = []
            for row in result:
                alert = {
                    'id': row['id'],
                    'timestamp': datetime.fromisoformat(row['timestamp'].isoformat()),
                    'symbol': row['symbol'],
                    'type': row['type'],
                    'message': row['message'],
                    'severity': row['severity'],
                    'data': row['data'] if row['data'] is not None else {}
                }
                alerts.append(alert)
            
            return alerts
        except Exception as e:
            self.logger.error(f"从数据库获取警报列表失败: {e}")
            # 出错时返回内存中的警报，以确保系统仍能正常工作
            filtered_alerts = self.alerts.copy()
            
            # 手动过滤内存中的警报
            if start_time:
                filtered_alerts = [alert for alert in filtered_alerts if alert['timestamp'] >= start_time]
            
            if alert_types:
                filtered_alerts = [alert for alert in filtered_alerts if alert['type'] in alert_types]
            
            if min_severity:
                severity_levels = {'low': 0, 'medium': 1, 'high': 2}
                min_level = severity_levels.get(min_severity.lower(), 0)
                filtered_alerts = [alert for alert in filtered_alerts if severity_levels.get(alert['severity'].lower(), 0) >= min_level]
            
            return filtered_alerts
    
    def get_market_summary(self) -> Dict:
        """
        获取市场概览
        
        返回:
            市场概览字典
        """
        summary = {
            'timestamp': datetime.now(),
            'symbols_count': len(self.symbols),
            'alerts_count': 0,
            'last_update': self.last_update_time,
            'symbols_data': {}
        }
        
        try:
            # 从数据库获取警报数量
            alerts_count_query = "SELECT COUNT(*) AS count FROM market_alerts"
            alerts_count_result = db_conn.execute_query(alerts_count_query)
            if alerts_count_result and len(alerts_count_result) > 0:
                summary['alerts_count'] = alerts_count_result[0]['count']
        except Exception as e:
            self.logger.error(f"获取警报数量失败: {e}")
            summary['alerts_count'] = len(self.alerts)
        
        # 添加各交易品种的摘要数据
        for symbol in self.symbols:
            try:
                # 尝试从数据库获取最新数据
                query = """
                SELECT price, volume
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """
                result = db_conn.execute_query(query, (symbol,))
                
                if result and len(result) > 0:
                    # 使用数据库中的最新数据
                    symbol_data = {
                        'last_price': result[0]['price'],
                        'last_volume': result[0]['volume'],
                        'volatility': 0.0,
                        'avg_volume': 0.0
                    }
                    
                    # 计算波动率和平均成交量
                    try:
                        volatility_query = """
                        SELECT price
                        FROM market_data
                        WHERE symbol = %s
                        ORDER BY timestamp DESC
                        LIMIT 20
                        """
                        volatility_result = db_conn.execute_query(volatility_query, (symbol,))
                        
                        if volatility_result and len(volatility_result) >= 20:
                            prices = [row['price'] for row in reversed(volatility_result)]  # 反转以按时间升序排列
                            price_returns = np.diff(np.log(prices))
                            symbol_data['volatility'] = np.std(price_returns) * np.sqrt(252)
                    except Exception as e:
                        self.logger.error(f"计算{symbol}的波动率失败: {e}")
                    
                    try:
                        avg_volume_query = """
                        SELECT AVG(volume) AS avg_volume
                        FROM market_data
                        WHERE symbol = %s
                        ORDER BY timestamp DESC
                        LIMIT 20
                        """
                        avg_volume_result = db_conn.execute_query(avg_volume_query, (symbol,))
                        
                        if avg_volume_result and len(avg_volume_result) > 0:
                            symbol_data['avg_volume'] = avg_volume_result[0]['avg_volume']
                    except Exception as e:
                        self.logger.error(f"计算{symbol}的平均成交量失败: {e}")
                    
                    summary['symbols_data'][symbol] = symbol_data
                else:
                    # 使用内存中的数据
                    data = self.market_data.get(symbol, {})
                    if data and 'last_price' in data:
                        summary['symbols_data'][symbol] = {
                            'last_price': data.get('last_price', 0.0),
                            'volatility': data.get('volatility', 0.0),
                            'avg_volume': data.get('avg_volume', 0.0),
                            'last_volume': data.get('last_volume', 0.0)
                        }
            except Exception as e:
                self.logger.error(f"获取{symbol}的市场概览失败: {e}")
        
        return summary

# 创建全局市场监控实例
market_monitor = MarketMonitor()