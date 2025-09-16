import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable
from datetime import datetime, timedelta
import threading
import time
from .database_connection import db_conn

class TradeMonitor:
    """
    交易监控类，用于实时监控交易执行情况
    支持订单执行监控、仓位监控和风险控制
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化交易监控器
        
        参数:
            config: 配置信息，包含监控参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('max_position_size', 0.2)  # 最大仓位比例
        self.config.setdefault('max_drawdown_threshold', 0.1)  # 最大回撤阈值
        self.config.setdefault('slippage_threshold', 0.005)  # 滑点阈值
        self.config.setdefault('monitoring_interval', 30)  # 监控间隔（秒）
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 账户信息
        self.account_info = {
            'initial_equity': 0.0,
            'current_equity': 0.0,
            'max_equity': 0.0,
            'cash_balance': 0.0,
            'margin_used': 0.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0
        }
        
        # 从数据库初始化账户信息
        self._update_account_info()
    
    def start_monitoring(self) -> bool:
        """
        启动交易监控
        
        返回:
            是否成功启动监控
        """
        if self.is_monitoring:
            self.logger.warning("交易监控已经在运行中")
            return False
        
        self.is_monitoring = True
        
        # 初始化账户信息
        self._update_account_info()
        if self.account_info['current_equity'] > 0:
            self.account_info['initial_equity'] = self.account_info['current_equity']
            self.account_info['max_equity'] = self.account_info['current_equity']
        else:
            # 如果数据库中没有账户数据，设置默认值
            self.account_info['initial_equity'] = 1000000.0
            self.account_info['current_equity'] = 1000000.0
            self.account_info['max_equity'] = 1000000.0
            self.account_info['cash_balance'] = 1000000.0
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"已启动交易监控，间隔{self.config['monitoring_interval']}秒")
        
        return True
    
    def stop_monitoring(self) -> bool:
        """
        停止交易监控
        
        返回:
            是否成功停止监控
        """
        if not self.is_monitoring:
            self.logger.warning("交易监控未在运行")
            return False
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            self.monitor_thread = None
        
        self.logger.info("已停止交易监控")
        
        return True
    
    def _monitoring_loop(self) -> None:
        """
        监控循环，定期获取交易数据并进行分析
        """
        while self.is_monitoring:
            try:
                # 更新账户信息
                self._update_account_info()
                
                # 更新订单和仓位信息
                self._update_trade_data()
                
                # 分析交易数据
                self._analyze_trade_data()
                
                # 记录监控日志到数据库
                self._log_monitoring_summary()
                
                # 等待下一次监控
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"交易监控出错: {e}")
                time.sleep(5)  # 出错后短暂等待再重试
    
    def _update_account_info(self) -> None:
        """
        从数据库更新账户信息
        """
        try:
            # 从数据库获取最新账户信息
            query = "SELECT * FROM accounts ORDER BY updated_at DESC LIMIT 1"
            result = db_conn.execute_query(query)
            
            if result and len(result) > 0:
                account_data = result[0]
                self.account_info['current_equity'] = account_data['equity']
                self.account_info['cash_balance'] = account_data['cash_balance']
                self.account_info['margin_used'] = account_data['margin_used']
                self.account_info['unrealized_pnl'] = account_data['unrealized_pnl']
                self.account_info['realized_pnl'] = account_data['realized_pnl']
                
                # 如果是初始运行，设置初始权益
                if self.account_info['initial_equity'] == 0:
                    self.account_info['initial_equity'] = account_data['equity']
                    self.account_info['max_equity'] = account_data['equity']
                
                # 更新最大权益
                if self.account_info['current_equity'] > self.account_info['max_equity']:
                    self.account_info['max_equity'] = self.account_info['current_equity']
            else:
                self.logger.warning("数据库中未找到账户信息")
                
        except Exception as e:
            self.logger.error(f"更新账户信息出错: {e}")
    
    def _update_trade_data(self) -> None:
        """
        从数据库更新交易数据
        """
        # 不需要在这个类中维护orders和positions列表，因为现在是直接从数据库获取
        pass
    
    def _analyze_trade_data(self) -> None:
        """
        分析交易数据，检测异常情况
        """
        try:
            # 检查回撤
            self._check_drawdown()
            
            # 检查仓位大小
            self._check_position_size()
            
            # 检查订单执行
            self._check_order_execution()
            
        except Exception as e:
            self.logger.error(f"分析交易数据出错: {e}")
    
    def _check_drawdown(self) -> None:
        """
        检查账户回撤
        """
        if self.account_info['max_equity'] <= 0:
            return
        
        # 计算当前回撤
        drawdown = 1 - self.account_info['current_equity'] / self.account_info['max_equity']
        
        # 检查是否超过回撤阈值
        if drawdown > self.config['max_drawdown_threshold']:
            severity = 'high' if drawdown > 1.5 * self.config['max_drawdown_threshold'] else 'medium'
            alert = {
                'timestamp': datetime.now().timestamp(),
                'type': 'drawdown_alert',
                'message': f"账户回撤超过阈值: {drawdown:.2%}",
                'severity': severity,
                'data': {
                    'current_equity': self.account_info['current_equity'],
                    'max_equity': self.account_info['max_equity'],
                    'drawdown': drawdown,
                    'threshold': self.config['max_drawdown_threshold']
                }
            }
            
            # 保存警报到数据库
            self._save_alert_to_db(alert)
            self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
    
    def _check_position_size(self) -> None:
        """
        检查仓位大小
        """
        if self.account_info['current_equity'] <= 0:
            return
        
        # 从数据库获取当前仓位
        query = "SELECT * FROM positions"
        positions = db_conn.execute_query(query)
        
        if not positions:
            return
        
        for position in positions:
            symbol = position['symbol']
            position_value = position['market_value']
            position_ratio = position_value / self.account_info['current_equity']
            
            # 检查是否超过最大仓位比例
            if position_ratio > self.config['max_position_size']:
                severity = 'high' if position_ratio > 1.5 * self.config['max_position_size'] else 'medium'
                alert = {
                    'timestamp': datetime.now().timestamp(),
                    'type': 'position_size_alert',
                    'symbol': symbol,
                    'message': f"{symbol}仓位比例超过阈值: {position_ratio:.2%}",
                    'severity': severity,
                    'data': {
                        'position_value': position_value,
                        'equity': self.account_info['current_equity'],
                        'position_ratio': position_ratio,
                        'threshold': self.config['max_position_size']
                    }
                }
                
                # 保存警报到数据库
                self._save_alert_to_db(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
    
    def _check_order_execution(self) -> None:
        """
        检查订单执行情况
        """
        # 从数据库获取最近的已完成订单（最近1小时内）
        one_hour_ago = datetime.now() - timedelta(hours=1)
        query = """
        SELECT * FROM orders 
        WHERE status = 'filled' AND updated_at >= %s
        ORDER BY updated_at DESC
        """
        recent_orders = db_conn.execute_query(query, (one_hour_ago,))
        
        for order in recent_orders:
            # 检查滑点
            if 'expected_price' in order and 'average_price' in order and order['expected_price'] > 0:
                side = order.get('side', '')
                expected_price = order['expected_price']
                executed_price = order['average_price']
                
                # 计算滑点比例（买入时希望价格低，卖出时希望价格高）
                if side.lower() == 'buy':
                    slippage_ratio = (executed_price / expected_price) - 1
                elif side.lower() == 'sell':
                    slippage_ratio = 1 - (executed_price / expected_price)
                else:
                    continue
                
                # 检查是否超过滑点阈值
                if slippage_ratio > self.config['slippage_threshold']:
                    alert = {
                        'timestamp': datetime.now().timestamp(),
                        'type': 'slippage_alert',
                        'order_id': order.get('order_id'),
                        'symbol': order.get('symbol'),
                        'message': f"{order.get('symbol')}订单滑点超过阈值: {slippage_ratio:.2%}",
                        'severity': 'medium',
                        'data': {
                            'side': side,
                            'expected_price': expected_price,
                            'executed_price': executed_price,
                            'slippage_ratio': slippage_ratio,
                            'threshold': self.config['slippage_threshold']
                        }
                    }
                    
                    # 保存警报到数据库
                    self._save_alert_to_db(alert)
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
    
    def _save_alert_to_db(self, alert: Dict) -> None:
        """
        将警报保存到数据库
        """
        try:
            query = """
            INSERT INTO alerts (timestamp, type, symbol, message, severity, data)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                alert['timestamp'],
                alert['type'],
                alert.get('symbol'),
                alert['message'],
                alert['severity'],
                str(alert['data'])
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"保存警报到数据库失败: {e}")
    
    def _log_monitoring_summary(self) -> None:
        """
        将监控摘要记录到数据库
        """
        try:
            # 获取当前交易概览
            summary = self.get_trade_summary()
            
            query = """
            INSERT INTO monitoring_logs (timestamp, account_info, positions_count, orders_count, alerts_count)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                summary['timestamp'].timestamp(),
                str(summary['account']),
                summary['positions_count'],
                summary['orders_count'],
                summary['alerts_count']
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"记录监控日志到数据库失败: {e}")
    
    def get_alerts(self, start_time: Optional[datetime] = None, 
                  alert_types: Optional[List[str]] = None, 
                  min_severity: Optional[str] = None) -> List[Dict]:
        """
        从数据库获取警报列表
        
        参数:
            start_time: 开始时间，只返回该时间之后的警报
            alert_types: 警报类型列表，只返回指定类型的警报
            min_severity: 最低严重程度，只返回不低于该严重程度的警报
            
        返回:
            警报列表
        """
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        # 按时间过滤
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time.timestamp())
        
        # 按类型过滤
        if alert_types:
            types_placeholder = ','.join(['%s'] * len(alert_types))
            query += f" AND type IN ({types_placeholder})"
            params.extend(alert_types)
        
        # 按严重程度过滤
        if min_severity:
            severity_levels = {'low': 0, 'medium': 1, 'high': 2}
            min_level = severity_levels.get(min_severity.lower(), 0)
            
            # 将严重程度转换为可查询的列表
            query_severities = [k for k, v in severity_levels.items() if v >= min_level]
            severities_placeholder = ','.join(['%s'] * len(query_severities))
            query += f" AND severity IN ({severities_placeholder})"
            params.extend(query_severities)
        
        # 按时间排序
        query += " ORDER BY timestamp DESC"
        
        results = db_conn.execute_query(query, tuple(params))
        
        # 处理数据格式
        if results:
            for result in results:
                # 删除不需要返回的字段
                for field in ['created_at', 'updated_at']:
                    if field in result:
                        del result[field]
                
                # 将时间戳转换为datetime对象
                result['timestamp'] = datetime.fromtimestamp(result['timestamp'])
        
        return results or []
    
    def get_trade_summary(self) -> Dict:
        """
        获取交易概览
        
        返回:
            交易概览字典
        """
        # 从数据库获取当前仓位和订单数量
        positions_count = len(db_conn.execute_query("SELECT * FROM positions"))
        orders_count = len(db_conn.execute_query("SELECT * FROM orders WHERE status != 'filled'"))
        alerts_count = len(db_conn.execute_query("SELECT * FROM alerts WHERE created_at >= NOW() - INTERVAL '24 HOURS'"))
        
        # 从数据库获取仓位详情
        positions_query = """
        SELECT symbol, quantity, entry_price, market_price, market_value, unrealized_pnl, unrealized_pnl_pct 
        FROM positions
        """
        positions_data = db_conn.execute_query(positions_query)
        
        positions = {}
        for pos in positions_data:
            symbol = pos['symbol']
            positions[symbol] = {
                'quantity': pos.get('quantity', 0),
                'entry_price': pos.get('entry_price', 0),
                'market_price': pos.get('market_price', 0),
                'market_value': pos.get('market_value', 0),
                'unrealized_pnl': pos.get('unrealized_pnl', 0),
                'unrealized_pnl_pct': pos.get('unrealized_pnl_pct', 0)
            }
        
        # 计算收益率和回撤
        return_pct = 0
        drawdown = 0
        if self.account_info['initial_equity'] > 0:
            return_pct = (self.account_info['current_equity'] / self.account_info['initial_equity'] - 1)
        if self.account_info['max_equity'] > 0:
            drawdown = 1 - self.account_info['current_equity'] / self.account_info['max_equity']
        
        summary = {
            'timestamp': datetime.now(),
            'account': {
                'initial_equity': self.account_info['initial_equity'],
                'current_equity': self.account_info['current_equity'],
                'cash_balance': self.account_info['cash_balance'],
                'unrealized_pnl': self.account_info['unrealized_pnl'],
                'realized_pnl': self.account_info['realized_pnl'],
                'return_pct': return_pct,
                'drawdown': drawdown
            },
            'positions_count': positions_count,
            'orders_count': orders_count,
            'alerts_count': alerts_count,
            'last_update': datetime.now(),
            'positions': positions
        }
        
        return summary

# 创建全局交易监控器实例
trade_monitor = TradeMonitor()