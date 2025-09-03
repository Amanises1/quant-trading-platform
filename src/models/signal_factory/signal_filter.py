# 信号过滤器模块

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable

class SignalFilter:
    """
    信号过滤器基类，用于过滤和优化交易信号
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信号过滤器
        
        参数:
            config: 配置信息，包含过滤器的参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def filter_signals(self, df: pd.DataFrame, signal_column: str = 'signal') -> pd.DataFrame:
        """
        过滤信号的基础方法，需要在子类中实现
        
        参数:
            df: 输入的数据框，包含信号列
            signal_column: 信号列的名称
            
        返回:
            过滤后的数据框
        """
        raise NotImplementedError("子类必须实现此方法")


class TimeFilterSignalFilter(SignalFilter):
    """
    基于时间的信号过滤器，可以限制特定时间段的交易
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化时间过滤器
        
        参数:
            config: 配置信息，包含以下参数：
                - trading_hours: 交易时间段，格式为[(start_hour, start_minute), (end_hour, end_minute)]
                - trading_days: 交易日，格式为[0, 1, 2, 3, 4]（0表示周一，6表示周日）
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('trading_hours', [(9, 30), (15, 0)])
        self.config.setdefault('trading_days', [0, 1, 2, 3, 4])  # 默认为工作日
    
    def filter_signals(self, df: pd.DataFrame, signal_column: str = 'signal') -> pd.DataFrame:
        """
        基于时间过滤信号
        
        参数:
            df: 输入的数据框，必须包含datetime索引或'datetime'列
            signal_column: 信号列的名称
            
        返回:
            过滤后的数据框
        """
        result = df.copy()
        
        # 确保有日期时间列
        if not isinstance(result.index, pd.DatetimeIndex) and 'datetime' not in result.columns:
            self.logger.error("数据框必须包含datetime索引或'datetime'列")
            return df
        
        datetime_col = result.index if isinstance(result.index, pd.DatetimeIndex) else result['datetime']
        
        # 过滤交易日
        if 'trading_days' in self.config:
            trading_days = self.config['trading_days']
            weekday = datetime_col.dt.weekday
            valid_days = weekday.isin(trading_days)
            result.loc[~valid_days, signal_column] = 0
        
        # 过滤交易时间
        if 'trading_hours' in self.config:
            trading_hours = self.config['trading_hours']
            start_hour, start_minute = trading_hours[0]
            end_hour, end_minute = trading_hours[1]
            
            hour = datetime_col.dt.hour
            minute = datetime_col.dt.minute
            
            # 创建时间戳以便比较
            time_stamp = hour * 100 + minute
            start_stamp = start_hour * 100 + start_minute
            end_stamp = end_hour * 100 + end_minute
            
            valid_time = (time_stamp >= start_stamp) & (time_stamp <= end_stamp)
            result.loc[~valid_time, signal_column] = 0
        
        self.logger.info(f"基于时间过滤了信号")
        
        return result


class VolatilitySignalFilter(SignalFilter):
    """
    基于波动率的信号过滤器，可以在高波动率环境下调整信号
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化波动率过滤器
        
        参数:
            config: 配置信息，包含以下参数：
                - volatility_period: 波动率计算周期，默认为20
                - volatility_threshold: 波动率阈值，默认为0.02 (2%)
                - volatility_adjustment: 波动率调整方式，可选值为'filter'或'scale'，默认为'filter'
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('volatility_period', 20)
        self.config.setdefault('volatility_threshold', 0.02)
        self.config.setdefault('volatility_adjustment', 'filter')  # 'filter'或'scale'
    
    def filter_signals(self, df: pd.DataFrame, signal_column: str = 'signal') -> pd.DataFrame:
        """
        基于波动率过滤信号
        
        参数:
            df: 输入的数据框，必须包含'close'列
            signal_column: 信号列的名称
            
        返回:
            过滤后的数据框
        """
        result = df.copy()
        
        # 确保有收盘价列
        if 'close' not in result.columns:
            self.logger.error("数据框必须包含'close'列")
            return df
        
        # 计算波动率（使用收益率的标准差）
        returns = result['close'].pct_change()
        volatility = returns.rolling(window=self.config['volatility_period']).std()
        result['volatility'] = volatility
        
        # 根据波动率调整信号
        if self.config['volatility_adjustment'] == 'filter':
            # 在高波动率环境下过滤掉信号
            high_volatility = volatility > self.config['volatility_threshold']
            result.loc[high_volatility, signal_column] = 0
            
            self.logger.info(f"在高波动率环境下过滤了信号 (阈值={self.config['volatility_threshold']})")
            
        elif self.config['volatility_adjustment'] == 'scale':
            # 根据波动率缩放信号强度
            volatility_ratio = self.config['volatility_threshold'] / volatility
            volatility_ratio = volatility_ratio.clip(upper=1.0)  # 最大不超过1
            
            # 保留信号方向，但缩放信号强度
            result[signal_column] = result[signal_column] * volatility_ratio
            
            # 将缩放后的连续值转回离散信号
            result.loc[result[signal_column] > 0.5, signal_column] = 1
            result.loc[result[signal_column] < -0.5, signal_column] = -1
            result.loc[(result[signal_column] >= -0.5) & (result[signal_column] <= 0.5), signal_column] = 0
            
            self.logger.info(f"根据波动率缩放了信号强度 (阈值={self.config['volatility_threshold']})")
            
        else:
            self.logger.error(f"不支持的波动率调整方式: {self.config['volatility_adjustment']}")
        
        return result


class TrendSignalFilter(SignalFilter):
    """
    基于趋势的信号过滤器，可以根据市场趋势调整信号
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化趋势过滤器
        
        参数:
            config: 配置信息，包含以下参数：
                - trend_ma_period: 趋势移动平均线周期，默认为50
                - trend_filter_type: 趋势过滤类型，可选值为'with_trend'或'against_trend'，默认为'with_trend'
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('trend_ma_period', 50)
        self.config.setdefault('trend_filter_type', 'with_trend')  # 'with_trend'或'against_trend'
    
    def filter_signals(self, df: pd.DataFrame, signal_column: str = 'signal') -> pd.DataFrame:
        """
        基于趋势过滤信号
        
        参数:
            df: 输入的数据框，必须包含'close'列
            signal_column: 信号列的名称
            
        返回:
            过滤后的数据框
        """
        result = df.copy()
        
        # 确保有收盘价列
        if 'close' not in result.columns:
            self.logger.error("数据框必须包含'close'列")
            return df
        
        # 计算趋势（使用移动平均线）
        ma_period = self.config['trend_ma_period']
        result['trend_ma'] = result['close'].rolling(window=ma_period).mean()
        
        # 确定趋势方向
        result['trend'] = 0
        result.loc[result['close'] > result['trend_ma'], 'trend'] = 1  # 上升趋势
        result.loc[result['close'] < result['trend_ma'], 'trend'] = -1  # 下降趋势
        
        # 根据趋势过滤信号
        if self.config['trend_filter_type'] == 'with_trend':
            # 只保留与趋势一致的信号
            valid_signal = (result[signal_column] > 0) & (result['trend'] > 0) | \
                          (result[signal_column] < 0) & (result['trend'] < 0)
            result.loc[~valid_signal, signal_column] = 0
            
            self.logger.info(f"保留了与趋势一致的信号 (MA周期={ma_period})")
            
        elif self.config['trend_filter_type'] == 'against_trend':
            # 只保留与趋势相反的信号（反转交易）
            valid_signal = (result[signal_column] > 0) & (result['trend'] < 0) | \
                          (result[signal_column] < 0) & (result['trend'] > 0)
            result.loc[~valid_signal, signal_column] = 0
            
            self.logger.info(f"保留了与趋势相反的信号 (MA周期={ma_period})")
            
        else:
            self.logger.error(f"不支持的趋势过滤类型: {self.config['trend_filter_type']}")
        
        return result


