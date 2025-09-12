<<<<<<< HEAD
# 实盘监控模块初始化文件
# 用于实时监控交易执行和市场数据
# 监控模块
# 负责市场监控、交易监控、风险控制等功能

# 导入子模块
from .alert_system import AlertSystem
from .market_monitor import MarketMonitor
from .risk_controller import RiskController
from .trade_monitor import TradeMonitor
from .position_manager import PositionManager
from .execution_engine import ExecutionEngine
from .trade_history_manager import TradeHistoryManager
from .risk_manager import RiskManager
from .notification_manager import NotificationManager
from .notification_service import NotificationService

# 创建类实例
alert_system = AlertSystem()
market_monitor = MarketMonitor()
risk_controller = RiskController()
trade_monitor = TradeMonitor()
position_manager = PositionManager()
execution_engine = ExecutionEngine()
trade_history_manager = TradeHistoryManager()
risk_manager = RiskManager()
notification_manager = NotificationManager()
notification_service = NotificationService()

__all__ = [
    'alert_system', 
    'market_monitor', 
    'risk_controller', 
    'trade_monitor',
    'position_manager',
    'execution_engine',
    'trade_history_manager',
    'risk_manager',
    'notification_manager',
    'notification_service'
]
