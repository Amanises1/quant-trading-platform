import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable, Any
from datetime import datetime, timedelta
import threading
import time
from .database_connection import db_conn

class RiskController:
    """
    风险控制类，用于实时监控和控制交易风险
    支持风险指标监控、风险预警和自动风险控制
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化风险控制器
        
        参数:
            config: 配置信息，包含风险控制参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('max_daily_loss_pct', 0.02)  # 最大日亏损比例
        self.config.setdefault('max_position_pct', 0.2)  # 最大单一仓位比例
        self.config.setdefault('max_sector_exposure_pct', 0.3)  # 最大行业敞口比例
        self.config.setdefault('max_leverage', 2.0)  # 最大杠杆倍数
        self.config.setdefault('stop_loss_pct', 0.05)  # 止损比例
        self.config.setdefault('monitoring_interval', 60)  # 监控间隔（秒）
        self.config.setdefault('auto_risk_control', False)  # 是否启用自动风险控制
        
        # 风险控制状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 数据源函数
        self.account_data_source = None
        self.position_data_source = None
        self.order_executor = None
        
        # 初始化数据库表
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            # 创建风险指标表
            create_risk_metrics_table = """
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                daily_pnl_pct DOUBLE PRECISION NOT NULL,
                max_position_pct DOUBLE PRECISION NOT NULL,
                max_sector_exposure_pct DOUBLE PRECISION NOT NULL,
                current_leverage DOUBLE PRECISION NOT NULL,
                portfolio_var DOUBLE PRECISION NOT NULL,
                portfolio_volatility DOUBLE PRECISION NOT NULL,
                drawdown DOUBLE PRECISION NOT NULL,
                risk_level VARCHAR(20) NOT NULL
            )
            """
            db_conn.execute_query(create_risk_metrics_table)
            
            # 创建风险警报表
            create_risk_alerts_table = """
            CREATE TABLE IF NOT EXISTS risk_alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(20) NOT NULL,
                data JSONB,
                symbol VARCHAR(50),
                is_resolved BOOLEAN DEFAULT FALSE
            )
            """
            db_conn.execute_query(create_risk_alerts_table)
            
            # 创建风险控制操作表
            create_risk_actions_table = """
            CREATE TABLE IF NOT EXISTS risk_actions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                type VARCHAR(50) NOT NULL,
                reason TEXT NOT NULL,
                positions JSONB NOT NULL,
                status VARCHAR(20) DEFAULT 'pending'
            )
            """
            db_conn.execute_query(create_risk_actions_table)
            
            # 创建配置表
            create_risk_config_table = """
            CREATE TABLE IF NOT EXISTS risk_config (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                value DOUBLE PRECISION,
                string_value VARCHAR(255),
                boolean_value BOOLEAN,
                description TEXT
            )
            """
            db_conn.execute_query(create_risk_config_table)
            
            # 创建索引
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_risk_metrics_timestamp ON risk_metrics (timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_risk_alerts_timestamp ON risk_alerts (timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_risk_alerts_severity ON risk_alerts (severity)",
                "CREATE INDEX IF NOT EXISTS idx_risk_alerts_is_resolved ON risk_alerts (is_resolved)",
                "CREATE INDEX IF NOT EXISTS idx_risk_actions_timestamp ON risk_actions (timestamp DESC)"
            ]
            
            for idx in create_indexes:
                db_conn.execute_query(idx)
            
            # 初始化配置
            self._init_config()
            
            self.logger.info("风险控制器数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化风险控制器数据库表失败: {e}")
    
    def _init_config(self) -> None:
        """初始化配置到数据库"""
        try:
            # 检查是否已有配置
            query = "SELECT COUNT(*) FROM risk_config"
            result = db_conn.execute_query(query)
            
            if result and result[0]['count'] == 0:
                # 插入配置项
                config_items = [
                    ('max_daily_loss_pct', self.config['max_daily_loss_pct'], None, None, '最大日亏损比例'),
                    ('max_position_pct', self.config['max_position_pct'], None, None, '最大单一仓位比例'),
                    ('max_sector_exposure_pct', self.config['max_sector_exposure_pct'], None, None, '最大行业敞口比例'),
                    ('max_leverage', self.config['max_leverage'], None, None, '最大杠杆倍数'),
                    ('stop_loss_pct', self.config['stop_loss_pct'], None, None, '止损比例'),
                    ('monitoring_interval', None, str(self.config['monitoring_interval']), None, '监控间隔（秒）'),
                    ('auto_risk_control', None, None, self.config['auto_risk_control'], '是否启用自动风险控制')
                ]
                
                insert_query = """
                INSERT INTO risk_config (name, value, string_value, boolean_value, description)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                for item in config_items:
                    db_conn.execute_query(insert_query, item)
                
                self.logger.info("已初始化风险控制配置")
        except Exception as e:
            self.logger.error(f"初始化风险控制配置失败: {e}")
    
    def start_monitoring(self, account_data_source: Callable, 
                        position_data_source: Callable, 
                        order_executor: Optional[Callable] = None) -> bool:
        """
        启动风险监控
        
        参数:
            account_data_source: 账户数据源函数，用于获取账户信息
            position_data_source: 仓位数据源函数，用于获取仓位信息
            order_executor: 订单执行函数，用于执行风险控制操作（如自动平仓）
            
        返回:
            是否成功启动监控
        """
        if self.is_monitoring:
            self.logger.warning("风险监控已经在运行中")
            return False
        
        self.is_monitoring = True
        self.account_data_source = account_data_source
        self.position_data_source = position_data_source
        self.order_executor = order_executor
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"已启动风险监控，间隔{self.config['monitoring_interval']}秒，自动风险控制：{'开启' if self.config['auto_risk_control'] else '关闭'}")
        
        return True
    
    def stop_monitoring(self) -> bool:
        """
        停止风险监控
        
        返回:
            是否成功停止监控
        """
        if not self.is_monitoring:
            self.logger.warning("风险监控未在运行")
            return False
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            self.monitor_thread = None
        
        self.logger.info("已停止风险监控")
        
        return True
    
    def _monitoring_loop(self) -> None:
        """
        监控循环，定期获取数据并进行风险分析
        """
        while self.is_monitoring:
            try:
                # 从数据库获取最新配置
                self._load_config_from_db()
                
                # 更新账户和仓位信息
                self._update_data()
                
                # 计算风险指标
                risk_metrics = self._calculate_risk_metrics()
                
                # 保存风险指标到数据库
                if risk_metrics:
                    self._save_risk_metrics(risk_metrics)
                
                # 检查风险阈值
                self._check_risk_thresholds(risk_metrics)
                
                # 执行风险控制（如果启用）
                if self.config['auto_risk_control']:
                    self._execute_risk_control(risk_metrics)
                
                # 等待下一次监控
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"风险监控出错: {e}")
                time.sleep(5)  # 出错后短暂等待再重试
    
    def _load_config_from_db(self) -> None:
        """从数据库加载配置"""
        try:
            query = "SELECT name, value, string_value, boolean_value FROM risk_config"
            results = db_conn.execute_query(query)
            
            if results:
                for result in results:
                    name = result['name']
                    if name in self.config:
                        if result['value'] is not None:
                            self.config[name] = result['value']
                        elif result['string_value'] is not None:
                            # 尝试转换为整数
                            try:
                                self.config[name] = int(result['string_value'])
                            except ValueError:
                                self.config[name] = result['string_value']
                        elif result['boolean_value'] is not None:
                            self.config[name] = result['boolean_value']
        except Exception as e:
            self.logger.error(f"加载风险配置失败: {e}")
    
    def _update_data(self) -> None:
        """
        更新账户和仓位数据
        """
        # 这个方法现在只需调用数据源函数获取最新数据
        # 数据处理已在计算风险指标时完成
        pass
    
    def _calculate_risk_metrics(self) -> Dict[str, Any]:
        """
        计算风险指标
        
        返回:
            风险指标字典
        """
        risk_metrics = {
            'timestamp': datetime.now(),
            'daily_pnl_pct': 0.0,  # 当日盈亏比例
            'max_position_pct': 0.0,  # 最大单一仓位比例
            'max_sector_exposure_pct': 0.0,  # 最大行业敞口比例
            'current_leverage': 1.0,  # 当前杠杆倍数
            'portfolio_var': 0.0,  # 组合风险价值
            'portfolio_volatility': 0.0,  # 组合波动率
            'drawdown': 0.0,  # 当前回撤
            'risk_level': 'low'  # 综合风险等级
        }
        
        try:
            # 获取账户信息
            account_data = self.account_data_source() if self.account_data_source else {}
            
            # 获取仓位信息
            position_data = self.position_data_source() if self.position_data_source else {}
            
            # 计算当日盈亏比例
            if account_data and 'daily_pnl' in account_data and 'equity' in account_data and account_data['equity'] > 0:
                risk_metrics['daily_pnl_pct'] = account_data['daily_pnl'] / account_data['equity']
            
            # 计算最大单一仓位比例
            if position_data and account_data and 'equity' in account_data and account_data['equity'] > 0:
                position_pcts = []
                for symbol, position in position_data.items():
                    if 'market_value' in position:
                        position_pct = abs(position['market_value']) / account_data['equity']
                        position_pcts.append(position_pct)
                
                if position_pcts:
                    risk_metrics['max_position_pct'] = max(position_pcts)
            
            # 计算最大行业敞口比例
            if position_data and account_data and 'equity' in account_data and account_data['equity'] > 0:
                # 按行业分组计算敞口
                sector_exposures = {}
                for symbol, position in position_data.items():
                    if 'market_value' in position and 'sector' in position:
                        sector = position['sector']
                        if sector not in sector_exposures:
                            sector_exposures[sector] = 0
                        sector_exposures[sector] += abs(position['market_value'])
                
                # 计算行业敞口比例
                if sector_exposures:
                    sector_exposure_pcts = [exposure / account_data['equity'] for exposure in sector_exposures.values()]
                    risk_metrics['max_sector_exposure_pct'] = max(sector_exposure_pcts)
            
            # 计算当前杠杆倍数
            if account_data and 'equity' in account_data and 'total_position_value' in account_data and account_data['equity'] > 0:
                risk_metrics['current_leverage'] = account_data['total_position_value'] / account_data['equity']
            
            # 计算组合波动率（简化计算）
            # 从数据库获取历史盈亏数据
            query = """
            SELECT daily_pnl_pct FROM risk_metrics 
            WHERE timestamp > NOW() - INTERVAL '30 days' 
            ORDER BY timestamp DESC LIMIT 20
            """
            results = db_conn.execute_query(query)
            
            if results and len(results) >= 5:
                # 使用最近的日收益率计算波动率
                recent_returns = [item['daily_pnl_pct'] for item in results]
                if recent_returns:
                    risk_metrics['portfolio_volatility'] = np.std(recent_returns) * np.sqrt(252)  # 年化波动率
            
            # 计算组合风险价值（VaR）
            if risk_metrics['portfolio_volatility'] > 0:
                # 使用参数化方法计算95%置信度的日VaR
                confidence_level = 1.645  # 95%置信度的Z值
                risk_metrics['portfolio_var'] = confidence_level * risk_metrics['portfolio_volatility'] / np.sqrt(252)
            
            # 计算当前回撤
            if account_data and 'equity' in account_data and 'high_watermark' in account_data and account_data['high_watermark'] > 0:
                risk_metrics['drawdown'] = 1 - account_data['equity'] / account_data['high_watermark']
            
            # 计算综合风险等级
            risk_metrics['risk_level'] = self._calculate_risk_level(risk_metrics)
            
        except Exception as e:
            self.logger.error(f"计算风险指标出错: {e}")
        
        return risk_metrics
    
    def _calculate_risk_level(self, risk_metrics: Dict[str, Any]) -> str:
        """
        计算综合风险等级
        
        参数:
            risk_metrics: 风险指标字典
        
        返回:
            风险等级字符串
        """
        # 风险评分（0-100）
        risk_score = 0
        
        # 根据各风险指标计算风险分数
        # 1. 日亏损
        daily_loss_score = min(100, max(0, risk_metrics['daily_pnl_pct'] * -100 / self.config['max_daily_loss_pct']))
        
        # 2. 最大仓位
        position_score = min(100, max(0, risk_metrics['max_position_pct'] * 100 / self.config['max_position_pct']))
        
        # 3. 行业敞口
        sector_score = min(100, max(0, risk_metrics['max_sector_exposure_pct'] * 100 / self.config['max_sector_exposure_pct']))
        
        # 4. 杠杆
        leverage_score = min(100, max(0, risk_metrics['current_leverage'] * 100 / self.config['max_leverage']))
        
        # 5. 回撤
        drawdown_score = min(100, max(0, risk_metrics['drawdown'] * 100 / 0.2))  # 假设20%回撤为满分
        
        # 加权计算总分
        weights = {
            'daily_loss': 0.25,
            'position': 0.2,
            'sector': 0.15,
            'leverage': 0.2,
            'drawdown': 0.2
        }
        
        risk_score = (
            daily_loss_score * weights['daily_loss'] +
            position_score * weights['position'] +
            sector_score * weights['sector'] +
            leverage_score * weights['leverage'] +
            drawdown_score * weights['drawdown']
        )
        
        # 根据风险分数确定风险等级
        if risk_score < 30:
            return 'low'
        elif risk_score < 60:
            return 'medium'
        else:
            return 'high'
    
    def _save_risk_metrics(self, risk_metrics: Dict[str, Any]) -> None:
        """
        保存风险指标到数据库
        
        参数:
            risk_metrics: 风险指标字典
        """
        try:
            query = """
            INSERT INTO risk_metrics (timestamp, daily_pnl_pct, max_position_pct, 
                                    max_sector_exposure_pct, current_leverage, 
                                    portfolio_var, portfolio_volatility, drawdown, 
                                    risk_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                risk_metrics['timestamp'],
                risk_metrics['daily_pnl_pct'],
                risk_metrics['max_position_pct'],
                risk_metrics['max_sector_exposure_pct'],
                risk_metrics['current_leverage'],
                risk_metrics['portfolio_var'],
                risk_metrics['portfolio_volatility'],
                risk_metrics['drawdown'],
                risk_metrics['risk_level']
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"保存风险指标失败: {e}")
    
    def _check_risk_thresholds(self, risk_metrics: Dict[str, Any]) -> None:
        """
        检查风险阈值，生成风险警报
        
        参数:
            risk_metrics: 风险指标字典
        """
        try:
            # 获取账户信息和仓位信息
            account_data = self.account_data_source() if self.account_data_source else {}
            position_data = self.position_data_source() if self.position_data_source else {}
            
            # 检查日亏损
            if risk_metrics['daily_pnl_pct'] < 0 and abs(risk_metrics['daily_pnl_pct']) > self.config['max_daily_loss_pct']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'daily_loss_alert',
                    'message': f"日亏损超过阈值: {risk_metrics['daily_pnl_pct']:.2%}",
                    'severity': 'high',
                    'data': {
                        'daily_pnl_pct': risk_metrics['daily_pnl_pct'],
                        'threshold': self.config['max_daily_loss_pct']
                    },
                    'symbol': None
                }
                self._save_risk_alert(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查单一仓位
            if risk_metrics['max_position_pct'] > self.config['max_position_pct']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'position_size_alert',
                    'message': f"单一仓位比例超过阈值: {risk_metrics['max_position_pct']:.2%}",
                    'severity': 'medium',
                    'data': {
                        'max_position_pct': risk_metrics['max_position_pct'],
                        'threshold': self.config['max_position_pct']
                    },
                    'symbol': None
                }
                self._save_risk_alert(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查行业敞口
            if risk_metrics['max_sector_exposure_pct'] > self.config['max_sector_exposure_pct']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'sector_exposure_alert',
                    'message': f"行业敞口比例超过阈值: {risk_metrics['max_sector_exposure_pct']:.2%}",
                    'severity': 'medium',
                    'data': {
                        'max_sector_exposure_pct': risk_metrics['max_sector_exposure_pct'],
                        'threshold': self.config['max_sector_exposure_pct']
                    },
                    'symbol': None
                }
                self._save_risk_alert(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查杠杆
            if risk_metrics['current_leverage'] > self.config['max_leverage']:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'leverage_alert',
                    'message': f"杠杆倍数超过阈值: {risk_metrics['current_leverage']:.2f}x",
                    'severity': 'high',
                    'data': {
                        'current_leverage': risk_metrics['current_leverage'],
                        'threshold': self.config['max_leverage']
                    },
                    'symbol': None
                }
                self._save_risk_alert(alert)
                self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
            # 检查止损
            for symbol, position in position_data.items():
                if 'unrealized_pnl_pct' in position and position['unrealized_pnl_pct'] < 0 and abs(position['unrealized_pnl_pct']) > self.config['stop_loss_pct']:
                    alert = {
                        'timestamp': datetime.now(),
                        'type': 'stop_loss_alert',
                        'symbol': symbol,
                        'message': f"{symbol}亏损超过止损阈值: {position['unrealized_pnl_pct']:.2%}",
                        'severity': 'high',
                        'data': {
                            'symbol': symbol,
                            'unrealized_pnl_pct': position['unrealized_pnl_pct'],
                            'threshold': self.config['stop_loss_pct']
                        }
                    }
                    self._save_risk_alert(alert)
                    self.logger.warning(f"{alert['message']} (严重程度: {alert['severity']})")
            
        except Exception as e:
            self.logger.error(f"检查风险阈值出错: {e}")
    
    def _save_risk_alert(self, alert: Dict[str, Any]) -> None:
        """
        保存风险警报到数据库
        
        参数:
            alert: 风险警报字典
        """
        try:
            query = """
            INSERT INTO risk_alerts (timestamp, type, message, severity, data, symbol)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                alert['timestamp'],
                alert['type'],
                alert['message'],
                alert['severity'],
                str(alert['data']),  # 将字典转换为字符串存储
                alert.get('symbol')
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"保存风险警报失败: {e}")
    
    def _execute_risk_control(self, risk_metrics: Dict[str, Any]) -> None:
        """
        执行风险控制操作
        
        参数:
            risk_metrics: 风险指标字典
        """
        if not self.order_executor or not self.position_data_source:
            return
        
        try:
            # 获取账户信息和仓位信息
            account_data = self.account_data_source() if self.account_data_source else {}
            position_data = self.position_data_source() if self.position_data_source else {}
            
            # 检查是否需要执行风险控制
            risk_control_needed = False
            risk_control_actions = []
            
            # 1. 日亏损控制 - 如果日亏损超过阈值的1.5倍，平掉所有亏损仓位
            if risk_metrics['daily_pnl_pct'] < 0 and abs(risk_metrics['daily_pnl_pct']) > 1.5 * self.config['max_daily_loss_pct']:
                risk_control_needed = True
                action = {
                    'type': 'close_losing_positions',
                    'reason': f"日亏损超过阈值的1.5倍: {risk_metrics['daily_pnl_pct']:.2%}",
                    'positions': []
                }
                
                # 找出所有亏损仓位
                for symbol, position in position_data.items():
                    if 'unrealized_pnl' in position and position['unrealized_pnl'] < 0:
                        action['positions'].append({
                            'symbol': symbol,
                            'quantity': position.get('quantity', 0),
                            'side': 'sell' if position.get('quantity', 0) > 0 else 'buy'
                        })
                
                if action['positions']:
                    risk_control_actions.append(action)
            
            # 2. 止损控制 - 平掉超过止损阈值的仓位
            for symbol, position in position_data.items():
                if 'unrealized_pnl_pct' in position and position['unrealized_pnl_pct'] < 0 and abs(position['unrealized_pnl_pct']) > self.config['stop_loss_pct']:
                    risk_control_needed = True
                    action = {
                        'type': 'stop_loss',
                        'reason': f"{symbol}亏损超过止损阈值: {position['unrealized_pnl_pct']:.2%}",
                        'positions': [{
                            'symbol': symbol,
                            'quantity': position.get('quantity', 0),
                            'side': 'sell' if position.get('quantity', 0) > 0 else 'buy'
                        }]
                    }
                    risk_control_actions.append(action)
            
            # 3. 杠杆控制 - 如果杠杆超过阈值，按比例减仓
            if risk_metrics['current_leverage'] > self.config['max_leverage']:
                risk_control_needed = True
                # 计算需要减仓的比例
                reduction_ratio = 1 - (self.config['max_leverage'] / risk_metrics['current_leverage'])
                
                action = {
                    'type': 'reduce_leverage',
                    'reason': f"杠杆倍数超过阈值: {risk_metrics['current_leverage']:.2f}x，需减仓{reduction_ratio:.2%}",
                    'positions': []
                }
                
                # 对所有仓位按比例减仓
                for symbol, position in position_data.items():
                    if 'quantity' in position and position['quantity'] != 0:
                        reduce_quantity = abs(position['quantity']) * reduction_ratio
                        action['positions'].append({
                            'symbol': symbol,
                            'quantity': reduce_quantity,
                            'side': 'sell' if position['quantity'] > 0 else 'buy'
                        })
                
                if action['positions']:
                    risk_control_actions.append(action)
            
            # 执行风险控制操作
            if risk_control_needed and risk_control_actions:
                for action in risk_control_actions:
                    self.logger.warning(f"执行风险控制: {action['type']} - {action['reason']}")
                    
                    # 保存风险控制操作到数据库
                    action_id = self._save_risk_action(action)
                    
                    # 执行订单
                    action_successful = True
                    for position in action['positions']:
                        try:
                            order_result = self.order_executor({
                                'symbol': position['symbol'],
                                'side': position['side'],
                                'quantity': position['quantity'],
                                'order_type': 'market',
                                'time_in_force': 'day',
                                'risk_control': True
                            })
                            
                            self.logger.info(f"风险控制订单执行结果: {order_result}")
                            
                        except Exception as e:
                            self.logger.error(f"执行风险控制订单出错: {e}")
                            action_successful = False
                    
                    # 更新风险控制操作状态
                    if action_id:
                        status = 'completed' if action_successful else 'failed'
                        self._update_risk_action_status(action_id, status)
            
        except Exception as e:
            self.logger.error(f"执行风险控制出错: {e}")
    
    def _save_risk_action(self, action: Dict[str, Any]) -> Optional[int]:
        """
        保存风险控制操作到数据库
        
        参数:
            action: 风险控制操作字典
        
        返回:
            操作ID
        """
        try:
            query = """
            INSERT INTO risk_actions (timestamp, type, reason, positions)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            params = (
                datetime.now(),
                action['type'],
                action['reason'],
                str(action['positions'])  # 将列表转换为字符串存储
            )
            
            result = db_conn.execute_query(query, params)
            
            if result and len(result) > 0:
                return result[0]['id']
            
            return None
        except Exception as e:
            self.logger.error(f"保存风险控制操作失败: {e}")
            return None
    
    def _update_risk_action_status(self, action_id: int, status: str) -> None:
        """
        更新风险控制操作状态
        
        参数:
            action_id: 操作ID
            status: 新状态
        """
        try:
            query = """
            UPDATE risk_actions
            SET status = %s
            WHERE id = %s
            """
            db_conn.execute_query(query, (status, action_id))
        except Exception as e:
            self.logger.error(f"更新风险控制操作状态失败: {e}")
    
    def get_risk_alerts(self, start_time: Optional[datetime] = None, 
                       alert_types: Optional[List[str]] = None, 
                       min_severity: Optional[str] = None) -> List[Dict]:
        """
        获取风险警报列表
        
        参数:
            start_time: 开始时间，只返回该时间之后的警报
            alert_types: 警报类型列表，只返回指定类型的警报
            min_severity: 最低严重程度，只返回不低于该严重程度的警报
            
        返回:
            风险警报列表
        """
        try:
            query = """
            SELECT id, timestamp, type, message, severity, data, symbol, is_resolved
            FROM risk_alerts
            WHERE 1=1
            """
            params = []
            
            # 按时间过滤
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            # 按类型过滤
            if alert_types:
                query += f" AND type IN ({','.join(['%s'] * len(alert_types))})"
                params.extend(alert_types)
            
            # 按严重程度过滤
            if min_severity:
                severity_levels = {'low': 0, 'medium': 1, 'high': 2}
                min_level = severity_levels.get(min_severity.lower(), 0)
                
                # 构建严重程度过滤条件
                severity_conditions = []
                for level_name, level_value in severity_levels.items():
                    if level_value >= min_level:
                        severity_conditions.append(level_name)
                
                if severity_conditions:
                    query += f" AND severity IN ({','.join(['%s'] * len(severity_conditions))})"
                    params.extend(severity_conditions)
            
            # 按时间排序（最新的在前）
            query += " ORDER BY timestamp DESC"
            
            results = db_conn.execute_query(query, tuple(params))
            
            # 转换数据格式
            alerts = []
            if results:
                for result in results:
                    # 尝试将data字符串转换回字典
                    try:
                        data = eval(result['data']) if result['data'] else {}
                    except:
                        data = {}
                    
                    alert = {
                        'id': result['id'],
                        'timestamp': result['timestamp'],
                        'type': result['type'],
                        'message': result['message'],
                        'severity': result['severity'],
                        'data': data,
                        'symbol': result['symbol'],
                        'is_resolved': result['is_resolved']
                    }
                    alerts.append(alert)
            
            return alerts
        except Exception as e:
            self.logger.error(f"获取风险警报失败: {e}")
            return []
    
    def get_risk_summary(self) -> Dict:
        """
        获取风险概览
        
        返回:
            风险概览字典
        """
        summary = {
            'timestamp': datetime.now(),
            'risk_level': 'low',
            'metrics': {},
            'alerts_count': 0,
            'actions_count': 0,
            'config': self.config
        }
        
        try:
            # 获取最新的风险指标
            metrics_query = """
            SELECT * FROM risk_metrics 
            ORDER BY timestamp DESC LIMIT 1
            """
            metrics_result = db_conn.execute_query(metrics_query)
            
            if metrics_result and len(metrics_result) > 0:
                metrics = metrics_result[0]
                summary['risk_level'] = metrics['risk_level']
                summary['metrics'] = metrics
            
            # 获取未解决的警报数量
            alerts_query = "SELECT COUNT(*) FROM risk_alerts WHERE is_resolved = false"
            alerts_result = db_conn.execute_query(alerts_query)
            
            if alerts_result and len(alerts_result) > 0:
                summary['alerts_count'] = alerts_result[0]['count']
            
            # 获取风险控制操作数量
            actions_query = "SELECT COUNT(*) FROM risk_actions"
            actions_result = db_conn.execute_query(actions_query)
            
            if actions_result and len(actions_result) > 0:
                summary['actions_count'] = actions_result[0]['count']
            
        except Exception as e:
            self.logger.error(f"获取风险概览失败: {e}")
        
        return summary

# 创建全局风险控制器实例
risk_controller = RiskController()