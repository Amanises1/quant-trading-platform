# 策略迁移工具

import logging
import os
import json
import shutil
from typing import Dict, List, Union, Optional, Any, Tuple
from datetime import datetime
import importlib.util
import inspect

class StrategyMigrator:
    """
    策略迁移工具类，用于在不同环境之间迁移交易策略
    支持策略代码、参数、历史性能数据的迁移
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化策略迁移工具
        
        参数:
            config: 配置信息，包含迁移参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('backup', True)  # 是否备份原始数据
        self.config.setdefault('validate', True)  # 是否验证迁移结果
        self.config.setdefault('strategy_dir', 'strategies')  # 策略目录
        
        # 迁移状态
        self.migration_stats = {
            'total_strategies': 0,
            'migrated_strategies': 0,
            'failed_strategies': 0,
            'start_time': None,
            'end_time': None,
            'duration': None,
            'status': 'not_started'  # not_started, in_progress, completed, failed
        }
    
    def export_strategy(self, strategy_name: str, export_dir: str, 
                       include_code: bool = True, include_params: bool = True, 
                       include_performance: bool = True) -> Dict:
        """
        导出交易策略到指定目录
        
        参数:
            strategy_name: 策略名称
            export_dir: 导出目录
            include_code: 是否包含策略代码
            include_params: 是否包含策略参数
            include_performance: 是否包含策略历史性能数据
            
        返回:
            导出结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 确保导出目录存在
            os.makedirs(export_dir, exist_ok=True)
            
            # 确定策略目录
            strategy_dir = os.path.join(self.config['strategy_dir'], strategy_name)
            if not os.path.exists(strategy_dir):
                raise FileNotFoundError(f"策略目录不存在: {strategy_dir}")
            
            # 创建策略导出目录
            strategy_export_dir = os.path.join(export_dir, strategy_name)
            os.makedirs(strategy_export_dir, exist_ok=True)
            
            # 导出策略元数据
            metadata = {
                'name': strategy_name,
                'export_time': datetime.now().isoformat(),
                'includes': {
                    'code': include_code,
                    'params': include_params,
                    'performance': include_performance
                }
            }
            
            with open(os.path.join(strategy_export_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 导出策略代码
            if include_code:
                code_dir = os.path.join(strategy_export_dir, 'code')
                os.makedirs(code_dir, exist_ok=True)
                
                # 复制策略代码文件
                for root, _, files in os.walk(strategy_dir):
                    for file in files:
                        if file.endswith('.py'):
                            src_file = os.path.join(root, file)
                            rel_path = os.path.relpath(src_file, strategy_dir)
                            dst_file = os.path.join(code_dir, rel_path)
                            
                            # 确保目标目录存在
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            
                            # 复制文件
                            shutil.copy2(src_file, dst_file)
                            self.logger.info(f"已导出策略代码文件: {rel_path}")
            
            # 导出策略参数
            if include_params:
                params_file = os.path.join(strategy_dir, 'params.json')
                if os.path.exists(params_file):
                    shutil.copy2(params_file, os.path.join(strategy_export_dir, 'params.json'))
                    self.logger.info("已导出策略参数")
                else:
                    self.logger.warning(f"策略参数文件不存在: {params_file}")
            
            # 导出策略历史性能数据
            if include_performance:
                performance_dir = os.path.join(strategy_dir, 'performance')
                if os.path.exists(performance_dir):
                    perf_export_dir = os.path.join(strategy_export_dir, 'performance')
                    os.makedirs(perf_export_dir, exist_ok=True)
                    
                    # 复制性能数据文件
                    for root, _, files in os.walk(performance_dir):
                        for file in files:
                            if file.endswith(('.json', '.csv', '.xlsx')):
                                src_file = os.path.join(root, file)
                                rel_path = os.path.relpath(src_file, performance_dir)
                                dst_file = os.path.join(perf_export_dir, rel_path)
                                
                                # 确保目标目录存在
                                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                                
                                # 复制文件
                                shutil.copy2(src_file, dst_file)
                                self.logger.info(f"已导出策略性能数据文件: {rel_path}")
                else:
                    self.logger.warning(f"策略性能数据目录不存在: {performance_dir}")
            
            # 创建导出包文件
            export_zip = f"{strategy_export_dir}.zip"
            shutil.make_archive(strategy_export_dir, 'zip', strategy_export_dir)
            self.logger.info(f"已创建策略导出包: {export_zip}")
            
            # 更新统计信息
            self.migration_stats['total_strategies'] = 1
            self.migration_stats['migrated_strategies'] = 1
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"策略导出完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"策略导出失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def import_strategy(self, import_file: str, target_dir: Optional[str] = None, 
                       overwrite: bool = False) -> Dict:
        """
        从导出包导入交易策略
        
        参数:
            import_file: 导入文件路径（ZIP包）
            target_dir: 目标目录，如果为None则使用默认策略目录
            overwrite: 是否覆盖已存在的策略
            
        返回:
            导入结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 检查导入文件是否存在
            if not os.path.exists(import_file):
                raise FileNotFoundError(f"导入文件不存在: {import_file}")
            
            # 确定目标目录
            if target_dir is None:
                target_dir = self.config['strategy_dir']
            
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            # 创建临时解压目录
            import_temp_dir = f"temp_import_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.makedirs(import_temp_dir, exist_ok=True)
            
            # 解压导入包
            shutil.unpack_archive(import_file, import_temp_dir, 'zip')
            
            # 获取策略名称（假设导入包中只有一个策略目录）
            strategy_dirs = [d for d in os.listdir(import_temp_dir) if os.path.isdir(os.path.join(import_temp_dir, d))]
            if not strategy_dirs:
                raise ValueError("导入包中未找到策略目录")
            
            strategy_name = strategy_dirs[0]
            strategy_import_dir = os.path.join(import_temp_dir, strategy_name)
            
            # 读取策略元数据
            metadata_file = os.path.join(strategy_import_dir, 'metadata.json')
            if not os.path.exists(metadata_file):
                raise ValueError(f"导入包中未找到策略元数据文件: {metadata_file}")
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 确定目标策略目录
            target_strategy_dir = os.path.join(target_dir, strategy_name)
            
            # 检查目标策略是否已存在
            if os.path.exists(target_strategy_dir):
                if not overwrite:
                    raise ValueError(f"目标策略已存在: {target_strategy_dir}，如需覆盖请设置overwrite=True")
                
                # 备份已存在的策略
                if self.config['backup']:
                    backup_dir = f"{target_strategy_dir}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    shutil.copytree(target_strategy_dir, backup_dir)
                    self.logger.info(f"已备份现有策略: {backup_dir}")
                
                # 删除已存在的策略目录
                shutil.rmtree(target_strategy_dir)
            
            # 创建目标策略目录
            os.makedirs(target_strategy_dir, exist_ok=True)
            
            # 导入策略代码
            if metadata['includes']['code']:
                code_dir = os.path.join(strategy_import_dir, 'code')
                if os.path.exists(code_dir):
                    for root, _, files in os.walk(code_dir):
                        for file in files:
                            if file.endswith('.py'):
                                src_file = os.path.join(root, file)
                                rel_path = os.path.relpath(src_file, code_dir)
                                dst_file = os.path.join(target_strategy_dir, rel_path)
                                
                                # 确保目标目录存在
                                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                                
                                # 复制文件
                                shutil.copy2(src_file, dst_file)
                                self.logger.info(f"已导入策略代码文件: {rel_path}")
                else:
                    self.logger.warning(f"导入包中未找到策略代码目录: {code_dir}")
            
            # 导入策略参数
            if metadata['includes']['params']:
                params_file = os.path.join(strategy_import_dir, 'params.json')
                if os.path.exists(params_file):
                    shutil.copy2(params_file, os.path.join(target_strategy_dir, 'params.json'))
                    self.logger.info("已导入策略参数")
                else:
                    self.logger.warning(f"导入包中未找到策略参数文件: {params_file}")
            
            # 导入策略历史性能数据
            if metadata['includes']['performance']:
                performance_dir = os.path.join(strategy_import_dir, 'performance')
                if os.path.exists(performance_dir):
                    target_perf_dir = os.path.join(target_strategy_dir, 'performance')
                    os.makedirs(target_perf_dir, exist_ok=True)
                    
                    for root, _, files in os.walk(performance_dir):
                        for file in files:
                            if file.endswith(('.json', '.csv', '.xlsx')):
                                src_file = os.path.join(root, file)
                                rel_path = os.path.relpath(src_file, performance_dir)
                                dst_file = os.path.join(target_perf_dir, rel_path)
                                
                                # 确保目标目录存在
                                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                                
                                # 复制文件
                                shutil.copy2(src_file, dst_file)
                                self.logger.info(f"已导入策略性能数据文件: {rel_path}")
                else:
                    self.logger.warning(f"导入包中未找到策略性能数据目录: {performance_dir}")
            
            # 验证导入结果
            if self.config['validate']:
                validation_result = self._validate_imported_strategy(target_strategy_dir)
                if not validation_result['success']:
                    self.logger.warning(f"策略导入验证失败: {validation_result['message']}")
                    self.migration_stats['failed_strategies'] = 1
                else:
                    self.logger.info("策略导入验证通过")
            
            # 清理临时目录
            shutil.rmtree(import_temp_dir)
            
            # 更新统计信息
            self.migration_stats['total_strategies'] = 1
            self.migration_stats['migrated_strategies'] = 1
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"策略导入完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"策略导入失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def _validate_imported_strategy(self, strategy_dir: str) -> Dict:
        """
        验证导入的策略
        
        参数:
            strategy_dir: 策略目录
            
        返回:
            验证结果
        """
        result = {'success': True, 'message': ''}
        
        try:
            # 检查策略主文件是否存在
            strategy_file = os.path.join(strategy_dir, 'strategy.py')
            if not os.path.exists(strategy_file):
                result['success'] = False
                result['message'] = f"策略主文件不存在: {strategy_file}"
                return result
            
            # 尝试加载策略模块
            try:
                spec = importlib.util.spec_from_file_location('strategy_module', strategy_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 检查是否包含Strategy类
                strategy_class = None
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and 'Strategy' in name:
                        strategy_class = obj
                        break
                
                if strategy_class is None:
                    result['success'] = False
                    result['message'] = f"策略文件中未找到Strategy类: {strategy_file}"
                    return result
                
                # 检查必要的方法
                required_methods = ['initialize', 'on_bar']
                for method in required_methods:
                    if not hasattr(strategy_class, method):
                        result['success'] = False
                        result['message'] = f"Strategy类缺少必要的方法: {method}"
                        return result
                
            except Exception as e:
                result['success'] = False
                result['message'] = f"加载策略模块失败: {e}"
                return result
            
            # 检查参数文件
            params_file = os.path.join(strategy_dir, 'params.json')
            if os.path.exists(params_file):
                try:
                    with open(params_file, 'r', encoding='utf-8') as f:
                        params = json.load(f)
                    
                    if not isinstance(params, dict):
                        result['success'] = False
                        result['message'] = f"参数文件格式错误: {params_file}"
                        return result
                    
                except Exception as e:
                    result['success'] = False
                    result['message'] = f"读取参数文件失败: {e}"
                    return result
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"验证策略失败: {e}"
        
        return result
    
    def migrate_strategy_params(self, source_strategy: str, target_strategy: str, 
                              param_mapping: Optional[Dict] = None) -> Dict:
        """
        将一个策略的参数迁移到另一个策略
        
        参数:
            source_strategy: 源策略名称
            target_strategy: 目标策略名称
            param_mapping: 参数映射，格式为{源参数名: 目标参数名}
            
        返回:
            迁移结果统计
        """
        self._reset_stats()
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['status'] = 'in_progress'
        
        try:
            # 确定策略目录
            source_dir = os.path.join(self.config['strategy_dir'], source_strategy)
            target_dir = os.path.join(self.config['strategy_dir'], target_strategy)
            
            if not os.path.exists(source_dir):
                raise FileNotFoundError(f"源策略目录不存在: {source_dir}")
            
            if not os.path.exists(target_dir):
                raise FileNotFoundError(f"目标策略目录不存在: {target_dir}")
            
            # 读取源策略参数
            source_params_file = os.path.join(source_dir, 'params.json')
            if not os.path.exists(source_params_file):
                raise FileNotFoundError(f"源策略参数文件不存在: {source_params_file}")
            
            with open(source_params_file, 'r', encoding='utf-8') as f:
                source_params = json.load(f)
            
            # 读取目标策略参数（如果存在）
            target_params = {}
            target_params_file = os.path.join(target_dir, 'params.json')
            if os.path.exists(target_params_file):
                with open(target_params_file, 'r', encoding='utf-8') as f:
                    target_params = json.load(f)
                
                # 备份目标参数文件
                if self.config['backup']:
                    backup_file = f"{target_params_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    shutil.copy2(target_params_file, backup_file)
                    self.logger.info(f"已备份目标策略参数文件: {backup_file}")
            
            # 应用参数映射
            migrated_params = {}
            if param_mapping:
                for source_param, target_param in param_mapping.items():
                    if source_param in source_params:
                        migrated_params[target_param] = source_params[source_param]
                        self.logger.info(f"已迁移参数: {source_param} -> {target_param}")
            else:
                # 如果没有提供参数映射，直接复制所有参数
                migrated_params = source_params.copy()
            
            # 更新目标参数
            target_params.update(migrated_params)
            
            # 保存目标参数
            with open(target_params_file, 'w', encoding='utf-8') as f:
                json.dump(target_params, f, ensure_ascii=False, indent=2)
            
            # 更新统计信息
            self.migration_stats['total_strategies'] = 1
            self.migration_stats['migrated_strategies'] = 1
            self.migration_stats['status'] = 'completed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            
            self.logger.info(f"策略参数迁移完成，耗时 {self.migration_stats['duration']:.2f} 秒")
            
            return self.migration_stats
            
        except Exception as e:
            self.logger.error(f"策略参数迁移失败: {e}")
            self.migration_stats['status'] = 'failed'
            self.migration_stats['end_time'] = datetime.now()
            self.migration_stats['duration'] = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
            raise
    
    def _reset_stats(self) -> None:
        """
        重置迁移统计信息
        """
        self.migration_stats = {
            'total_strategies': 0,
            'migrated_strategies': 0,
            'failed_strategies': 0,
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