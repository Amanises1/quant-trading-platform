# 警报系统模块

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
        self.config.setdefault('alert_history_file', 'alert_history.json')  # 警报历史文件
        self.config.setdefault('max_alerts_in_memory', 1000)  # 内存中保存的最大警报数量
        
        # 警报历史
        self.alerts = []
        
        # 加载历史警报
        self._load_alert_history()
    
    def _load_alert_history(self) -> None:
        """
        从文件加载历史警报
        """
        history_file = self.config['alert_history_file']
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.alerts = json.load(f)
                self.logger.info(f"已加载{len(self.alerts)}条历史警报")
            except Exception as e:
                self.logger.error(f"加载历史警报出错: {e}")
    
    def _save_alert_history(self) -> None:
        """
        保存警报历史到文件
        """
        history_file = self.config['alert_history_file']
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, default=str)
            self.logger.info(f"已保存{len(self.alerts)}条警报到历史文件")
        except Exception as e:
            self.logger.error(f"保存警报历史出错: {e}")
    
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
        alert = {
            'id': len(self.alerts) + 1,
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'level': level,
            'data': data or {},
            'source': source or 'system',
            'acknowledged': False,
            'acknowledged_time': None,
            'acknowledged_by': None
        }
        
        # 添加到警报列表
        self.alerts.append(alert)
        
        # 限制内存中的警报数量
        if len(self.alerts) > self.config['max_alerts_in_memory']:
            self.alerts = self.alerts[-self.config['max_alerts_in_memory']:]
        
        # 发送通知
        self._send_notification(alert)
        
        # 保存警报历史
        self._save_alert_history()
        
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
        filtered_alerts = self.alerts
        
        # 按时间过滤
        if start_time:
            filtered_alerts = [alert for alert in filtered_alerts 
                              if isinstance(alert['timestamp'], datetime) and alert['timestamp'] >= start_time]
        
        if end_time:
            filtered_alerts = [alert for alert in filtered_alerts 
                              if isinstance(alert['timestamp'], datetime) and alert['timestamp'] <= end_time]
        
        # 按类型过滤
        if alert_types:
            filtered_alerts = [alert for alert in filtered_alerts if alert['type'] in alert_types]
        
        # 按级别过滤
        if levels:
            filtered_alerts = [alert for alert in filtered_alerts if alert['level'].lower() in [l.lower() for l in levels]]
        
        # 按确认状态过滤
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
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_time'] = datetime.now()
                alert['acknowledged_by'] = acknowledged_by
                
                # 保存警报历史
                self._save_alert_history()
                
                self.logger.info(f"警报 {alert_id} 已被 {acknowledged_by} 确认")
                return True
        
        self.logger.warning(f"确认警报失败: 警报ID {alert_id} 不存在")
        return False
    
    def clear_alerts(self, older_than: Optional[datetime] = None) -> int:
        """
        清除警报
        
        参数:
            older_than: 只清除该时间之前的警报，如果为None则清除所有警报
            
        返回:
            清除的警报数量
        """
        if older_than is None:
            count = len(self.alerts)
            self.alerts = []
        else:
            original_count = len(self.alerts)
            self.alerts = [alert for alert in self.alerts 
                          if not isinstance(alert['timestamp'], datetime) or alert['timestamp'] >= older_than]
            count = original_count - len(self.alerts)
        
        # 保存警报历史
        self._save_alert_history()
        
        self.logger.info(f"已清除{count}条警报")
        return count
    
    def get_alert_summary(self) -> Dict:
        """
        获取警报概览
        
        返回:
            警报概览字典
        """
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
    
    def add_rule(self, rule: AlertRule) -> None:
        """
        添加规则
        
        参数:
            rule: 警报规则对象
        """
        self.rules[rule.rule_id] = rule
        self.logger.info(f"已添加警报规则: {rule.name} (ID: {rule.rule_id})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        移除规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            是否成功移除
        """
        if rule_id in self.rules:
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