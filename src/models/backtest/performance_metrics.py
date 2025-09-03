# 回测性能评估模块

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime

class PerformanceMetrics:
    """
    回测性能评估类，用于计算和展示策略性能指标
    支持多种性能指标计算和可视化
    """
    
    def __init__(self):
        """
        初始化性能评估类
        """
        pass
    
    @staticmethod
    def calculate_returns(equity_curve: pd.Series) -> pd.Series:
        """
        计算收益率序列
        
        参数:
            equity_curve: 权益曲线
            
        返回:
            收益率序列
        """
        returns = equity_curve.pct_change().fillna(0)
        return returns
    
    @staticmethod
    def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
        """
        计算累积收益率
        
        参数:
            returns: 收益率序列
            
        返回:
            累积收益率序列
        """
        cumulative_returns = (1 + returns).cumprod() - 1
        return cumulative_returns
    
    @staticmethod
    def calculate_drawdown(equity_curve: pd.Series) -> Tuple[pd.Series, float, pd.Timestamp, pd.Timestamp]:
        """
        计算回撤序列和最大回撤
        
        参数:
            equity_curve: 权益曲线
            
        返回:
            (回撤序列, 最大回撤值, 最大回撤开始时间, 最大回撤结束时间)
        """
        # 计算累计最大值
        running_max = equity_curve.cummax()
        # 计算回撤序列
        drawdown = (equity_curve - running_max) / running_max
        # 计算最大回撤及其发生时间
        max_drawdown = drawdown.min()
        max_drawdown_end = drawdown.idxmin()
        # 找到最大回撤开始时间
        if max_drawdown < 0:
            # 找到在最大回撤结束前的最后一个峰值
            temp = equity_curve[:max_drawdown_end]
            max_drawdown_start = temp.idxmax()
        else:
            max_drawdown_start = max_drawdown_end
        
        return drawdown, max_drawdown, max_drawdown_start, max_drawdown_end
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """
        计算夏普比率
        
        参数:
            returns: 收益率序列
            risk_free_rate: 无风险利率，默认为0
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            夏普比率
        """
        excess_returns = returns - risk_free_rate / periods_per_year
        if len(excess_returns) < 2:
            return 0.0
        
        volatility = returns.std()
        if volatility == 0:
            return 0.0
        
        sharpe_ratio = np.sqrt(periods_per_year) * excess_returns.mean() / volatility
        return sharpe_ratio
    
    @staticmethod
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """
        计算索提诺比率
        
        参数:
            returns: 收益率序列
            risk_free_rate: 无风险利率，默认为0
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            索提诺比率
        """
        excess_returns = returns - risk_free_rate / periods_per_year
        if len(excess_returns) < 2:
            return 0.0
        
        # 只考虑负收益的标准差
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf')  # 如果没有负收益，返回无穷大
        
        sortino_ratio = np.sqrt(periods_per_year) * excess_returns.mean() / downside_returns.std()
        return sortino_ratio
    
    @staticmethod
    def calculate_calmar_ratio(returns: pd.Series, max_drawdown: float, periods_per_year: int = 252) -> float:
        """
        计算卡玛比率
        
        参数:
            returns: 收益率序列
            max_drawdown: 最大回撤值（正值）
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            卡玛比率
        """
        if max_drawdown >= 0:
            return 0.0
        
        annual_return = returns.mean() * periods_per_year
        calmar_ratio = -annual_return / max_drawdown
        return calmar_ratio
    
    @staticmethod
    def calculate_omega_ratio(returns: pd.Series, threshold: float = 0.0, periods_per_year: int = 252) -> float:
        """
        计算欧米伽比率
        
        参数:
            returns: 收益率序列
            threshold: 阈值，默认为0
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            欧米伽比率
        """
        threshold_return = threshold / periods_per_year
        excess_returns = returns - threshold_return
        
        positive_returns = excess_returns[excess_returns > 0].sum()
        negative_returns = -excess_returns[excess_returns < 0].sum()
        
        if negative_returns == 0:
            return float('inf')  # 如果没有负超额收益，返回无穷大
        
        omega_ratio = positive_returns / negative_returns
        return omega_ratio
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict]) -> float:
        """
        计算胜率
        
        参数:
            trades: 交易记录列表
            
        返回:
            胜率
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for trade in trades if trade.get('net_profit', 0) > 0)
        win_rate = winning_trades / len(trades)
        return win_rate
    
    @staticmethod
    def calculate_profit_factor(trades: List[Dict]) -> float:
        """
        计算盈亏比
        
        参数:
            trades: 交易记录列表
            
        返回:
            盈亏比
        """
        if not trades:
            return 0.0
        
        gross_profit = sum(trade.get('net_profit', 0) for trade in trades if trade.get('net_profit', 0) > 0)
        gross_loss = abs(sum(trade.get('net_profit', 0) for trade in trades if trade.get('net_profit', 0) <= 0))
        
        if gross_loss == 0:
            return float('inf')  # 如果没有亏损，返回无穷大
        
        profit_factor = gross_profit / gross_loss
        return profit_factor
    
    @staticmethod
    def calculate_expectancy(trades: List[Dict]) -> float:
        """
        计算期望值
        
        参数:
            trades: 交易记录列表
            
        返回:
            期望值
        """
        if not trades:
            return 0.0
        
        total_profit = sum(trade.get('net_profit', 0) for trade in trades)
        expectancy = total_profit / len(trades)
        return expectancy
    
    @staticmethod
    def calculate_average_trade(trades: List[Dict]) -> Dict:
        """
        计算平均交易统计
        
        参数:
            trades: 交易记录列表
            
        返回:
            平均交易统计字典
        """
        if not trades:
            return {
                'avg_profit': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_duration': 0.0
            }
        
        # 计算平均盈利
        total_profit = sum(trade.get('net_profit', 0) for trade in trades)
        avg_profit = total_profit / len(trades)
        
        # 计算平均盈利交易
        winning_trades = [trade for trade in trades if trade.get('net_profit', 0) > 0]
        avg_win = sum(trade.get('net_profit', 0) for trade in winning_trades) / len(winning_trades) if winning_trades else 0.0
        
        # 计算平均亏损交易
        losing_trades = [trade for trade in trades if trade.get('net_profit', 0) <= 0]
        avg_loss = sum(trade.get('net_profit', 0) for trade in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        # 计算平均持仓时间
        if 'entry_time' in trades[0] and 'exit_time' in trades[0]:
            if isinstance(trades[0]['entry_time'], (pd.Timestamp, datetime)):
                # 如果是时间戳，计算实际持仓时间
                durations = [(trade['exit_time'] - trade['entry_time']).total_seconds() / 86400 for trade in trades]  # 转换为天数
                avg_duration = sum(durations) / len(durations)
            else:
                # 如果是索引，计算持仓周期数
                durations = [trade['exit_time'] - trade['entry_time'] for trade in trades]
                avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0.0
        
        return {
            'avg_profit': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_duration': avg_duration
        }
    
    @staticmethod
    def calculate_var(returns: pd.Series, alpha: float = 0.05) -> float:
        """
        计算风险价值(VaR)
        
        参数:
            returns: 收益率序列
            alpha: 置信水平，默认为0.05（95%置信度）
            
        返回:
            VaR值
        """
        if len(returns) < 3:
            return 0.0
        
        # 使用历史模拟法计算VaR
        var = -np.percentile(returns, alpha * 100)
        return var
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, alpha: float = 0.05) -> float:
        """
        计算条件风险价值(CVaR)
        
        参数:
            returns: 收益率序列
            alpha: 置信水平，默认为0.05（95%置信度）
            
        返回:
            CVaR值
        """
        if len(returns) < 3:
            return 0.0
        
        # 计算VaR
        var = PerformanceMetrics.calculate_var(returns, alpha)
        # 计算CVaR（超过VaR的损失的平均值）
        cvar = -returns[returns <= -var].mean()
        return cvar if not np.isnan(cvar) else 0.0
    
    @staticmethod
    def calculate_annual_return(returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        计算年化收益率
        
        参数:
            returns: 收益率序列
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            年化收益率
        """
        if len(returns) < 1:
            return 0.0
        
        # 计算累积收益率
        cumulative_return = (1 + returns).prod() - 1
        # 计算年化收益率
        years = len(returns) / periods_per_year
        annual_return = (1 + cumulative_return) ** (1 / max(years, 1e-6)) - 1
        return annual_return
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        计算波动率
        
        参数:
            returns: 收益率序列
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            年化波动率
        """
        if len(returns) < 2:
            return 0.0
        
        # 计算年化波动率
        volatility = returns.std() * np.sqrt(periods_per_year)
        return volatility
    
    @staticmethod
    def calculate_beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算贝塔系数
        
        参数:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列
            
        返回:
            贝塔系数
        """
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 0.0
        
        # 计算协方差和方差
        covariance = returns.cov(benchmark_returns)
        variance = benchmark_returns.var()
        
        if variance == 0:
            return 0.0
        
        beta = covariance / variance
        return beta
    
    @staticmethod
    def calculate_alpha(returns: pd.Series, benchmark_returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """
        计算阿尔法系数
        
        参数:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列
            risk_free_rate: 无风险利率，默认为0
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            阿尔法系数
        """
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 0.0
        
        # 计算贝塔系数
        beta = PerformanceMetrics.calculate_beta(returns, benchmark_returns)
        
        # 计算年化收益率
        strategy_return = PerformanceMetrics.calculate_annual_return(returns, periods_per_year)
        benchmark_return = PerformanceMetrics.calculate_annual_return(benchmark_returns, periods_per_year)
        
        # 计算阿尔法系数
        alpha = strategy_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
        return alpha
    
    @staticmethod
    def calculate_information_ratio(returns: pd.Series, benchmark_returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        计算信息比率
        
        参数:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            信息比率
        """
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return 0.0
        
        # 计算超额收益
        excess_returns = returns - benchmark_returns
        
        # 计算跟踪误差
        tracking_error = excess_returns.std()
        if tracking_error == 0:
            return 0.0
        
        # 计算信息比率
        information_ratio = np.sqrt(periods_per_year) * excess_returns.mean() / tracking_error
        return information_ratio
    
    @staticmethod
    def calculate_all_metrics(equity_curve: pd.Series, trades: List[Dict], benchmark_returns: Optional[pd.Series] = None, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> Dict:
        """
        计算所有性能指标
        
        参数:
            equity_curve: 权益曲线
            trades: 交易记录列表
            benchmark_returns: 基准收益率序列，默认为None
            risk_free_rate: 无风险利率，默认为0
            periods_per_year: 每年的周期数，日线为252，周线为52，月线为12
            
        返回:
            所有性能指标字典
        """
        # 计算收益率序列
        returns = PerformanceMetrics.calculate_returns(equity_curve)
        
        # 计算累积收益率
        cumulative_returns = PerformanceMetrics.calculate_cumulative_returns(returns)
        
        # 计算回撤
        drawdown, max_drawdown, max_dd_start, max_dd_end = PerformanceMetrics.calculate_drawdown(equity_curve)
        
        # 计算基本指标
        metrics = {
            'total_return': cumulative_returns.iloc[-1] if len(cumulative_returns) > 0 else 0.0,
            'annual_return': PerformanceMetrics.calculate_annual_return(returns, periods_per_year),
            'volatility': PerformanceMetrics.calculate_volatility(returns, periods_per_year),
            'sharpe_ratio': PerformanceMetrics.calculate_sharpe_ratio(returns, risk_free_rate, periods_per_year),
            'sortino_ratio': PerformanceMetrics.calculate_sortino_ratio(returns, risk_free_rate, periods_per_year),
            'max_drawdown': max_drawdown,
            'max_drawdown_start': max_dd_start,
            'max_drawdown_end': max_dd_end,
            'calmar_ratio': PerformanceMetrics.calculate_calmar_ratio(returns, max_drawdown, periods_per_year),
            'omega_ratio': PerformanceMetrics.calculate_omega_ratio(returns, risk_free_rate, periods_per_year),
            'var': PerformanceMetrics.calculate_var(returns),
            'cvar': PerformanceMetrics.calculate_cvar(returns),
        }
        
        # 计算交易统计
        metrics.update({
            'win_rate': PerformanceMetrics.calculate_win_rate(trades),
            'profit_factor': PerformanceMetrics.calculate_profit_factor(trades),
            'expectancy': PerformanceMetrics.calculate_expectancy(trades),
            'total_trades': len(trades),
            'winning_trades': sum(1 for trade in trades if trade.get('net_profit', 0) > 0),
            'losing_trades': sum(1 for trade in trades if trade.get('net_profit', 0) <= 0),
        })
        
        # 计算平均交易统计
        avg_trade = PerformanceMetrics.calculate_average_trade(trades)
        metrics.update(avg_trade)
        
        # 如果有基准收益率，计算相对指标
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            metrics.update({
                'beta': PerformanceMetrics.calculate_beta(returns, benchmark_returns),
                'alpha': PerformanceMetrics.calculate_alpha(returns, benchmark_returns, risk_free_rate, periods_per_year),
                'information_ratio': PerformanceMetrics.calculate_information_ratio(returns, benchmark_returns, periods_per_year),
            })
        
        return metrics
    
    @staticmethod
    def plot_equity_curve(equity_curve: pd.Series, benchmark: Optional[pd.Series] = None, figsize: tuple = (12, 6)):
        """
        绘制权益曲线
        
        参数:
            equity_curve: 权益曲线
            benchmark: 基准权益曲线，默认为None
            figsize: 图表大小
        """
        plt.figure(figsize=figsize)
        
        # 绘制策略权益曲线
        plt.plot(equity_curve, label='Strategy')
        
        # 如果有基准，绘制基准权益曲线
        if benchmark is not None and len(benchmark) == len(equity_curve):
            plt.plot(benchmark, label='Benchmark', alpha=0.7)
        
        plt.title('Equity Curve')
        plt.xlabel('Date' if isinstance(equity_curve.index, pd.DatetimeIndex) else 'Bar')
        plt.ylabel('Equity')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_drawdown(drawdown: pd.Series, figsize: tuple = (12, 6)):
        """
        绘制回撤曲线
        
        参数:
            drawdown: 回撤序列
            figsize: 图表大小
        """
        plt.figure(figsize=figsize)
        plt.plot(drawdown, color='red', alpha=0.7)
        plt.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
        plt.title('Drawdown')
        plt.xlabel('Date' if isinstance(drawdown.index, pd.DatetimeIndex) else 'Bar')
        plt.ylabel('Drawdown')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_returns_distribution(returns: pd.Series, figsize: tuple = (12, 6)):
        """
        绘制收益率分布
        
        参数:
            returns: 收益率序列
            figsize: 图表大小
        """
        plt.figure(figsize=figsize)
        
        # 绘制收益率直方图
        plt.hist(returns, bins=50, alpha=0.7, color='blue')
        
        # 添加正态分布曲线
        x = np.linspace(returns.min(), returns.max(), 100)
        y = len(returns) * (returns.max() - returns.min()) / 50 * np.exp(-(x - returns.mean())**2 / (2 * returns.std()**2)) / (returns.std() * np.sqrt(2 * np.pi))
        plt.plot(x, y, 'r-', alpha=0.7)
        
        plt.title('Returns Distribution')
        plt.xlabel('Return')
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_monthly_returns_heatmap(returns: pd.Series, figsize: tuple = (12, 8)):
        """
        绘制月度收益率热图
        
        参数:
            returns: 收益率序列，索引必须是DatetimeIndex
            figsize: 图表大小
        """
        if not isinstance(returns.index, pd.DatetimeIndex):
            print("收益率序列索引必须是DatetimeIndex")
            return
        
        # 计算月度收益率
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # 创建月度收益率矩阵
        monthly_returns_matrix = monthly_returns.groupby([monthly_returns.index.year, monthly_returns.index.month]).first().unstack()
        
        # 绘制热图
        plt.figure(figsize=figsize)
        sns.heatmap(monthly_returns_matrix, annot=True, fmt='.2%', cmap='RdYlGn', center=0, linewidths=1)
        plt.title('Monthly Returns Heatmap')
        plt.xlabel('Month')
        plt.ylabel('Year')
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def generate_performance_report(metrics: Dict) -> str:
        """
        生成性能报告
        
        参数:
            metrics: 性能指标字典
            
        返回:
            性能报告文本
        """
        report = "性能评估报告\n"
        report += "==============\n\n"
        
        # 收益指标
        report += "收益指标:\n"
        report += f"总收益率: {metrics.get('total_return', 0.0):.2%}\n"
        report += f"年化收益率: {metrics.get('annual_return', 0.0):.2%}\n"
        report += f"波动率: {metrics.get('volatility', 0.0):.2%}\n\n"
        
        # 风险指标
        report += "风险指标:\n"
        report += f"夏普比率: {metrics.get('sharpe_ratio', 0.0):.2f}\n"
        report += f"索提诺比率: {metrics.get('sortino_ratio', 0.0):.2f}\n"
        report += f"最大回撤: {metrics.get('max_drawdown', 0.0):.2%}\n"
        report += f"卡玛比率: {metrics.get('calmar_ratio', 0.0):.2f}\n"
        report += f"欧米伽比率: {metrics.get('omega_ratio', 0.0):.2f}\n"
        report += f"VaR (95%): {metrics.get('var', 0.0):.2%}\n"
        report += f"CVaR (95%): {metrics.get('cvar', 0.0):.2%}\n\n"
        
        # 交易统计
        report += "交易统计:\n"
        report += f"总交易次数: {metrics.get('total_trades', 0)}\n"
        report += f"盈利交易次数: {metrics.get('winning_trades', 0)}\n"
        report += f"亏损交易次数: {metrics.get('losing_trades', 0)}\n"
        report += f"胜率: {metrics.get('win_rate', 0.0):.2%}\n"
        report += f"盈亏比: {metrics.get('profit_factor', 0.0):.2f}\n"
        report += f"期望值: {metrics.get('expectancy', 0.0):.2f}\n"
        report += f"平均盈利: {metrics.get('avg_profit', 0.0):.2f}\n"
        report += f"平均盈利交易: {metrics.get('avg_win', 0.0):.2f}\n"
        report += f"平均亏损交易: {metrics.get('avg_loss', 0.0):.2f}\n"
        report += f"平均持仓时间: {metrics.get('avg_duration', 0.0):.2f} 天\n\n"
        
        # 相对指标（如果有）
        if 'beta' in metrics:
            report += "相对指标:\n"
            report += f"贝塔系数: {metrics.get('beta', 0.0):.2f}\n"
            report += f"阿尔法系数: {metrics.get('alpha', 0.0):.2%}\n"
            report += f"信息比率: {metrics.get('information_ratio', 0.0):.2f}\n\n"
        
        return report