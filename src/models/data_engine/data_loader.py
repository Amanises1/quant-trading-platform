# 数据加载模块

import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict, Union, Optional, Tuple

class DataLoader:
    """
    数据加载类，负责加载历史数据和实时数据
    支持从本地文件、数据库和API加载数据
    """
    
    def __init__(self, data_dir: str = None, db_config: Dict = None):
        """
        初始化数据加载器
        
        Args:
            data_dir: 本地数据目录
            db_config: 数据库配置信息
        """
        self.data_dir = data_dir
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
    
    def load_from_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        从CSV文件加载数据
        
        Args:
            file_path: CSV文件路径
            **kwargs: 传递给pd.read_csv的参数
            
        Returns:
            DataFrame: 加载的数据
        """
        self.logger.info(f"从CSV文件加载数据: {file_path}")
        try:
            df = pd.read_csv(file_path, **kwargs)
            self.logger.info(f"成功加载数据，形状: {df.shape}")
            return df
        except Exception as e:
            self.logger.error(f"加载CSV文件失败: {e}")
            raise
    
    def load_from_excel(self, file_path: str, sheet_name=0, **kwargs) -> pd.DataFrame:
        """
        从Excel文件加载数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
            **kwargs: 传递给pd.read_excel的参数
            
        Returns:
            DataFrame: 加载的数据
        """
        self.logger.info(f"从Excel文件加载数据: {file_path}, 工作表: {sheet_name}")
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            self.logger.info(f"成功加载数据，形状: {df.shape}")
            return df
        except Exception as e:
            self.logger.error(f"加载Excel文件失败: {e}")
            raise
    
    def load_from_database(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        从数据库加载数据
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            DataFrame: 加载的数据
        """
        self.logger.info(f"从数据库加载数据，查询: {query}")
        
        if not self.db_config:
            raise ValueError("未配置数据库连接信息")
        
        # 这里应该实现实际的数据库连接和查询
        # 由于是示例代码，这里返回一个空的DataFrame
        self.logger.warning("数据库连接功能尚未实现，返回空DataFrame")
        return pd.DataFrame()
    
    def load_stock_history(self, stock_codes: List[str], start_date: str, end_date: str, 
                           fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        加载股票历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要加载的字段，默认为None表示加载所有字段
            
        Returns:
            DataFrame: 加载的股票历史数据
        """
        self.logger.info(f"加载股票历史数据: {stock_codes}, 时间范围: {start_date} - {end_date}")
        
        # 如果配置了本地数据目录，尝试从本地加载
        if self.data_dir:
            return self._load_stock_history_from_local(stock_codes, start_date, end_date, fields)
        
        # 如果配置了数据库，尝试从数据库加载
        if self.db_config:
            return self._load_stock_history_from_db(stock_codes, start_date, end_date, fields)
        
        # 如果都没有配置，抛出异常
        raise ValueError("未配置数据源，无法加载股票历史数据")
    
    def _load_stock_history_from_local(self, stock_codes: List[str], start_date: str, end_date: str, 
                                      fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        从本地文件加载股票历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要加载的字段，默认为None表示加载所有字段
            
        Returns:
            DataFrame: 加载的股票历史数据
        """
        all_data = []
        
        for code in stock_codes:
            # 构建文件路径，假设文件名格式为 code.csv
            file_path = os.path.join(self.data_dir, f"{code}.csv")
            
            if not os.path.exists(file_path):
                self.logger.warning(f"股票 {code} 的历史数据文件不存在: {file_path}")
                continue
            
            try:
                # 加载数据
                df = pd.read_csv(file_path)
                
                # 确保有日期列
                if 'date' not in df.columns:
                    self.logger.warning(f"股票 {code} 的历史数据文件缺少日期列")
                    continue
                
                # 转换日期列为日期类型
                df['date'] = pd.to_datetime(df['date'])
                
                # 筛选日期范围
                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)
                df = df[(df['date'] >= start) & (df['date'] <= end)]
                
                # 添加股票代码列
                if 'code' not in df.columns:
                    df['code'] = code
                
                # 筛选字段
                if fields:
                    # 确保code和date列始终存在
                    required_fields = ['code', 'date']
                    fields_to_select = list(set(required_fields + fields))
                    df = df[fields_to_select]
                
                all_data.append(df)
            except Exception as e:
                self.logger.error(f"加载股票 {code} 的历史数据失败: {e}")
        
        if not all_data:
            self.logger.warning("未能加载任何股票历史数据")
            return pd.DataFrame()
        
        # 合并所有股票的数据
        result = pd.concat(all_data, ignore_index=True)
        self.logger.info(f"成功加载 {len(stock_codes)} 只股票的历史数据，形状: {result.shape}")
        
        return result
    
    def _load_stock_history_from_db(self, stock_codes: List[str], start_date: str, end_date: str, 
                                   fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        从数据库加载股票历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要加载的字段，默认为None表示加载所有字段
            
        Returns:
            DataFrame: 加载的股票历史数据
        """
        # 构建SQL查询
        fields_str = "*" if not fields else ", ".join(["code", "date"] + fields)
        codes_str = ", ".join([f"'{code}'" for code in stock_codes])
        
        query = f"""
        SELECT {fields_str}
        FROM stock_history
        WHERE code IN ({codes_str})
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY code, date
        """
        
        # 执行查询
        try:
            return self.load_from_database(query)
        except Exception as e:
            self.logger.error(f"从数据库加载股票历史数据失败: {e}")
            return pd.DataFrame()
    
    def load_futures_history(self, future_codes: List[str], start_date: str, end_date: str, 
                            fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        加载期货历史数据
        
        Args:
            future_codes: 期货代码列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要加载的字段，默认为None表示加载所有字段
            
        Returns:
            DataFrame: 加载的期货历史数据
        """
        # 实现类似股票历史数据的加载逻辑
        # 这里简化处理，假设期货数据也存储在相同的格式中
        self.logger.info(f"加载期货历史数据: {future_codes}, 时间范围: {start_date} - {end_date}")
        
        # 如果配置了本地数据目录，尝试从本地加载
        if self.data_dir:
            # 假设期货数据存储在futures子目录中
            original_data_dir = self.data_dir
            self.data_dir = os.path.join(self.data_dir, 'futures')
            result = self._load_stock_history_from_local(future_codes, start_date, end_date, fields)
            self.data_dir = original_data_dir
            return result
        
        # 如果配置了数据库，尝试从数据库加载
        if self.db_config:
            # 修改表名为期货表
            query = f"""
            SELECT * FROM futures_history
            WHERE code IN ({', '.join([f"'{code}'" for code in future_codes])})
            AND date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY code, date
            """
            return self.load_from_database(query)
        
        # 如果都没有配置，抛出异常
        raise ValueError("未配置数据源，无法加载期货历史数据")
    
    def load_options_history(self, option_codes: List[str], start_date: str, end_date: str, 
                           fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        加载期权历史数据
        
        Args:
            option_codes: 期权代码列表
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要加载的字段，默认为None表示加载所有字段
            
        Returns:
            DataFrame: 加载的期权历史数据
        """
        # 实现类似股票历史数据的加载逻辑
        # 这里简化处理，假设期权数据也存储在相同的格式中
        self.logger.info(f"加载期权历史数据: {option_codes}, 时间范围: {start_date} - {end_date}")
        
        # 如果配置了本地数据目录，尝试从本地加载
        if self.data_dir:
            # 假设期权数据存储在options子目录中
            original_data_dir = self.data_dir
            self.data_dir = os.path.join(self.data_dir, 'options')
            result = self._load_stock_history_from_local(option_codes, start_date, end_date, fields)
            self.data_dir = original_data_dir
            return result
        
        # 如果配置了数据库，尝试从数据库加载
        if self.db_config:
            # 修改表名为期权表
            query = f"""
            SELECT * FROM options_history
            WHERE code IN ({', '.join([f"'{code}'" for code in option_codes])})
            AND date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY code, date
            """
            return self.load_from_database(query)
        
        # 如果都没有配置，抛出异常
        raise ValueError("未配置数据源，无法加载期权历史数据")
    
    def save_to_csv(self, df: pd.DataFrame, file_path: str, **kwargs) -> None:
        """
        将数据保存为CSV文件
        
        Args:
            df: 要保存的DataFrame数据
            file_path: 保存路径
            **kwargs: 传递给pd.to_csv的参数
        """
        self.logger.info(f"将数据保存为CSV文件: {file_path}")
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存数据
            df.to_csv(file_path, **kwargs)
            self.logger.info(f"成功保存数据，形状: {df.shape}")
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")
            raise
    
    def save_to_database(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace') -> None:
        """
        将数据保存到数据库
        
        Args:
            df: 要保存的DataFrame数据
            table_name: 表名
            if_exists: 如果表已存在，采取的操作，可选值为'fail', 'replace', 'append'
        """
        self.logger.info(f"将数据保存到数据库表: {table_name}")
        
        if not self.db_config:
            raise ValueError("未配置数据库连接信息")
        
        # 这里应该实现实际的数据库连接和保存
        # 由于是示例代码，这里只记录日志
        self.logger.warning("数据库保存功能尚未实现")