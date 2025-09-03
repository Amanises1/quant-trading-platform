# 交易监控模块

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable
from datetime import datetime, timedelta
import threading
import time

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
        
        # 监控数据
        self.orders = []
        self.positions = {}
        self.trade_history = []
        self.alerts = []
        self.last_update_time = None
        
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
    
    def start_monitoring(self, trade_data_source: Callable, account_data_source: Callable) -> bool:
        """
        启动交易监控
        
        参数:
            trade_data_source: 交易数据源函数，用于获取订单和仓位信息
            account_data_source: 账户数据源函数，用于获取账户信息
            
        返回:
            是否成功启动监控
        """
        if self.is_monitoring:
            self.logger.warning("交易监控已经在运行中")
            return False
        
        self.is_monitoring = True
        self.trade_data_source = trade_data_source
        self.account_data_source = account_data_source
        
        # 初始化账户信息
        self._update_account_info()
        self.account_info['initial_equity'] = self.account_info['current_equity']
        self.account_info['max_equity'] = self.account_info['current_equity']
        
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
                
                # 更新最后更新时间
                self.last_update_time = datetime.now()
                
                # 等待下一次监控
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"交易监控出错: {e}")
                time.sleep(5)  # 出错后短暂等待再重试
    
    def _update_account_info(self) -> None:
        """
        更新账户信息
        """
        try:
            # 调用账户数据源函数获取最新账户信息
            account_data = self.account_data_source()
            
            if account_data is None or not isinstance(account_data, dict):
                self.logger.warning("获取账户信息失败")
                return
            
            # 更新账户信息
            self.account_info['current_equity'] = account_data.get('equity', self.account_info['current_equity'])
            self.account_info['cash_balance'] = account_data.get('cash', self.account_info['cash_balance'])
            self.account_info['margin_used'] = account_data.get('margin', self.account_info['margin_used'])
            self.account_info['unrealized_pnl'] = account_data.get('unrealized_pnl', self.account_info['unrealized_pnl'])
            self.account_info['realized_pnl'] = account_data.get('realized_pnl', self.account_info['realized_pnl'])
            
            # 更新最大权益
            if self.account_info['current_equity'] > self.account_info['max_equity']:
                self.account_info['max_equity'] = self.account_info['current_equity']
            
        except Exception as e:
            self.logger.error(f"更新账户信息出错: {e}")
    
    def _update_trade_data(self) -> None:
        """
        更新交易数据
        """
        try:
            # 调用交易数据源函数获取最新订单和仓位信息
            trade_data = self.trade_data_source()
            
            if trade_data is None or not isinstance(trade_data, dict):
                self.logger.warning("获取交易数据失败")
                return
            
            # 更新订单信息
            new_orders = trade_data.get('orders', [])
            if new_orders:
                # 合并新订单，避免重复
                existing_order_ids = {order['order_id'] for order in self.orders}
                for order in new_orders:
                    if order.get('order_id') not in existing_order_ids:
                        self.orders.append(order)
                        # 如果是已完成的订单，添加到交易历史
                        if order.get('status') in ['filled', 'partially_filled', 'canceled', 'rejected']:
                            self.trade_history.append({
                                'timestamp': order.get('update_time', datetime.now()),
                                'order_id': order.get('order_id'),
                                'symbol': order.get('symbol'),
                                'side': order.get('side'),
                                'quantity': order.get('filled_quantity', 0),
                                'price': order.get('average_price', 0),
                                'status': order.get('status'),
                                'order_type': order.get('order_type')
                            })
            
            # 更新仓位信息
            new_positions = trade_data.get('positions', {})
            if new_positions:
                self.positions = new_positions
            
        except Exception as e:
            self.logger.error(f"更新交易数据出错: {e}")
    
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
            alert = {
                'timestamp': datetime.now(),
                'type': 'drawdown_alert',
                'message': f"账户回撤超过阈值: {drawdown:.2%}",
                'severity': 'high' if drawdown > 1.5 * self.config['max_drawdown_threshold'] else 'medium',
                'data': {
                    'current_equity': self.account_info['current_equity'],
                    'max_equity': self.account_info['max_equity'],
                    'drawdown': drawdown,
                    'threshold': self.config['max_drawdown_threshold']
                }
            }
            self.alerts.append(alert)
            self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
    
    def _check_position_size(self) -> None:
        """
        检查仓位大小
        """
        if not self.positions or self.account_info['current_equity'] <= 0:
            return
        
        for symbol, position in self.positions.items():
            # 计算仓位比例
            position_value = position.get('market_value', 0)
            position_ratio = position_value / self.account_info['current_equity']
            
            # 检查是否超过最大仓位比例
            if position_ratio > self.config['max_position_size']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'position_size_alert',
                    'symbol': symbol,
                    'message': f"{symbol}仓位比例超过阈值: {position_ratio:.2%}",
                    'severity': 'high' if position_ratio > 1.5 * self.config['max_position_size'] else 'medium',
                    'data': {
                        'position_value': position_value,
                        'equity': self.account_info['current_equity'],
                        'position_ratio': position_ratio,
                        'threshold': self.config['max_position_size']
                    }
                }
                self.alerts.append(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
    
    def _check_order_execution(self) -> None:
        """
        检查订单执行情况
        """
        # 检查最近的订单
        recent_orders = [order for order in self.orders if order.get('status') == 'filled' and 
                        order.get('update_time') and 
                        (datetime.now() - order['update_time']).total_seconds() < 3600]  # 最近1小时内的订单
        
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
                        'timestamp': datetime.now(),
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
                    self.alerts.append(alert)
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
    
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
        filtered_alerts = self.alerts
        
        # 按时间过滤
        if start_time:
            filtered_alerts = [alert for alert in filtered_alerts if alert['timestamp'] >= start_time]
        
        # 按类型过滤
        if alert_types:
            filtered_alerts = [alert for alert in filtered_alerts if alert['type'] in alert_types]
        
        # 按严重程度过滤
        if min_severity:
            severity_levels = {'low': 0, 'medium': 1, 'high': 2}
            min_level = severity_levels.get(min_severity.lower(), 0)
            filtered_alerts = [alert for alert in filtered_alerts if severity_levels.get(alert['severity'].lower(), 0) >= min_level]
        
        return filtered_alerts
    
    def get_trade_summary(self) -> Dict:
        """
        获取交易概览
        
        返回:
            交易概览字典
        """
        summary = {
            'timestamp': datetime.now(),
            'account': {
                'initial_equity': self.account_info['initial_equity'],
                'current_equity': self.account_info['current_equity'],
                'cash_balance': self.account_info['cash_balance'],
                'unrealized_pnl': self.account_info['unrealized_pnl'],
                'realized_pnl': self.account_info['realized_pnl'],
                'return_pct': (self.account_info['current_equity'] / self.account_info['initial_equity'] - 1) if self.account_info['initial_equity'] > 0 else 0,
                'drawdown': (1 - self.account_info['current_equity'] / self.account_info['max_equity']) if self.account_info['max_equity'] > 0 else 0
            },
            'positions_count': len(self.positions),
            'orders_count': len(self.orders),
            'alerts_count': len(self.alerts),
            'last_update': self.last_update_time,
            'positions': {}
        }
        
        # 添加各仓位的摘要数据
        for symbol, position in self.positions.items():
            summary['positions'][symbol] = {
                'quantity': position.get('quantity', 0),
                'entry_price': position.get('entry_price', 0),
                'market_price': position.get('market_price', 0),
                'market_value': position.get('market_value', 0),
                'unrealized_pnl': position.get('unrealized_pnl', 0),
                'unrealized_pnl_pct': position.get('unrealized_pnl_pct', 0)
            }
        
        return summary