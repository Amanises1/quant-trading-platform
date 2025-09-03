# 图表生成器模块

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Union, Optional, Tuple, Any
import os
import logging
from datetime import datetime, timedelta
import mplfinance as mpf

class ChartGenerator:
    """
    图表生成器类，用于生成各种交易相关的图表
    支持多种图表类型和输出格式
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化图表生成器
        
        参数:
            config: 配置信息，包含图表生成参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 设置默认参数
        self.config.setdefault('output_dir', 'charts')  # 图表输出目录
        self.config.setdefault('default_figsize', (12, 8))  # 默认图表大小
        self.config.setdefault('default_dpi', 100)  # 默认DPI
        self.config.setdefault('theme', 'default')  # 默认主题
        self.config.setdefault('watermark', None)  # 水印
        
        # 创建输出目录
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
        # 设置主题
        self._set_theme(self.config['theme'])
    
    def _set_theme(self, theme: str) -> None:
        """
        设置图表主题
        
        参数:
            theme: 主题名称
        """
        if theme == 'dark':
            plt.style.use('dark_background')
            self.colors = ['#ff9500', '#00b3ff', '#00f900', '#ff00e0', '#ffff00']
        elif theme == 'light':
            plt.style.use('seaborn-v0_8-whitegrid')
            self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        elif theme == 'seaborn':
            plt.style.use('seaborn-v0_8')
            self.colors = sns.color_palette('deep')
        else:  # default
            plt.style.use('default')
            self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    def _add_watermark(self, fig: plt.Figure) -> None:
        """
        添加水印到图表
        
        参数:
            fig: matplotlib图表对象
        """
        watermark = self.config.get('watermark')
        if watermark:
            fig.text(0.5, 0.5, watermark, 
                     fontsize=40, color='gray', 
                     ha='center', va='center', alpha=0.3,
                     rotation=30)
    
    def plot_price_chart(self, data: pd.DataFrame, title: str = "价格走势图", 
                        save_path: Optional[str] = None, show: bool = True,
                        additional_indicators: Optional[List[Dict]] = None) -> plt.Figure:
        """
        绘制价格走势图
        
        参数:
            data: 包含价格数据的DataFrame，必须包含'date'和'close'列，可选包含'open'、'high'、'low'、'volume'列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            additional_indicators: 额外指标列表，每个指标为一个字典，包含'name'、'column'、'color'等键
            
        返回:
            matplotlib图表对象
        """
        # 检查必要的列
        if 'date' not in data.columns or 'close' not in data.columns:
            raise ValueError("数据必须包含'date'和'close'列")
        
        # 创建图表
        fig, axes = plt.subplots(2, 1, figsize=self.config['default_figsize'], 
                                gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        
        # 绘制价格
        axes[0].plot(data['date'], data['close'], label='收盘价', color=self.colors[0])
        
        # 绘制额外指标
        if additional_indicators:
            for i, indicator in enumerate(additional_indicators):
                if indicator['column'] in data.columns:
                    color = indicator.get('color', self.colors[(i+1) % len(self.colors)])
                    axes[0].plot(data['date'], data[indicator['column']], 
                                label=indicator['name'], color=color)
        
        # 绘制成交量
        if 'volume' in data.columns:
            axes[1].bar(data['date'], data['volume'], label='成交量', color=self.colors[1], alpha=0.5)
            axes[1].set_ylabel('成交量')
        
        # 设置标题和标签
        axes[0].set_title(title)
        axes[0].set_ylabel('价格')
        axes[0].legend(loc='best')
        axes[0].grid(True)
        
        # 设置x轴格式
        date_format = mdates.DateFormatter('%Y-%m-%d')
        axes[1].xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存价格走势图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_candlestick_chart(self, data: pd.DataFrame, title: str = "K线图", 
                              save_path: Optional[str] = None, show: bool = True,
                              additional_indicators: Optional[List[Dict]] = None) -> Any:
        """
        绘制K线图
        
        参数:
            data: 包含OHLC数据的DataFrame，必须包含'date'、'open'、'high'、'low'、'close'列，可选包含'volume'列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            additional_indicators: 额外指标列表，每个指标为一个字典，包含'name'、'column'、'panel'等键
            
        返回:
            mplfinance图表对象
        """
        # 检查必要的列
        required_columns = ['date', 'open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"数据必须包含{required_columns}列")
        
        # 准备数据
        df = data.copy()
        df.set_index('date', inplace=True)
        
        # 准备附加指标
        apds = []
        if additional_indicators:
            for indicator in additional_indicators:
                if indicator['column'] in df.columns:
                    panel = indicator.get('panel', 0)
                    apds.append(mpf.make_addplot(df[indicator['column']], panel=panel, 
                                               secondary_y=indicator.get('secondary_y', False),
                                               color=indicator.get('color', 'blue'),
                                               title=indicator.get('name', indicator['column'])))
        
        # 设置样式
        style = mpf.make_mpf_style(base_mpf_style='charles', 
                                 gridstyle=':', 
                                 y_on_right=False,
                                 marketcolors=mpf.make_marketcolors(
                                     up='red', down='green',
                                     edge='inherit',
                                     wick='inherit',
                                     volume='inherit'))
        
        # 绘制K线图
        kwargs = {
            'type': 'candle',
            'style': style,
            'title': title,
            'figsize': self.config['default_figsize'],
            'volume': 'volume' in df.columns,
            'panel_ratios': (4, 1) if 'volume' in df.columns else None,
            'addplot': apds if apds else None,
            'returnfig': True
        }
        
        fig, axes = mpf.plot(df, **kwargs)
        
        # 添加水印
        self._add_watermark(fig)
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            fig.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存K线图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_indicator_chart(self, data: pd.DataFrame, indicators: List[Dict], 
                            title: str = "技术指标图", save_path: Optional[str] = None, 
                            show: bool = True) -> plt.Figure:
        """
        绘制技术指标图
        
        参数:
            data: 包含指标数据的DataFrame，必须包含'date'列和指标列
            indicators: 指标列表，每个指标为一个字典，包含'name'、'column'、'panel'、'color'等键
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            matplotlib图表对象
        """
        # 检查必要的列
        if 'date' not in data.columns:
            raise ValueError("数据必须包含'date'列")
        
        # 确定面板数量
        panels = set()
        for indicator in indicators:
            if 'column' in indicator and indicator['column'] in data.columns:
                panels.add(indicator.get('panel', 0))
        
        num_panels = max(panels) + 1 if panels else 1
        
        # 创建图表
        fig, axes = plt.subplots(num_panels, 1, figsize=self.config['default_figsize'], sharex=True)
        if num_panels == 1:
            axes = [axes]
        
        # 绘制指标
        for indicator in indicators:
            if 'column' in indicator and indicator['column'] in data.columns:
                panel = indicator.get('panel', 0)
                color = indicator.get('color', self.colors[0])
                label = indicator.get('name', indicator['column'])
                
                axes[panel].plot(data['date'], data[indicator['column']], 
                                label=label, color=color)
                
                # 添加水平线
                if 'hlines' in indicator:
                    for hline in indicator['hlines']:
                        axes[panel].axhline(y=hline['value'], color=hline.get('color', 'gray'), 
                                           linestyle=hline.get('style', '--'), 
                                           alpha=hline.get('alpha', 0.7))
                        if 'label' in hline:
                            axes[panel].text(data['date'].iloc[0], hline['value'], 
                                           hline['label'], va='center')
        
        # 设置标题和标签
        fig.suptitle(title)
        
        # 为每个面板添加图例和网格
        for i, ax in enumerate(axes):
            ax.legend(loc='best')
            ax.grid(True)
            
            # 设置y轴标签
            panel_indicators = [ind for ind in indicators if ind.get('panel', 0) == i]
            if panel_indicators:
                ax.set_ylabel(panel_indicators[0].get('name', ''))
        
        # 设置x轴格式
        date_format = mdates.DateFormatter('%Y-%m-%d')
        axes[-1].xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存技术指标图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_portfolio_performance(self, data: pd.DataFrame, benchmark_data: Optional[pd.DataFrame] = None,
                                 title: str = "投资组合表现", save_path: Optional[str] = None, 
                                 show: bool = True) -> plt.Figure:
        """
        绘制投资组合表现图
        
        参数:
            data: 包含投资组合数据的DataFrame，必须包含'date'和'equity'列
            benchmark_data: 包含基准数据的DataFrame，必须包含'date'和'close'列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            matplotlib图表对象
        """
        # 检查必要的列
        if 'date' not in data.columns or 'equity' not in data.columns:
            raise ValueError("投资组合数据必须包含'date'和'equity'列")
        
        if benchmark_data is not None and ('date' not in benchmark_data.columns or 'close' not in benchmark_data.columns):
            raise ValueError("基准数据必须包含'date'和'close'列")
        
        # 创建图表
        fig, axes = plt.subplots(2, 1, figsize=self.config['default_figsize'], 
                                gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        
        # 绘制权益曲线
        axes[0].plot(data['date'], data['equity'], label='投资组合', color=self.colors[0])
        
        # 绘制基准
        if benchmark_data is not None:
            # 将基准数据重采样到与投资组合数据相同的日期
            benchmark_resampled = pd.DataFrame()
            benchmark_resampled['date'] = data['date']
            benchmark_resampled['close'] = np.nan
            
            for i, date in enumerate(data['date']):
                idx = benchmark_data['date'].searchsorted(date)
                if idx < len(benchmark_data):
                    benchmark_resampled.loc[i, 'close'] = benchmark_data.loc[idx, 'close']
            
            # 归一化基准数据
            benchmark_resampled['normalized'] = benchmark_resampled['close'] / benchmark_resampled['close'].iloc[0] * data['equity'].iloc[0]
            
            axes[0].plot(benchmark_resampled['date'], benchmark_resampled['normalized'], 
                        label='基准', color=self.colors[1], linestyle='--')
        
        # 计算并绘制回撤
        if 'equity' in data.columns:
            # 计算回撤
            data['peak'] = data['equity'].cummax()
            data['drawdown'] = (data['equity'] - data['peak']) / data['peak'] * 100
            
            # 绘制回撤
            axes[1].fill_between(data['date'], data['drawdown'], 0, 
                                color=self.colors[2], alpha=0.3, label='回撤 (%)')
            axes[1].set_ylabel('回撤 (%)')
        
        # 设置标题和标签
        axes[0].set_title(title)
        axes[0].set_ylabel('权益')
        axes[0].legend(loc='best')
        axes[0].grid(True)
        axes[1].grid(True)
        
        # 设置x轴格式
        date_format = mdates.DateFormatter('%Y-%m-%d')
        axes[1].xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存投资组合表现图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_returns_distribution(self, returns: pd.Series, title: str = "收益分布图", 
                                save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        绘制收益分布图
        
        参数:
            returns: 收益率序列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            matplotlib图表对象
        """
        # 创建图表
        fig, ax = plt.subplots(figsize=self.config['default_figsize'])
        
        # 绘制直方图和核密度估计
        sns.histplot(returns, kde=True, ax=ax, color=self.colors[0])
        
        # 添加统计信息
        mean = returns.mean()
        std = returns.std()
        skew = returns.skew()
        kurt = returns.kurtosis()
        
        stats_text = f"均值: {mean:.4f}\n标准差: {std:.4f}\n偏度: {skew:.4f}\n峰度: {kurt:.4f}"
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
        
        # 设置标题和标签
        ax.set_title(title)
        ax.set_xlabel('收益率')
        ax.set_ylabel('频率')
        ax.grid(True)
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存收益分布图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_monthly_returns_heatmap(self, returns: pd.Series, title: str = "月度收益热图", 
                                    save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        绘制月度收益热图
        
        参数:
            returns: 带有日期索引的收益率序列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            matplotlib图表对象
        """
        # 确保索引是日期类型
        if not isinstance(returns.index, pd.DatetimeIndex):
            raise ValueError("收益率序列必须有日期索引")
        
        # 计算月度收益
        monthly_returns = returns.groupby([returns.index.year, returns.index.month]).sum()
        
        # 重塑数据为年月矩阵
        monthly_returns_matrix = monthly_returns.unstack(level=1)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.config['default_figsize'])
        
        # 绘制热图
        sns.heatmap(monthly_returns_matrix, annot=True, fmt='.2%', cmap='RdYlGn', 
                   center=0, ax=ax, cbar_kws={'label': '收益率'})
        
        # 设置标题和标签
        ax.set_title(title)
        ax.set_ylabel('年份')
        ax.set_xlabel('月份')
        
        # 设置月份标签
        month_labels = ['一月', '二月', '三月', '四月', '五月', '六月', 
                       '七月', '八月', '九月', '十月', '十一月', '十二月']
        ax.set_xticklabels(month_labels, rotation=45)
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存月度收益热图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_correlation_matrix(self, data: pd.DataFrame, title: str = "相关性矩阵", 
                              save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        绘制相关性矩阵
        
        参数:
            data: 包含多个资产或指标的DataFrame
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            matplotlib图表对象
        """
        # 计算相关性矩阵
        corr_matrix = data.corr()
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.config['default_figsize'])
        
        # 绘制热图
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, cmap='coolwarm', annot=True, 
                   fmt='.2f', square=True, linewidths=.5, ax=ax, 
                   cbar_kws={'label': '相关系数'})
        
        # 设置标题
        ax.set_title(title)
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存相关性矩阵到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig
    
    def plot_interactive_candlestick(self, data: pd.DataFrame, title: str = "交互式K线图", 
                                    save_path: Optional[str] = None, show: bool = True) -> go.Figure:
        """
        绘制交互式K线图
        
        参数:
            data: 包含OHLC数据的DataFrame，必须包含'date'、'open'、'high'、'low'、'close'列，可选包含'volume'列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            plotly图表对象
        """
        # 检查必要的列
        required_columns = ['date', 'open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"数据必须包含{required_columns}列")
        
        # 创建子图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.02, 
                           row_heights=[0.8, 0.2])
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=data['date'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='K线'
        ), row=1, col=1)
        
        # 添加成交量
        if 'volume' in data.columns:
            fig.add_trace(go.Bar(
                x=data['date'],
                y=data['volume'],
                name='成交量',
                marker_color='rgba(0, 0, 255, 0.5)'
            ), row=2, col=1)
        
        # 更新布局
        fig.update_layout(
            title=title,
            xaxis_title='日期',
            yaxis_title='价格',
            xaxis_rangeslider_visible=False,
            template='plotly_white'
        )
        
        # 更新Y轴标题
        fig.update_yaxes(title_text='价格', row=1, col=1)
        if 'volume' in data.columns:
            fig.update_yaxes(title_text='成交量', row=2, col=1)
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            fig.write_html(full_path)
            self.logger.info(f"已保存交互式K线图到: {full_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        return fig
    
    def plot_interactive_portfolio_performance(self, data: pd.DataFrame, 
                                             benchmark_data: Optional[pd.DataFrame] = None,
                                             title: str = "交互式投资组合表现", 
                                             save_path: Optional[str] = None, 
                                             show: bool = True) -> go.Figure:
        """
        绘制交互式投资组合表现图
        
        参数:
            data: 包含投资组合数据的DataFrame，必须包含'date'和'equity'列
            benchmark_data: 包含基准数据的DataFrame，必须包含'date'和'close'列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            plotly图表对象
        """
        # 检查必要的列
        if 'date' not in data.columns or 'equity' not in data.columns:
            raise ValueError("投资组合数据必须包含'date'和'equity'列")
        
        if benchmark_data is not None and ('date' not in benchmark_data.columns or 'close' not in benchmark_data.columns):
            raise ValueError("基准数据必须包含'date'和'close'列")
        
        # 创建子图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.02, 
                           row_heights=[0.7, 0.3])
        
        # 添加权益曲线
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data['equity'],
            mode='lines',
            name='投资组合',
            line=dict(color='blue')
        ), row=1, col=1)
        
        # 添加基准
        if benchmark_data is not None:
            # 将基准数据重采样到与投资组合数据相同的日期
            benchmark_resampled = pd.DataFrame()
            benchmark_resampled['date'] = data['date']
            benchmark_resampled['close'] = np.nan
            
            for i, date in enumerate(data['date']):
                idx = benchmark_data['date'].searchsorted(date)
                if idx < len(benchmark_data):
                    benchmark_resampled.loc[i, 'close'] = benchmark_data.loc[idx, 'close']
            
            # 归一化基准数据
            benchmark_resampled['normalized'] = benchmark_resampled['close'] / benchmark_resampled['close'].iloc[0] * data['equity'].iloc[0]
            
            fig.add_trace(go.Scatter(
                x=benchmark_resampled['date'],
                y=benchmark_resampled['normalized'],
                mode='lines',
                name='基准',
                line=dict(color='red', dash='dash')
            ), row=1, col=1)
        
        # 计算并添加回撤
        if 'equity' in data.columns:
            # 计算回撤
            data['peak'] = data['equity'].cummax()
            data['drawdown'] = (data['equity'] - data['peak']) / data['peak'] * 100
            
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['drawdown'],
                mode='lines',
                name='回撤 (%)',
                fill='tozeroy',
                line=dict(color='green')
            ), row=2, col=1)
        
        # 更新布局
        fig.update_layout(
            title=title,
            xaxis_title='日期',
            template='plotly_white'
        )
        
        # 更新Y轴标题
        fig.update_yaxes(title_text='权益', row=1, col=1)
        fig.update_yaxes(title_text='回撤 (%)', row=2, col=1)
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            fig.write_html(full_path)
            self.logger.info(f"已保存交互式投资组合表现图到: {full_path}")
        
        # 显示图表
        if show:
            fig.show()
        
        return fig
    
    def plot_trade_analysis(self, trades: pd.DataFrame, title: str = "交易分析", 
                          save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        绘制交易分析图
        
        参数:
            trades: 包含交易数据的DataFrame，必须包含'entry_date'、'exit_date'、'profit'、'type'列
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show: 是否显示图表
            
        返回:
            matplotlib图表对象
        """
        # 检查必要的列
        required_columns = ['entry_date', 'exit_date', 'profit', 'type']
        for col in required_columns:
            if col not in trades.columns:
                raise ValueError(f"交易数据必须包含{required_columns}列")
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=self.config['default_figsize'])
        
        # 1. 绘制盈亏分布
        axes[0, 0].hist(trades['profit'], bins=20, color=self.colors[0], alpha=0.7)
        axes[0, 0].axvline(x=0, color='black', linestyle='--')
        axes[0, 0].set_title('盈亏分布')
        axes[0, 0].set_xlabel('盈亏')
        axes[0, 0].set_ylabel('频率')
        axes[0, 0].grid(True)
        
        # 2. 绘制累计盈亏曲线
        trades_sorted = trades.sort_values('exit_date')
        trades_sorted['cumulative_profit'] = trades_sorted['profit'].cumsum()
        
        axes[0, 1].plot(trades_sorted['exit_date'], trades_sorted['cumulative_profit'], 
                       color=self.colors[1])
        axes[0, 1].set_title('累计盈亏曲线')
        axes[0, 1].set_xlabel('日期')
        axes[0, 1].set_ylabel('累计盈亏')
        axes[0, 1].grid(True)
        
        # 3. 绘制多空盈亏对比
        if 'type' in trades.columns:
            long_trades = trades[trades['type'] == 'long']
            short_trades = trades[trades['type'] == 'short']
            
            labels = ['多头', '空头']
            profits = [long_trades['profit'].sum(), short_trades['profit'].sum()]
            counts = [len(long_trades), len(short_trades)]
            
            axes[1, 0].bar(labels, profits, color=[self.colors[2], self.colors[3]])
            axes[1, 0].set_title('多空盈亏对比')
            axes[1, 0].set_ylabel('总盈亏')
            axes[1, 0].grid(True)
            
            # 添加交易次数标签
            for i, count in enumerate(counts):
                axes[1, 0].text(i, profits[i], f"n={count}", ha='center', va='bottom')
        
        # 4. 绘制持仓时间分布
        if 'entry_date' in trades.columns and 'exit_date' in trades.columns:
            # 计算持仓时间（天）
            trades['holding_period'] = (trades['exit_date'] - trades['entry_date']).dt.days
            
            axes[1, 1].hist(trades['holding_period'], bins=20, color=self.colors[4], alpha=0.7)
            axes[1, 1].set_title('持仓时间分布')
            axes[1, 1].set_xlabel('持仓时间（天）')
            axes[1, 1].set_ylabel('频率')
            axes[1, 1].grid(True)
        
        # 设置总标题
        fig.suptitle(title, fontsize=16)
        
        # 添加水印
        self._add_watermark(fig)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # 保存图表
        if save_path:
            full_path = os.path.join(self.config['output_dir'], save_path)
            plt.savefig(full_path, dpi=self.config['default_dpi'])
            self.logger.info(f"已保存交易分析图到: {full_path}")
        
        # 显示图表
        if show:
            plt.show()
        
        return fig