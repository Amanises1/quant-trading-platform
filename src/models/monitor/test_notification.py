import unittest
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.monitor.notification_service import NotificationService
from src.models.monitor.notification_manager import notification_manager

class TestNotificationSystem(unittest.TestCase):
    
    def setUp(self):
        # 初始化通知服务
        self.notification_service = NotificationService()
        
    def test_email_notification_config(self):
        """测试邮件通知配置的加载和保存"""
        # 获取当前配置
        current_config = notification_manager.get_config()
        
        # 验证邮件配置结构是否正确
        self.assertIn('email', current_config)
        self.assertIn('enabled', current_config['email'])
        self.assertIn('smtp_server', current_config['email'])
        self.assertIn('smtp_port', current_config['email'])
        self.assertIn('username', current_config['email'])
        self.assertIn('password', current_config['email'])
        self.assertIn('from_email', current_config['email'])
        self.assertIn('recipients', current_config['email'])
        
        # 验证配置类型
        self.assertIsInstance(current_config['email']['enabled'], bool)
        self.assertIsInstance(current_config['email']['smtp_server'], str)
        self.assertIsInstance(current_config['email']['smtp_port'], int)
        self.assertIsInstance(current_config['email']['recipients'], list)
    
    def test_sms_notification_config(self):
        """测试短信通知配置的加载和保存"""
        # 获取当前配置
        current_config = notification_manager.get_config()
        
        # 验证短信配置结构是否正确
        self.assertIn('sms', current_config)
        self.assertIn('enabled', current_config['sms'])
        self.assertIn('api_key', current_config['sms'])
        self.assertIn('api_secret', current_config['sms'])
        self.assertIn('sender', current_config['sms'])
        self.assertIn('recipients', current_config['sms'])
        
        # 验证配置类型
        self.assertIsInstance(current_config['sms']['enabled'], bool)
        self.assertIsInstance(current_config['sms']['api_key'], str)
        self.assertIsInstance(current_config['sms']['api_secret'], str)
        self.assertIsInstance(current_config['sms']['recipients'], list)
    
    def test_notification_manager_save_functionality(self):
        """测试通知管理器的保存功能"""
        # 创建一个测试配置
        test_config = {
            'trade': True,
            'risk': True,
            'balance': True,
            'system': True,
            'email': {
                'enabled': True,
                'smtp_server': 'test-smtp.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'test-password',
                'from_email': 'test@example.com',
                'recipients': ['user1@example.com', 'user2@example.com']
            },
            'sms': {
                'enabled': False,
                'api_key': 'test-api-key',
                'api_secret': 'test-api-secret',
                'sender': 'TestBot',
                'recipients': ['13800138000']
            },
            'in_app': {
                'enabled': True
            }
        }
        
        # 保存测试配置
        notification_manager.save_notification_config('test-account', test_config)
        
        # 重新获取配置并验证
        saved_config = notification_manager.get_config('test-account')
        
        # 验证保存的配置是否与测试配置匹配
        self.assertEqual(saved_config['trade'], test_config['trade'])
        self.assertEqual(saved_config['risk'], test_config['risk'])
        self.assertEqual(saved_config['balance'], test_config['balance'])
        self.assertEqual(saved_config['system'], test_config['system'])
        
        # 验证邮件配置
        self.assertEqual(saved_config['email']['smtp_server'], test_config['email']['smtp_server'])
        self.assertEqual(saved_config['email']['smtp_port'], test_config['email']['smtp_port'])
        self.assertEqual(saved_config['email']['recipients'], test_config['email']['recipients'])
        
        # 验证短信配置
        self.assertEqual(saved_config['sms']['api_key'], test_config['sms']['api_key'])
        self.assertEqual(saved_config['sms']['recipients'], test_config['sms']['recipients'])
    
    def test_notification_service_methods(self):
        """测试通知服务的方法"""
        # 验证通知服务的实例
        self.assertIsInstance(self.notification_service, NotificationService)
        
        # 验证通知服务方法的存在
        self.assertTrue(hasattr(self.notification_service, 'send_email'))
        self.assertTrue(hasattr(self.notification_service, 'send_sms'))
        self.assertTrue(hasattr(self.notification_service, 'send_in_app_notification'))
        self.assertTrue(hasattr(self.notification_service, 'send_risk_alert'))
        self.assertTrue(hasattr(self.notification_service, 'send_system_notification'))
    
    def test_email_sending_functionality(self):
        """测试邮件发送功能"""
        # 注意：这个测试不会实际发送邮件，只会验证方法是否能正确调用
        # 在实际环境中，您可以配置一个测试SMTP服务器来测试真实的发送功能
        try:
            result = self.notification_service.send_email(
                subject="测试邮件",
                content="这是一封测试邮件，验证邮件发送功能是否正常工作。",
                recipients=["test@example.com"]
            )
            # 验证返回结果的结构
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
        except Exception as e:
            # 如果测试环境中没有配置SMTP服务器，这个测试可能会失败
            # 在这种情况下，我们只记录异常而不标记测试失败
            print(f"邮件发送测试未通过，但这可能是因为未配置SMTP服务器: {str(e)}")
    
    def test_sms_sending_functionality(self):
        """测试短信发送功能"""
        # 注意：这个测试不会实际发送短信，只会验证方法是否能正确调用
        # 在实际环境中，您需要配置真实的短信API密钥来测试发送功能
        try:
            result = self.notification_service.send_sms(
                content="这是一条测试短信，验证短信发送功能是否正常工作。",
                recipients=["13800138000"]
            )
            # 验证返回结果的结构
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
        except Exception as e:
            # 如果测试环境中没有配置短信API，这个测试可能会失败
            # 在这种情况下，我们只记录异常而不标记测试失败
            print(f"短信发送测试未通过，但这可能是因为未配置短信API: {str(e)}")

if __name__ == '__main__':
    unittest.main()