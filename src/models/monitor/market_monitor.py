# 市场监控模块

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable
from datetime import datetime, timedelta
import threading
import time

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
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 监控数据
        self.market_data = {}
        self.alerts = []
        self.last_update_time = None
    
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
        
        # 初始化市场数据
        for symbol in symbols:
            self.market_data[symbol] = {
                'price_history': [],
                'volume_history': [],
                'volatility': 0.0,
                'avg_volume': 0.0,
                'last_price': 0.0,
                'last_volume': 0.0
            }
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"已启动市场监控，监控{len(symbols)}个交易品种，间隔{self.config['monitoring_interval']}秒")
        
        return True
    
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
                
                # 更新历史数据
                self.market_data[symbol]['price_history'].append(price)
                self.market_data[symbol]['volume_history'].append(volume)
                
                # 限制历史数据长度
                max_history = 100  # 保留最近100个数据点
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
    
    def get_market_summary(self) -> Dict:
        """
        获取市场概览
        
        返回:
            市场概览字典
        """
        summary = {
            'timestamp': datetime.now(),
            'symbols_count': len(self.symbols),
            'alerts_count': len(self.alerts),
            'last_update': self.last_update_time,
            'symbols_data': {}
        }
        
        # 添加各交易品种的摘要数据
        for symbol in self.symbols:
            data = self.market_data.get(symbol, {})
            if not data or 'last_price' not in data:
                continue
                
            summary['symbols_data'][symbol] = {
                'last_price': data.get('last_price', 0.0),
                'volatility': data.get('volatility', 0.0),
                'avg_volume': data.get('avg_volume', 0.0),
                'last_volume': data.get('last_volume', 0.0)
            }
        
        return summary