# 数据清洗模块

import pandas as pd
import numpy as np
import logging

class DataCleaner:
    """
    数据清洗类，负责处理原始数据中的异常值、缺失值等问题
    提供各种数据清洗和预处理方法
    """
    
    def __init__(self):
        """
        初始化数据清洗器
        """
        self.logger = logging.getLogger(__name__)
    
    def remove_duplicates(self, df):
        """
        移除重复数据
        
        参数:
            df (pandas.DataFrame): 输入数据框
            
        返回:
            pandas.DataFrame: 去除重复后的数据框
        """
        original_len = len(df)
        df = df.drop_duplicates()
        new_len = len(df)
        
        if original_len > new_len:
            self.logger.info(f"移除了 {original_len - new_len} 条重复记录")
        
        return df
    
    def handle_missing_values(self, df, method='ffill', columns=None):
        """
        处理缺失值
        
        参数:
            df (pandas.DataFrame): 输入数据框
            method (str): 处理方法，可选值：'ffill'(前向填充), 'bfill'(后向填充), 
                         'mean'(均值填充), 'median'(中位数填充), 'drop'(删除)
            columns (list): 需要处理的列，默认为None表示所有列
            
        返回:
            pandas.DataFrame: 处理缺失值后的数据框
        """
        # 创建数据副本，避免修改原始数据
        df_cleaned = df.copy()
        
        # 确定要处理的列
        if columns is None:
            columns = df.columns
        
        # 记录缺失值数量
        missing_count = df_cleaned[columns].isnull().sum().sum()
        
        # 根据不同方法处理缺失值
        if method == 'ffill':
            df_cleaned[columns] = df_cleaned[columns].fillna(method='ffill')
            # 处理开头的缺失值
            df_cleaned[columns] = df_cleaned[columns].fillna(method='bfill')
        
        elif method == 'bfill':
            df_cleaned[columns] = df_cleaned[columns].fillna(method='bfill')
            # 处理结尾的缺失值
            df_cleaned[columns] = df_cleaned[columns].fillna(method='ffill')
        
        elif method == 'mean':
            for col in columns:
                if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mean())
        
        elif method == 'median':
            for col in columns:
                if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                    df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
        
        elif method == 'drop':
            df_cleaned = df_cleaned.dropna(subset=columns)
        
        # 记录处理后的缺失值数量
        remaining_missing = df_cleaned[columns].isnull().sum().sum()
        
        self.logger.info(f"处理前缺失值数量: {missing_count}, 处理后缺失值数量: {remaining_missing}")
        
        return df_cleaned
    
    def handle_outliers(self, df, columns=None, method='zscore', threshold=3.0):
        """
        处理异常值
        
        参数:
            df (pandas.DataFrame): 输入数据框
            columns (list): 需要处理的列，默认为None表示所有数值列
            method (str): 检测方法，可选值：'zscore', 'iqr'
            threshold (float): 阈值，对于zscore方法表示标准差倍数，对于iqr方法表示四分位距倍数
            
        返回:
            pandas.DataFrame: 处理异常值后的数据框
        """
        # 创建数据副本
        df_cleaned = df.copy()
        
        # 如果未指定列，则选择所有数值列
        if columns is None:
            columns = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()
        
        outlier_count = 0
        
        for col in columns:
            # 确保列是数值类型
            if not pd.api.types.is_numeric_dtype(df_cleaned[col]):
                continue
                
            # 使用Z-score方法检测异常值
            if method == 'zscore':
                mean = df_cleaned[col].mean()
                std = df_cleaned[col].std()
                
                if std == 0:  # 避免除以零
                    continue
                    
                z_scores = np.abs((df_cleaned[col] - mean) / std)
                outliers = z_scores > threshold
                
            # 使用IQR方法检测异常值
            elif method == 'iqr':
                q1 = df_cleaned[col].quantile(0.25)
                q3 = df_cleaned[col].quantile(0.75)
                iqr = q3 - q1
                
                if iqr == 0:  # 避免除以零
                    continue
                    
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                
                outliers = (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)
            
            # 统计异常值数量
            col_outlier_count = outliers.sum()
            outlier_count += col_outlier_count
            
            # 将异常值替换为边界值
            if method == 'zscore':
                df_cleaned.loc[outliers, col] = np.sign(df_cleaned.loc[outliers, col] - mean) * threshold * std + mean
            elif method == 'iqr':
                df_cleaned.loc[df_cleaned[col] < lower_bound, col] = lower_bound
                df_cleaned.loc[df_cleaned[col] > upper_bound, col] = upper_bound
        
        self.logger.info(f"处理了 {outlier_count} 个异常值")
        
        return df_cleaned
    
    def normalize_data(self, df, columns=None, method='minmax'):
        """
        数据归一化
        
        参数:
            df (pandas.DataFrame): 输入数据框
            columns (list): 需要归一化的列，默认为None表示所有数值列
            method (str): 归一化方法，可选值：'minmax', 'zscore'
            
        返回:
            pandas.DataFrame: 归一化后的数据框
        """
        # 创建数据副本
        df_normalized = df.copy()
        
        # 如果未指定列，则选择所有数值列
        if columns is None:
            columns = df_normalized.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in columns:
            # 确保列是数值类型
            if not pd.api.types.is_numeric_dtype(df_normalized[col]):
                continue
                
            # 最小-最大归一化
            if method == 'minmax':
                min_val = df_normalized[col].min()
                max_val = df_normalized[col].max()
                
                if max_val == min_val:  # 避免除以零
                    df_normalized[col] = 0.5
                else:
                    df_normalized[col] = (df_normalized[col] - min_val) / (max_val - min_val)
            
            # Z-score标准化
            elif method == 'zscore':
                mean = df_normalized[col].mean()
                std = df_normalized[col].std()
                
                if std == 0:  # 避免除以零
                    df_normalized[col] = 0
                else:
                    df_normalized[col] = (df_normalized[col] - mean) / std
        
        self.logger.info(f"使用 {method} 方法对 {len(columns)} 列进行了归一化")
        
        return df_normalized
    
    def resample_data(self, df, freq='D', agg_dict=None):
        """
        重采样时间序列数据
        
        参数:
            df (pandas.DataFrame): 输入数据框，索引必须是日期时间类型
            freq (str): 重采样频率，如'D'表示日，'W'表示周，'M'表示月
            agg_dict (dict): 聚合方法字典，如{'close': 'last', 'volume': 'sum'}
            
        返回:
            pandas.DataFrame: 重采样后的数据框
        """
        # 确保索引是日期时间类型
        if not isinstance(df.index, pd.DatetimeIndex):
            self.logger.error("索引必须是日期时间类型才能进行重采样")
            return df
        
        # 默认聚合方法
        if agg_dict is None:
            agg_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
        
        # 只使用存在的列
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
        
        # 如果没有可用的聚合方法，返回原始数据
        if not agg_dict:
            self.logger.warning("没有找到可用的聚合方法，返回原始数据")
            return df
        
        # 执行重采样
        resampled = df.resample(freq).agg(agg_dict)
        
        self.logger.info(f"将数据从 {len(df)} 行重采样为 {len(resampled)} 行，频率为 {freq}")
        
        return resampled