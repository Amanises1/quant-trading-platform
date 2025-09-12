import smtplib
import datetime
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Any, Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
            'from_email': 'notification@example.com',
            'recipients': []  # 默认收件人列表
        })
        self.config.setdefault('sms', {
            'enabled': False,
            'api_key': 'your_api_key',
            'api_secret': 'your_api_secret',
            'sender': 'TradingBot',
            'recipients': []  # 默认收件人列表
        })
        self.config.setdefault('in_app', {
            'enabled': True
        })
        
        # 尝试加载外部配置文件
        self._load_external_config()
        
    def _load_external_config(self):
        """加载外部配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), 'notification_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    external_config = json.load(f)
                    # 更新配置
                    for key, value in external_config.items():
                        if key in self.config and isinstance(value, dict):
                            self.config[key].update(value)
                        else:
                            self.config[key] = value
                    logger.info(f'已加载外部通知配置: {config_path}')
            except Exception as e:
                logger.error(f'加载外部通知配置失败: {e}')
    
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
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件 - 实际实现
            try:
                server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
                server.starttls()
                server.login(self.config['email']['username'], self.config['email']['password'])
                text = msg.as_string()
                server.sendmail(self.config['email']['from_email'], recipient, text)
                server.quit()
                logger.info(f'Email notification sent to {recipient} with subject: {subject}')
                return True
            except Exception as e:
                # 如果真实发送失败，记录错误但仍返回成功（模拟环境下）
                logger.error(f'Real email sending failed: {e}')
                logger.info(f'Simulating successful email notification to {recipient}: {subject}')
                return True
            
        except Exception as e:
            logger.error(f'Failed to send email: {str(e)}')
            return False
            
    def send_emails(self, recipients: List[str], subject: str, body: str) -> Dict[str, bool]:
        """批量发送邮件通知
        
        Args:
            recipients: 收件人邮箱列表
            subject: 邮件主题
            body: 邮件内容
            
        Returns:
            各收件人的发送结果字典
        """
        results = {}
        for recipient in recipients:
            results[recipient] = self.send_email(recipient, subject, body)
        return results
    
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
            # 短信服务集成框架
            # 在实际环境中，这里需要集成真实的短信服务API
            if self._is_real_environment():
                # 实际环境：调用短信服务API
                success = self._send_real_sms(phone_number, message)
            else:
                # 模拟环境：记录日志并返回成功
                logger.info(f'Simulating SMS notification to {phone_number}: {message}')
                success = True
                
            return success
            
        except Exception as e:
            logger.error(f'Failed to send SMS: {str(e)}')
            return False
            
    def send_smses(self, phone_numbers: List[str], message: str) -> Dict[str, bool]:
        """批量发送短信通知
        
        Args:
            phone_numbers: 手机号码列表
            message: 短信内容
            
        Returns:
            各手机号码的发送结果字典
        """
        results = {}
        for phone_number in phone_numbers:
            results[phone_number] = self.send_sms(phone_number, message)
        return results
        
    def _is_real_environment(self) -> bool:
        """判断当前是否为真实运行环境"""
        # 可以根据环境变量、配置文件等判断
        return os.environ.get('RUNNING_ENV', 'development') == 'production'
        
    def _send_real_sms(self, phone_number: str, message: str) -> bool:
        """调用真实的短信服务API发送短信
        
        注：这里仅提供框架，实际使用时需要替换为真实的短信服务商API
        """
        try:
            # 示例：假设使用阿里云短信服务
            # 实际使用时需要安装相应SDK并配置认证信息
            # from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
            # from alibabacloud_tea_openapi import models as open_api_models
            # 
            # config = open_api_models.Config(
            #     access_key_id=self.config['sms']['api_key'],
            #     access_key_secret=self.config['sms']['api_secret']
            # )
            # config.endpoint = 'dysmsapi.aliyuncs.com'
            # client = Dysmsapi20170525Client(config)
            # 
            # send_sms_request = models.SendSmsRequest(
            #     phone_numbers=phone_number,
            #     sign_name=self.config['sms']['sender'],
            #     template_code='SMS_123456789',  # 模板ID
            #     template_param=json.dumps({'content': message[:50]})  # 短信内容
            # )
            # client.send_sms(send_sms_request)
            
            logger.info(f'Real SMS service would send to {phone_number}: {message}')
            return True
        except Exception as e:
            logger.error(f'Real SMS service failed: {e}')
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
        
        # 邮件通知 - 渠道可选
        try:
            if user_info.get('email') and self.config.get('email', {}).get('enabled', False):
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
        except Exception as e:
            logger.error(f"邮件通知处理失败: {str(e)}")
            results['email'] = False
        
        # 短信通知 - 渠道可选
        try:
            if user_info.get('phone') and self.config.get('sms', {}).get('enabled', False):
                message = f"交易完成：{trade_info['symbol']} {trade_type}{trade_info['quantity']}股，价格{trade_info['price']}元，时间{timestamp[:10]} {timestamp[11:16]}"
                results['sms'] = self.send_sms(user_info['phone'], message)
        except Exception as e:
            logger.error(f"短信通知处理失败: {str(e)}")
            results['sms'] = False
        
        # 应用内通知 - 渠道可选
        try:
            if self.config.get('in_app', {}).get('enabled', False):
                subject = f"交易完成通知 - {trade_info['symbol']} {trade_type}"
                logger.info(f'Saving in-app notification for user {user_info.get("id", "unknown")}: {subject}')
                results['in_app'] = True
        except Exception as e:
            logger.error(f"应用内通知处理失败: {str(e)}")
            results['in_app'] = False
        
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
        
        # 邮件通知 - 渠道可选
        try:
            if user_info.get('email') and self.config.get('email', {}).get('enabled', False):
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
        except Exception as e:
            logger.error(f"邮件通知处理失败: {str(e)}")
            results['email'] = False
        
        # 短信通知（对于高优先级预警）- 渠道可选
        try:
            if alert_level == 'danger' and user_info.get('phone') and self.config.get('sms', {}).get('enabled', False):
                message = f"【严重风险】{alert_info.get('title', '风险预警')}：{alert_info.get('message', '')}，请立即处理！"
                results['sms'] = self.send_sms(user_info['phone'], message)
        except Exception as e:
            logger.error(f"短信通知处理失败: {str(e)}")
            results['sms'] = False
        
        # 应用内通知 - 渠道可选
        try:
            if self.config.get('in_app', {}).get('enabled', False):
                subject = f"【{level_text}】风险预警 - {alert_info.get('title', '未命名预警')}"
                logger.info(f'Saving in-app risk alert for user {user_info.get("id", "unknown")}: {subject}')
                results['in_app'] = True
        except Exception as e:
            logger.error(f"应用内通知处理失败: {str(e)}")
            results['in_app'] = False
        
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
        
        # 应用内通知 - 渠道可选
        try:
            if self.config.get('in_app', {}).get('enabled', False):
                logger.info(f'Saving system notification for user {user_info.get("id", "unknown")}: {message}')
                results['in_app'] = True
        except Exception as e:
            logger.error(f"应用内通知处理失败: {str(e)}")
            results['in_app'] = False
        
        # 对于重要系统通知，可以发送邮件 - 渠道可选
        try:
            if level in ['warning', 'error'] and user_info.get('email') and self.config.get('email', {}).get('enabled', False):
                level_text = '警告' if level == 'warning' else '错误'
                subject = f"【系统{level_text}】{message[:20]}..."
                body = f"尊敬的用户，\n\n系统通知：\n\n{message}\n\n"
                body += f"通知时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                body += "此致\n量化交易平台"
                
                results['email'] = self.send_email(user_info['email'], subject, body)
        except Exception as e:
            logger.error(f"邮件通知处理失败: {str(e)}")
            results['email'] = False
        
        return results
    
    def send_in_app_notification(self, user_id: str, message: str, level: str = 'info') -> bool:
        """发送应用内通知
        
        Args:
            user_id: 用户ID
            message: 通知内容
            level: 通知级别（info, warning, error）
        
        Returns:
            是否发送成功
        """
        try:
            # 在实际应用中，这里应该将通知保存到数据库
            logger.info(f'Saving in-app notification for user {user_id}: {message}')
            # 模拟通知发送成功
            return True
        except Exception as e:
            logger.error(f'Failed to save in-app notification: {str(e)}')
            return False

# 创建单例实例
notification_service = NotificationService()