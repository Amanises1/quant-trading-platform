# 均值回归策略

import pandas as pd
from ..strategy_base import BaseStrategy
from typing import Dict, Optional

class MeanReversionStrategy(BaseStrategy):
    """
    均值回归策略
    
    当价格低于移动平均线一定标准差时买入，当价格高于移动平均线一定标准差时卖出。
    这是一种基于统计均值回归理论的策略，适用于震荡市场环境。
    """
    
    def __init__(self, params: Optional[Dict] = None):
        """
        初始化均值回归策略
        
        参数:
            params: 策略参数字典，包含以下可选参数:
                - window: 移动平均线窗口大小，默认20
                - num_std: 标准差倍数，默认2.0
                - column: 用于计算的价格列，默认'close'
        """
        # 设置默认参数
        default_params = {
            'window': 20,
            'num_std': 2.0,
            'column': 'close'
        }
        
        # 合并用户参数和默认参数
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成均值回归交易信号
        
        参数:
            data: 包含价格数据的DataFrame，必须包含'close'列
            
        返回:
            包含交易信号的DataFrame，新增'mean', 'std', 'upper_band', 'lower_band'和'signal'列
        """
        # 验证数据
        if self.params['column'] not in data.columns:
            raise ValueError(f"数据中缺少{self.params['column']}列")
        
        # 复制数据以避免修改原始数据
        data_copy = data.copy()
        
        # 计算移动平均线和标准差
        window = self.params['window']
        num_std = self.params['num_std']
        column = self.params['column']
        
        data_copy['mean'] = data_copy[column].rolling(window=window).mean()
        data_copy['std'] = data_copy[column].rolling(window=window).std()
        data_copy['upper_band'] = data_copy['mean'] + (data_copy['std'] * num_std)
        data_copy['lower_band'] = data_copy['mean'] - (data_copy['std'] * num_std)
        
        # 初始化信号列
        data_copy['signal'] = 0
        
        # 生成交叉信号：当价格从下方穿越下轨时买入，从上方穿越上轨时卖出
        # 先计算前一个周期的价格
        data_copy['prev_price'] = data_copy[column].shift(1)
        
        # 买入信号：价格从下方穿越下轨（回到正常区间）
        data_copy.loc[
            (data_copy[column] >= data_copy['lower_band']) & 
            (data_copy['prev_price'] < data_copy['lower_band']), 
            'signal'
        ] = 1
        
        # 卖出信号：价格从上方穿越上轨（回到正常区间）
        data_copy.loc[
            (data_copy[column] <= data_copy['upper_band']) & 
            (data_copy['prev_price'] > data_copy['upper_band']), 
            'signal'
        ] = -1
        
        # 删除临时列
        data_copy.drop('prev_price', axis=1, inplace=True)
        
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
        # 确保有足够的数据计算移动平均线和标准差
        if len(data) < self.params['window']:
            return 0
        
        # 计算最近的移动平均线和标准差
        column = self.params['column']
        recent_data = data.tail(self.params['window'])
        
        mean = recent_data[column].mean()
        std = recent_data[column].std()
        num_std = self.params['num_std']
        
        upper_band = mean + (std * num_std)
        lower_band = mean - (std * num_std)
        
        # 获取当前价格
        current_price = data[column].iloc[-1]
        
        # 生成交易信号
        if current_price < lower_band:
            return 1  # 买入信号
        elif current_price > upper_band:
            return -1  # 卖出信号
        else:
            return 0  # 持有
    
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
        # 调用基类方法计算布林带
        return super().calculate_bollinger_bands(data, window, num_std, column)