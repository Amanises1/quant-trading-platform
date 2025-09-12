# 移动平均线交叉策略

import pandas as pd
from ..strategy_base import BaseStrategy
from typing import Dict, Optional

class SimpleMovingAverageStrategy(BaseStrategy):
    """
    移动平均线交叉策略
    
    当短期移动平均线上穿长期移动平均线时买入，当短期移动平均线下穿长期移动平均线时卖出。
    这是一种趋势跟踪策略，适用于有明显趋势的市场环境。
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化移动平均线交叉策略
        
        参数:
            params: 策略参数字典，包含以下可选参数:
                - short_window: 短期移动平均线窗口大小，默认5
                - long_window: 长期移动平均线窗口大小，默认20
                - column: 用于计算移动平均线的价格列，默认'close'
        """
        # 设置默认参数
        default_params = {
            'short_window': 5,
            'long_window': 20,
            'column': 'close'
        }
        
        # 合并用户参数和默认参数
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成移动平均线交叉交易信号
        
        参数:
            data: 包含价格数据的DataFrame，必须包含'close'列
            
        返回:
            包含交易信号的DataFrame，新增'short_sma', 'long_sma'和'signal'列
        """
        # 验证数据
        if self.params['column'] not in data.columns:
            raise ValueError(f"数据中缺少{self.params['column']}列")
        
        # 复制数据以避免修改原始数据
        data_copy = data.copy()
        
        # 计算短期和长期移动平均线
        short_window = self.params['short_window']
        long_window = self.params['long_window']
        column = self.params['column']
        
        data_copy['short_sma'] = self.calculate_sma(data_copy, short_window, column)
        data_copy['long_sma'] = self.calculate_sma(data_copy, long_window, column)
        
        # 初始化信号列
        data_copy['signal'] = 0
        
        # 生成交叉信号：当短期均线上穿长期均线时买入，下穿时卖出
        # 先计算前一个周期的信号
        data_copy['prev_short_sma'] = data_copy['short_sma'].shift(1)
        data_copy['prev_long_sma'] = data_copy['long_sma'].shift(1)
        
        # 金叉信号：短期均线上穿长期均线
        data_copy.loc[
            (data_copy['short_sma'] > data_copy['long_sma']) & 
            (data_copy['prev_short_sma'] <= data_copy['prev_long_sma']), 
            'signal'
        ] = 1
        
        # 死叉信号：短期均线下穿长期均线
        data_copy.loc[
            (data_copy['short_sma'] < data_copy['long_sma']) & 
            (data_copy['prev_short_sma'] >= data_copy['prev_long_sma']), 
            'signal'
        ] = -1
        
        # 删除临时列
        data_copy.drop(['prev_short_sma', 'prev_long_sma'], axis=1, inplace=True)
        
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
        # 确保有足够的数据计算移动平均线
        if len(data) < max(self.params['short_window'], self.params['long_window']):
            return 0
        
        # 计算最近一个周期的移动平均线
        short_sma = self.calculate_sma(data, self.params['short_window'], self.params['column']).iloc[-1]
        long_sma = self.calculate_sma(data, self.params['long_window'], self.params['column']).iloc[-1]
        
        # 生成交易信号
        if short_sma > long_sma:
            return 1  # 买入信号
        elif short_sma < long_sma:
            return -1  # 卖出信号
        else:
            return 0  # 持有