class FrequencySignalFilter(SignalFilter):
    """
    基于频率的信号过滤器，可以限制信号生成的频率
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化频率过滤器
        
        参数:
            config: 配置信息，包含以下参数：
                - min_periods_between_signals: 信号之间的最小周期数，默认为5
                - reset_after_opposite: 是否在出现相反信号后重置计数器，默认为True
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('min_periods_between_signals', 5)
        self.config.setdefault('reset_after_opposite', True)
    
    def filter_signals(self, df: pd.DataFrame, signal_column: str = 'signal') -> pd.DataFrame:
        """
        基于频率过滤信号
        
        参数:
            df: 输入的数据框，包含信号列
            signal_column: 信号列的名称
            
        返回:
            过滤后的数据框
        """
        result = df.copy()
        min_periods = self.config['min_periods_between_signals']
        reset_after_opposite = self.config['reset_after_opposite']
        
        # 初始化计数器和过滤后的信号列
        result['filtered_signal'] = 0
        last_signal = 0
        periods_since_last_signal = min_periods  # 初始化为最小周期数，以便第一个信号可以通过
        
        # 逐行处理信号
        for i in range(len(result)):
            current_signal = result.iloc[i][signal_column]
            
            # 如果当前有信号
            if current_signal != 0:
                # 如果已经过了足够的周期，或者出现了相反的信号且设置了重置
                if periods_since_last_signal >= min_periods or \
                   (reset_after_opposite and current_signal * last_signal < 0):
                    result.iloc[i, result.columns.get_loc('filtered_signal')] = current_signal
                    last_signal = current_signal
                    periods_since_last_signal = 0
            
            periods_since_last_signal += 1
        
        # 用过滤后的信号替换原信号
        result[signal_column] = result['filtered_signal']
        result = result.drop('filtered_signal', axis=1)
        
        self.logger.info(f"基于频率过滤了信号 (最小周期数={min_periods})")
        
        return result


class SignalFilterPipeline:
    """
    信号过滤器管道，可以按顺序应用多个过滤器
    """
    
    def __init__(self):
        """
        初始化信号过滤器管道
        """
        self.filters = []
        self.logger = logging.getLogger(__name__)
    
    def add_filter(self, filter_instance: SignalFilter):
        """
        添加过滤器到管道
        
        参数:
            filter_instance: 信号过滤器实例
        """
        self.filters.append(filter_instance)
        self.logger.info(f"添加了过滤器: {filter_instance.__class__.__name__}")
    
    def apply_filters(self, df: pd.DataFrame, signal_column: str = 'signal') -> pd.DataFrame:
        """
        按顺序应用所有过滤器
        
        参数:
            df: 输入的数据框，包含信号列
            signal_column: 信号列的名称
            
        返回:
            过滤后的数据框
        """
        result = df.copy()
        
        for filter_instance in self.filters:
            result = filter_instance.filter_signals(result, signal_column)
        
        self.logger.info(f"应用了{len(self.filters)}个过滤器")
        
        return result