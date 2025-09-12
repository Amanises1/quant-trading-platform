# 策略基类模块

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Callable
import logging

class Strategy:
    """
    交易策略基类，所有具体策略都应该继承自这个类
    提供统一的策略接口和基础功能
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化策略
        
        参数:
            params: 策略参数字典
        """
        self.params = params or {}
        self.logger = logging.getLogger(__name__)
        self.name = self.__class__.__name__
        self.initialized = False
        
    def initialize(self):
        """
        初始化策略的资源和状态
        在策略开始运行前调用
        """
        self.initialized = True
        self.logger.info(f"策略 {self.name} 初始化完成")
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        必须在子类中实现
        
        参数:
            data: 包含价格数据的DataFrame
            
        返回:
            包含交易信号的DataFrame
        """
        raise NotImplementedError("generate_signals 方法必须在子类中实现")
    
    def on_bar(self, data: pd.DataFrame) -> int:
        """
        处理单个时间周期的数据并返回交易信号
        可以在子类中实现
        
        参数:
            data: 包含当前和历史价格数据的DataFrame
            
        返回:
            交易信号 (1=买入, -1=卖出, 0=持有)
        """
        return 0
    
    def on_tick(self, data: Dict) -> int:
        """
        处理tick级数据并返回交易信号
        可以在子类中实现
        
        参数:
            data: 包含当前tick数据的字典
            
        返回:
            交易信号 (1=买入, -1=卖出, 0=持有)
        """
        return 0
    
    def update_params(self, params: Dict):
        """
        更新策略参数
        
        参数:
            params: 新的策略参数字典
        """
        self.params.update(params)
        self.logger.info(f"策略 {self.name} 参数已更新: {params}")
        
    def get_params(self) -> Dict:
        """
        获取策略当前参数
        
        返回:
            策略参数字典
        """
        return self.params
    
    def get_name(self) -> str:
        """
        获取策略名称
        
        返回:
            策略名称字符串
        """
        return self.name
    
    def __str__(self) -> str:
        return f"Strategy(name={self.name}, params={self.params})"

class BaseStrategy(Strategy):
    """
    基础策略实现，提供一些常用的技术指标计算方法
    """
    
    def __init__(self, params: Optional[Dict] = None):
        super().__init__(params)
        
    def calculate_sma(self, data: pd.DataFrame, window: int, column: str = 'close') -> pd.Series:
        """
        计算简单移动平均线
        
        参数:
            data: 价格数据
            window: 窗口大小
            column: 要计算的列名
            
        返回:
            移动平均线序列
        """
        return data[column].rolling(window=window).mean()
    
    def calculate_ema(self, data: pd.DataFrame, window: int, column: str = 'close') -> pd.Series:
        """
        计算指数移动平均线
        
        参数:
            data: 价格数据
            window: 窗口大小
            column: 要计算的列名
            
        返回:
            指数移动平均线序列
        """
        return data[column].ewm(span=window, adjust=False).mean()
    
    def calculate_rsi(self, data: pd.DataFrame, window: int = 14, column: str = 'close') -> pd.Series:
        """
        计算相对强弱指标RSI
        
        参数:
            data: 价格数据
            window: 窗口大小，默认14
            column: 要计算的列名
            
        返回:
            RSI序列
        """
        delta = data[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_bollinger_bands(self, data: pd.DataFrame, window: int = 20, num_std: float = 2.0, column: str = 'close') -> Dict[str, pd.Series]:
        """
        计算布林带指标
        
        参数:
            data: 价格数据
            window: 窗口大小，默认20
            num_std: 标准差倍数，默认2.0
            column: 要计算的列名
            
        返回:
            包含中轨、上轨和下轨的字典
        """
        middle_band = data[column].rolling(window=window).mean()
        std = data[column].rolling(window=window).std()
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)
        
        return {
            'middle_band': middle_band,
            'upper_band': upper_band,
            'lower_band': lower_band
        }
    
    def calculate_macd(self, data: pd.DataFrame, fast_window: int = 12, slow_window: int = 26, signal_window: int = 9, column: str = 'close') -> Dict[str, pd.Series]:
        """
        计算MACD指标
        
        参数:
            data: 价格数据
            fast_window: 快线窗口大小，默认12
            slow_window: 慢线窗口大小，默认26
            signal_window: 信号线窗口大小，默认9
            column: 要计算的列名
            
        返回:
            包含MACD线、信号线和MACD柱状图的字典
        """
        fast_ema = self.calculate_ema(data, fast_window, column)
        slow_ema = self.calculate_ema(data, slow_window, column)
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
        macd_hist = macd_line - signal_line
        
        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'macd_hist': macd_hist
        }
    
    def calculate_atr(self, data: pd.DataFrame, window: int = 14) -> pd.Series:
        """
        计算平均真实波动幅度ATR
        
        参数:
            data: 包含high, low, close列的价格数据
            window: 窗口大小，默认14
            
        返回:
            ATR序列
        """
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()
        
        return atr
    
    def calculate_obv(self, data: pd.DataFrame) -> pd.Series:
        """
        计算能量潮指标OBV
        
        参数:
            data: 包含close和volume列的价格数据
            
        返回:
            OBV序列
        """
        obv = pd.Series(0, index=data.index)
        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
            elif data['close'].iloc[i] < data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv


# 注意：策略模块应使用trade_executor.py中的Order、Trade和Position类
# 这里不重复定义这些类，以避免混淆和冲突

# 策略开发者可以通过以下方式导入这些类：
# from .trade_executor import Order, Trade, Position