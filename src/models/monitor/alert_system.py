import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Callable, Tuple
from datetime import datetime, timedelta
import threading
import time
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .database_connection import db_conn

class AlertSystem:
    """
    警报系统类，用于生成和发送交易警报
    支持多种警报类型和通知方式
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化警报系统
        
        参数:
            config: 配置信息，包含警报系统参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('alert_levels', ['info', 'warning', 'error', 'critical'])  # 警报级别
        self.config.setdefault('notification_methods', ['log'])  # 通知方式，如log, email, sms
        self.config.setdefault('max_alerts_in_memory', 1000)  # 内存中保存的最大警报数量
        
        # 初始化数据库表
        self._init_database()
        
        # 警报历史（内存缓存）
        self.alerts = []
        
        # 加载历史警报到内存
        self._load_recent_alerts()
    
    def _init_database(self) -> None:
        """
        初始化数据库表结构
        """
        try:
            # 创建alerts表
            create_alerts_table = """
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                level VARCHAR(20) NOT NULL,
                data JSONB,
                source VARCHAR(100),
                acknowledged BOOLEAN DEFAULT false,
                acknowledged_time TIMESTAMP,
                acknowledged_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
            db_conn.execute_query(create_alerts_table)
            
            # 创建索引以提高查询性能
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts (type)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts (level)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts (acknowledged)"
            ]
            
            for idx in create_indexes:
                db_conn.execute_query(idx)
            
            self.logger.info("警报系统数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化警报系统数据库表失败: {e}")
    
    def _load_recent_alerts(self) -> None:
        """
        从数据库加载最近的警报到内存
        """
        try:
            query = """
            SELECT id, timestamp, type, message, level, data, source, 
                   acknowledged, acknowledged_time, acknowledged_by
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT %s
            """
            
            result = db_conn.execute_query(query, (self.config['max_alerts_in_memory'],))
            
            # 将数据库结果转换为警报对象列表
            for row in result:
                alert = {
                    'id': row['id'],
                    'timestamp': datetime.fromisoformat(row['timestamp'].isoformat()),
                    'type': row['type'],
                    'message': row['message'],
                    'level': row['level'],
                    'data': row['data'] if row['data'] is not None else {},
                    'source': row['source'] if row['source'] is not None else 'system',
                    'acknowledged': row['acknowledged'],
                    'acknowledged_time': datetime.fromisoformat(row['acknowledged_time'].isoformat()) 
                        if row['acknowledged_time'] is not None else None,
                    'acknowledged_by': row['acknowledged_by']
                }
                self.alerts.append(alert)
            
            # 按时间排序
            self.alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            self.logger.info(f"已从数据库加载{len(self.alerts)}条最近警报")
        except Exception as e:
            self.logger.error(f"加载最近警报失败: {e}")
    
    def add_alert(self, alert_type: str, message: str, level: str = 'info', 
                 data: Optional[Dict] = None, source: Optional[str] = None) -> Dict:
        """
        添加警报
        
        参数:
            alert_type: 警报类型
            message: 警报消息
            level: 警报级别，如info, warning, error, critical
            data: 警报相关数据
            source: 警报来源
            
        返回:
            警报字典
        """
        # 创建警报
        timestamp = datetime.now()
        alert = {
            'timestamp': timestamp,
            'type': alert_type,
            'message': message,
            'level': level,
            'data': data or {},
            'source': source or 'system',
            'acknowledged': False,
            'acknowledged_time': None,
            'acknowledged_by': None
        }
        
        # 保存到数据库
        try:
            query = """
            INSERT INTO alerts (timestamp, type, message, level, data, source)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                alert['timestamp'],
                alert['type'],
                alert['message'],
                alert['level'],
                json.dumps(alert['data']) if alert['data'] else None,
                alert['source']
            )
            
            result = db_conn.execute_query(query, params)
            if result and len(result) > 0:
                alert['id'] = result[0]['id']
            
            self.logger.info(f"已将警报保存到数据库: ID={alert.get('id')}")
        except Exception as e:
            self.logger.error(f"保存警报到数据库失败: {e}")
        
        # 添加到内存中的警报列表
        self.alerts.insert(0, alert.copy())  # 插入到列表开头
        
        # 限制内存中的警报数量
        if len(self.alerts) > self.config['max_alerts_in_memory']:
            self.alerts = self.alerts[:self.config['max_alerts_in_memory']]
        
        # 发送通知
        self._send_notification(alert)
        
        return alert
    
    def _send_notification(self, alert: Dict) -> None:
        """
        发送警报通知
        
        参数:
            alert: 警报字典
        """
        notification_methods = self.config['notification_methods']
        
        for method in notification_methods:
            if method == 'log':
                self._log_alert(alert)
            elif method == 'email':
                self._email_alert(alert)
            elif method == 'sms':
                self._sms_alert(alert)
            elif method == 'webhook':
                self._webhook_alert(alert)
    
    def _log_alert(self, alert: Dict) -> None:
        """
        记录警报到日志
        
        参数:
            alert: 警报字典
        """
        level = alert['level'].lower()
        message = f"[{alert['type']}] {alert['message']}"
        
        if level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'critical':
            self.logger.critical(message)
        else:
            self.logger.info(message)
    
    def _email_alert(self, alert: Dict) -> None:
        """
        通过邮件发送警报
        
        参数:
            alert: 警报字典
        """
        if 'email' not in self.config:
            self.logger.warning("未配置邮件发送参数，无法发送邮件警报")
            return
        
        email_config = self.config['email']
        if not all(k in email_config for k in ['smtp_server', 'smtp_port', 'username', 'password', 'from_addr', 'to_addrs']):
            self.logger.warning("邮件发送参数不完整，无法发送邮件警报")
            return
        
        # 只发送warning及以上级别的警报
        level = alert['level'].lower()
        if level not in ['warning', 'error', 'critical']:
            return
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_config['from_addr']
            msg['To'] = ', '.join(email_config['to_addrs'])
            msg['Subject'] = f"[{level.upper()}] {alert['type']} Alert"
            
            # 邮件内容
            body = f"""<html>
            <body>
                <h2>{alert['type']} Alert</h2>
                <p><strong>Level:</strong> {level.upper()}</p>
                <p><strong>Time:</strong> {alert['timestamp']}</p>
                <p><strong>Message:</strong> {alert['message']}</p>
                <p><strong>Source:</strong> {alert['source']}</p>
                <h3>Additional Data:</h3>
                <pre>{json.dumps(alert['data'], indent=4, default=str)}</pre>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # 发送邮件
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
                
            self.logger.info(f"已发送邮件警报: {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"发送邮件警报出错: {e}")
    
    def _sms_alert(self, alert: Dict) -> None:
        """
        通过短信发送警报
        
        参数:
            alert: 警报字典
        """
        if 'sms' not in self.config:
            self.logger.warning("未配置短信发送参数，无法发送短信警报")
            return
        
        # 只发送error及以上级别的警报
        level = alert['level'].lower()
        if level not in ['error', 'critical']:
            return
        
        # 短信发送逻辑（需要根据具体的短信服务提供商实现）
        self.logger.info(f"已发送短信警报: {alert['type']}")
    
    def _webhook_alert(self, alert: Dict) -> None:
        """
        通过Webhook发送警报
        
        参数:
            alert: 警报字典
        """
        if 'webhook' not in self.config:
            self.logger.warning("未配置Webhook参数，无法发送Webhook警报")
            return
        
        # Webhook发送逻辑（需要根据具体的Webhook服务实现）
        self.logger.info(f"已发送Webhook警报: {alert['type']}")
    
    def get_alerts(self, start_time: Optional[datetime] = None, 
                  end_time: Optional[datetime] = None,
                  alert_types: Optional[List[str]] = None, 
                  levels: Optional[List[str]] = None,
                  acknowledged: Optional[bool] = None) -> List[Dict]:
        """
        获取警报列表
        
        参数:
            start_time: 开始时间，只返回该时间之后的警报
            end_time: 结束时间，只返回该时间之前的警报
            alert_types: 警报类型列表，只返回指定类型的警报
            levels: 警报级别列表，只返回指定级别的警报
            acknowledged: 是否已确认，如果为True只返回已确认的警报，为False只返回未确认的警报
            
        返回:
            警报列表
        """
        try:
            # 构建查询语句
            query_parts = ["""SELECT id, timestamp, type, message, level, data, source,
                            acknowledged, acknowledged_time, acknowledged_by FROM alerts WHERE 1=1"""]
            params = []
            
            # 按时间过滤
            if start_time:
                query_parts.append("AND timestamp >= %s")
                params.append(start_time)
            
            if end_time:
                query_parts.append("AND timestamp <= %s")
                params.append(end_time)
            
            # 按类型过滤
            if alert_types:
                placeholders = ",".join(["%s"] * len(alert_types))
                query_parts.append(f"AND type IN ({placeholders})")
                params.extend(alert_types)
            
            # 按级别过滤
            if levels:
                # 转换为小写以进行不区分大小写的匹配
                lower_levels = [l.lower() for l in levels]
                placeholders = ",".join(["%s"] * len(lower_levels))
                query_parts.append(f"AND LOWER(level) IN ({placeholders})")
                params.extend(lower_levels)
            
            # 按确认状态过滤
            if acknowledged is not None:
                query_parts.append("AND acknowledged = %s")
                params.append(acknowledged)
            
            # 添加排序
            query_parts.append("ORDER BY timestamp DESC")
            
            # 组合完整查询
            query = " ".join(query_parts)
            
            # 执行查询
            result = db_conn.execute_query(query, tuple(params))
            
            # 转换结果格式
            alerts = []
            for row in result:
                alert = {
                    'id': row['id'],
                    'timestamp': datetime.fromisoformat(row['timestamp'].isoformat()),
                    'type': row['type'],
                    'message': row['message'],
                    'level': row['level'],
                    'data': row['data'] if row['data'] is not None else {},
                    'source': row['source'] if row['source'] is not None else 'system',
                    'acknowledged': row['acknowledged'],
                    'acknowledged_time': datetime.fromisoformat(row['acknowledged_time'].isoformat()) 
                        if row['acknowledged_time'] is not None else None,
                    'acknowledged_by': row['acknowledged_by']
                }
                alerts.append(alert)
            
            return alerts
        except Exception as e:
            self.logger.error(f"获取警报列表失败: {e}")
            # 出错时返回内存中的警报，以确保系统仍能正常工作
            filtered_alerts = self.alerts.copy()
            
            # 手动过滤内存中的警报
            if start_time:
                filtered_alerts = [alert for alert in filtered_alerts 
                                  if isinstance(alert['timestamp'], datetime) and alert['timestamp'] >= start_time]
            
            if end_time:
                filtered_alerts = [alert for alert in filtered_alerts 
                                  if isinstance(alert['timestamp'], datetime) and alert['timestamp'] <= end_time]
            
            if alert_types:
                filtered_alerts = [alert for alert in filtered_alerts if alert['type'] in alert_types]
            
            if levels:
                filtered_alerts = [alert for alert in filtered_alerts if alert['level'].lower() in [l.lower() for l in levels]]
            
            if acknowledged is not None:
                filtered_alerts = [alert for alert in filtered_alerts if alert['acknowledged'] == acknowledged]
            
            return filtered_alerts
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """
        确认警报
        
        参数:
            alert_id: 警报ID
            acknowledged_by: 确认人
            
        返回:
            是否成功确认
        """
        try:
            # 更新数据库
            query = """
            UPDATE alerts
            SET acknowledged = true,
                acknowledged_time = NOW(),
                acknowledged_by = %s,
                updated_at = NOW()
            WHERE id = %s
            """
            
            params = (acknowledged_by, alert_id)
            db_conn.execute_query(query, params)
            
            # 更新内存中的警报
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_time'] = datetime.now()
                    alert['acknowledged_by'] = acknowledged_by
                    break
            
            self.logger.info(f"警报 {alert_id} 已被 {acknowledged_by} 确认")
            return True
        except Exception as e:
            self.logger.error(f"确认警报失败: {e}")
            return False
    
    def clear_alerts(self, older_than: Optional[datetime] = None) -> int:
        """
        清除警报
        
        参数:
            older_than: 只清除该时间之前的警报，如果为None则清除所有警报
            
        返回:
            清除的警报数量
        """
        try:
            if older_than is None:
                # 清除所有警报
                query = "DELETE FROM alerts RETURNING id"
                result = db_conn.execute_query(query)
                count = len(result)
            else:
                # 清除指定时间之前的警报
                query = "DELETE FROM alerts WHERE timestamp < %s RETURNING id"
                result = db_conn.execute_query(query, (older_than,))
                count = len(result)
            
            # 更新内存中的警报列表
            if older_than is None:
                self.alerts = []
            else:
                self.alerts = [alert for alert in self.alerts 
                              if not isinstance(alert['timestamp'], datetime) or alert['timestamp'] >= older_than]
            
            self.logger.info(f"已清除{count}条警报")
            return count
        except Exception as e:
            self.logger.error(f"清除警报失败: {e}")
            return 0
    
    def get_alert_summary(self) -> Dict:
        """
        获取警报概览
        
        返回:
            警报概览字典
        """
        try:
            # 从数据库获取统计信息
            stats_query = """
            SELECT 
                COUNT(*) AS total_alerts,
                SUM(CASE WHEN NOT acknowledged THEN 1 ELSE 0 END) AS unacknowledged_alerts,
                COUNT(DISTINCT type) AS distinct_types
            FROM alerts
            """
            
            stats_result = db_conn.execute_query(stats_query)
            stats = stats_result[0] if stats_result and len(stats_result) > 0 else {
                'total_alerts': 0,
                'unacknowledged_alerts': 0,
                'distinct_types': 0
            }
            
            # 按级别统计警报数量
            level_counts_query = """
            SELECT level, COUNT(*) AS count
            FROM alerts
            GROUP BY level
            """
            
            level_counts_result = db_conn.execute_query(level_counts_query)
            level_counts = {row['level']: row['count'] for row in level_counts_result}
            
            # 确保所有警报级别都在统计结果中
            for level in self.config['alert_levels']:
                if level.lower() not in [k.lower() for k in level_counts.keys()]:
                    level_counts[level] = 0
            
            # 按类型统计警报数量
            type_counts_query = """
            SELECT type, COUNT(*) AS count
            FROM alerts
            GROUP BY type
            ORDER BY count DESC
            """
            
            type_counts_result = db_conn.execute_query(type_counts_query)
            type_counts = {row['type']: row['count'] for row in type_counts_result}
            
            # 获取最近的警报
            recent_alerts_query = """
            SELECT id, timestamp, type, message, level, source, acknowledged
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT 10
            """
            
            recent_alerts_result = db_conn.execute_query(recent_alerts_query)
            recent_alerts = []
            for row in recent_alerts_result:
                alert = {
                    'id': row['id'],
                    'timestamp': datetime.fromisoformat(row['timestamp'].isoformat()),
                    'type': row['type'],
                    'message': row['message'],
                    'level': row['level'],
                    'source': row['source'],
                    'acknowledged': row['acknowledged']
                }
                recent_alerts.append(alert)
            
            return {
                'total_alerts': stats['total_alerts'],
                'unacknowledged_alerts': stats['unacknowledged_alerts'],
                'level_counts': level_counts,
                'type_counts': type_counts,
                'recent_alerts': recent_alerts
            }
        except Exception as e:
            self.logger.error(f"获取警报概览失败: {e}")
            # 出错时使用内存中的警报数据生成概览
            
            # 按级别统计警报数量
            level_counts = {}
            for level in self.config['alert_levels']:
                level_counts[level] = len([a for a in self.alerts if a['level'].lower() == level.lower()])
            
            # 按类型统计警报数量
            type_counts = {}
            for alert in self.alerts:
                alert_type = alert['type']
                if alert_type not in type_counts:
                    type_counts[alert_type] = 0
                type_counts[alert_type] += 1
            
            # 统计未确认的警报数量
            unacknowledged_count = len([a for a in self.alerts if not a['acknowledged']])
            
            # 获取最近的警报
            recent_alerts = sorted([a for a in self.alerts if isinstance(a['timestamp'], datetime)], 
                                  key=lambda x: x['timestamp'], reverse=True)[:10]
            
            return {
                'total_alerts': len(self.alerts),
                'unacknowledged_alerts': unacknowledged_count,
                'level_counts': level_counts,
                'type_counts': type_counts,
                'recent_alerts': recent_alerts
            }


class AlertRule:
    """
    警报规则类，用于定义警报触发条件
    """
    
    def __init__(self, rule_id: str, name: str, condition: Callable, 
                 alert_type: str, message_template: str, level: str = 'info',
                 cooldown_period: int = 0, enabled: bool = True):
        """
        初始化警报规则
        
        参数:
            rule_id: 规则ID
            name: 规则名称
            condition: 条件函数，接收数据并返回布尔值
            alert_type: 警报类型
            message_template: 消息模板
            level: 警报级别
            cooldown_period: 冷却期（秒），在此期间内不会重复触发同一规则
            enabled: 是否启用
        """
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.alert_type = alert_type
        self.message_template = message_template
        self.level = level
        self.cooldown_period = cooldown_period
        self.enabled = enabled
        
        # 上次触发时间
        self.last_triggered = None
    
    def check(self, data: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        检查规则是否触发
        
        参数:
            data: 要检查的数据
            
        返回:
            (是否触发, 消息, 相关数据)的元组
        """
        if not self.enabled:
            return False, None, None
        
        # 检查冷却期
        if self.last_triggered and self.cooldown_period > 0:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_period:
                return False, None, None
        
        # 检查条件
        try:
            result = self.condition(data)
            if not result:
                return False, None, None
            
            # 生成消息
            message = self.message_template
            for key, value in data.items():
                placeholder = '{' + key + '}'
                if placeholder in message:
                    message = message.replace(placeholder, str(value))
            
            # 更新上次触发时间
            self.last_triggered = datetime.now()
            
            return True, message, data
            
        except Exception as e:
            logging.error(f"检查警报规则 {self.name} 出错: {e}")
            return False, None, None


class AlertRuleEngine:
    """
    警报规则引擎，用于管理和执行警报规则
    """
    
    def __init__(self, alert_system: AlertSystem):
        """
        初始化警报规则引擎
        
        参数:
            alert_system: 警报系统对象
        """
        self.alert_system = alert_system
        self.logger = logging.getLogger(__name__)
        self.rules = {}  # 规则字典，键为规则ID
        
        # 初始化规则表
        self._init_rules_database()
        
        # 加载已保存的规则
        self._load_rules()
    
    def _init_rules_database(self) -> None:
        """
        初始化规则数据库表
        """
        try:
            # 创建alert_rules表
            create_rules_table = """
            CREATE TABLE IF NOT EXISTS alert_rules (
                rule_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT true,
                cooldown_period INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
            db_conn.execute_query(create_rules_table)
            
            self.logger.info("警报规则数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"初始化警报规则数据库表失败: {e}")
    
    def _load_rules(self) -> None:
        """
        从数据库加载规则
        注意：由于规则包含代码逻辑（条件函数），无法完全从数据库恢复
        这里只是记录日志，表示已从数据库获取规则信息
        """
        try:
            query = "SELECT rule_id, name, enabled, cooldown_period FROM alert_rules"
            result = db_conn.execute_query(query)
            
            for row in result:
                self.logger.info(f"从数据库加载规则信息: {row['name']} (ID: {row['rule_id']}, 启用: {row['enabled']})")
                
                # 实际的规则对象需要通过代码创建，这里只记录信息
        except Exception as e:
            self.logger.error(f"从数据库加载规则信息失败: {e}")
    
    def add_rule(self, rule: AlertRule) -> None:
        """
        添加规则
        
        参数:
            rule: 警报规则对象
        """
        self.rules[rule.rule_id] = rule
        
        # 保存规则信息到数据库
        try:
            query = """
            INSERT INTO alert_rules (rule_id, name, enabled, cooldown_period)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (rule_id) DO UPDATE
            SET name = EXCLUDED.name,
                enabled = EXCLUDED.enabled,
                cooldown_period = EXCLUDED.cooldown_period,
                updated_at = NOW()
            """
            
            params = (rule.rule_id, rule.name, rule.enabled, rule.cooldown_period)
            db_conn.execute_query(query, params)
            
            self.logger.info(f"已添加警报规则并保存到数据库: {rule.name} (ID: {rule.rule_id})")
        except Exception as e:
            self.logger.error(f"保存警报规则到数据库失败: {e}")
            # 即使保存失败，也要将规则添加到内存中以确保功能正常
            self.logger.info(f"已添加警报规则到内存: {rule.name} (ID: {rule.rule_id})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        移除规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            是否成功移除
        """
        if rule_id in self.rules:
            # 从数据库删除规则
            try:
                query = "DELETE FROM alert_rules WHERE rule_id = %s"
                db_conn.execute_query(query, (rule_id,))
                self.logger.info(f"已从数据库删除警报规则: {rule_id}")
            except Exception as e:
                self.logger.error(f"从数据库删除警报规则失败: {e}")
            
            # 从内存删除规则
            del self.rules[rule_id]
            self.logger.info(f"已移除警报规则: {rule_id}")
            return True
        else:
            self.logger.warning(f"移除警报规则失败: 规则ID {rule_id} 不存在")
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """
        启用规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            是否成功启用
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            
            # 更新数据库
            try:
                query = """
                UPDATE alert_rules
                SET enabled = true,
                    updated_at = NOW()
                WHERE rule_id = %s
                """
                db_conn.execute_query(query, (rule_id,))
                self.logger.info(f"已更新数据库中的规则启用状态: {rule_id}")
            except Exception as e:
                self.logger.error(f"更新规则启用状态失败: {e}")
            
            self.logger.info(f"已启用警报规则: {rule_id}")
            return True
        else:
            self.logger.warning(f"启用警报规则失败: 规则ID {rule_id} 不存在")
            return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """
        禁用规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            是否成功禁用
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            
            # 更新数据库
            try:
                query = """
                UPDATE alert_rules
                SET enabled = false,
                    updated_at = NOW()
                WHERE rule_id = %s
                """
                db_conn.execute_query(query, (rule_id,))
                self.logger.info(f"已更新数据库中的规则禁用状态: {rule_id}")
            except Exception as e:
                self.logger.error(f"更新规则禁用状态失败: {e}")
            
            self.logger.info(f"已禁用警报规则: {rule_id}")
            return True
        else:
            self.logger.warning(f"禁用警报规则失败: 规则ID {rule_id} 不存在")
            return False
    
    def check_rules(self, data: Dict) -> List[Dict]:
        """
        检查所有规则
        
        参数:
            data: 要检查的数据
            
        返回:
            触发的警报列表
        """
        triggered_alerts = []
        
        for rule_id, rule in self.rules.items():
            triggered, message, alert_data = rule.check(data)
            if triggered:
                alert = self.alert_system.add_alert(
                    alert_type=rule.alert_type,
                    message=message,
                    level=rule.level,
                    data=alert_data,
                    source=f"rule:{rule_id}"
                )
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def get_rules(self) -> Dict[str, AlertRule]:
        """
        获取所有规则
        
        返回:
            规则字典，键为规则ID
        """
        return self.rules

# 创建全局警报系统实例
alert_system = AlertSystem()