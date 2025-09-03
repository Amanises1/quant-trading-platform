# 回测引擎模块

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from typing import Dict, List, Union, Optional, Callable, Tuple
from datetime import datetime
import os

class BacktestEngine:
    """
    回测引擎类，用于执行交易策略的历史回测
    支持多种资产类型、交易成本、滑点模型和绩效评估
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化回测引擎
        
        参数:
            config: 配置信息，包含回测参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('initial_capital', 100000.0)  # 初始资金
        self.config.setdefault('commission_rate', 0.0003)    # 佣金率
        self.config.setdefault('slippage', 0.0001)           # 滑点
        self.config.setdefault('position_size', 1.0)          # 仓位大小（占总资金比例）
        
        # 回测结果
        self.results = None
        self.trades = []
        self.positions = []
        self.equity_curve = None
    
    def run(self, data: pd.DataFrame, signal_column: str = 'signal') -> Dict:
        """
        执行回测
        
        参数:
            data: 输入的数据框，包含价格和信号数据
            signal_column: 信号列名，默认为'signal'
            
        返回:
            回测结果字典
        """
        # 验证数据
        required_columns = ['open', 'high', 'low', 'close', 'volume', signal_column]
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            self.logger.error(f"数据中缺少以下列: {missing_columns}")
            return {}
        
        # 初始化回测状态
        initial_capital = self.config['initial_capital']
        commission_rate = self.config['commission_rate']
        slippage = self.config['slippage']
        position_size = self.config['position_size']
        
        # 创建结果数据框
        results = data.copy()
        
        # 初始化列
        results['position'] = 0       # 持仓状态
        results['entry_price'] = 0.0   # 入场价格
        results['exit_price'] = 0.0    # 出场价格
        results['trade_profit'] = 0.0  # 交易盈亏
        results['equity'] = initial_capital  # 账户权益
        
        # 当前持仓状态
        current_position = 0
        entry_price = 0.0
        entry_index = 0
        
        # 遍历数据执行回测
        for i in range(1, len(results)):
            # 获取当前行数据
            current_row = results.iloc[i]
            prev_row = results.iloc[i-1]
            
            # 获取信号
            signal = current_row[signal_column]
            
            # 更新持仓状态
            results.at[i, 'position'] = current_position
            
            # 处理信号
            if signal == 1 and current_position == 0:  # 买入信号且当前无持仓
                # 计算买入价格（考虑滑点）
                entry_price = current_row['open'] * (1 + slippage)
                
                # 计算买入数量
                capital_to_use = results.at[i-1, 'equity'] * position_size
                position_size_units = capital_to_use / entry_price
                
                # 更新持仓状态
                current_position = 1
                entry_index = i
                
                # 记录入场价格
                results.at[i, 'entry_price'] = entry_price
                results.at[i, 'position'] = current_position
                
                # 记录交易
                self.trades.append({
                    'type': 'buy',
                    'date': current_row.name,
                    'price': entry_price,
                    'units': position_size_units,
                    'commission': capital_to_use * commission_rate
                })
                
                # 更新账户权益（扣除佣金）
                results.at[i, 'equity'] = results.at[i-1, 'equity'] - (capital_to_use * commission_rate)
                
            elif (signal == -1 or signal == 0) and current_position == 1:  # 卖出信号且当前有持仓
                # 计算卖出价格（考虑滑点）
                exit_price = current_row['open'] * (1 - slippage)
                
                # 计算持仓市值
                capital_used = results.at[entry_index, 'equity'] * position_size
                position_size_units = capital_used / entry_price
                position_value = position_size_units * exit_price
                
                # 计算交易盈亏
                trade_profit = position_value - capital_used
                results.at[i, 'trade_profit'] = trade_profit
                
                # 更新持仓状态
                current_position = 0
                
                # 记录出场价格
                results.at[i, 'exit_price'] = exit_price
                results.at[i, 'position'] = current_position
                
                # 记录交易
                self.trades.append({
                    'type': 'sell',
                    'date': current_row.name,
                    'price': exit_price,
                    'units': position_size_units,
                    'commission': position_value * commission_rate,
                    'profit': trade_profit
                })
                
                # 更新账户权益（加上交易盈亏，扣除佣金）
                results.at[i, 'equity'] = results.at[i-1, 'equity'] + trade_profit - (position_value * commission_rate)
                
            else:  # 无交易
                # 如果有持仓，更新账户权益（根据持仓市值变化）
                if current_position == 1:
                    capital_used = results.at[entry_index, 'equity'] * position_size
                    position_size_units = capital_used / entry_price
                    current_position_value = position_size_units * current_row['close']
                    prev_position_value = position_size_units * prev_row['close']
                    
                    # 更新账户权益
                    results.at[i, 'equity'] = results.at[i-1, 'equity'] + (current_position_value - prev_position_value)
                else:
                    # 无持仓，权益不变
                    results.at[i, 'equity'] = results.at[i-1, 'equity']
        
        # 保存回测结果
        self.results = results
        self.equity_curve = results[['equity']]
        
        # 计算回测绩效指标
        performance_metrics = self._calculate_performance_metrics()
        
        # 记录回测完成
        self.logger.info(f"回测完成，总交易次数: {len(self.trades)}，最终权益: {results.iloc[-1]['equity']:.2f}")
        
        return performance_metrics
    
    def _calculate_performance_metrics(self) -> Dict:
        """
        计算回测绩效指标
        
        返回:
            绩效指标字典
        """
        if self.results is None or self.equity_curve is None:
            self.logger.error("没有回测结果可供分析")
            return {}
        
        # 提取权益曲线
        equity = self.equity_curve['equity']
        
        # 计算收益率
        initial_capital = self.config['initial_capital']
        final_equity = equity.iloc[-1]
        total_return = (final_equity / initial_capital) - 1
        
        # 计算年化收益率（假设252个交易日）
        n_days = len(equity)
        annual_return = (1 + total_return) ** (252 / n_days) - 1
        
        # 计算日收益率
        daily_returns = equity.pct_change().dropna()
        
        # 计算波动率（年化）
        volatility = daily_returns.std() * np.sqrt(252)
        
        # 计算夏普比率（假设无风险利率为0）
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 计算最大回撤
        cumulative_max = equity.cummax()
        drawdown = (equity - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # 计算盈利交易和亏损交易
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty and 'profit' in trades_df.columns:
            profitable_trades = trades_df[trades_df['profit'] > 0]
            losing_trades = trades_df[trades_df['profit'] < 0]
            
            win_rate = len(profitable_trades) / len(trades_df) if len(trades_df) > 0 else 0
            avg_profit = profitable_trades['profit'].mean() if not profitable_trades.empty else 0
            avg_loss = losing_trades['profit'].mean() if not losing_trades.empty else 0
            profit_factor = abs(profitable_trades['profit'].sum() / losing_trades['profit'].sum()) if not losing_trades.empty and losing_trades['profit'].sum() != 0 else 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
        
        # 返回绩效指标
        return {
            'initial_capital': initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_trades': len(self.trades)
        }
    
    def plot_results(self, save_path: Optional[str] = None) -> None:
        """
        绘制回测结果图表
        
        参数:
            save_path: 图表保存路径，如果为None则显示图表
        """
        if self.results is None or self.equity_curve is None:
            self.logger.error("没有回测结果可供绘图")
            return
        
        # 创建图表
        fig, axes = plt.subplots(3, 1, figsize=(12, 16), gridspec_kw={'height_ratios': [2, 1, 1]})
        
        # 绘制价格和信号
        ax1 = axes[0]
        ax1.set_title('价格和交易信号')
        ax1.plot(self.results['close'], label='收盘价')
        
        # 标记买入点和卖出点
        buy_signals = self.results[self.results['entry_price'] > 0]
        sell_signals = self.results[self.results['exit_price'] > 0]
        
        ax1.scatter(buy_signals.index, buy_signals['entry_price'], 
                   marker='^', color='g', s=100, label='买入')
        ax1.scatter(sell_signals.index, sell_signals['exit_price'], 
                   marker='v', color='r', s=100, label='卖出')
        
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制权益曲线
        ax2 = axes[1]
        ax2.set_title('账户权益曲线')
        ax2.plot(self.equity_curve, label='权益')
        ax2.set_ylabel('权益')
        ax2.legend()
        ax2.grid(True)
        
        # 绘制回撤
        ax3 = axes[2]
        ax3.set_title('回撤')
        equity = self.equity_curve['equity']
        cumulative_max = equity.cummax()
        drawdown = (equity - cumulative_max) / cumulative_max
        ax3.fill_between(drawdown.index, drawdown, 0, color='r', alpha=0.3)
        ax3.set_ylabel('回撤比例')
        ax3.grid(True)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存或显示图表
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"回测结果图表已保存至: {save_path}")
        else:
            plt.show()
    
    def generate_report(self, output_dir: Optional[str] = None) -> str:
        """
        生成回测报告
        
        参数:
            output_dir: 报告输出目录，如果为None则使用当前目录
            
        返回:
            报告文件路径
        """
        if self.results is None:
            self.logger.error("没有回测结果可供生成报告")
            return ""
        
        # 计算绩效指标
        metrics = self._calculate_performance_metrics()
        
        # 创建输出目录
        if output_dir is None:
            output_dir = os.getcwd()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"backtest_report_{timestamp}.html")
        
        # 生成HTML报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>回测报告</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1, h2 { color: #333; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    .positive { color: green; }
                    .negative { color: red; }
                    .chart-container { margin: 20px 0; }
                </style>
            </head>
            <body>
            """)
            
            # 添加标题
            f.write(f"<h1>量化交易策略回测报告</h1>")
            f.write(f"<p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
            
            # 添加绩效指标表格
            f.write("<h2>绩效指标</h2>")
            f.write("<table>")
            f.write("<tr><th>指标</th><th>值</th></tr>")
            
            # 格式化绩效指标
            f.write(f"<tr><td>初始资金</td><td>{metrics['initial_capital']:.2f}</td></tr>")
            f.write(f"<tr><td>最终权益</td><td>{metrics['final_equity']:.2f}</td></tr>")
            
            total_return_class = "positive" if metrics['total_return'] >= 0 else "negative"
            f.write(f"<tr><td>总收益率</td><td class='{total_return_class}'>{metrics['total_return']*100:.2f}%</td></tr>")
            
            annual_return_class = "positive" if metrics['annual_return'] >= 0 else "negative"
            f.write(f"<tr><td>年化收益率</td><td class='{annual_return_class}'>{metrics['annual_return']*100:.2f}%</td></tr>")
            
            f.write(f"<tr><td>波动率（年化）</td><td>{metrics['volatility']*100:.2f}%</td></tr>")
            f.write(f"<tr><td>夏普比率</td><td>{metrics['sharpe_ratio']:.2f}</td></tr>")
            f.write(f"<tr><td>最大回撤</td><td class='negative'>{metrics['max_drawdown']*100:.2f}%</td></tr>")
            f.write(f"<tr><td>胜率</td><td>{metrics['win_rate']*100:.2f}%</td></tr>")
            
            avg_profit_class = "positive" if metrics['avg_profit'] >= 0 else "negative"
            f.write(f"<tr><td>平均盈利</td><td class='{avg_profit_class}'>{metrics['avg_profit']:.2f}</td></tr>")
            
            avg_loss_class = "negative"
            f.write(f"<tr><td>平均亏损</td><td class='{avg_loss_class}'>{metrics['avg_loss']:.2f}</td></tr>")
            
            f.write(f"<tr><td>盈亏比</td><td>{metrics['profit_factor']:.2f}</td></tr>")
            f.write(f"<tr><td>总交易次数</td><td>{metrics['total_trades']}</td></tr>")
            f.write("</table>")
            
            # 添加图表（使用base64编码的图片）
            f.write("<h2>回测图表</h2>")
            f.write("<div class='chart-container'>")
            
            # 生成图表并保存为临时文件
            chart_file = os.path.join(output_dir, f"temp_chart_{timestamp}.png")
            self.plot_results(save_path=chart_file)
            
            # 将图表嵌入HTML（简化处理，实际应用中可以使用base64编码）
            f.write(f"<img src='{chart_file}' alt='回测图表' style='width:100%;'>")
            f.write("</div>")
            
            # 添加交易记录表格
            f.write("<h2>交易记录</h2>")
            f.write("<table>")
            f.write("<tr><th>日期</th><th>类型</th><th>价格</th><th>数量</th><th>佣金</th><th>盈亏</th></tr>")
            
            for trade in self.trades:
                trade_type = "买入" if trade['type'] == 'buy' else "卖出"
                profit_class = ""
                profit_value = ""
                
                if 'profit' in trade:
                    profit_class = "positive" if trade['profit'] >= 0 else "negative"
                    profit_value = f"{trade['profit']:.2f}"
                
                f.write(f"<tr>")
                f.write(f"<td>{trade['date']}</td>")
                f.write(f"<td>{trade_type}</td>")
                f.write(f"<td>{trade['price']:.4f}</td>")
                f.write(f"<td>{trade['units']:.4f}</td>")
                f.write(f"<td>{trade['commission']:.2f}</td>")
                f.write(f"<td class='{profit_class}'>{profit_value}</td>")
                f.write(f"</tr>")
            
            f.write("</table>")
            
            # 结束HTML
            f.write("""</body>
            </html>""")
        
        self.logger.info(f"回测报告已生成: {report_file}")
        
        return report_file