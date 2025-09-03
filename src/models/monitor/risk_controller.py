# 风险控制模块

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable
from datetime import datetime, timedelta
import threading
import time

class RiskController:
    """
    风险控制类，用于实时监控和控制交易风险
    支持风险指标监控、风险预警和自动风险控制
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化风险控制器
        
        参数:
            config: 配置信息，包含风险控制参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('max_daily_loss_pct', 0.02)  # 最大日亏损比例
        self.config.setdefault('max_position_pct', 0.2)  # 最大单一仓位比例
        self.config.setdefault('max_sector_exposure_pct', 0.3)  # 最大行业敞口比例
        self.config.setdefault('max_leverage', 2.0)  # 最大杠杆倍数
        self.config.setdefault('stop_loss_pct', 0.05)  # 止损比例
        self.config.setdefault('monitoring_interval', 60)  # 监控间隔（秒）
        self.config.setdefault('auto_risk_control', False)  # 是否启用自动风险控制
        
        # 风险控制状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 风险数据
        self.risk_metrics = {}
        self.risk_alerts = []
        self.risk_actions = []
        self.last_update_time = None
        
        # 账户和交易数据
        self.account_info = {}
        self.positions = {}
        self.daily_pnl = []
    
    def start_monitoring(self, account_data_source: Callable, 
                        position_data_source: Callable,
                        order_executor: Optional[Callable] = None) -> bool:
        """
        启动风险监控
        
        参数:
            account_data_source: 账户数据源函数，用于获取账户信息
            position_data_source: 仓位数据源函数，用于获取仓位信息
            order_executor: 订单执行函数，用于执行风险控制操作（如自动平仓）
            
        返回:
            是否成功启动监控
        """
        if self.is_monitoring:
            self.logger.warning("风险监控已经在运行中")
            return False
        
        self.is_monitoring = True
        self.account_data_source = account_data_source
        self.position_data_source = position_data_source
        self.order_executor = order_executor
        
        # 初始化风险指标
        self._init_risk_metrics()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"已启动风险监控，间隔{self.config['monitoring_interval']}秒，自动风险控制：{'开启' if self.config['auto_risk_control'] else '关闭'}")
        
        return True
    
    def stop_monitoring(self) -> bool:
        """
        停止风险监控
        
        返回:
            是否成功停止监控
        """
        if not self.is_monitoring:
            self.logger.warning("风险监控未在运行")
            return False
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            self.monitor_thread = None
        
        self.logger.info("已停止风险监控")
        
        return True
    
    def _init_risk_metrics(self) -> None:
        """
        初始化风险指标
        """
        self.risk_metrics = {
            'daily_pnl_pct': 0.0,  # 当日盈亏比例
            'max_position_pct': 0.0,  # 最大单一仓位比例
            'max_sector_exposure_pct': 0.0,  # 最大行业敞口比例
            'current_leverage': 1.0,  # 当前杠杆倍数
            'portfolio_var': 0.0,  # 组合风险价值
            'portfolio_volatility': 0.0,  # 组合波动率
            'drawdown': 0.0,  # 当前回撤
            'risk_level': 'low'  # 综合风险等级
        }
    
    def _monitoring_loop(self) -> None:
        """
        监控循环，定期获取数据并进行风险分析
        """
        while self.is_monitoring:
            try:
                # 更新账户和仓位信息
                self._update_data()
                
                # 计算风险指标
                self._calculate_risk_metrics()
                
                # 检查风险阈值
                self._check_risk_thresholds()
                
                # 执行风险控制（如果启用）
                if self.config['auto_risk_control']:
                    self._execute_risk_control()
                
                # 更新最后更新时间
                self.last_update_time = datetime.now()
                
                # 等待下一次监控
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"风险监控出错: {e}")
                time.sleep(5)  # 出错后短暂等待再重试
    
    def _update_data(self) -> None:
        """
        更新账户和仓位数据
        """
        try:
            # 获取账户信息
            account_data = self.account_data_source()
            if account_data and isinstance(account_data, dict):
                self.account_info = account_data
                
                # 更新日内盈亏
                if 'daily_pnl' in account_data and 'equity' in account_data and account_data['equity'] > 0:
                    daily_pnl_pct = account_data['daily_pnl'] / account_data['equity']
                    self.daily_pnl.append({
                        'timestamp': datetime.now(),
                        'pnl': account_data['daily_pnl'],
                        'pnl_pct': daily_pnl_pct
                    })
            
            # 获取仓位信息
            position_data = self.position_data_source()
            if position_data and isinstance(position_data, dict):
                self.positions = position_data
                
        except Exception as e:
            self.logger.error(f"更新风险数据出错: {e}")
    
    def _calculate_risk_metrics(self) -> None:
        """
        计算风险指标
        """
        try:
            # 计算当日盈亏比例
            if self.daily_pnl and 'equity' in self.account_info and self.account_info['equity'] > 0:
                self.risk_metrics['daily_pnl_pct'] = self.daily_pnl[-1]['pnl_pct']
            
            # 计算最大单一仓位比例
            if self.positions and 'equity' in self.account_info and self.account_info['equity'] > 0:
                position_pcts = []
                for symbol, position in self.positions.items():
                    if 'market_value' in position:
                        position_pct = abs(position['market_value']) / self.account_info['equity']
                        position_pcts.append(position_pct)
                
                if position_pcts:
                    self.risk_metrics['max_position_pct'] = max(position_pcts)
            
            # 计算最大行业敞口比例
            if self.positions and 'equity' in self.account_info and self.account_info['equity'] > 0:
                # 按行业分组计算敞口
                sector_exposures = {}
                for symbol, position in self.positions.items():
                    if 'market_value' in position and 'sector' in position:
                        sector = position['sector']
                        if sector not in sector_exposures:
                            sector_exposures[sector] = 0
                        sector_exposures[sector] += abs(position['market_value'])
                
                # 计算行业敞口比例
                if sector_exposures:
                    sector_exposure_pcts = [exposure / self.account_info['equity'] for exposure in sector_exposures.values()]
                    self.risk_metrics['max_sector_exposure_pct'] = max(sector_exposure_pcts)
            
            # 计算当前杠杆倍数
            if 'equity' in self.account_info and 'total_position_value' in self.account_info and self.account_info['equity'] > 0:
                self.risk_metrics['current_leverage'] = self.account_info['total_position_value'] / self.account_info['equity']
            
            # 计算组合波动率（简化计算）
            if self.daily_pnl and len(self.daily_pnl) >= 5:
                # 使用最近的日收益率计算波动率
                recent_returns = [item['pnl_pct'] for item in self.daily_pnl[-20:] if 'pnl_pct' in item]
                if recent_returns:
                    self.risk_metrics['portfolio_volatility'] = np.std(recent_returns) * np.sqrt(252)  # 年化波动率
            
            # 计算组合风险价值（VaR）
            if 'portfolio_volatility' in self.risk_metrics and self.risk_metrics['portfolio_volatility'] > 0:
                # 使用参数化方法计算95%置信度的日VaR
                confidence_level = 1.645  # 95%置信度的Z值
                self.risk_metrics['portfolio_var'] = confidence_level * self.risk_metrics['portfolio_volatility'] / np.sqrt(252)
            
            # 计算当前回撤
            if 'equity' in self.account_info and 'high_watermark' in self.account_info and self.account_info['high_watermark'] > 0:
                self.risk_metrics['drawdown'] = 1 - self.account_info['equity'] / self.account_info['high_watermark']
            
            # 计算综合风险等级
            self._calculate_risk_level()
            
        except Exception as e:
            self.logger.error(f"计算风险指标出错: {e}")
    
    def _calculate_risk_level(self) -> None:
        """
        计算综合风险等级
        """
        # 风险评分（0-100）
        risk_score = 0
        
        # 根据各风险指标计算风险分数
        # 1. 日亏损
        daily_loss_score = min(100, max(0, self.risk_metrics['daily_pnl_pct'] * -100 / self.config['max_daily_loss_pct']))
        
        # 2. 最大仓位
        position_score = min(100, max(0, self.risk_metrics['max_position_pct'] * 100 / self.config['max_position_pct']))
        
        # 3. 行业敞口
        sector_score = min(100, max(0, self.risk_metrics['max_sector_exposure_pct'] * 100 / self.config['max_sector_exposure_pct']))
        
        # 4. 杠杆
        leverage_score = min(100, max(0, self.risk_metrics['current_leverage'] * 100 / self.config['max_leverage']))
        
        # 5. 回撤
        drawdown_score = min(100, max(0, self.risk_metrics['drawdown'] * 100 / 0.2))  # 假设20%回撤为满分
        
        # 加权计算总分
        weights = {
            'daily_loss': 0.25,
            'position': 0.2,
            'sector': 0.15,
            'leverage': 0.2,
            'drawdown': 0.2
        }
        
        risk_score = (daily_loss_score * weights['daily_loss'] +
                     position_score * weights['position'] +
                     sector_score * weights['sector'] +
                     leverage_score * weights['leverage'] +
                     drawdown_score * weights['drawdown'])
        
        # 根据风险分数确定风险等级
        if risk_score < 30:
            self.risk_metrics['risk_level'] = 'low'
        elif risk_score < 60:
            self.risk_metrics['risk_level'] = 'medium'
        else:
            self.risk_metrics['risk_level'] = 'high'
    
    def _check_risk_thresholds(self) -> None:
        """
        检查风险阈值，生成风险警报
        """
        try:
            # 检查日亏损
            if self.risk_metrics['daily_pnl_pct'] < 0 and abs(self.risk_metrics['daily_pnl_pct']) > self.config['max_daily_loss_pct']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'daily_loss_alert',
                    'message': f"日亏损超过阈值: {self.risk_metrics['daily_pnl_pct']:.2%}",
                    'severity': 'high',
                    'data': {
                        'daily_pnl_pct': self.risk_metrics['daily_pnl_pct'],
                        'threshold': self.config['max_daily_loss_pct']
                    }
                }
                self.risk_alerts.append(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查单一仓位
            if self.risk_metrics['max_position_pct'] > self.config['max_position_pct']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'position_size_alert',
                    'message': f"单一仓位比例超过阈值: {self.risk_metrics['max_position_pct']:.2%}",
                    'severity': 'medium',
                    'data': {
                        'max_position_pct': self.risk_metrics['max_position_pct'],
                        'threshold': self.config['max_position_pct']
                    }
                }
                self.risk_alerts.append(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查行业敞口
            if self.risk_metrics['max_sector_exposure_pct'] > self.config['max_sector_exposure_pct']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'sector_exposure_alert',
                    'message': f"行业敞口比例超过阈值: {self.risk_metrics['max_sector_exposure_pct']:.2%}",
                    'severity': 'medium',
                    'data': {
                        'max_sector_exposure_pct': self.risk_metrics['max_sector_exposure_pct'],
                        'threshold': self.config['max_sector_exposure_pct']
                    }
                }
                self.risk_alerts.append(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查杠杆
            if self.risk_metrics['current_leverage'] > self.config['max_leverage']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'leverage_alert',
                    'message': f"杠杆倍数超过阈值: {self.risk_metrics['current_leverage']:.2f}x",
                    'severity': 'high',
                    'data': {
                        'current_leverage': self.risk_metrics['current_leverage'],
                        'threshold': self.config['max_leverage']
                    }
                }
                self.risk_alerts.append(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查止损
            for symbol, position in self.positions.items():
                if 'unrealized_pnl_pct' in position and position['unrealized_pnl_pct'] < 0 and abs(position['unrealized_pnl_pct']) > self.config['stop_loss_pct']:
                    alert = {
                        'timestamp': datetime.now(),
                        'type': 'stop_loss_alert',
                        'symbol': symbol,
                        'message': f"{symbol}亏损超过止损阈值: {position['unrealized_pnl_pct']:.2%}",
                        'severity': 'high',
                        'data': {
                            'symbol': symbol,
                            'unrealized_pnl_pct': position['unrealized_pnl_pct'],
                            'threshold': self.config['stop_loss_pct']
                        }
                    }
                    self.risk_alerts.append(alert)
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
        except Exception as e:
            self.logger.error(f"检查风险阈值出错: {e}")
    
    def _execute_risk_control(self) -> None:
        """
        执行风险控制操作
        """
        if not self.order_executor:
            return
        
        try:
            # 检查是否需要执行风险控制
            risk_control_needed = False
            risk_control_actions = []
            
            # 1. 日亏损控制 - 如果日亏损超过阈值的1.5倍，平掉所有亏损仓位
            if self.risk_metrics['daily_pnl_pct'] < 0 and abs(self.risk_metrics['daily_pnl_pct']) > 1.5 * self.config['max_daily_loss_pct']:
                risk_control_needed = True
                action = {
                    'type': 'close_losing_positions',
                    'reason': f"日亏损超过阈值的1.5倍: {self.risk_metrics['daily_pnl_pct']:.2%}",
                    'positions': []
                }
                
                # 找出所有亏损仓位
                for symbol, position in self.positions.items():
                    if 'unrealized_pnl' in position and position['unrealized_pnl'] < 0:
                        action['positions'].append({
                            'symbol': symbol,
                            'quantity': position.get('quantity', 0),
                            'side': 'sell' if position.get('quantity', 0) > 0 else 'buy'
                        })
                
                if action['positions']:
                    risk_control_actions.append(action)
            
            # 2. 止损控制 - 平掉超过止损阈值的仓位
            for symbol, position in self.positions.items():
                if 'unrealized_pnl_pct' in position and position['unrealized_pnl_pct'] < 0 and abs(position['unrealized_pnl_pct']) > self.config['stop_loss_pct']:
                    risk_control_needed = True
                    action = {
                        'type': 'stop_loss',
                        'reason': f"{symbol}亏损超过止损阈值: {position['unrealized_pnl_pct']:.2%}",
                        'positions': [{
                            'symbol': symbol,
                            'quantity': position.get('quantity', 0),
                            'side': 'sell' if position.get('quantity', 0) > 0 else 'buy'
                        }]
                    }
                    risk_control_actions.append(action)
            
            # 3. 杠杆控制 - 如果杠杆超过阈值，按比例减仓
            if self.risk_metrics['current_leverage'] > self.config['max_leverage']:
                risk_control_needed = True
                # 计算需要减仓的比例
                reduction_ratio = 1 - (self.config['max_leverage'] / self.risk_metrics['current_leverage'])
                
                action = {
                    'type': 'reduce_leverage',
                    'reason': f"杠杆倍数超过阈值: {self.risk_metrics['current_leverage']:.2f}x，需减仓{reduction_ratio:.2%}",
                    'positions': []
                }
                
                # 对所有仓位按比例减仓
                for symbol, position in self.positions.items():
                    if 'quantity' in position and position['quantity'] != 0:
                        reduce_quantity = abs(position['quantity']) * reduction_ratio
                        action['positions'].append({
                            'symbol': symbol,
                            'quantity': reduce_quantity,
                            'side': 'sell' if position['quantity'] > 0 else 'buy'
                        })
                
                if action['positions']:
                    risk_control_actions.append(action)
            
            # 执行风险控制操作
            if risk_control_needed and risk_control_actions:
                for action in risk_control_actions:
                    self.logger.warning(f"执行风险控制: {action['type']} - {action['reason']}")
                    
                    # 记录风险控制操作
                    self.risk_actions.append({
                        'timestamp': datetime.now(),
                        'type': action['type'],
                        'reason': action['reason'],
                        'positions': action['positions']
                    })
                    
                    # 执行订单
                    for position in action['positions']:
                        try:
                            order_result = self.order_executor({
                                'symbol': position['symbol'],
                                'side': position['side'],
                                'quantity': position['quantity'],
                                'order_type': 'market',
                                'time_in_force': 'day',
                                'risk_control': True
                            })
                            
                            self.logger.info(f"风险控制订单执行结果: {order_result}")
                            
                        except Exception as e:
                            self.logger.error(f"执行风险控制订单出错: {e}")
            
        except Exception as e:
            self.logger.error(f"执行风险控制出错: {e}")
    
    def get_risk_alerts(self, start_time: Optional[datetime] = None, 
                       alert_types: Optional[List[str]] = None, 
                       min_severity: Optional[str] = None) -> List[Dict]:
        """
        获取风险警报列表
        
        参数:
            start_time: 开始时间，只返回该时间之后的警报
            alert_types: 警报类型列表，只返回指定类型的警报
            min_severity: 最低严重程度，只返回不低于该严重程度的警报
            
        返回:
            风险警报列表
        """
        filtered_alerts = self.risk_alerts
        
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
    
    def get_risk_summary(self) -> Dict:
        """
        获取风险概览
        
        返回:
            风险概览字典
        """
        summary = {
            'timestamp': datetime.now(),
            'risk_level': self.risk_metrics['risk_level'],
            'metrics': self.risk_metrics,
            'alerts_count': len(self.risk_alerts),
            'actions_count': len(self.risk_actions),
            'last_update': self.last_update_time,
            'config': {
                'max_daily_loss_pct': self.config['max_daily_loss_pct'],
                'max_position_pct': self.config['max_position_pct'],
                'max_sector_exposure_pct': self.config['max_sector_exposure_pct'],
                'max_leverage': self.config['max_leverage'],
                'stop_loss_pct': self.config['stop_loss_pct'],
                'auto_risk_control': self.config['auto_risk_control']
            }
        }
        
        return summary