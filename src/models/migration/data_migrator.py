# 数据迁移工具

import pandas as pd
import numpy as np
import logging
import os
import json
import csv
import sqlite3
from typing import Dict, List, Union, Optional, Any, Tuple
from datetime import datetime
import shutil

class DataMigrator:
    """
    数据迁移工具类，用于在不同数据源之间迁移金融数据
    支持CSV、Excel、JSON、数据库等多种格式的数据迁移
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化数据迁移工具
        
        参数:
            config: 配置信息，包含迁移参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('batch_size', 10000)  # 批处理大小
        self.config.setdefault('date_format', '%Y-%m-%d')  # 日期格式
        self.config.setdefault('backup', True)  # 是否备份原始数据
        self.config.setdefault('validate', True)  # 是否验证迁移结果
        
        # 迁移状态
        self.migration_stats = {
            'total_records': 0,
            'migrated_records': 0,
            'failed_records': 0,
            'start_time': None,
            'end_time': None,
            'duration': None,
            'status': 'not_started'  # not_started, in_progress, completed, failed
        }
    
    def migrate_csv_to_db(self, csv_file: str, db_file: str, table_name: str, 
                         schema: Optional[Dict] = None, index_columns: Optional[List[str]] = None) -> Dict:
        """
        将CSV文件数据迁移到SQLite数据库
        
        参数:
            csv_file: CSV文件路径
            db_file: 数据库文件路径
            table_name: 目标表名
            schema: 表结构定义，格式为{列名: 数据类型}
            index_columns: 需要创建索引的列名列表
            
        返回:
            迁移结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 检查源文件是否存在
            if not os.path.exists(csv_file):
                raise FileNotFoundError(f"源CSV文件不存在: {csv_file}")
            
            # 备份目标数据库（如果存在且启用备份）
            if os.path.exists(db_file) and self.config['backup']:
                backup_file = f"{db_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(db_file, backup_file)
                self.logger.info(f"已备份数据库文件: {backup_file}")
            
            # 读取CSV文件，计算总记录数
            with open(csv_file, 'r', encoding='utf-8') as f:
                total_records = sum(1 for _ in f) - 1  # 减去标题行
            self.migration_stats['total_records'] = total_records
            
            # 创建数据库连接
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 读取CSV文件头，确定列名
            df_sample = pd.read_csv(csv_file, nrows=1)
            columns = list(df_sample.columns)
            
            # 如果没有提供schema，根据数据推断
            if not schema:
                schema = {}
                for col in columns:
                    if 'date' in col.lower() or 'time' in col.lower():
                        schema[col] = 'TEXT'
                    elif 'price' in col.lower() or 'value' in col.lower() or 'amount' in col.lower():
                        schema[col] = 'REAL'
                    elif 'volume' in col.lower() or 'quantity' in col.lower() or 'count' in col.lower():
                        schema[col] = 'INTEGER'
                    else:
                        schema[col] = 'TEXT'
            
            # 创建表
            columns_def = [f"\"{col}\" {schema.get(col, 'TEXT')}" for col in columns]
            create_table_sql = f"CREATE TABLE IF NOT EXISTS \"{table_name}\" ({', '.join(columns_def)})"
            cursor.execute(create_table_sql)
            
            # 创建索引
            if index_columns:
                for col in index_columns:
                    if col in columns:
                        index_name = f"idx_{table_name}_{col}"
                        create_index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON \"{table_name}\" (\"{col}\")"
                        cursor.execute(create_index_sql)
            
            # 分批读取CSV并插入数据库
            batch_size = self.config['batch_size']
            for chunk in pd.read_csv(csv_file, chunksize=batch_size):
                # 准备插入语句
                placeholders = ', '.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO \"{table_name}\" ({', '.join([f'\"{col}\"' for col in columns])}) VALUES ({placeholders})"
                
                # 准备数据
                records = []
                for _, row in chunk.iterrows():
                    record = []
                    for col in columns:
                        value = row[col]
                        # 处理NaN和None
                        if pd.isna(value):
                            value = None
                        record.append(value)
                    records.append(record)
                
                # 执行批量插入
                cursor.executemany(insert_sql, records)
                conn.commit()
                
                # 更新统计信息
                self.migration_stats['migrated_records'] += len(records)
                self.logger.info(f"已迁移 {self.migration_stats['migrated_records']} / {total_records} 条记录")
            
            # 验证迁移结果
            if self.config['validate']:
                cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
                db_count = cursor.fetchone()[0]
                if db_count != total_records:
                    self.logger.warning(f"迁移验证不一致: CSV记录数 {total_records}, 数据库记录数 {db_count}")
                    self.migration_stats['failed_records'] = total_records - db_count
                else:
                    self.logger.info(f"迁移验证通过: 共 {db_count} 条记录")
            
            # 关闭数据库连接
            conn.close()
            
            # 更新统计信息
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"CSV到数据库迁移完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"CSV到数据库迁移失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def migrate_db_to_csv(self, db_file: str, table_name: str, csv_file: str, 
                         query: Optional[str] = None, chunk_size: Optional[int] = None) -> Dict:
        """
        将SQLite数据库表数据迁移到CSV文件
        
        参数:
            db_file: 数据库文件路径
            table_name: 源表名
            csv_file: 目标CSV文件路径
            query: 自定义查询SQL，如果为None则查询整个表
            chunk_size: 分块大小，如果为None则使用默认batch_size
            
        返回:
            迁移结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 检查源数据库是否存在
            if not os.path.exists(db_file):
                raise FileNotFoundError(f"源数据库文件不存在: {db_file}")
            
            # 备份目标CSV文件（如果存在且启用备份）
            if os.path.exists(csv_file) and self.config['backup']:
                backup_file = f"{csv_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(csv_file, backup_file)
                self.logger.info(f"已备份CSV文件: {backup_file}")
            
            # 创建数据库连接
            conn = sqlite3.connect(db_file)
            
            # 确定查询SQL
            if query is None:
                query = f"SELECT * FROM \"{table_name}\""
            
            # 获取总记录数
            count_query = f"SELECT COUNT(*) FROM ({query})"
            total_records = pd.read_sql_query(count_query, conn).iloc[0, 0]
            self.migration_stats['total_records'] = total_records
            
            # 设置分块大小
            if chunk_size is None:
                chunk_size = self.config['batch_size']
            
            # 分批读取数据库并写入CSV
            chunks = pd.read_sql_query(query, conn, chunksize=chunk_size)
            
            # 写入第一个分块，包含表头
            first_chunk = True
            for chunk in chunks:
                if first_chunk:
                    chunk.to_csv(csv_file, index=False, mode='w', encoding='utf-8')
                    first_chunk = False
                else:
                    chunk.to_csv(csv_file, index=False, mode='a', header=False, encoding='utf-8')
                
                # 更新统计信息
                self.migration_stats['migrated_records'] += len(chunk)
                self.logger.info(f"已迁移 {self.migration_stats['migrated_records']} / {total_records} 条记录")
            
            # 关闭数据库连接
            conn.close()
            
            # 验证迁移结果
            if self.config['validate']:
                # 计算CSV文件中的记录数
                with open(csv_file, 'r', encoding='utf-8') as f:
                    csv_count = sum(1 for _ in f) - 1  # 减去标题行
                
                if csv_count != total_records:
                    self.logger.warning(f"迁移验证不一致: 数据库记录数 {total_records}, CSV记录数 {csv_count}")
                    self.migration_stats['failed_records'] = total_records - csv_count
                else:
                    self.logger.info(f"迁移验证通过: 共 {csv_count} 条记录")
            
            # 更新统计信息
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"数据库到CSV迁移完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"数据库到CSV迁移失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def migrate_excel_to_csv(self, excel_file: str, sheet_name: Optional[str] = None, 
                           csv_file: Optional[str] = None, multiple_sheets: bool = False) -> Dict:
        """
        将Excel文件数据迁移到CSV文件
        
        参数:
            excel_file: Excel文件路径
            sheet_name: 工作表名称，如果为None则使用第一个工作表
            csv_file: 目标CSV文件路径，如果为None则使用Excel文件名
            multiple_sheets: 是否处理多个工作表，如果为True则每个工作表生成一个CSV文件
            
        返回:
            迁移结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 检查源文件是否存在
            if not os.path.exists(excel_file):
                raise FileNotFoundError(f"源Excel文件不存在: {excel_file}")
            
            # 确定目标CSV文件路径
            if csv_file is None:
                base_name = os.path.splitext(excel_file)[0]
                csv_file = f"{base_name}.csv"
            
            # 读取Excel文件
            excel = pd.ExcelFile(excel_file)
            
            # 处理多个工作表
            if multiple_sheets:
                sheet_names = excel.sheet_names
                total_records = 0
                
                for sheet in sheet_names:
                    # 读取工作表数据
                    df = pd.read_excel(excel, sheet_name=sheet)
                    total_records += len(df)
                    
                    # 确定输出文件名
                    output_file = f"{os.path.splitext(csv_file)[0]}_{sheet}.csv"
                    
                    # 备份目标CSV文件（如果存在且启用备份）
                    if os.path.exists(output_file) and self.config['backup']:
                        backup_file = f"{output_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        shutil.copy2(output_file, backup_file)
                        self.logger.info(f"已备份CSV文件: {backup_file}")
                    
                    # 写入CSV文件
                    df.to_csv(output_file, index=False, encoding='utf-8')
                    
                    # 更新统计信息
                    self.migration_stats['migrated_records'] += len(df)
                    self.logger.info(f"已迁移工作表 {sheet} 的 {len(df)} 条记录到 {output_file}")
                
                self.migration_stats['total_records'] = total_records
                
            else:
                # 确定要处理的工作表
                if sheet_name is None:
                    sheet_name = excel.sheet_names[0]
                
                # 读取工作表数据
                df = pd.read_excel(excel, sheet_name=sheet_name)
                self.migration_stats['total_records'] = len(df)
                
                # 备份目标CSV文件（如果存在且启用备份）
                if os.path.exists(csv_file) and self.config['backup']:
                    backup_file = f"{csv_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    shutil.copy2(csv_file, backup_file)
                    self.logger.info(f"已备份CSV文件: {backup_file}")
                
                # 写入CSV文件
                df.to_csv(csv_file, index=False, encoding='utf-8')
                
                # 更新统计信息
                self.migration_stats['migrated_records'] = len(df)
                self.logger.info(f"已迁移工作表 {sheet_name} 的 {len(df)} 条记录到 {csv_file}")
            
            # 验证迁移结果
            if self.config['validate']:
                if multiple_sheets:
                    for sheet in sheet_names:
                        output_file = f"{os.path.splitext(csv_file)[0]}_{sheet}.csv"
                        with open(output_file, 'r', encoding='utf-8') as f:
                            csv_count = sum(1 for _ in f) - 1  # 减去标题行
                        
                        df = pd.read_excel(excel, sheet_name=sheet)
                        if csv_count != len(df):
                            self.logger.warning(f"工作表 {sheet} 迁移验证不一致: Excel记录数 {len(df)}, CSV记录数 {csv_count}")
                            self.migration_stats['failed_records'] += len(df) - csv_count
                else:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        csv_count = sum(1 for _ in f) - 1  # 减去标题行
                    
                    if csv_count != self.migration_stats['total_records']:
                        self.logger.warning(f"迁移验证不一致: Excel记录数 {self.migration_stats['total_records']}, CSV记录数 {csv_count}")
                        self.migration_stats['failed_records'] = self.migration_stats['total_records'] - csv_count
                    else:
                        self.logger.info(f"迁移验证通过: 共 {csv_count} 条记录")
            
            # 更新统计信息
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"Excel到CSV迁移完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"Excel到CSV迁移失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def migrate_json_to_csv(self, json_file: str, csv_file: str, 
                          flatten: bool = False, root_element: Optional[str] = None) -> Dict:
        """
        将JSON文件数据迁移到CSV文件
        
        参数:
            json_file: JSON文件路径
            csv_file: 目标CSV文件路径
            flatten: 是否扁平化嵌套结构
            root_element: JSON根元素，如果为None则使用整个JSON
            
        返回:
            迁移结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 检查源文件是否存在
            if not os.path.exists(json_file):
                raise FileNotFoundError(f"源JSON文件不存在: {json_file}")
            
            # 备份目标CSV文件（如果存在且启用备份）
            if os.path.exists(csv_file) and self.config['backup']:
                backup_file = f"{csv_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(csv_file, backup_file)
                self.logger.info(f"已备份CSV文件: {backup_file}")
            
            # 读取JSON文件
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 提取根元素（如果指定）
            if root_element is not None:
                if root_element in json_data:
                    json_data = json_data[root_element]
                else:
                    raise KeyError(f"在JSON中找不到指定的根元素: {root_element}")
            
            # 确保数据是列表形式
            if not isinstance(json_data, list):
                json_data = [json_data]
            
            self.migration_stats['total_records'] = len(json_data)
            
            # 扁平化嵌套结构（如果需要）
            if flatten:
                flattened_data = []
                for item in json_data:
                    flattened_item = {}
                    self._flatten_json(item, flattened_item)
                    flattened_data.append(flattened_item)
                json_data = flattened_data
            
            # 转换为DataFrame并写入CSV
            df = pd.json_normalize(json_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            # 更新统计信息
            self.migration_stats['migrated_records'] = len(json_data)
            self.logger.info(f"已迁移 {len(json_data)} 条记录到 {csv_file}")
            
            # 验证迁移结果
            if self.config['validate']:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    csv_count = sum(1 for _ in f) - 1  # 减去标题行
                
                if csv_count != self.migration_stats['total_records']:
                    self.logger.warning(f"迁移验证不一致: JSON记录数 {self.migration_stats['total_records']}, CSV记录数 {csv_count}")
                    self.migration_stats['failed_records'] = self.migration_stats['total_records'] - csv_count
                else:
                    self.logger.info(f"迁移验证通过: 共 {csv_count} 条记录")
            
            # 更新统计信息
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"JSON到CSV迁移完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"JSON到CSV迁移失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def _flatten_json(self, json_obj: Dict, flattened_obj: Dict, prefix: str = '') -> None:
        """
        递归扁平化嵌套的JSON对象
        
        参数:
            json_obj: 要扁平化的JSON对象
            flattened_obj: 存储扁平化结果的字典
            prefix: 当前键的前缀
        """
        for key, value in json_obj.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._flatten_json(value, flattened_obj, new_key)
            elif isinstance(value, list):
                # 对于列表，我们将其转换为JSON字符串
                flattened_obj[new_key] = json.dumps(value)
            else:
                flattened_obj[new_key] = value
    
    def _reset_stats(self) -> None:
        """
        重置迁移统计信息
        """
        self.migration_stats = {
            'total_records': 0,
            'migrated_records': 0,
            'failed_records': 0,
            'start_time': None,
            'end_time': None,
            'duration': None,
            'status': 'not_started'
        }
    
    def get_migration_stats(self) -> Dict:
        """
        获取迁移统计信息
        
        返回:
            迁移统计信息字典
        """
        return self.migration_stats