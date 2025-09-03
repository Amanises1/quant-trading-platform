# 策略评估器模块

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from typing import Dict, List, Union, Optional, Tuple
import os
from datetime import datetime

class StrategyEvaluator:
    """
    策略评估器类，用于评估交易策略的性能
    提供多种评估指标和可视化工具
    """
    
    def __init__(self):
        """
        初始化策略评估器
        """
        self.logger = logging.getLogger(__name__)
    
    def evaluate(self, equity_curve: pd.DataFrame, trades: List[Dict], 
                benchmark: Optional[pd.DataFrame] = None) -> Dict:
        """
        评估策略性能
        
        参数:
            equity_curve: 权益曲线数据框
            trades: 交易记录列表
            benchmark: 基准数据框，可选
            
        返回:
            评估指标字典
        """
        # 验证输入
        if equity_curve is None or equity_curve.empty:
            self.logger.error("权益曲线为空")
            return {}
        
        # 提取权益数据
        if 'equity' in equity_curve.columns:
            equity = equity_curve['equity']
        else:
            equity = equity_curve.iloc[:, 0]  # 假设第一列是权益
        
        # 计算收益率
        initial_equity = equity.iloc[0]
        final_equity = equity.iloc[-1]
        total_return = (final_equity / initial_equity) - 1
        
        # 计算日收益率
        daily_returns = equity.pct_change().dropna()
        
        # 计算年化收益率（假设252个交易日）
        n_days = len(equity)
        annual_return = (1 + total_return) ** (252 / n_days) - 1
        
        # 计算波动率（年化）
        volatility = daily_returns.std() * np.sqrt(252)
        
        # 计算夏普比率（假设无风险利率为0）
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 计算索提诺比率（假设无风险利率为0，目标收益率为0）
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if not downside_returns.empty else 0
        sortino_ratio = annual_return / downside_deviation if downside_deviation > 0 else 0
        
        # 计算最大回撤
        cumulative_max = equity.cummax()
        drawdown = (equity - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # 计算卡玛比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 计算盈利交易和亏损交易
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        
        if not trades_df.empty and 'profit' in trades_df.columns:
            profitable_trades = trades_df[trades_df['profit'] > 0]
            losing_trades = trades_df[trades_df['profit'] < 0]
            
            win_rate = len(profitable_trades) / len(trades_df) if len(trades_df) > 0 else 0
            avg_profit = profitable_trades['profit'].mean() if not profitable_trades.empty else 0
            avg_loss = losing_trades['profit'].mean() if not losing_trades.empty else 0
            profit_factor = abs(profitable_trades['profit'].sum() / losing_trades['profit'].sum()) if not losing_trades.empty and losing_trades['profit'].sum() != 0 else 0
            
            # 计算期望值
            expectancy = (win_rate * avg_profit) + ((1 - win_rate) * avg_loss)
            
            # 计算系统质量指数
            if avg_loss != 0:
                sqn = np.sqrt(len(trades_df)) * (expectancy / abs(avg_loss))
            else:
                sqn = 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
            expectancy = 0
            sqn = 0
        
        # 计算基准相关指标
        alpha = 0
        beta = 0
        r_squared = 0
        information_ratio = 0
        
        if benchmark is not None and not benchmark.empty:
            # 提取基准数据
            if 'close' in benchmark.columns:
                benchmark_prices = benchmark['close']
            else:
                benchmark_prices = benchmark.iloc[:, 0]  # 假设第一列是价格
            
            # 确保基准数据与权益曲线长度一致
            if len(benchmark_prices) >= len(equity):
                benchmark_prices = benchmark_prices[:len(equity)]
            else:
                self.logger.warning("基准数据长度小于权益曲线长度，无法计算相对指标")
                benchmark_prices = None
            
            if benchmark_prices is not None:
                # 计算基准收益率
                benchmark_returns = benchmark_prices.pct_change().dropna()
                
                # 确保收益率数据长度一致
                min_length = min(len(daily_returns), len(benchmark_returns))
                strategy_returns = daily_returns[:min_length]
                benchmark_returns = benchmark_returns[:min_length]
                
                # 计算Beta（策略相对于基准的波动性）
                covariance = np.cov(strategy_returns, benchmark_returns)[0, 1]
                benchmark_variance = np.var(benchmark_returns)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                
                # 计算Alpha（策略超额收益）
                benchmark_annual_return = (1 + benchmark_returns.mean()) ** 252 - 1
                alpha = annual_return - (beta * benchmark_annual_return)
                
                # 计算R方（策略收益率被基准解释的比例）
                correlation = np.corrcoef(strategy_returns, benchmark_returns)[0, 1]
                r_squared = correlation ** 2
                
                # 计算信息比率（超额收益与跟踪误差的比值）
                tracking_error = (strategy_returns - benchmark_returns).std() * np.sqrt(252)
                information_ratio = (annual_return - benchmark_annual_return) / tracking_error if tracking_error > 0 else 0
        
        # 返回评估指标
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'sqn': sqn,
            'alpha': alpha,
            'beta': beta,
            'r_squared': r_squared,
            'information_ratio': information_ratio,
            'total_trades': len(trades) if trades else 0
        }
    
    def plot_equity_curve(self, equity_curve: pd.DataFrame, benchmark: Optional[pd.DataFrame] = None,
                         save_path: Optional[str] = None) -> None:
        """
        绘制权益曲线
        
        参数:
            equity_curve: 权益曲线数据框
            benchmark: 基准数据框，可选
            save_path: 图表保存路径，如果为None则显示图表
        """
        if equity_curve is None or equity_curve.empty:
            self.logger.error("权益曲线为空")
            return
        
        # 提取权益数据
        if 'equity' in equity_curve.columns:
            equity = equity_curve['equity']
        else:
            equity = equity_curve.iloc[:, 0]  # 假设第一列是权益
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 绘制权益曲线
        plt.plot(equity, label='策略权益')
        
        # 如果有基准数据，也绘制基准曲线
        if benchmark is not None and not benchmark.empty:
            # 提取基准数据
            if 'close' in benchmark.columns:
                benchmark_prices = benchmark['close']
            else:
                benchmark_prices = benchmark.iloc[:, 0]  # 假设第一列是价格
            
            # 确保基准数据与权益曲线长度一致
            if len(benchmark_prices) >= len(equity):
                benchmark_prices = benchmark_prices[:len(equity)]
                
                # 归一化基准数据，使起点与权益曲线相同
                initial_equity = equity.iloc[0]
                normalized_benchmark = benchmark_prices / benchmark_prices.iloc[0] * initial_equity
                
                plt.plot(normalized_benchmark, label='基准', alpha=0.7)
        
        # 设置图表属性
        plt.title('策略权益曲线')
        plt.xlabel('日期')
        plt.ylabel('权益')
        plt.legend()
        plt.grid(True)
        
        # 保存或显示图表
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"权益曲线图表已保存至: {save_path}")
        else:
            plt.show()
    
    def plot_drawdown(self, equity_curve: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        绘制回撤曲线
        
        参数:
            equity_curve: 权益曲线数据框
            save_path: 图表保存路径，如果为None则显示图表
        """
        if equity_curve is None or equity_curve.empty:
            self.logger.error("权益曲线为空")
            return
        
        # 提取权益数据
        if 'equity' in equity_curve.columns:
            equity = equity_curve['equity']
        else:
            equity = equity_curve.iloc[:, 0]  # 假设第一列是权益
        
        # 计算回撤
        cumulative_max = equity.cummax()
        drawdown = (equity - cumulative_max) / cumulative_max
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 绘制回撤曲线
        plt.fill_between(drawdown.index, drawdown, 0, color='r', alpha=0.3)
        plt.plot(drawdown, color='r', label='回撤')
        
        # 设置图表属性
        plt.title('策略回撤曲线')
        plt.xlabel('日期')
        plt.ylabel('回撤比例')
        plt.legend()
        plt.grid(True)
        
        # 保存或显示图表
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"回撤曲线图表已保存至: {save_path}")
        else:
            plt.show()
    
    def plot_monthly_returns(self, equity_curve: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        绘制月度收益热图
        
        参数:
            equity_curve: 权益曲线数据框
            save_path: 图表保存路径，如果为None则显示图表
        """
        if equity_curve is None or equity_curve.empty:
            self.logger.error("权益曲线为空")
            return
        
        # 提取权益数据
        if 'equity' in equity_curve.columns:
            equity = equity_curve['equity']
        else:
            equity = equity_curve.iloc[:, 0]  # 假设第一列是权益
        
        # 确保索引是日期类型
        if not isinstance(equity.index, pd.DatetimeIndex):
            self.logger.error("权益曲线索引不是日期类型，无法计算月度收益")
            return
        
        # 计算日收益率
        daily_returns = equity.pct_change().dropna()
        
        # 计算月度收益率
        monthly_returns = daily_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # 创建月度收益矩阵
        monthly_returns_matrix = monthly_returns.groupby([monthly_returns.index.year, monthly_returns.index.month]).first().unstack()
        
        # 创建图表
        plt.figure(figsize=(12, 8))
        
        # 绘制热图
        cmap = plt.cm.RdYlGn  # 红黄绿色图，负值为红色，正值为绿色
        ax = plt.pcolor(monthly_returns_matrix, cmap=cmap, vmin=-0.1, vmax=0.1)
        
        # 设置坐标轴
        plt.yticks(np.arange(0.5, len(monthly_returns_matrix.index), 1), monthly_returns_matrix.index)
        plt.xticks(np.arange(0.5, len(monthly_returns_matrix.columns), 1), ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'])
        
        # 添加颜色条
        plt.colorbar(ax, label='月度收益率')
        
        # 在每个单元格中添加收益率值
        for i in range(len(monthly_returns_matrix.index)):
            for j in range(len(monthly_returns_matrix.columns)):
                if not np.isnan(monthly_returns_matrix.iloc[i, j]):
                    plt.text(j + 0.5, i + 0.5, f'{monthly_returns_matrix.iloc[i, j]:.1%}',
                            ha='center', va='center',
                            color='white' if abs(monthly_returns_matrix.iloc[i, j]) > 0.05 else 'black')
        
        # 设置图表属性
        plt.title('月度收益热图')
        plt.tight_layout()
        
        # 保存或显示图表
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"月度收益热图已保存至: {save_path}")
        else:
            plt.show()
    
    def generate_report(self, equity_curve: pd.DataFrame, trades: List[Dict], 
                       benchmark: Optional[pd.DataFrame] = None, output_dir: Optional[str] = None) -> str:
        """
        生成策略评估报告
        
        参数:
            equity_curve: 权益曲线数据框
            trades: 交易记录列表
            benchmark: 基准数据框，可选
            output_dir: 报告输出目录，如果为None则使用当前目录
            
        返回:
            报告文件路径
        """
        if equity_curve is None or equity_curve.empty:
            self.logger.error("权益曲线为空")
            return ""
        
        # 评估策略
        metrics = self.evaluate(equity_curve, trades, benchmark)
        
        # 创建输出目录
        if output_dir is None:
            output_dir = os.getcwd()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"strategy_report_{timestamp}.html")
        
        # 生成图表文件
        equity_chart_file = os.path.join(output_dir, f"equity_curve_{timestamp}.png")
        drawdown_chart_file = os.path.join(output_dir, f"drawdown_{timestamp}.png")
        monthly_returns_chart_file = os.path.join(output_dir, f"monthly_returns_{timestamp}.png")
        
        # 绘制图表
        self.plot_equity_curve(equity_curve, benchmark, save_path=equity_chart_file)
        self.plot_drawdown(equity_curve, save_path=drawdown_chart_file)
        
        try:
            self.plot_monthly_returns(equity_curve, save_path=monthly_returns_chart_file)
            monthly_returns_available = True
        except Exception as e:
            self.logger.warning(f"无法生成月度收益热图: {e}")
            monthly_returns_available = False
        
        # 生成HTML报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>策略评估报告</title>
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
            f.write(f"<h1>量化交易策略评估报告</h1>")
            f.write(f"<p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
            
            # 添加绩效指标表格
            f.write("<h2>绩效指标</h2>")
            f.write("<table>")
            f.write("<tr><th>指标</th><th>值</th></tr>")
            
            # 格式化绩效指标
            total_return_class = "positive" if metrics['total_return'] >= 0 else "negative"
            f.write(f"<tr><td>总收益率</td><td class='{total_return_class}'>{metrics['total_return']*100:.2f}%</td></tr>")
            
            annual_return_class = "positive" if metrics['annual_return'] >= 0 else "negative"
            f.write(f"<tr><td>年化收益率</td><td class='{annual_return_class}'>{metrics['annual_return']*100:.2f}%</td></tr>")
            
            f.write(f"<tr><td>波动率（年化）</td><td>{metrics['volatility']*100:.2f}%</td></tr>")
            f.write(f"<tr><td>夏普比率</td><td>{metrics['sharpe_ratio']:.2f}</td></tr>")
            f.write(f"<tr><td>索提诺比率</td><td>{metrics['sortino_ratio']:.2f}</td></tr>")
            f.write(f"<tr><td>最大回撤</td><td class='negative'>{metrics['max_drawdown']*100:.2f}%</td></tr>")
            f.write(f"<tr><td>卡玛比率</td><td>{metrics['calmar_ratio']:.2f}</td></tr>")
            f.write(f"<tr><td>胜率</td><td>{metrics['win_rate']*100:.2f}%</td></tr>")
            
            avg_profit_class = "positive" if metrics['avg_profit'] >= 0 else "negative"
            f.write(f"<tr><td>平均盈利</td><td class='{avg_profit_class}'>{metrics['avg_profit']:.2f}</td></tr>")
            
            avg_loss_class = "negative"
            f.write(f"<tr><td>平均亏损</td><td class='{avg_loss_class}'>{metrics['avg_loss']:.2f}</td></tr>")
            
            f.write(f"<tr><td>盈亏比</td><td>{metrics['profit_factor']:.2f}</td></tr>")
            f.write(f"<tr><td>期望值</td><td>{metrics['expectancy']:.2f}</td></tr>")
            f.write(f"<tr><td>系统质量指数</td><td>{metrics['sqn']:.2f}</td></tr>")
            
            # 如果有基准数据，添加相对指标
            if benchmark is not None:
                alpha_class = "positive" if metrics['alpha'] >= 0 else "negative"
                f.write(f"<tr><td>Alpha</td><td class='{alpha_class}'>{metrics['alpha']*100:.2f}%</td></tr>")
                f.write(f"<tr><td>Beta</td><td>{metrics['beta']:.2f}</td></tr>")
                f.write(f"<tr><td>R方</td><td>{metrics['r_squared']:.2f}</td></tr>")
                f.write(f"<tr><td>信息比率</td><td>{metrics['information_ratio']:.2f}</td></tr>")
            
            f.write(f"<tr><td>总交易次数</td><td>{metrics['total_trades']}</td></tr>")
            f.write("</table>")
            
            # 添加图表
            f.write("<h2>策略图表</h2>")
            
            # 权益曲线图
            f.write("<div class='chart-container'>")
            f.write("<h3>权益曲线</h3>")
            f.write(f"<img src='{equity_chart_file}' alt='权益曲线' style='width:100%;'>")
            f.write("</div>")
            
            # 回撤曲线图
            f.write("<div class='chart-container'>")
            f.write("<h3>回撤曲线</h3>")
            f.write(f"<img src='{drawdown_chart_file}' alt='回撤曲线' style='width:100%;'>")
            f.write("</div>")
            
            # 月度收益热图
            if monthly_returns_available:
                f.write("<div class='chart-container'>")
                f.write("<h3>月度收益热图</h3>")
                f.write(f"<img src='{monthly_returns_chart_file}' alt='月度收益热图' style='width:100%;'>")
                f.write("</div>")
            
            # 添加交易记录表格
            if trades:
                f.write("<h2>交易记录</h2>")
                f.write("<table>")
                f.write("<tr><th>日期</th><th>类型</th><th>价格</th><th>数量</th><th>佣金</th><th>盈亏</th></tr>")
                
                for trade in trades:
                    trade_type = "买入" if trade.get('type') == 'buy' else "卖出"
                    profit_class = ""
                    profit_value = ""
                    
                    if 'profit' in trade:
                        profit_class = "positive" if trade['profit'] >= 0 else "negative"
                        profit_value = f"{trade['profit']:.2f}"
                    
                    f.write(f"<tr>")
                    f.write(f"<td>{trade.get('date', '')}</td>")
                    f.write(f"<td>{trade_type}</td>")
                    f.write(f"<td>{trade.get('price', 0):.4f}</td>")
                    f.write(f"<td>{trade.get('units', 0):.4f}</td>")
                    f.write(f"<td>{trade.get('commission', 0):.2f}</td>")
                    f.write(f"<td class='{profit_class}'>{profit_value}</td>")
                    f.write(f"</tr>")
                
                f.write("</table>")
            
            # 结束HTML
            f.write("""</body>
            </html>""")
        
        self.logger.info(f"策略评估报告已生成: {report_file}")
        
        return report_file