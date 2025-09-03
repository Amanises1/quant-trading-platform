# 技术指标计算模块

import pandas as pd
import numpy as np
import logging

class TechnicalIndicators:
    """
    技术指标计算类，提供各种常用技术分析指标的计算方法
    """
    
    def __init__(self):
        """
        初始化技术指标计算器
        """
        self.logger = logging.getLogger(__name__)
    
    def calculate_ma(self, df, column='close', periods=[5, 10, 20, 60]):
        """
        计算移动平均线
        
        参数:
            df (pandas.DataFrame): 输入数据框
            column (str): 用于计算的列名，默认为'close'
            periods (list): 周期列表，默认为[5, 10, 20, 60]
            
        返回:
            pandas.DataFrame: 添加了移动平均线的数据框
        """
        result = df.copy()
        
        for period in periods:
            result[f'MA_{period}'] = result[column].rolling(window=period).mean()
        
        self.logger.info(f"计算了 {len(periods)} 个移动平均线指标")
        
        return result
    
    def calculate_ema(self, df, column='close', periods=[5, 10, 20, 60]):
        """
        计算指数移动平均线
        
        参数:
            df (pandas.DataFrame): 输入数据框
            column (str): 用于计算的列名，默认为'close'
            periods (list): 周期列表，默认为[5, 10, 20, 60]
            
        返回:
            pandas.DataFrame: 添加了指数移动平均线的数据框
        """
        result = df.copy()
        
        for period in periods:
            result[f'EMA_{period}'] = result[column].ewm(span=period, adjust=False).mean()
        
        self.logger.info(f"计算了 {len(periods)} 个指数移动平均线指标")
        
        return result
    
    def calculate_macd(self, df, column='close', fast_period=12, slow_period=26, signal_period=9):
        """
        计算MACD指标
        
        参数:
            df (pandas.DataFrame): 输入数据框
            column (str): 用于计算的列名，默认为'close'
            fast_period (int): 快线周期，默认为12
            slow_period (int): 慢线周期，默认为26
            signal_period (int): 信号线周期，默认为9
            
        返回:
            pandas.DataFrame: 添加了MACD指标的数据框
        """
        result = df.copy()
        
        # 计算快线和慢线的EMA
        fast_ema = result[column].ewm(span=fast_period, adjust=False).mean()
        slow_ema = result[column].ewm(span=slow_period, adjust=False).mean()
        
        # 计算MACD线
        result['MACD_line'] = fast_ema - slow_ema
        
        # 计算信号线
        result['MACD_signal'] = result['MACD_line'].ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱状图
        result['MACD_histogram'] = result['MACD_line'] - result['MACD_signal']
        
        self.logger.info(f"计算了MACD指标 (快线={fast_period}, 慢线={slow_period}, 信号线={signal_period})")
        
        return result
    
    def calculate_rsi(self, df, column='close', periods=[6, 12, 24]):
        """
        计算相对强弱指标(RSI)
        
        参数:
            df (pandas.DataFrame): 输入数据框
            column (str): 用于计算的列名，默认为'close'
            periods (list): 周期列表，默认为[6, 12, 24]
            
        返回:
            pandas.DataFrame: 添加了RSI指标的数据框
        """
        result = df.copy()
        
        # 计算价格变化
        delta = result[column].diff()
        
        for period in periods:
            # 分别计算上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 计算平均上涨和平均下跌
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # 计算相对强度
            rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)  # 避免除以零
            
            # 计算RSI
            result[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        
        self.logger.info(f"计算了 {len(periods)} 个RSI指标")
        
        return result
    
    def calculate_bollinger_bands(self, df, column='close', period=20, std_dev=2):
        """
        计算布林带指标
        
        参数:
            df (pandas.DataFrame): 输入数据框
            column (str): 用于计算的列名，默认为'close'
            period (int): 移动平均周期，默认为20
            std_dev (float): 标准差倍数，默认为2
            
        返回:
            pandas.DataFrame: 添加了布林带指标的数据框
        """
        result = df.copy()
        
        # 计算中轨(SMA)
        result['BB_middle'] = result[column].rolling(window=period).mean()
        
        # 计算标准差
        rolling_std = result[column].rolling(window=period).std()
        
        # 计算上轨和下轨
        result['BB_upper'] = result['BB_middle'] + (rolling_std * std_dev)
        result['BB_lower'] = result['BB_middle'] - (rolling_std * std_dev)
        
        # 计算带宽
        result['BB_width'] = (result['BB_upper'] - result['BB_lower']) / result['BB_middle']
        
        self.logger.info(f"计算了布林带指标 (周期={period}, 标准差倍数={std_dev})")
        
        return result
    
    def calculate_stochastic(self, df, k_period=14, d_period=3, slowing=3):
        """
        计算随机指标(KDJ)
        
        参数:
            df (pandas.DataFrame): 输入数据框，必须包含'high', 'low', 'close'列
            k_period (int): K线周期，默认为14
            d_period (int): D线周期，默认为3
            slowing (int): 减速因子，默认为3
            
        返回:
            pandas.DataFrame: 添加了随机指标的数据框
        """
        result = df.copy()
        
        # 检查必要的列是否存在
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in result.columns:
                self.logger.error(f"计算随机指标需要 {col} 列")
                return df
        
        # 计算最高价和最低价的滚动窗口
        high_roll = result['high'].rolling(window=k_period).max()
        low_roll = result['low'].rolling(window=k_period).min()
        
        # 计算未成熟随机值(%K Raw)
        result['K_raw'] = 100 * ((result['close'] - low_roll) / (high_roll - low_roll + np.finfo(float).eps))
        
        # 计算%K
        result['K'] = result['K_raw'].rolling(window=slowing).mean()
        
        # 计算%D
        result['D'] = result['K'].rolling(window=d_period).mean()
        
        # 计算%J
        result['J'] = 3 * result['K'] - 2 * result['D']
        
        self.logger.info(f"计算了随机指标 (K周期={k_period}, D周期={d_period}, 减速因子={slowing})")
        
        return result
    
    def calculate_atr(self, df, period=14):
        """
        计算平均真实范围(ATR)
        
        参数:
            df (pandas.DataFrame): 输入数据框，必须包含'high', 'low', 'close'列
            period (int): 周期，默认为14
            
        返回:
            pandas.DataFrame: 添加了ATR指标的数据框
        """
        result = df.copy()
        
        # 检查必要的列是否存在
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in result.columns:
                self.logger.error(f"计算ATR需要 {col} 列")
                return df
        
        # 计算真实范围(TR)
        result['TR'] = np.maximum(
            result['high'] - result['low'],
            np.maximum(
                np.abs(result['high'] - result['close'].shift(1)),
                np.abs(result['low'] - result['close'].shift(1))
            )
        )
        
        # 计算ATR
        result['ATR'] = result['TR'].rolling(window=period).mean()
        
        # 删除临时列
        result = result.drop('TR', axis=1)
        
        self.logger.info(f"计算了ATR指标 (周期={period})")
        
        return result
    
    def calculate_obv(self, df):
        """
        计算能量潮指标(OBV)
        
        参数:
            df (pandas.DataFrame): 输入数据框，必须包含'close'和'volume'列
            
        返回:
            pandas.DataFrame: 添加了OBV指标的数据框
        """
        result = df.copy()
        
        # 检查必要的列是否存在
        required_columns = ['close', 'volume']
        for col in required_columns:
            if col not in result.columns:
                self.logger.error(f"计算OBV需要 {col} 列")
                return df
        
        # 计算价格变化方向
        price_change = result['close'].diff()
        
        # 初始化OBV列
        result['OBV'] = 0
        
        # 根据价格变化方向累加或累减成交量
        result.loc[price_change > 0, 'OBV'] = result['volume']
        result.loc[price_change < 0, 'OBV'] = -result['volume']
        
        # 计算累积OBV
        result['OBV'] = result['OBV'].cumsum()
        
        self.logger.info("计算了OBV指标")
        
        return result
    
    def calculate_all(self, df):
        """
        计算所有技术指标
        
        参数:
            df (pandas.DataFrame): 输入数据框，必须包含OHLCV数据
            
        返回:
            pandas.DataFrame: 添加了所有技术指标的数据框
        """
        result = df.copy()
        
        # 检查必要的列是否存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in result.columns:
                self.logger.error(f"计算所有技术指标需要 {col} 列")
                return df
        
        # 计算各种技术指标
        result = self.calculate_ma(result)
        result = self.calculate_ema(result)
        result = self.calculate_macd(result)
        result = self.calculate_rsi(result)
        result = self.calculate_bollinger_bands(result)
        result = self.calculate_stochastic(result)
        result = self.calculate_atr(result)
        result = self.calculate_obv(result)
        
        self.logger.info("计算了所有技术指标")
        
        return result