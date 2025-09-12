# 回测系统模块初始化文件
# 用于策略回测

"""
回测系统模块

该模块提供完整的量化交易策略回测功能，包括回测引擎、性能指标计算、
风险管理、策略评估和交易执行等组件。
"""

# 导入回测引擎
from .backtest_engine import BacktestEngine

# 导入性能指标计算模块
from .performance_metrics import PerformanceMetrics

# 导入风险管理模块
from .risk_manager import RiskManager, PositionSizer

# 导入策略评估模块
from .strategy_evaluator import StrategyEvaluator

# 导入交易执行模块
from .trade_executor import Order, Trade, Position, TradeExecutor

# 导入策略基础类和演示类
from .strategy_base import Strategy, BaseStrategy
from .strategy_demo import StrategyDemo

# 导入策略实现
from .strategies.sma_strategy import SimpleMovingAverageStrategy
from .strategies.rsi_strategy import RsiStrategy
from .strategies.mean_reversion_strategy import MeanReversionStrategy
from .strategies.macd_strategy import MacdStrategy

__all__ = [
    'BacktestEngine',
    'PerformanceMetrics',
    'RiskManager',
    'PositionSizer',
    'StrategyEvaluator',
    'Order',
    'Trade',
    'Position',
    'TradeExecutor',
    'Strategy',
    'BaseStrategy',
    'StrategyDemo',
    'SimpleMovingAverageStrategy',
    'RsiStrategy',
    'MeanReversionStrategy',
    'MacdStrategy'
]
