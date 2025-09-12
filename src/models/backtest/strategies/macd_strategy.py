# MACD策略

import pandas as pd
from ..strategy_base import BaseStrategy
from typing import Dict, Optional

class MacdStrategy(BaseStrategy):
    """
    MACD（移动平均线收敛/发散）策略
    
    当MACD线（快线）上穿信号线（慢线）时买入，当MACD线下穿信号线时卖出。
    这是一种趋势跟踪策略，通过比较不同时间周期的移动平均线来识别趋势变化。
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化MACD策略
        
        参数:
            params: 策略参数字典，包含以下可选参数:
                - fast_period: 快速EMA周期，默认12
                - slow_period: 慢速EMA周期，默认26
                - signal_period: 信号线EMA周期，默认9
                - column: 用于计算的价格列，默认'close'
        """
        # 设置默认参数
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'column': 'close'
        }
        
        # 合并用户参数和默认参数
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成MACD交易信号
        
        参数:
            data: 包含价格数据的DataFrame，必须包含'close'列
            
        返回:
            包含交易信号的DataFrame，新增'fast_ema', 'slow_ema', 'macd_line', 'signal_line'和'signal'列
        """
        # 验证数据
        if self.params['column'] not in data.columns:
            raise ValueError(f"数据中缺少{self.params['column']}列")
        
        # 复制数据以避免修改原始数据
        data_copy = data.copy()
        
        # 计算MACD指标
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        signal_period = self.params['signal_period']
        column = self.params['column']
        
        # 计算快速和慢速EMA
        data_copy['fast_ema'] = self.calculate_ema(data_copy, fast_period, column)
        data_copy['slow_ema'] = self.calculate_ema(data_copy, slow_period, column)
        
        # 计算MACD线
        data_copy['macd_line'] = data_copy['fast_ema'] - data_copy['slow_ema']
        
        # 计算信号线
        data_copy['signal_line'] = data_copy['macd_line'].ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱状图
        data_copy['macd_hist'] = data_copy['macd_line'] - data_copy['signal_line']
        
        # 初始化信号列
        data_copy['signal'] = 0
        
        # 生成买入信号：MACD线上穿信号线
        cross_up = (data_copy['macd_line'] > data_copy['signal_line']) & (data_copy['macd_line'].shift(1) <= data_copy['signal_line'].shift(1))
        data_copy.loc[cross_up, 'signal'] = 1
        
        # 生成卖出信号：MACD线下穿信号线
        cross_down = (data_copy['macd_line'] < data_copy['signal_line']) & (data_copy['macd_line'].shift(1) >= data_copy['signal_line'].shift(1))
        data_copy.loc[cross_down, 'signal'] = -1
        
        # 填充NaN值
        data_copy.fillna(0, inplace=True)
        
        return data_copy
    
    def on_bar(self, data: pd.DataFrame) -> int:
        """
        处理单个时间周期的数据并返回交易信号
        
        参数:
            data: 包含当前和历史价格数据的DataFrame
            
        返回:
            交易信号 (1=买入, -1=卖出, 0=持有)
        """
        # 确保有足够的数据计算MACD
        if len(data) < self.params['slow_period'] + 1:
            return 0
        
        # 获取最近需要的数据
        recent_data = data.tail(self.params['slow_period'] + 1)
        column = self.params['column']
        
        # 计算最近的MACD线和信号线
        fast_ema = self.calculate_ema(recent_data, self.params['fast_period'], column)
        slow_ema = self.calculate_ema(recent_data, self.params['slow_period'], column)
        
        # 获取最后两个值进行交叉判断
        if len(fast_ema) < 2 or len(slow_ema) < 2:
            return 0
        
        # 计算MACD线的最后两个值
        current_macd = fast_ema.iloc[-1] - slow_ema.iloc[-1]
        prev_macd = fast_ema.iloc[-2] - slow_ema.iloc[-2]
        
        # 计算信号线
        signal_line = pd.Series([prev_macd, current_macd]).ewm(span=self.params['signal_period'], adjust=False).mean()
        
        # 获取最后两个信号线值
        prev_signal = signal_line.iloc[0]
        current_signal = signal_line.iloc[1]
        
        # 生成交易信号
        if current_macd > current_signal and prev_macd <= prev_signal:
            return 1  # 买入信号 (MACD线上穿信号线)
        elif current_macd < current_signal and prev_macd >= prev_signal:
            return -1  # 卖出信号 (MACD线下穿信号线)
        else:
            return 0  # 持有
    
    def calculate_macd(self, data: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, column: str = 'close') -> Dict[str, pd.Series]:
        """
        计算MACD指标
        
        参数:
            data: 价格数据
            fast_period: 快速EMA周期，默认12
            slow_period: 慢速EMA周期，默认26
            signal_period: 信号线EMA周期，默认9
            column: 要计算的列名
            
        返回:
            包含MACD线、信号线和MACD柱状图的字典
        """
        # 调用基类方法计算MACD
        return super().calculate_macd(data, fast_period, slow_period, signal_period, column)