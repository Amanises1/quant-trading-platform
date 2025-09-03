# 信号组合器模块

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable
from .signal_generator import SignalGenerator

class SignalCombiner:
    """
    信号组合器，用于组合多个信号生成器的信号
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信号组合器
        
        参数:
            config: 配置信息，包含组合策略的参数
        """
        self.config = config or {}
        self.signal_generators = []
        self.weights = []
        self.logger = logging.getLogger(__name__)
    
    def add_signal_generator(self, generator: SignalGenerator, weight: float = 1.0):
        """
        添加信号生成器
        
        参数:
            generator: 信号生成器实例
            weight: 该信号生成器的权重，默认为1.0
        """
        self.signal_generators.append(generator)
        self.weights.append(weight)
        self.logger.info(f"添加了信号生成器: {generator.__class__.__name__}, 权重: {weight}")
    
    def combine_signals(self, df: pd.DataFrame, method: str = 'weighted_average') -> pd.DataFrame:
        """
        组合多个信号生成器的信号
        
        参数:
            df: 输入的数据框
            method: 组合方法，可选值为：
                - 'weighted_average': 加权平均
                - 'majority_vote': 多数投票
                - 'unanimous': 一致同意
                - 'custom': 自定义组合函数（需要在config中提供'custom_combiner'函数）
            
        返回:
            添加了组合信号列的数据框
        """
        if not self.signal_generators:
            self.logger.warning("没有添加任何信号生成器")
            return df
        
        result = df.copy()
        signals = []
        
        # 生成各个信号
        for i, generator in enumerate(self.signal_generators):
            signal_df = generator.generate_signals(df)
            signal_col = f"signal_{i}"
            result[signal_col] = signal_df['signal']
            signals.append(signal_col)
        
        # 组合信号
        if method == 'weighted_average':
            self._combine_weighted_average(result, signals)
        elif method == 'majority_vote':
            self._combine_majority_vote(result, signals)
        elif method == 'unanimous':
            self._combine_unanimous(result, signals)
        elif method == 'custom' and 'custom_combiner' in self.config:
            custom_combiner = self.config['custom_combiner']
            if callable(custom_combiner):
                result = custom_combiner(result, signals, self.weights)
            else:
                self.logger.error("自定义组合函数不可调用")
        else:
            self.logger.error(f"不支持的组合方法: {method}")
            return df
        
        self.logger.info(f"使用{method}方法组合了{len(signals)}个信号")
        
        return result
    
    def _combine_weighted_average(self, df: pd.DataFrame, signal_columns: List[str]):
        """
        使用加权平均方法组合信号
        
        参数:
            df: 输入的数据框
            signal_columns: 信号列名列表
        """
        df['combined_signal_value'] = 0
        
        total_weight = sum(self.weights)
        normalized_weights = [w / total_weight for w in self.weights]
        
        for i, col in enumerate(signal_columns):
            df['combined_signal_value'] += df[col] * normalized_weights[i]
        
        # 将连续值转换为离散信号
        df['combined_signal'] = 0
        threshold = self.config.get('signal_threshold', 0.5)
        
        df.loc[df['combined_signal_value'] >= threshold, 'combined_signal'] = 1
        df.loc[df['combined_signal_value'] <= -threshold, 'combined_signal'] = -1
    
    def _combine_majority_vote(self, df: pd.DataFrame, signal_columns: List[str]):
        """
        使用多数投票方法组合信号
        
        参数:
            df: 输入的数据框
            signal_columns: 信号列名列表
        """
        df['buy_votes'] = 0
        df['sell_votes'] = 0
        
        for i, col in enumerate(signal_columns):
            df.loc[df[col] == 1, 'buy_votes'] += self.weights[i]
            df.loc[df[col] == -1, 'sell_votes'] += self.weights[i]
        
        df['combined_signal'] = 0
        df.loc[df['buy_votes'] > df['sell_votes'], 'combined_signal'] = 1
        df.loc[df['sell_votes'] > df['buy_votes'], 'combined_signal'] = -1
    
    def _combine_unanimous(self, df: pd.DataFrame, signal_columns: List[str]):
        """
        使用一致同意方法组合信号（所有信号一致才生成组合信号）
        
        参数:
            df: 输入的数据框
            signal_columns: 信号列名列表
        """
        df['combined_signal'] = 0
        
        # 检查是否所有信号都是买入
        all_buy = df[signal_columns].eq(1).all(axis=1)
        df.loc[all_buy, 'combined_signal'] = 1
        
        # 检查是否所有信号都是卖出
        all_sell = df[signal_columns].eq(-1).all(axis=1)
        df.loc[all_sell, 'combined_signal'] = -1


