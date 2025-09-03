# 风险管理模块

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Callable
import logging

class RiskManager:
    """
    风险管理类，用于管理交易风险
    支持多种风险控制策略和仓位管理方法
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化风险管理器
        
        参数:
            config: 配置信息，包含风险管理参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('max_position_size', 1.0)  # 最大仓位比例
        self.config.setdefault('max_drawdown', 0.1)      # 最大回撤限制
        self.config.setdefault('stop_loss_pct', 0.02)     # 止损百分比
        self.config.setdefault('take_profit_pct', 0.05)   # 止盈百分比
        self.config.setdefault('max_trades_per_day', 5)   # 每日最大交易次数
        self.config.setdefault('position_sizing_method', 'fixed')  # 仓位管理方法
    
    def check_max_drawdown(self, equity_curve: pd.Series) -> bool:
        """
        检查是否超过最大回撤限制
        
        参数:
            equity_curve: 权益曲线
            
        返回:
            是否允许交易
        """
        if len(equity_curve) < 2:
            return True
        
        # 计算当前回撤
        peak = equity_curve.max()
        current = equity_curve.iloc[-1]
        drawdown = (peak - current) / peak
        
        # 检查是否超过最大回撤限制
        max_drawdown = self.config['max_drawdown']
        if drawdown > max_drawdown:
            self.logger.warning(f"当前回撤 {drawdown:.2%} 超过最大回撤限制 {max_drawdown:.2%}，暂停交易")
            return False
        
        return True
    
    def calculate_position_size(self, equity: float, price: float, volatility: Optional[float] = None) -> float:
        """
        计算仓位大小
        
        参数:
            equity: 当前权益
            price: 当前价格
            volatility: 波动率，可选
            
        返回:
            仓位大小（资金比例）
        """
        method = self.config['position_sizing_method']
        max_position_size = self.config['max_position_size']
        
        if method == 'fixed':
            # 固定比例仓位
            return max_position_size
        
        elif method == 'kelly':
            # 凯利公式仓位管理（需要胜率和盈亏比）
            win_rate = self.config.get('win_rate', 0.5)
            profit_loss_ratio = self.config.get('profit_loss_ratio', 1.0)
            
            # 凯利公式：f = (p*b - q) / b，其中p是胜率，q是败率，b是盈亏比
            kelly = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
            
            # 通常使用半凯利或分数凯利以降低风险
            kelly_fraction = self.config.get('kelly_fraction', 0.5)
            position_size = max(0, min(kelly * kelly_fraction, max_position_size))
            
            return position_size
        
        elif method == 'volatility':
            # 基于波动率的仓位管理
            if volatility is None or volatility == 0:
                return max_position_size
            
            # 目标波动率
            target_volatility = self.config.get('target_volatility', 0.01)  # 1%
            
            # 根据波动率调整仓位大小
            position_size = target_volatility / volatility
            
            # 限制在最大仓位范围内
            position_size = max(0, min(position_size, max_position_size))
            
            return position_size
        
        elif method == 'percent_of_equity':
            # 权益百分比仓位管理
            percent = self.config.get('equity_percent', 0.02)  # 默认2%
            return min(percent, max_position_size)
        
        else:
            # 默认使用固定比例
            self.logger.warning(f"未知的仓位管理方法: {method}，使用固定比例")
            return max_position_size
    
    def apply_stop_loss(self, current_price: float, entry_price: float, position: int) -> bool:
        """
        应用止损策略
        
        参数:
            current_price: 当前价格
            entry_price: 入场价格
            position: 持仓方向（1为多头，-1为空头）
            
        返回:
            是否触发止损
        """
        if position == 0:
            return False
        
        stop_loss_pct = self.config['stop_loss_pct']
        
        if position == 1:  # 多头
            loss_pct = (entry_price - current_price) / entry_price
            if loss_pct > stop_loss_pct:
                self.logger.info(f"触发多头止损: 入场价 {entry_price:.4f}, 当前价 {current_price:.4f}, 亏损 {loss_pct:.2%}")
                return True
        
        elif position == -1:  # 空头
            loss_pct = (current_price - entry_price) / entry_price
            if loss_pct > stop_loss_pct:
                self.logger.info(f"触发空头止损: 入场价 {entry_price:.4f}, 当前价 {current_price:.4f}, 亏损 {loss_pct:.2%}")
                return True
        
        return False
    
    def apply_take_profit(self, current_price: float, entry_price: float, position: int) -> bool:
        """
        应用止盈策略
        
        参数:
            current_price: 当前价格
            entry_price: 入场价格
            position: 持仓方向（1为多头，-1为空头）
            
        返回:
            是否触发止盈
        """
        if position == 0:
            return False
        
        take_profit_pct = self.config['take_profit_pct']
        
        if position == 1:  # 多头
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct > take_profit_pct:
                self.logger.info(f"触发多头止盈: 入场价 {entry_price:.4f}, 当前价 {current_price:.4f}, 盈利 {profit_pct:.2%}")
                return True
        
        elif position == -1:  # 空头
            profit_pct = (entry_price - current_price) / entry_price
            if profit_pct > take_profit_pct:
                self.logger.info(f"触发空头止盈: 入场价 {entry_price:.4f}, 当前价 {current_price:.4f}, 盈利 {profit_pct:.2%}")
                return True
        
        return False
    
    def apply_trailing_stop(self, current_price: float, highest_price: float, lowest_price: float, position: int) -> bool:
        """
        应用追踪止损策略
        
        参数:
            current_price: 当前价格
            highest_price: 持仓期间最高价
            lowest_price: 持仓期间最低价
            position: 持仓方向（1为多头，-1为空头）
            
        返回:
            是否触发追踪止损
        """
        if position == 0:
            return False
        
        trailing_stop_pct = self.config.get('trailing_stop_pct', 0.03)  # 默认3%
        
        if position == 1:  # 多头
            # 从最高点回落超过追踪止损比例
            if highest_price > 0 and (highest_price - current_price) / highest_price > trailing_stop_pct:
                self.logger.info(f"触发多头追踪止损: 最高价 {highest_price:.4f}, 当前价 {current_price:.4f}, 回落 {(highest_price - current_price) / highest_price:.2%}")
                return True
        
        elif position == -1:  # 空头
            # 从最低点反弹超过追踪止损比例
            if lowest_price > 0 and (current_price - lowest_price) / lowest_price > trailing_stop_pct:
                self.logger.info(f"触发空头追踪止损: 最低价 {lowest_price:.4f}, 当前价 {current_price:.4f}, 反弹 {(current_price - lowest_price) / lowest_price:.2%}")
                return True
        
        return False
    
    def check_max_trades_per_day(self, trade_dates: List[pd.Timestamp], current_date: pd.Timestamp) -> bool:
        """
        检查是否超过每日最大交易次数
        
        参数:
            trade_dates: 交易日期列表
            current_date: 当前日期
            
        返回:
            是否允许交易
        """
        max_trades = self.config['max_trades_per_day']
        
        # 计算当日交易次数
        today_trades = sum(1 for date in trade_dates if date.date() == current_date.date())
        
        if today_trades >= max_trades:
            self.logger.warning(f"当日交易次数 {today_trades} 已达到最大限制 {max_trades}，暂停交易")
            return False
        
        return True
    
    def check_time_filter(self, current_time: pd.Timestamp) -> bool:
        """
        检查时间过滤器
        
        参数:
            current_time: 当前时间
            
        返回:
            是否允许交易
        """
        # 检查是否在交易时间内
        if 'trading_hours' in self.config:
            trading_hours = self.config['trading_hours']
            
            # 检查是否在交易日
            if 'trading_days' in trading_hours:
                trading_days = trading_hours['trading_days']
                weekday = current_time.weekday()
                if weekday not in trading_days:
                    return False
            
            # 检查是否在交易时段
            if 'start_time' in trading_hours and 'end_time' in trading_hours:
                start_time = trading_hours['start_time']  # 格式: 'HH:MM'
                end_time = trading_hours['end_time']      # 格式: 'HH:MM'
                
                current_time_str = current_time.strftime('%H:%M')
                if current_time_str < start_time or current_time_str > end_time:
                    return False
        
        return True
    
    def apply_risk_management(self, signal: int, current_price: float, entry_price: float, 
                             highest_price: float, lowest_price: float, position: int, 
                             equity_curve: pd.Series, trade_dates: List[pd.Timestamp], 
                             current_time: pd.Timestamp, volatility: Optional[float] = None) -> Dict:
        """
        应用风险管理策略
        
        参数:
            signal: 原始信号（1为买入，-1为卖出，0为不操作）
            current_price: 当前价格
            entry_price: 入场价格
            highest_price: 持仓期间最高价
            lowest_price: 持仓期间最低价
            position: 当前持仓（1为多头，-1为空头，0为空仓）
            equity_curve: 权益曲线
            trade_dates: 交易日期列表
            current_time: 当前时间
            volatility: 波动率，可选
            
        返回:
            风险管理结果字典
        """
        # 初始化结果
        result = {
            'signal': signal,  # 风险管理后的信号
            'position_size': 0.0,  # 仓位大小
            'stop_loss_triggered': False,  # 是否触发止损
            'take_profit_triggered': False,  # 是否触发止盈
            'trailing_stop_triggered': False,  # 是否触发追踪止损
            'max_drawdown_exceeded': False,  # 是否超过最大回撤
            'max_trades_exceeded': False,  # 是否超过最大交易次数
            'time_filter_passed': True,  # 是否通过时间过滤
        }
        
        # 检查时间过滤器
        result['time_filter_passed'] = self.check_time_filter(current_time)
        if not result['time_filter_passed']:
            result['signal'] = 0  # 不在交易时间内，不交易
            return result
        
        # 检查最大回撤
        if not self.check_max_drawdown(equity_curve):
            result['max_drawdown_exceeded'] = True
            result['signal'] = 0  # 超过最大回撤，不交易
            return result
        
        # 检查每日最大交易次数
        if not self.check_max_trades_per_day(trade_dates, current_time):
            result['max_trades_exceeded'] = True
            result['signal'] = 0  # 超过每日最大交易次数，不交易
            return result
        
        # 如果有持仓，检查止损和止盈
        if position != 0:
            # 检查止损
            if self.apply_stop_loss(current_price, entry_price, position):
                result['stop_loss_triggered'] = True
                result['signal'] = 0  # 触发止损，平仓
                return result
            
            # 检查止盈
            if self.apply_take_profit(current_price, entry_price, position):
                result['take_profit_triggered'] = True
                result['signal'] = 0  # 触发止盈，平仓
                return result
            
            # 检查追踪止损
            if self.apply_trailing_stop(current_price, highest_price, lowest_price, position):
                result['trailing_stop_triggered'] = True
                result['signal'] = 0  # 触发追踪止损，平仓
                return result
        
        # 如果有交易信号，计算仓位大小
        if signal != 0:
            equity = equity_curve.iloc[-1]
            result['position_size'] = self.calculate_position_size(equity, current_price, volatility)
        
        return result


class PositionSizer:
    """
    仓位管理类，用于计算交易仓位大小
    支持多种仓位管理方法
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化仓位管理器
        
        参数:
            config: 配置信息，包含仓位管理参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('method', 'fixed')  # 仓位管理方法
        self.config.setdefault('max_position_size', 1.0)  # 最大仓位比例
    
    def fixed_percent(self, equity: float, price: float) -> float:
        """
        固定比例仓位管理
        
        参数:
            equity: 当前权益
            price: 当前价格
            
        返回:
            仓位大小（资金比例）
        """
        percent = self.config.get('fixed_percent', 0.1)  # 默认10%
        max_position_size = self.config['max_position_size']
        return min(percent, max_position_size)
    
    def kelly_criterion(self, equity: float, price: float, win_rate: float, profit_loss_ratio: float) -> float:
        """
        凯利公式仓位管理
        
        参数:
            equity: 当前权益
            price: 当前价格
            win_rate: 胜率
            profit_loss_ratio: 盈亏比
            
        返回:
            仓位大小（资金比例）
        """
        max_position_size = self.config['max_position_size']
        
        # 凯利公式：f = (p*b - q) / b，其中p是胜率，q是败率，b是盈亏比
        kelly = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
        
        # 通常使用半凯利或分数凯利以降低风险
        kelly_fraction = self.config.get('kelly_fraction', 0.5)
        position_size = max(0, min(kelly * kelly_fraction, max_position_size))
        
        return position_size
    
    def volatility_based(self, equity: float, price: float, volatility: float) -> float:
        """
        基于波动率的仓位管理
        
        参数:
            equity: 当前权益
            price: 当前价格
            volatility: 波动率
            
        返回:
            仓位大小（资金比例）
        """
        max_position_size = self.config['max_position_size']
        
        if volatility <= 0:
            return max_position_size
        
        # 目标波动率
        target_volatility = self.config.get('target_volatility', 0.01)  # 1%
        
        # 根据波动率调整仓位大小
        position_size = target_volatility / volatility
        
        # 限制在最大仓位范围内
        position_size = max(0, min(position_size, max_position_size))
        
        return position_size
    
    def percent_of_equity(self, equity: float, price: float) -> float:
        """
        权益百分比仓位管理
        
        参数:
            equity: 当前权益
            price: 当前价格
            
        返回:
            仓位大小（资金比例）
        """
        max_position_size = self.config['max_position_size']
        percent = self.config.get('equity_percent', 0.02)  # 默认2%
        return min(percent, max_position_size)
    
    def optimal_f(self, equity: float, price: float, trades: List[Dict]) -> float:
        """
        基于最优f值的仓位管理
        
        参数:
            equity: 当前权益
            price: 当前价格
            trades: 历史交易记录
            
        返回:
            仓位大小（资金比例）
        """
        max_position_size = self.config['max_position_size']
        
        if not trades:
            return max_position_size * 0.5  # 没有历史交易记录，使用一半的最大仓位
        
        # 计算最优f值
        # 简化版本：使用历史交易的平均盈亏比和胜率
        winning_trades = [trade for trade in trades if trade.get('net_profit', 0) > 0]
        losing_trades = [trade for trade in trades if trade.get('net_profit', 0) <= 0]
        
        if not winning_trades or not losing_trades:
            return max_position_size * 0.5
        
        avg_win = sum(trade.get('net_profit', 0) for trade in winning_trades) / len(winning_trades)
        avg_loss = abs(sum(trade.get('net_profit', 0) for trade in losing_trades) / len(losing_trades))
        win_rate = len(winning_trades) / len(trades)
        
        # 使用凯利公式计算最优f值
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
        optimal_f = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
        
        # 使用分数f值以降低风险
        f_fraction = self.config.get('f_fraction', 0.5)
        position_size = max(0, min(optimal_f * f_fraction, max_position_size))
        
        return position_size
    
    def calculate_position_size(self, equity: float, price: float, volatility: Optional[float] = None, trades: Optional[List[Dict]] = None) -> float:
        """
        计算仓位大小
        
        参数:
            equity: 当前权益
            price: 当前价格
            volatility: 波动率，可选
            trades: 历史交易记录，可选
            
        返回:
            仓位大小（资金比例）
        """
        method = self.config['method']
        
        if method == 'fixed':
            return self.fixed_percent(equity, price)
        
        elif method == 'kelly':
            win_rate = self.config.get('win_rate', 0.5)
            profit_loss_ratio = self.config.get('profit_loss_ratio', 1.0)
            return self.kelly_criterion(equity, price, win_rate, profit_loss_ratio)
        
        elif method == 'volatility':
            if volatility is None:
                self.logger.warning("使用波动率仓位管理方法，但未提供波动率参数")
                return self.fixed_percent(equity, price)
            return self.volatility_based(equity, price, volatility)
        
        elif method == 'percent_of_equity':
            return self.percent_of_equity(equity, price)
        
        elif method == 'optimal_f':
            if trades is None:
                self.logger.warning("使用最优f值仓位管理方法，但未提供历史交易记录")
                return self.fixed_percent(equity, price)
            return self.optimal_f(equity, price, trades)
        
        else:
            self.logger.warning(f"未知的仓位管理方法: {method}，使用固定比例")
            return self.fixed_percent(equity, price)