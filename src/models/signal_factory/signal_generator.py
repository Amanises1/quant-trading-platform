# 信号生成器模块

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional

class SignalGenerator:
    """
    信号生成器基类，提供交易信号生成的基础功能
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信号生成器
        
        参数:
            config: 配置信息，包含信号生成的参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号的基础方法，需要在子类中实现
        
        参数:
            df: 输入的数据框，包含价格和技术指标数据
            
        返回:
            添加了信号列的数据框
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def _validate_data(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        验证数据是否包含所需的列
        
        参数:
            df: 输入的数据框
            required_columns: 所需的列名列表
            
        返回:
            如果数据包含所有所需的列，则返回True，否则返回False
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"数据缺少所需的列: {missing_columns}")
            return False
        return True
    
    def _add_signal_metadata(self, df: pd.DataFrame, signal_column: str) -> pd.DataFrame:
        """
        添加信号元数据，如信号强度、持续时间等
        
        参数:
            df: 输入的数据框，包含信号列
            signal_column: 信号列的名称
            
        返回:
            添加了信号元数据的数据框
        """
        result = df.copy()
        
        # 计算信号变化点
        result['signal_change'] = result[signal_column].diff().ne(0).astype(int)
        
        # 计算信号持续时间
        result['signal_duration'] = 0
        current_duration = 0
        
        for i in range(len(result)):
            if i > 0 and result.iloc[i]['signal_change'] == 0:
                current_duration += 1
            else:
                current_duration = 0
            result.iloc[i, result.columns.get_loc('signal_duration')] = current_duration
        
        # 计算信号强度（示例：基于信号持续时间）
        result['signal_strength'] = result['signal_duration'].apply(lambda x: min(x / 5, 1.0))
        
        return result


class MovingAverageCrossSignalGenerator(SignalGenerator):
    """
    基于移动平均线交叉的信号生成器
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化移动平均线交叉信号生成器
        
        参数:
            config: 配置信息，包含以下参数：
                - fast_ma_period: 快速移动平均线周期，默认为5
                - slow_ma_period: 慢速移动平均线周期，默认为20
                - ma_type: 移动平均线类型，可选值为'SMA'或'EMA'，默认为'SMA'
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('fast_ma_period', 5)
        self.config.setdefault('slow_ma_period', 20)
        self.config.setdefault('ma_type', 'SMA')
        
        self.fast_period = self.config['fast_ma_period']
        self.slow_period = self.config['slow_ma_period']
        self.ma_type = self.config['ma_type']
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于移动平均线交叉生成交易信号
        
        参数:
            df: 输入的数据框，必须包含'close'列
            
        返回:
            添加了信号列的数据框，其中：
            1 表示买入信号
            -1 表示卖出信号
            0 表示无信号
        """
        # 验证数据
        if not self._validate_data(df, ['close']):
            return df
        
        result = df.copy()
        
        # 计算移动平均线
        if self.ma_type == 'SMA':
            result[f'fast_ma'] = result['close'].rolling(window=self.fast_period).mean()
            result[f'slow_ma'] = result['close'].rolling(window=self.slow_period).mean()
        elif self.ma_type == 'EMA':
            result[f'fast_ma'] = result['close'].ewm(span=self.fast_period, adjust=False).mean()
            result[f'slow_ma'] = result['close'].ewm(span=self.slow_period, adjust=False).mean()
        else:
            self.logger.error(f"不支持的移动平均线类型: {self.ma_type}")
            return df
        
        # 初始化信号列
        result['signal'] = 0
        
        # 计算快线和慢线的交叉点
        result['fast_gt_slow'] = (result['fast_ma'] > result['slow_ma']).astype(int)
        result['cross'] = result['fast_gt_slow'].diff()
        
        # 生成信号
        result.loc[result['cross'] == 1, 'signal'] = 1  # 金叉，买入信号
        result.loc[result['cross'] == -1, 'signal'] = -1  # 死叉，卖出信号
        
        # 删除临时列
        result = result.drop(['fast_gt_slow', 'cross'], axis=1)
        
        # 添加信号元数据
        result = self._add_signal_metadata(result, 'signal')
        
        self.logger.info(f"基于移动平均线交叉生成了信号 (快线周期={self.fast_period}, 慢线周期={self.slow_period}, 类型={self.ma_type})")
        
        return result


class RSISignalGenerator(SignalGenerator):
    """
    基于RSI指标的信号生成器
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化RSI信号生成器
        
        参数:
            config: 配置信息，包含以下参数：
                - rsi_period: RSI计算周期，默认为14
                - overbought_threshold: 超买阈值，默认为70
                - oversold_threshold: 超卖阈值，默认为30
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('rsi_period', 14)
        self.config.setdefault('overbought_threshold', 70)
        self.config.setdefault('oversold_threshold', 30)
        
        self.period = self.config['rsi_period']
        self.overbought = self.config['overbought_threshold']
        self.oversold = self.config['oversold_threshold']
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于RSI指标生成交易信号
        
        参数:
            df: 输入的数据框，必须包含'close'列或'RSI_{period}'列
            
        返回:
            添加了信号列的数据框，其中：
            1 表示买入信号（RSI从超卖区域向上穿越）
            -1 表示卖出信号（RSI从超买区域向下穿越）
            0 表示无信号
        """
        # 验证数据
        result = df.copy()
        
        # 检查是否已经有RSI列，如果没有则计算
        rsi_col = f'RSI_{self.period}'
        if rsi_col not in result.columns:
            if not self._validate_data(df, ['close']):
                return df
            
            # 计算RSI
            delta = result['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=self.period).mean()
            avg_loss = loss.rolling(window=self.period).mean()
            
            rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)  # 避免除以零
            result[rsi_col] = 100 - (100 / (1 + rs))
        
        # 初始化信号列
        result['signal'] = 0
        
        # 计算RSI穿越超买和超卖阈值的点
        result['oversold_cross_up'] = ((result[rsi_col].shift(1) < self.oversold) & 
                                      (result[rsi_col] >= self.oversold)).astype(int)
        
        result['overbought_cross_down'] = ((result[rsi_col].shift(1) > self.overbought) & 
                                          (result[rsi_col] <= self.overbought)).astype(int)
        
        # 生成信号
        result.loc[result['oversold_cross_up'] == 1, 'signal'] = 1  # 超卖区域向上穿越，买入信号
        result.loc[result['overbought_cross_down'] == 1, 'signal'] = -1  # 超买区域向下穿越，卖出信号
        
        # 删除临时列
        result = result.drop(['oversold_cross_up', 'overbought_cross_down'], axis=1)
        
        # 添加信号元数据
        result = self._add_signal_metadata(result, 'signal')
        
        self.logger.info(f"基于RSI指标生成了信号 (周期={self.period}, 超买阈值={self.overbought}, 超卖阈值={self.oversold})")
        
        return result


class MACDSignalGenerator(SignalGenerator):
    """
    基于MACD指标的信号生成器
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化MACD信号生成器
        
        参数:
            config: 配置信息，包含以下参数：
                - fast_period: 快线周期，默认为12
                - slow_period: 慢线周期，默认为26
                - signal_period: 信号线周期，默认为9
        """
        super().__init__(config)
        
        # 设置默认参数
        self.config.setdefault('fast_period', 12)
        self.config.setdefault('slow_period', 26)
        self.config.setdefault('signal_period', 9)
        
        self.fast_period = self.config['fast_period']
        self.slow_period = self.config['slow_period']
        self.signal_period = self.config['signal_period']
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于MACD指标生成交易信号
        
        参数:
            df: 输入的数据框，必须包含'close'列或MACD相关列
            
        返回:
            添加了信号列的数据框，其中：
            1 表示买入信号（MACD线上穿信号线）
            -1 表示卖出信号（MACD线下穿信号线）
            0 表示无信号
        """
        # 验证数据
        result = df.copy()
        
        # 检查是否已经有MACD列，如果没有则计算
        if 'MACD_line' not in result.columns or 'MACD_signal' not in result.columns:
            if not self._validate_data(df, ['close']):
                return df
            
            # 计算MACD
            fast_ema = result['close'].ewm(span=self.fast_period, adjust=False).mean()
            slow_ema = result['close'].ewm(span=self.slow_period, adjust=False).mean()
            
            result['MACD_line'] = fast_ema - slow_ema
            result['MACD_signal'] = result['MACD_line'].ewm(span=self.signal_period, adjust=False).mean()
            result['MACD_histogram'] = result['MACD_line'] - result['MACD_signal']
        
        # 初始化信号列
        result['signal'] = 0
        
        # 计算MACD线和信号线的交叉点
        result['macd_gt_signal'] = (result['MACD_line'] > result['MACD_signal']).astype(int)
        result['cross'] = result['macd_gt_signal'].diff()
        
        # 生成信号
        result.loc[result['cross'] == 1, 'signal'] = 1  # MACD线上穿信号线，买入信号
        result.loc[result['cross'] == -1, 'signal'] = -1  # MACD线下穿信号线，卖出信号
        
        # 删除临时列
        result = result.drop(['macd_gt_signal', 'cross'], axis=1)
        
        # 添加信号元数据
        result = self._add_signal_metadata(result, 'signal')
        
        self.logger.info(f"基于MACD指标生成了信号 (快线周期={self.fast_period}, 慢线周期={self.slow_period}, 信号线周期={self.signal_period})")
        
        return result