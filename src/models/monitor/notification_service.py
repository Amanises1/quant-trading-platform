import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Any, Optional

# 配置日志\logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务类，负责发送各种通知"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化通知服务
        
        Args:
            config: 通知服务配置，包含邮件服务器等信息
        """
        self.config = config or {}
        # 设置默认配置
        self.config.setdefault('email', {
            'enabled': True,
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'notification@example.com',
            'password': 'password',
            'from_email': 'notification@example.com'
        })
        self.config.setdefault('sms', {
            'enabled': False,
            # SMS API配置可以在这里添加
        })
        self.config.setdefault('in_app', {
            'enabled': True
        })
    
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """发送邮件通知
        
        Args:
            recipient: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            
        Returns:
            是否发送成功
        """
        if not self.config['email'].get('enabled', False):
            logger.info('Email notification is disabled')
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from_email']
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(body, 'plain'))
            
            # 注意：在实际应用中，这里应该连接到真实的SMTP服务器
            # 这里只是模拟发送邮件的过程
            logger.info(f'Simulating email sending to {recipient} with subject: {subject}')
            logger.info(f'Email body: {body}')
            
            # 以下代码在实际应用中应该取消注释，并配置正确的SMTP服务器
            """
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['username'], self.config['email']['password'])
            text = msg.as_string()
            server.sendmail(self.config['email']['from_email'], recipient, text)
            server.quit()
            """
            
            return True
        except Exception as e:
            logger.error(f'Failed to send email: {str(e)}')
            return False
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """发送短信通知
        
        Args:
            phone_number: 手机号码
            message: 短信内容
            
        Returns:
            是否发送成功
        """
        if not self.config['sms'].get('enabled', False):
            logger.info('SMS notification is disabled')
            return False
        
        try:
            # 在实际应用中，这里应该调用短信API发送短信
            logger.info(f'Simulating SMS sending to {phone_number}: {message}')
            return True
        except Exception as e:
            logger.error(f'Failed to send SMS: {str(e)}')
            return False
    
    def send_trade_notification(self, user_info: Dict[str, Any], trade_info: Dict[str, Any]) -> Dict[str, bool]:
        """发送交易完成通知
        
        Args:
            user_info: 用户信息，包含联系方式等
            trade_info: 交易信息
            
        Returns:
            各通知渠道的发送结果
        """
        results = {}
        
        # 格式化交易信息
        timestamp = datetime.datetime.fromtimestamp(trade_info['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        trade_type = '买入' if trade_info['type'] == 'buy' else '卖出'
        
        # 邮件通知
        if user_info.get('email') and self.config['email'].get('enabled', False):
            subject = f"交易完成通知 - {trade_info['symbol']} {trade_type}"
            body = f"尊敬的用户，\n\n您的交易已完成：\n\n"
            body += f"交易标的：{trade_info['name']} ({trade_info['symbol']})\n"
            body += f"交易类型：{trade_type}\n"
            body += f"交易数量：{trade_info['quantity']}\n"
            body += f"交易价格：{trade_info['price']}\n"
            body += f"交易金额：{trade_info['amount']}\n"
            body += f"交易时间：{timestamp}\n\n"
            body += f"交易状态：{trade_info['status']}\n\n"
            body += "如有疑问，请联系客服。\n\n"
            body += "此致\n量化交易平台"
            
            results['email'] = self.send_email(user_info['email'], subject, body)
        
        # 短信通知
        if user_info.get('phone') and self.config['sms'].get('enabled', False):
            message = f"交易完成：{trade_info['symbol']} {trade_type}{trade_info['quantity']}股，价格{trade_info['price']}元，时间{timestamp[:10]} {timestamp[11:16]}"
            results['sms'] = self.send_sms(user_info['phone'], message)
        
        # 应用内通知（在实际应用中，这里应该存储通知到数据库）
        if self.config['in_app'].get('enabled', False):
            logger.info(f'Saving in-app notification for user {user_info.get("id", "unknown")}: {subject}')
            results['in_app'] = True
        
        return results
    
    def send_risk_alert(self, user_info: Dict[str, Any], alert_info: Dict[str, Any]) -> Dict[str, bool]:
        """发送风险预警通知
        
        Args:
            user_info: 用户信息
            alert_info: 风险预警信息
            
        Returns:
            各通知渠道的发送结果
        """
        results = {}
        
        # 格式化预警信息
        alert_level = alert_info.get('level', 'warning')
        level_text = '严重' if alert_level == 'danger' else '警告' if alert_level == 'warning' else '提示'
        
        # 邮件通知
        if user_info.get('email') and self.config['email'].get('enabled', False):
            subject = f"【{level_text}】风险预警 - {alert_info.get('title', '未命名预警')}"
            body = f"尊敬的用户，\n\n您的账户存在风险预警：\n\n"
            body += f"预警类型：{alert_info.get('title', '未命名预警')}\n"
            body += f"预警级别：{level_text}\n"
            body += f"预警内容：{alert_info.get('message', '')}\n"
            if 'account_id' in alert_info:
                body += f"相关账户：{alert_info['account_id']}\n"
            if 'position' in alert_info:
                body += f"相关持仓：{alert_info['position'].get('symbol', '')} {alert_info['position'].get('name', '')}\n"
            body += f"预警时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            body += "请及时处理，以避免潜在损失。\n\n"
            body += "此致\n量化交易平台"
            
            results['email'] = self.send_email(user_info['email'], subject, body)
        
        # 短信通知（对于高优先级预警）
        if alert_level == 'danger' and user_info.get('phone') and self.config['sms'].get('enabled', False):
            message = f"【严重风险】{alert_info.get('title', '风险预警')}：{alert_info.get('message', '')}，请立即处理！"
            results['sms'] = self.send_sms(user_info['phone'], message)
        
        # 应用内通知
        if self.config['in_app'].get('enabled', False):
            logger.info(f'Saving in-app risk alert for user {user_info.get("id", "unknown")}: {subject}')
            results['in_app'] = True
        
        return results
    
    def send_system_notification(self, user_info: Dict[str, Any], message: str, level: str = 'info') -> Dict[str, bool]:
        """发送系统通知
        
        Args:
            user_info: 用户信息
            message: 通知内容
            level: 通知级别（info, warning, error）
            
        Returns:
            各通知渠道的发送结果
        """
        results = {}
        
        # 应用内通知
        if self.config['in_app'].get('enabled', False):
            logger.info(f'Saving system notification for user {user_info.get("id", "unknown")}: {message}')
            results['in_app'] = True
        
        # 对于重要系统通知，可以发送邮件
        if level in ['warning', 'error'] and user_info.get('email') and self.config['email'].get('enabled', False):
            level_text = '警告' if level == 'warning' else '错误'
            subject = f"【系统{level_text}】{message[:20]}..."
            body = f"尊敬的用户，\n\n系统通知：\n\n{message}\n\n"
            body += f"通知时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            body += "此致\n量化交易平台"
            
            results['email'] = self.send_email(user_info['email'], subject, body)
        
        return results

# 创建单例实例
notification_service = NotificationService()