# 数据处理模块

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Union, Optional

class DataProcessor:
    """
    数据处理类，负责对采集到的原始数据进行清洗、处理和转换
    包括异常值处理、缺失值填充、数据标准化等功能
    """
    
    def __init__(self):
        """
        初始化数据处理器
        """
        self.logger = logging.getLogger(__name__)
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗数据，包括去除异常值、处理缺失值等
        
        Args:
            df: 输入的DataFrame数据
            
        Returns:
            DataFrame: 清洗后的数据
        """
        self.logger.info(f"开始清洗数据，原始数据形状: {df.shape}")
        
        # 复制数据，避免修改原始数据
        cleaned_df = df.copy()
        
        # 1. 处理缺失值
        cleaned_df = self._handle_missing_values(cleaned_df)
        
        # 2. 处理异常值
        cleaned_df = self._handle_outliers(cleaned_df)
        
        # 3. 数据类型转换
        cleaned_df = self._convert_data_types(cleaned_df)
        
        self.logger.info(f"数据清洗完成，清洗后数据形状: {cleaned_df.shape}")
        
        return cleaned_df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理缺失值
        
        Args:
            df: 输入的DataFrame数据
            
        Returns:
            DataFrame: 处理缺失值后的数据
        """
        # 记录原始缺失值情况
        missing_stats = df.isnull().sum()
        if missing_stats.sum() > 0:
            self.logger.info(f"发现缺失值:\n{missing_stats[missing_stats > 0]}")
        
        # 对不同类型的列采用不同的缺失值处理策略
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        datetime_cols = df.select_dtypes(include=['datetime']).columns
        
        # 数值型列使用中位数填充
        if len(numeric_cols) > 0:
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # 类别型列使用众数填充
        if len(categorical_cols) > 0:
            for col in categorical_cols:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'unknown')
        
        # 日期型列使用前向填充
        if len(datetime_cols) > 0:
            df[datetime_cols] = df[datetime_cols].fillna(method='ffill')
            # 如果仍有缺失值（例如第一行），使用后向填充
            df[datetime_cols] = df[datetime_cols].fillna(method='bfill')
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理异常值，使用IQR方法检测并处理异常值
        
        Args:
            df: 输入的DataFrame数据
            
        Returns:
            DataFrame: 处理异常值后的数据
        """
        # 只对数值型列进行异常值处理
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            # 跳过日期列和ID列
            if col in ['date', 'id', 'code']:
                continue
                
            # 计算IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # 定义异常值的上下界
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            # 检测异常值
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
            if not outliers.empty:
                self.logger.info(f"列 {col} 发现 {len(outliers)} 个异常值")
                
                # 将异常值替换为上下界
                df.loc[df[col] < lower_bound, col] = lower_bound
                df.loc[df[col] > upper_bound, col] = upper_bound
        
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        转换数据类型，优化内存使用
        
        Args:
            df: 输入的DataFrame数据
            
        Returns:
            DataFrame: 转换数据类型后的数据
        """
        # 转换日期列
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # 转换数值列为适当的类型
        for col in df.select_dtypes(include=['number']).columns:
            # 整数列
            if df[col].apply(lambda x: x.is_integer() if pd.notnull(x) else True).all():
                df[col] = df[col].astype('Int64')  # 使用可空整数类型
            # 浮点数列保持不变
        
        # 转换分类列
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # 如果唯一值比例小于50%，转换为分类类型
                df[col] = df[col].astype('category')
        
        return df
    
    def normalize_data(self, df: pd.DataFrame, method: str = 'z-score', columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        标准化数据
        
        Args:
            df: 输入的DataFrame数据
            method: 标准化方法，支持'z-score'、'min-max'、'robust'
            columns: 需要标准化的列，默认为None表示所有数值列
            
        Returns:
            DataFrame: 标准化后的数据
        """
        # 复制数据，避免修改原始数据
        normalized_df = df.copy()
        
        # 如果未指定列，则选择所有数值列
        if columns is None:
            columns = normalized_df.select_dtypes(include=['number']).columns
            # 排除日期列和ID列
            columns = [col for col in columns if col not in ['date', 'id', 'code']]
        
        self.logger.info(f"使用 {method} 方法标准化以下列: {columns}")
        
        if method == 'z-score':
            # Z-score标准化: (x - mean) / std
            for col in columns:
                mean = normalized_df[col].mean()
                std = normalized_df[col].std()
                if std != 0:  # 避免除以零
                    normalized_df[col] = (normalized_df[col] - mean) / std
                else:
                    self.logger.warning(f"列 {col} 的标准差为零，跳过标准化")
        
        elif method == 'min-max':
            # Min-Max标准化: (x - min) / (max - min)
            for col in columns:
                min_val = normalized_df[col].min()
                max_val = normalized_df[col].max()
                if max_val > min_val:  # 避免除以零
                    normalized_df[col] = (normalized_df[col] - min_val) / (max_val - min_val)
                else:
                    self.logger.warning(f"列 {col} 的最大值等于最小值，跳过标准化")
        
        elif method == 'robust':
            # 稳健标准化: (x - median) / IQR
            for col in columns:
                median = normalized_df[col].median()
                q1 = normalized_df[col].quantile(0.25)
                q3 = normalized_df[col].quantile(0.75)
                iqr = q3 - q1
                if iqr != 0:  # 避免除以零
                    normalized_df[col] = (normalized_df[col] - median) / iqr
                else:
                    self.logger.warning(f"列 {col} 的IQR为零，跳过标准化")
        
        else:
            raise ValueError(f"不支持的标准化方法: {method}，支持的方法有: 'z-score', 'min-max', 'robust'")
        
        return normalized_df
    
    def calculate_technical_indicators(self, df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: 输入的DataFrame数据，必须包含OHLCV数据
            indicators: 需要计算的技术指标列表
            
        Returns:
            DataFrame: 添加了技术指标的数据
        """
        # 确保数据按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # 复制数据，避免修改原始数据
        result_df = df.copy()
        
        # 检查必要的列是否存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in result_df.columns]
        if missing_cols:
            raise ValueError(f"计算技术指标需要以下列: {required_cols}，但缺少: {missing_cols}")
        
        # 按股票代码分组计算技术指标
        if 'code' in result_df.columns:
            grouped = result_df.groupby('code')
            result_dfs = []
            
            for code, group_df in grouped:
                # 计算该股票的技术指标
                group_with_indicators = self._calculate_indicators_for_single_stock(group_df, indicators)
                result_dfs.append(group_with_indicators)
            
            # 合并结果
            result_df = pd.concat(result_dfs)
        else:
            # 如果没有code列，直接计算
            result_df = self._calculate_indicators_for_single_stock(result_df, indicators)
        
        return result_df
    
    def _calculate_indicators_for_single_stock(self, df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
        """
        为单个股票计算技术指标
        
        Args:
            df: 单个股票的DataFrame数据
            indicators: 需要计算的技术指标列表
            
        Returns:
            DataFrame: 添加了技术指标的数据
        """
        result_df = df.copy()
        
        for indicator in indicators:
            if indicator == 'MA':
                # 移动平均线 (MA5, MA10, MA20, MA60)
                for window in [5, 10, 20, 60]:
                    result_df[f'MA{window}'] = result_df['close'].rolling(window=window).mean()
            
            elif indicator == 'EMA':
                # 指数移动平均线 (EMA12, EMA26)
                for window in [12, 26]:
                    result_df[f'EMA{window}'] = result_df['close'].ewm(span=window, adjust=False).mean()
            
            elif indicator == 'MACD':
                # MACD指标
                ema12 = result_df['close'].ewm(span=12, adjust=False).mean()
                ema26 = result_df['close'].ewm(span=26, adjust=False).mean()
                result_df['MACD'] = ema12 - ema26
                result_df['MACD_signal'] = result_df['MACD'].ewm(span=9, adjust=False).mean()
                result_df['MACD_hist'] = result_df['MACD'] - result_df['MACD_signal']
            
            elif indicator == 'RSI':
                # 相对强弱指标 (RSI14)
                delta = result_df['close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                
                rs = avg_gain / avg_loss
                result_df['RSI14'] = 100 - (100 / (1 + rs))
            
            elif indicator == 'BOLL':
                # 布林带指标
                result_df['BOLL_mid'] = result_df['close'].rolling(window=20).mean()
                result_df['BOLL_std'] = result_df['close'].rolling(window=20).std()
                result_df['BOLL_upper'] = result_df['BOLL_mid'] + 2 * result_df['BOLL_std']
                result_df['BOLL_lower'] = result_df['BOLL_mid'] - 2 * result_df['BOLL_std']
            
            elif indicator == 'KDJ':
                # KDJ指标
                low_min = result_df['low'].rolling(window=9).min()
                high_max = result_df['high'].rolling(window=9).max()
                
                result_df['KDJ_K'] = 50.0
                result_df['KDJ_D'] = 50.0
                
                for i in range(9, len(result_df)):
                    if high_max.iloc[i] != low_min.iloc[i]:
                        rsv = (result_df['close'].iloc[i] - low_min.iloc[i]) / (high_max.iloc[i] - low_min.iloc[i]) * 100
                    else:
                        rsv = 50
                    
                    result_df.loc[result_df.index[i], 'KDJ_K'] = 2/3 * result_df['KDJ_K'].iloc[i-1] + 1/3 * rsv
                    result_df.loc[result_df.index[i], 'KDJ_D'] = 2/3 * result_df['KDJ_D'].iloc[i-1] + 1/3 * result_df['KDJ_K'].iloc[i]
                
                result_df['KDJ_J'] = 3 * result_df['KDJ_K'] - 2 * result_df['KDJ_D']
            
            else:
                self.logger.warning(f"不支持的技术指标: {indicator}")
        
        return result_df