class AdaptiveSignalCombiner(SignalCombiner):
    """
    自适应信号组合器，根据历史表现动态调整信号生成器的权重
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化自适应信号组合器
        
        参数:
            config: 配置信息，包含以下参数：
                - lookback_period: 回顾期，用于评估信号生成器的表现，默认为20
                - learning_rate: 学习率，用于调整权重，默认为0.1
                - performance_metric: 性能指标，可选值为'accuracy'、'profit'，默认为'profit'
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('lookback_period', 20)
        self.config.setdefault('learning_rate', 0.1)
        self.config.setdefault('performance_metric', 'profit')
        
        self.lookback_period = self.config['lookback_period']
        self.learning_rate = self.config['learning_rate']
        self.performance_metric = self.config['performance_metric']
        
        # 存储历史信号和实际价格变动
        self.historical_signals = []
        self.historical_returns = []
    
    def update_weights(self, df: pd.DataFrame):
        """
        根据历史表现更新信号生成器的权重
        
        参数:
            df: 输入的数据框，必须包含'close'列和各个信号生成器的信号列
        """
        if len(df) < self.lookback_period + 1:
            self.logger.warning(f"数据长度不足，需要至少{self.lookback_period + 1}个数据点来更新权重")
            return
        
        # 计算实际收益率
        returns = df['close'].pct_change().shift(-1)  # 使用下一期的收益率
        
        # 评估每个信号生成器的表现
        performances = []
        
        for i, generator in enumerate(self.signal_generators):
            signal_col = f"signal_{i}"
            
            if self.performance_metric == 'accuracy':
                # 计算准确率（信号方向与价格变动方向一致的比例）
                correct_predictions = ((df[signal_col] > 0) & (returns > 0)) | \
                                     ((df[signal_col] < 0) & (returns < 0))
                performance = correct_predictions.rolling(window=self.lookback_period).mean().iloc[-1]
            
            elif self.performance_metric == 'profit':
                # 计算信号产生的收益
                signal_returns = df[signal_col] * returns
                performance = signal_returns.rolling(window=self.lookback_period).sum().iloc[-1]
            
            else:
                self.logger.error(f"不支持的性能指标: {self.performance_metric}")
                return
            
            performances.append(max(0.1, performance))  # 确保权重不会变为负数或零
        
        # 更新权重
        total_performance = sum(performances)
        if total_performance > 0:
            new_weights = [p / total_performance for p in performances]
            
            # 使用学习率平滑权重变化
            for i in range(len(self.weights)):
                self.weights[i] = (1 - self.learning_rate) * self.weights[i] + self.learning_rate * new_weights[i]
            
            self.logger.info(f"更新了信号生成器权重: {self.weights}")
        else:
            self.logger.warning("所有信号生成器的表现都不佳，保持原有权重")
    
    def combine_signals(self, df: pd.DataFrame, method: str = 'weighted_average', update_weights: bool = True) -> pd.DataFrame:
        """
        组合多个信号生成器的信号，并可选择性地更新权重
        
        参数:
            df: 输入的数据框
            method: 组合方法
            update_weights: 是否更新权重，默认为True
            
        返回:
            添加了组合信号列的数据框
        """
        result = super().combine_signals(df, method)
        
        if update_weights and len(df) > self.lookback_period:
            self.update_weights(result)
        
        return result