# RSI策略

import pandas as pd
from ..strategy_base import BaseStrategy
from typing import Dict, Optional

class RsiStrategy(BaseStrategy):
    """
    RSI（相对强弱指标）策略
    
    当RSI指标低于超卖阈值时买入，当RSI指标高于超买阈值时卖出。
    这是一种超买超卖策略，适用于震荡市场环境。
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化RSI策略
        
        参数:
            params: 策略参数字典，包含以下可选参数:
                - window: RSI计算窗口大小，默认14
                - oversold: 超卖阈值，默认30
                - overbought: 超买阈值，默认70
                - column: 用于计算RSI的价格列，默认'close'
        """
        # 设置默认参数
        default_params = {
            'window': 14,
            'oversold': 30,
            'overbought': 70,
            'column': 'close'
        }
        
        # 合并用户参数和默认参数
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成RSI交易信号
        
        参数:
            data: 包含价格数据的DataFrame，必须包含'close'列
            
        返回:
            包含交易信号的DataFrame，新增'rsi'和'signal'列
        """
        # 验证数据
        if self.params['column'] not in data.columns:
            raise ValueError(f"数据中缺少{self.params['column']}列")
        
        # 复制数据以避免修改原始数据
        data_copy = data.copy()
        
        # 计算RSI指标
        window = self.params['window']
        column = self.params['column']
        
        data_copy['rsi'] = self.calculate_rsi(data_copy, window, column)
        
        # 初始化信号列
        data_copy['signal'] = 0
        
        # 生成交叉信号：当RSI从超卖区间进入正常区间时买入，从超买区间进入正常区间时卖出
        oversold = self.params['oversold']
        overbought = self.params['overbought']
        
        # 先计算前一个周期的RSI
        data_copy['prev_rsi'] = data_copy['rsi'].shift(1)
        
        # 买入信号：RSI从下方穿越超卖阈值（进入正常区间）
        data_copy.loc[
            (data_copy['rsi'] >= oversold) & 
            (data_copy['prev_rsi'] < oversold), 
            'signal'
        ] = 1
        
        # 卖出信号：RSI从上方穿越超买阈值（进入正常区间）
        data_copy.loc[
            (data_copy['rsi'] <= overbought) & 
            (data_copy['prev_rsi'] > overbought), 
            'signal'
        ] = -1
        
        # 删除临时列
        data_copy.drop('prev_rsi', axis=1, inplace=True)
        
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
        # 确保有足够的数据计算RSI
        if len(data) < self.params['window'] + 1:
            return 0
        
        # 计算最近一个周期的RSI
        rsi = self.calculate_rsi(data, self.params['window'], self.params['column']).iloc[-1]
        
        # 生成交易信号
        if rsi < self.params['oversold']:
            return 1  # 买入信号
        elif rsi > self.params['overbought']:
            return -1  # 卖出信号
        else:
            return 0  # 持有
    
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
        # 调用基类方法计算RSI
        return super().calculate_rsi(data, window, column)