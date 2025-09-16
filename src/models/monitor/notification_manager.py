# 通知管理模块
import datetime
import json
import os
import logging
from typing import List, Dict, Any, Optional
from .database_connection import db_conn
from .alert_system import alert_system

# 默认通知配置
default_notification_config = {
    'channels': {
        'email': {
            'enabled': True,
            'recipients': ['user@example.com']
        },
        'sms': {
            'enabled': False,
            'recipients': ['13800138000']
        },
        'app': {
            'enabled': True
        }
    },
    'notification_types': {
        'trade': {
            'enabled': True,
            'channels': ['app', 'email'],
            'min_amount': 10000  # 交易金额大于此值时才通知
        },
        'risk': {
            'enabled': True,
            'channels': ['app', 'email', 'sms'],  # 风险通知通过所有渠道
            'levels': ['warning', 'danger']  # 只通知警告和危险级别的风险
        },
        'system': {
            'enabled': True,
            'channels': ['app', 'email']
        },
        'balance': {
            'enabled': True,
            'channels': ['app', 'email'],
            'min_balance': 10000  # 余额低于此值时通知
        }
    }
}

class NotificationManager:
    """通知管理类，负责管理通知配置和发送通知"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 初始化数据库表
        self._init_database()
        # 初始化配置
        self.config = self._load_config()
        
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            # 创建通知配置表
            create_config_table = """
            CREATE TABLE IF NOT EXISTS notification_config (
                id SERIAL PRIMARY KEY,
                account_id VARCHAR(50) NOT NULL DEFAULT 'default',
                config_key VARCHAR(100) NOT NULL,
                config_value JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (account_id, config_key)
            )
            """
            db_conn.execute_query(create_config_table)
            
            # 创建通知日志表
            create_log_table = """
            CREATE TABLE IF NOT EXISTS notification_log (
                id SERIAL PRIMARY KEY,
                account_id VARCHAR(50),
                type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                level VARCHAR(20) DEFAULT 'info',
                channels JSONB NOT NULL,
                success BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            db_conn.execute_query(create_log_table)
            
            # 创建索引
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_notification_config_account ON notification_config(account_id)",
                "CREATE INDEX IF NOT EXISTS idx_notification_log_account ON notification_log(account_id)",
                "CREATE INDEX IF NOT EXISTS idx_notification_log_type ON notification_log(type)",
                "CREATE INDEX IF NOT EXISTS idx_notification_log_timestamp ON notification_log(timestamp)"
            ]
            
            for idx in indexes_sql:
                db_conn.execute_query(idx)
                
            self.logger.info("通知系统数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化通知系统数据库表失败: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """从数据库加载通知配置
        
        Returns:
            通知配置
        """
        try:
            # 查询默认配置
            query = """
            SELECT config_key, config_value 
            FROM notification_config 
            WHERE account_id = 'default'
            """
            
            results = db_conn.execute_query(query)
            
            if results:
                # 构建配置字典
                config = {}
                for row in results:
                    config[row['config_key']] = row['config_value']
                return config
            else:
                # 如果数据库中没有配置，使用默认配置并保存
                self._save_config(default_notification_config)
                return default_notification_config
        except Exception as e:
            self.logger.error(f"从数据库加载通知配置失败: {e}")
            return default_notification_config.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """保存通知配置到数据库
        
        Args:
            config: 通知配置
        
        Returns:
            保存是否成功
        """
        try:
            # 清空默认配置
            delete_query = "DELETE FROM notification_config WHERE account_id = 'default'"
            db_conn.execute_query(delete_query)
            
            # 插入新配置
            insert_query = """
            INSERT INTO notification_config (account_id, config_key, config_value)
            VALUES ('default', %s, %s)
            """
            
            for key, value in config.items():
                params = (key, json.dumps(value, ensure_ascii=False))
                db_conn.execute_query(insert_query, params)
                
            self.logger.info("通知配置已保存到数据库")
            return True
        except Exception as e:
            self.logger.error(f"保存通知配置到数据库失败: {e}")
            return False
    
    def get_notification_config(self) -> Dict[str, Any]:
        """获取通知配置
        
        Returns:
            通知配置
        """
        return self.config.copy()
    
    def update_notification_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新通知配置
        
        Args:
            new_config: 新的通知配置
        
        Returns:
            更新后的通知配置
        """
        self.config.update(new_config)
        self._save_config(self.config)
        return self.config.copy()
        
    def _log_notification(self, notification_data: Dict[str, Any], results: Dict[str, Any], success: bool) -> None:
        """记录通知日志到数据库
        
        Args:
            notification_data: 通知数据
            results: 通知发送结果
            success: 是否成功
        """
        try:
            query = """
            INSERT INTO notification_log (account_id, type, title, message, level, channels, success)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                notification_data.get('accountId'),
                notification_data.get('type', 'system'),
                notification_data.get('title', '系统通知'),
                notification_data.get('message', ''),
                notification_data.get('level', 'info'),
                json.dumps(results),
                success
            )
            
            db_conn.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"记录通知日志失败: {e}")
    
    def get_channel_config(self, channel: str) -> Optional[Dict[str, Any]]:
        """获取指定通知渠道的配置
        
        Args:
            channel: 通知渠道（email、sms、app等）
        
        Returns:
            通知渠道配置
        """
        return self.config.get('channels', {}).get(channel)
    
    def update_channel_config(self, channel: str, channel_config: Dict[str, Any]) -> bool:
        """更新通知渠道配置
        
        Args:
            channel: 通知渠道
            channel_config: 渠道配置
        
        Returns:
            更新是否成功
        """
        if 'channels' not in self.config:
            self.config['channels'] = {}
        
        self.config['channels'][channel] = channel_config
        return self._save_config(self.config)
    
    def get_notification_type_config(self, notification_type: str) -> Optional[Dict[str, Any]]:
        """获取指定通知类型的配置
        
        Args:
            notification_type: 通知类型（trade、risk、system等）
        
        Returns:
            通知类型配置
        """
        return self.config.get('notification_types', {}).get(notification_type)
    
    def update_notification_type_config(self, notification_type: str, type_config: Dict[str, Any]) -> bool:
        """更新通知类型配置
        
        Args:
            notification_type: 通知类型
            type_config: 类型配置
        
        Returns:
            更新是否成功
        """
        if 'notification_types' not in self.config:
            self.config['notification_types'] = {}
        
        self.config['notification_types'][notification_type] = type_config
        return self._save_config(self.config)
    
    def should_send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """判断是否应该发送通知
        
        Args:
            notification_data: 通知数据
        
        Returns:
            是否应该发送通知
        """
        notification_type = notification_data.get('type', 'system')
        
        # 检查通知类型是否启用
        type_config = self.get_notification_type_config(notification_type)
        if not type_config or not type_config.get('enabled', False):
            return False
        
        # 根据不同类型的特定条件进行判断
        if notification_type == 'trade':
            # 检查交易金额是否达到最小通知金额
            min_amount = type_config.get('min_amount', 0)
            amount = notification_data.get('amount', 0)
            if amount < min_amount:
                return False
        elif notification_type == 'risk':
            # 检查风险级别是否在配置范围内
            levels = type_config.get('levels', ['warning', 'danger'])
            level = notification_data.get('level', 'info')
            if level not in levels:
                return False
        elif notification_type == 'balance':
            # 检查余额是否低于最小通知余额
            min_balance = type_config.get('min_balance', 0)
            balance = notification_data.get('balance', 0)
            if balance >= min_balance:
                return False
        
        return True
    
    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送通知
        
        Args:
            notification_data: 通知数据
        
        Returns:
            通知发送结果
        """
        # 首先检查是否应该发送通知
        if not self.should_send_notification(notification_data):
            return {
                'success': False,
                'message': '通知未达到发送条件',
                'skipped': True
            }
        
        notification_type = notification_data.get('type', 'system')
        type_config = self.get_notification_type_config(notification_type)
        channels = type_config.get('channels', ['app']) if type_config else ['app']
        
        # 准备通知内容
        title = notification_data.get('title', '系统通知')
        message = notification_data.get('message', '')
        level = notification_data.get('level', 'info')
        timestamp = notification_data.get('timestamp', datetime.datetime.now().timestamp())
        account_id = notification_data.get('accountId')
        
        # 发送到指定渠道
        results = {}
        for channel in channels:
            if self._should_use_channel(channel):
                results[channel] = self._send_via_channel(channel, {
                    'title': title,
                    'message': message,
                    'level': level,
                    'timestamp': timestamp,
                    'accountId': account_id,
                    'type': notification_type
                })
        
        # 记录到警报系统
        alert_result = alert_system.add_alert(notification_data)
        
        # 记录通知日志
        success = all(r.get('success', False) for r in results.values())
        self._log_notification(notification_data, results, success)
        
        return {
            'success': success,
            'channels': results,
            'alertId': alert_result.get('id')
        }
    
    def _should_use_channel(self, channel: str) -> bool:
        """检查是否应该使用指定的通知渠道
        
        Args:
            channel: 通知渠道
        
        Returns:
            是否应该使用该渠道
        """
        # 应用内通知(app)始终可用，即使没有配置
        if channel == 'app':
            return True
        
        # 其他渠道需要检查配置和启用状态
        channel_config = self.get_channel_config(channel)
        return channel_config and channel_config.get('enabled', False)
    
    def _send_via_channel(self, channel: str, notification: Dict[str, Any]) -> Dict[str, Any]:
        """通过指定渠道发送通知
        
        Args:
            channel: 通知渠道
            notification: 通知内容
        
        Returns:
            发送结果
        """
        # 在实际应用中，这里应该实现真实的通知发送逻辑
        # 这里仅做模拟
        try:
            if channel == 'email':
                # 模拟发送邮件
                channel_config = self.get_channel_config('email')
                recipients = channel_config.get('recipients', [])
                self.logger.info(f"[邮件通知] 发送给: {recipients}, 标题: {notification['title']}")
                return {'success': True, 'recipients': recipients}
                
            elif channel == 'sms':
                # 模拟发送短信
                channel_config = self.get_channel_config('sms')
                recipients = channel_config.get('recipients', [])
                self.logger.info(f"[短信通知] 发送给: {recipients}, 内容: {notification['message']}")
                return {'success': True, 'recipients': recipients}
                
            elif channel == 'app':
                # 应用内通知已通过alert_system处理
                self.logger.info(f"[应用内通知] 标题: {notification['title']}")
                return {'success': True}
                
            else:
                self.logger.warning(f"未知的通知渠道: {channel}")
                return {'success': False, 'error': '未知的通知渠道'}
                
        except Exception as e:
            self.logger.error(f"通过渠道{channel}发送通知失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_trade_notification(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送交易通知
        
        Args:
            trade_data: 交易数据
        
        Returns:
            通知发送结果
        """
        # 构建交易通知内容
        trade_type = trade_data.get('type', 'buy')
        type_text = '买入' if trade_type == 'buy' else '卖出'
        symbol = trade_data.get('symbol', '')
        name = trade_data.get('name', '')
        quantity = trade_data.get('quantity', 0)
        price = trade_data.get('price', 0)
        amount = trade_data.get('amount', 0)
        status = trade_data.get('status', 'completed')
        
        # 根据交易状态确定通知内容
        if status == 'completed':
            title = f'交易执行成功'
            message = f'{type_text}{name}({symbol}) {quantity}股，价格{price:.2f}元，金额{amount:.2f}元'
            level = 'info'
        else:
            title = f'交易执行失败'
            message = f'{type_text}{name}({symbol}) 失败，状态: {status}'
            level = 'warning'
        
        # 发送通知
        return self.send_notification({
            'type': 'trade',
            'title': title,
            'message': message,
            'level': level,
            'accountId': trade_data.get('accountId'),
            'amount': amount
        })
    
    def send_risk_notification(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送风险通知
        
        Args:
            risk_data: 风险数据
        
        Returns:
            通知发送结果
        """
        # 构建风险通知内容
        title = risk_data.get('title', '风险预警')
        message = risk_data.get('message', '')
        level = risk_data.get('level', 'warning')
        
        # 发送通知
        return self.send_notification({
            'type': 'risk',
            'title': title,
            'message': message,
            'level': level,
            'accountId': risk_data.get('accountId')
        })

    def save_notification_config(self, account_id: str = 'default', config: Dict[str, Any] = None) -> Dict[str, Any]:
        """保存通知配置到数据库
        
        Args:
            account_id: 账户ID
            config: 要保存的配置
        
        Returns:
            保存后的配置
        """
        if account_id == 'default':
            # 更新默认配置
            if config:
                self.config.update(config)
            self._save_config(self.config)
            return self.config.copy()
        else:
            # 保存特定账户的配置
            try:
                # 先检查是否存在该账户的配置
                query = """
                SELECT config_key, config_value 
                FROM notification_config 
                WHERE account_id = %s
                """
                
                results = db_conn.execute_query(query, (account_id,))
                
                # 构建账户配置
                account_config = {}
                for row in results:
                    account_config[row['config_key']] = row['config_value']
                
                # 更新配置
                if config:
                    account_config.update(config)
                
                # 清空旧配置并保存新配置
                delete_query = "DELETE FROM notification_config WHERE account_id = %s"
                db_conn.execute_query(delete_query, (account_id,))
                
                insert_query = """
                INSERT INTO notification_config (account_id, config_key, config_value)
                VALUES (%s, %s, %s)
                """
                
                for key, value in account_config.items():
                    params = (account_id, key, json.dumps(value, ensure_ascii=False))
                    db_conn.execute_query(insert_query, params)
                
                self.logger.info(f"已保存账户{account_id}的通知配置")
                return account_config.copy()
            except Exception as e:
                self.logger.error(f"保存账户{account_id}的通知配置失败: {e}")
                return self.config.copy()
    
    def get_config(self, account_id: str = 'default') -> Dict[str, Any]:
        """获取通知配置
        
        Args:
            account_id: 账户ID，默认为'default'
        
        Returns:
            通知配置字典
        """
        if account_id == 'default':
            return self.config.copy()
        
        # 获取特定账户的配置
        try:
            query = """
            SELECT config_key, config_value 
            FROM notification_config 
            WHERE account_id = %s
            """
            
            results = db_conn.execute_query(query, (account_id,))
            
            if results:
                # 构建配置字典
                config = {}
                for row in results:
                    config[row['config_key']] = row['config_value']
                return config
            
            # 如果特定账户配置不存在，返回默认配置的副本
            self.logger.info(f"账户{account_id}的通知配置不存在，返回默认配置")
            return self.config.copy()
        except Exception as e:
            self.logger.error(f"获取账户{account_id}的通知配置失败: {e}")
            return self.config.copy()
            
    def get_notification_history(self, account_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取通知历史记录
        
        Args:
            account_id: 账户ID，可选
            limit: 限制返回的记录数
        
        Returns:
            通知历史记录列表
        """
        try:
            query_parts = ["SELECT id, account_id, type, title, message, level, channels, success, timestamp FROM notification_log WHERE 1=1"]
            params = []
            
            if account_id:
                query_parts.append("AND account_id = %s")
                params.append(account_id)
            
            query_parts.append("ORDER BY timestamp DESC")
            query_parts.append(f"LIMIT %s")
            params.append(limit)
            
            query = " ".join(query_parts)
            results = db_conn.execute_query(query, tuple(params))
            
            return results or []
        except Exception as e:
            self.logger.error(f"获取通知历史记录失败: {e}")
            return []

# 创建全局通知管理器实例
notification_manager = NotificationManager()