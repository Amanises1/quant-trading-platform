from flask import Flask, jsonify, request
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import logging
import os
import sys
import time
import io
import base64
import tempfile

# 设置matplotlib使用非交互式后端
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mplfinance as mpf

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入监控模块
try:
    from models.monitor import (
        position_manager,
        execution_engine,
        trade_history_manager,
        risk_manager,
        notification_manager
    )
except ImportError:
    # 如果导入失败，尝试使用相对导入
    import sys
    import os
    # 确保当前目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入ChartGenerator类
try:
    from src.models.visualization.chart_generator import ChartGenerator
except ImportError:
    # 如果导入失败，尝试使用相对导入
    # 动态加载ChartGenerator类
    chart_generator_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'visualization', 'chart_generator.py')
    import importlib.util
    spec = importlib.util.spec_from_file_location("chart_generator", chart_generator_path)
    chart_generator_module = importlib.util.module_from_spec(spec)
    sys.modules["chart_generator"] = chart_generator_module
    spec.loader.exec_module(chart_generator_module)
    ChartGenerator = chart_generator_module.ChartGenerator

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置ChartGenerator
chart_config = {
    'output_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output'),
    'default_figsize': (12, 8),
    'default_dpi': 300,
    'theme': 'light',
    'watermark_text': 'Quant Trading Platform',
    'watermark_alpha': 0.1
}

# 创建ChartGenerator实例
chart_generator = ChartGenerator(config=chart_config)

# 生成模拟股票数据的函数
def generate_mock_stock_data(symbol, start_date, end_date):
    # 将字符串日期转换为datetime对象
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 计算日期差
    delta = end - start
    days = delta.days + 1
    
    # 生成模拟数据
    data = []
    
    # 随机初始价格
    base_price = random.uniform(50, 200)
    
    for i in range(days):
        # 跳过周末
        current_date = start + timedelta(days=i)
        if current_date.weekday() >= 5:  # 5和6表示周六和周日
            continue
        
        # 模拟价格波动
        change_percent = random.uniform(-2, 2)  # 每日涨跌幅范围-2%到+2%
        change_price = base_price * (change_percent / 100)
        
        open_price = base_price
        close_price = base_price + change_price
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.5) / 100)
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.5) / 100)
        volume = random.randint(1000000, 10000000)
        
        # 更新下一天的基准价格
        base_price = close_price
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    return data

# 生成模拟投资组合数据
def generate_mock_portfolio_data(start_date, end_date):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 生成日期范围
    date_range = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            date_range.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # 生成权益曲线，从100000开始
    initial_equity = 100000
    equity = [initial_equity]
    
    for i in range(1, len(date_range)):
        # 每日收益随机波动
        daily_return = random.uniform(-0.02, 0.025)
        new_equity = equity[-1] * (1 + daily_return)
        equity.append(new_equity)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'date': pd.to_datetime(date_range),
        'equity': equity
    })
    
    return df

# 生成模拟基准数据
def generate_mock_benchmark_data(start_date, end_date):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 生成日期范围
    date_range = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            date_range.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # 生成基准指数，从1000开始
    initial_value = 1000
    values = [initial_value]
    
    for i in range(1, len(date_range)):
        # 基准指数波动较小
        daily_change = random.uniform(-0.015, 0.015)
        new_value = values[-1] * (1 + daily_change)
        values.append(new_value)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'date': pd.to_datetime(date_range),
        'close': values
    })
    
    return df

# 生成模拟交易数据
def generate_mock_trade_data(start_date, end_date, n_trades=50):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 生成随机交易日期
    all_dates = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            all_dates.append(current)
        current += timedelta(days=1)
    
    # 随机选择交易日期
    trade_dates = random.sample(all_dates, min(n_trades * 2, len(all_dates)))
    trade_dates.sort()
    
    # 生成交易数据
    trades = []
    symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA']
    
    for i in range(0, len(trade_dates), 2):
        entry_date = trade_dates[i]
        exit_date = trade_dates[i+1] if i+1 < len(trade_dates) else trade_dates[i] + timedelta(days=random.randint(1, 30))
        
        # 确保退出日期不超过结束日期
        if exit_date > end:
            exit_date = end
        
        # 生成随机盈亏
        profit = random.uniform(-5000, 10000)
        
        # 生成交易类型
        trade_type = 'long' if random.random() > 0.3 else 'short'
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': exit_date,
            'profit': profit,
            'type': trade_type,
            'symbol': random.choice(symbols),
            'quantity': random.randint(10, 100)
        })
    
    # 创建DataFrame
    df = pd.DataFrame(trades)
    
    return df

# 生成因子贡献度数据
def generate_mock_factor_contribution_data():
    # 模拟因子列表
    factors = ['价值因子', '成长因子', '动量因子', '波动率因子', '规模因子', '质量因子', '流动性因子']
    
    # 模拟因子贡献度
    contributions = np.random.uniform(-2, 3, len(factors))
    
    # 确保总和不为零
    if np.sum(contributions) < 0.5:
        contributions += (0.5 - np.sum(contributions)) / len(factors)
    
    df = pd.DataFrame({
        'Factor': factors,
        'Contribution': contributions
    })
    
    return df

# 生成资金流向桑基图数据
def generate_mock_sankey_data():
    # 模拟资金流向数据
    sources = ['股票A', '股票B', '股票C', '债券', '现金', '基金A', '基金B']
    targets = ['股票A', '股票B', '股票C', '债券', '现金', '基金A', '基金B', '银行存款', '其他投资']
    
    # 生成链接数据
    links = []
    for _ in range(15):
        source = random.choice(sources)
        target = random.choice(targets)
        if source != target:
            value = random.randint(100, 1000)
            links.append({
                'source': sources.index(source) if source in sources else len(sources) + targets.index(source),
                'target': sources.index(target) if target in sources else len(sources) + targets.index(target),
                'value': value
            })
    
    # 合并节点
    nodes = sources + [t for t in targets if t not in sources]
    
    return {
        'nodes': nodes,
        'links': links
    }

# 生成市场情绪热力图数据
def generate_mock_sentiment_data():
    # 模拟行业列表
    industries = ['金融', '科技', '消费', '医药', '能源', '材料', '工业', '房地产']
    
    # 模拟时间周期（最近12个月）
    today = datetime.now()
    months = []
    for i in range(11, -1, -1):
        month = today - timedelta(days=i*30)
        months.append(month.strftime('%Y-%m'))
    
    # 生成情绪数据
    sentiment_data = np.random.normal(0, 0.5, (len(industries), len(months)))
    
    # 创建DataFrame
    df = pd.DataFrame(sentiment_data, index=industries, columns=months)
    
    return df

# 生成风险数据
def generate_mock_risk_data():
    # 模拟风险数据
    risk_data = {
        'status': '低风险',
        'marginRatio': round(random.uniform(150, 200), 2),
        'maxDrawdown': round(random.uniform(-15, -5), 2),
        'sharpeRatio': round(random.uniform(1.0, 2.5), 2),
        'volatility': round(random.uniform(10, 20), 2),
        'positionRatio': round(random.uniform(50, 80), 2),
        'dailyProfit': round(random.uniform(-3, 3), 2)
    }
    
    # 根据保证金比例设置风险状态
    if risk_data['marginRatio'] < 100:
        risk_data['status'] = '高风险'
    elif risk_data['marginRatio'] < 130:
        risk_data['status'] = '中风险'
    
    # 模拟风险阈值
    thresholds = {
        'marginWarning': 130,
        'marginLiquidation': 100,
        'positionLimit': 90,
        'maxDrawdownDaily': 5
    }
    
    return risk_data, thresholds

# 生成风险趋势数据
def generate_mock_risk_trend_data(start_date, end_date):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 生成日期范围
    date_range = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            date_range.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    n_days = len(date_range)
    
    # 生成模拟的风险指标趋势
    margin_ratio = 180 + np.cumsum(np.random.normal(0, 2, n_days))
    margin_ratio = np.maximum(100, margin_ratio)  # 确保不低于100%
    
    volatility = 15 + np.cumsum(np.random.normal(0, 0.1, n_days))
    volatility = np.maximum(5, volatility)  # 确保有意义的波动性
    
    sharpe = 1.8 + np.cumsum(np.random.normal(0, 0.02, n_days))
    sharpe = np.maximum(0.5, sharpe)  # 确保Sharpe比率为正
    
    df = pd.DataFrame({
        'date': date_range,
        'Margin_Ratio': margin_ratio,
        'Volatility': volatility,
        'Sharpe_Ratio': sharpe
    })
    
    return df

# 模拟通知数据
notifications_db = [
    {
        'id': 1,
        'title': '交易执行成功',
        'message': '买入贵州茅台(600519) 100股，价格1680.00元',
        'type': 'trade',
        'timestamp': datetime.now().timestamp() - 300,
        'read': False
    },
    {
        'id': 2,
        'title': '保证金预警',
        'message': '您的保证金比例已降至135%，接近预警线，请及时补充保证金',
        'type': 'risk',
        'timestamp': datetime.now().timestamp() - 900,
        'read': False
    },
    {
        'id': 3,
        'title': '账户余额不足',
        'message': '您的账户余额不足，部分委托可能无法执行',
        'type': 'balance',
        'timestamp': datetime.now().timestamp() - 1800,
        'read': True
    },
    {
        'id': 4,
        'title': '系统维护通知',
        'message': '系统将于2023-12-31 22:00-24:00进行例行维护，请提前做好准备',
        'type': 'system',
        'timestamp': datetime.now().timestamp() - 3600,
        'read': True
    }
]

# 通知ID计数器
next_notification_id = 5

# 简单的健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# 数据加载接口
@app.route('/api/data/load', methods=['POST'])
def load_data():
    try:
        data = request.json
        symbol = data.get('symbol', '000001')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2023-12-31')
        
        # 生成模拟数据
        mock_data = generate_mock_stock_data(symbol, start_date, end_date)
        
        return jsonify({
            'success': True,
            'message': f'成功加载股票 {symbol} 的数据',
            'data': mock_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 数据采集接口
@app.route('/api/data/collect', methods=['POST'])
def collect_data():
    try:
        data = request.json
        symbol = data.get('symbol', '000001')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2023-12-31')
        interval = data.get('interval', '1d')
        
        # 模拟采集延迟
        time.sleep(0.5)  # 模拟网络请求延迟
        
        # 生成模拟数据
        mock_data = generate_mock_stock_data(symbol, start_date, end_date)
        
        return jsonify({
            'success': True,
            'message': f'成功采集股票 {symbol} 的数据',
            'data': mock_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 可视化生成接口
@app.route('/api/visualization/generate', methods=['POST'])
def generate_visualization():
    try:
        # 获取请求数据
        data = request.json
        chart_type = data.get('chart_type', 'price_chart')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2023-12-31')
        config = data.get('config', {})
        
        logger.info(f'Generating {chart_type} visualization for period {start_date} to {end_date}')
        
        # 根据图表类型生成数据和图表
        if chart_type == 'price_chart':
            # 生成股票数据
            mock_data = generate_mock_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            
            # 创建图表
            fig = chart_generator.plot_price_chart(
                data=df,
                title=config.get('title', '股票价格走势图'),
                show=False
            )
            
            # 转换为base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            chart_url = f'data:image/png;base64,{image_base64}'
            
            # 计算统计数据
            stats = calculate_price_stats(df)
            
            return jsonify({
                'success': True,
                'chart_url': chart_url,
                'stats': stats
            })
            
        elif chart_type == 'candlestick_chart':
            # 生成股票数据
            mock_data = generate_mock_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            
            # 创建交互式K线图
            fig = chart_generator.plot_interactive_candlestick(
                data=df,
                title=config.get('title', '交互式K线图'),
                show=False
            )
            
            # 转换为HTML
            chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 计算统计数据
            stats = calculate_price_stats(df)
            
            return jsonify({
                'success': True,
                'chart_html': chart_html,
                'stats': stats
            })
            
        elif chart_type == 'portfolio_performance':
            # 生成投资组合数据
            portfolio_df = generate_mock_portfolio_data(start_date, end_date)
            benchmark_df = generate_mock_benchmark_data(start_date, end_date)
            
            # 创建交互式投资组合表现图
            fig = chart_generator.plot_interactive_portfolio_performance(
                data=portfolio_df,
                benchmark_data=benchmark_df if config.get('showBenchmark', True) else None,
                title=config.get('title', '交互式投资组合表现'),
                show=False
            )
            
            # 转换为HTML
            chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            # 计算统计数据
            stats = calculate_portfolio_stats(portfolio_df)
            
            return jsonify({
                'success': True,
                'chart_html': chart_html,
                'stats': stats
            })
            
        elif chart_type == 'correlation_matrix':
            # 生成多只股票数据
            symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA']
            correlation_data = {}
            
            for symbol in symbols:
                mock_data = generate_mock_stock_data(symbol, start_date, end_date)
                df = pd.DataFrame(mock_data)
                correlation_data[symbol] = df['close']
            
            # 创建相关性矩阵DataFrame
            corr_df = pd.DataFrame(correlation_data)
            
            # 创建相关性矩阵图表
            fig = chart_generator.plot_correlation_matrix(
                data=corr_df,
                title=config.get('title', '相关性矩阵'),
                show=False
            )
            
            # 转换为base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            chart_url = f'data:image/png;base64,{image_base64}'
            
            return jsonify({
                'success': True,
                'chart_url': chart_url
            })
            
        elif chart_type == 'returns_distribution':
            # 生成股票数据
            mock_data = generate_mock_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            
            # 计算收益率
            df['returns'] = df['close'].pct_change()
            
            # 创建收益分布图
            fig = chart_generator.plot_returns_distribution(
                data=df['returns'].dropna(),
                title=config.get('title', '收益分布'),
                show=False
            )
            
            # 转换为base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            chart_url = f'data:image/png;base64,{image_base64}'
            
            # 计算统计数据
            stats = calculate_returns_stats(df['returns'].dropna())
            
            return jsonify({
                'success': True,
                'chart_url': chart_url,
                'stats': stats
            })
            
        elif chart_type == 'monthly_returns_heatmap':
            # 生成股票数据
            mock_data = generate_mock_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            
            # 计算月度收益率
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            monthly_returns = df['close'].resample('M').ffill().pct_change()
            monthly_returns = monthly_returns.dropna()
            
            # 转换为DataFrame
            monthly_df = pd.DataFrame({
                'date': monthly_returns.index,
                'returns': monthly_returns.values
            })
            
            # 创建月度收益热图
            fig = chart_generator.plot_monthly_returns_heatmap(
                data=monthly_df,
                title=config.get('title', '月度收益热图'),
                show=False
            )
            
            # 转换为base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            chart_url = f'data:image/png;base64,{image_base64}'
            
            return jsonify({
                'success': True,
                'chart_url': chart_url
            })
            
        elif chart_type == 'trade_analysis':
            # 生成交易数据
            df = generate_mock_trade_data(start_date, end_date)
            
            # 创建交易分析图表
            fig = chart_generator.plot_trade_analysis(
                trades=df,
                title=config.get('title', '交易分析'),
                show=False
            )
            
            # 转换为base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            chart_url = f'data:image/png;base64,{image_base64}'
            
            # 计算统计数据
            stats = calculate_trade_stats(df)
            
            return jsonify({
                'success': True,
                'chart_url': chart_url,
                'stats': stats
            })
            
        elif chart_type == 'factor_contribution':
            # 生成因子贡献度数据
            df = generate_mock_factor_contribution_data()
            
            # 创建瀑布图
            fig = go.Figure()
            fig.add_trace(go.Waterfall(
                orientation = "v",
                measure = ["relative"] * len(df),
                x = df['Factor'],
                textposition = "outside",
                text = [f"{val:.2f}" for val in df['Contribution']],
                y = df['Contribution'],
                connector = {"line": {"color": "rgb(63, 63, 63)"}}
            ))
            
            fig.update_layout(
                title=config.get('title', '因子收益率贡献度瀑布图'),
                showlegend=False,
                template='plotly_white',
                height=600
            )
            
            # 转换为HTML
            chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            return jsonify({
                'success': True,
                'chart_html': chart_html
            })
            
        elif chart_type == 'sankey_diagram':
            # 生成桑基图数据
            sankey_data = generate_mock_sankey_data()
            
            # 创建桑基图
            fig = go.Figure(data=[go.Sankey(
                node = dict(
                    pad = 15,
                    thickness = 20,
                    line = dict(color = "black", width = 0.5),
                    label = sankey_data['nodes'],
                    color = [f'rgba({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)},0.8)' for _ in range(len(sankey_data['nodes']))]
                ),
                link = dict(
                    source = [link['source'] for link in sankey_data['links']],
                    target = [link['target'] for link in sankey_data['links']],
                    value = [link['value'] for link in sankey_data['links']],
                    color = [f'rgba({random.randint(100,200)},{random.randint(100,200)},{random.randint(100,200)},0.4)' for _ in range(len(sankey_data['links']))]
                )
            )])
            
            fig.update_layout(
                title=config.get('title', '资金流向桑基图'),
                font=dict(size=10),
                height=700
            )
            
            # 转换为HTML
            chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            return jsonify({
                'success': True,
                'chart_html': chart_html
            })
            
        elif chart_type == 'sentiment_heatmap':
            # 生成市场情绪数据
            df = generate_mock_sentiment_data()
            
            # 创建热力图
            fig = go.Figure(data=go.Heatmap(
                z=df.values,
                x=df.columns,
                y=df.index,
                colorscale='RdBu',
                zmin=-2,
                zmax=2,
                colorbar=dict(title='情绪值')
            ))
            
            fig.update_layout(
                title=config.get('title', '市场情绪变化热力图'),
                xaxis_title='时间',
                yaxis_title='行业',
                height=600
            )
            
            # 转换为HTML
            chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            return jsonify({
                'success': True,
                'chart_html': chart_html
            })
            
        else:
            return jsonify({
                'success': False,
                'message': f'Unsupported chart type: {chart_type}'
            }), 400
            
    except Exception as e:
        logger.error(f'Error generating visualization: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 图表下载接口
@app.route('/api/visualization/download', methods=['POST'])
def download_visualization():
    try:
        # 获取请求数据
        data = request.json
        if not data:
            # 尝试从form参数中获取
            params = request.form.get('params')
            if params:
                import json
                data = json.loads(params)
            else:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
        
        chart_type = data.get('chart_type', 'price_chart')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2023-12-31')
        config = data.get('config', {})
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            file_path = tmp_file.name
        
        # 生成图表并保存
        if chart_type == 'price_chart':
            mock_data = generate_mock_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            chart_generator.plot_price_chart(
                data=df,
                title=config.get('title', '股票价格走势图'),
                save_path=file_path,
                show=False
            )
        elif chart_type == 'candlestick_chart':
            # K线图使用HTML格式
            mock_data = generate_mock_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            fig = chart_generator.plot_interactive_candlestick(
                data=df,
                title=config.get('title', '交互式K线图'),
                show=False
            )
            file_path = file_path.replace('.png', '.html')
            fig.write_html(file_path)
        elif chart_type == 'portfolio_performance':
            # 投资组合表现使用HTML格式
            portfolio_df = generate_mock_portfolio_data(start_date, end_date)
            benchmark_df = generate_mock_benchmark_data(start_date, end_date)
            fig = chart_generator.plot_interactive_portfolio_performance(
                data=portfolio_df,
                benchmark_data=benchmark_df if config.get('showBenchmark', True) else None,
                title=config.get('title', '交互式投资组合表现'),
                show=False
            )
            file_path = file_path.replace('.png', '.html')
            fig.write_html(file_path)
        else:
            # 其他图表类型使用PNG格式
            if chart_type == 'correlation_matrix':
                symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA']
                correlation_data = {}
                for symbol in symbols:
                    mock_data = generate_mock_stock_data(symbol, start_date, end_date)
                    df = pd.DataFrame(mock_data)
                    correlation_data[symbol] = df['close']
                corr_df = pd.DataFrame(correlation_data)
                chart_generator.plot_correlation_matrix(
                    data=corr_df,
                    title=config.get('title', '相关性矩阵'),
                    save_path=file_path,
                    show=False
                )
            elif chart_type == 'returns_distribution':
                mock_data = generate_mock_stock_data('000001', start_date, end_date)
                df = pd.DataFrame(mock_data)
                df['returns'] = df['close'].pct_change()
                chart_generator.plot_returns_distribution(
                    data=df['returns'].dropna(),
                    title=config.get('title', '收益分布'),
                    save_path=file_path,
                    show=False
                )
            elif chart_type == 'monthly_returns_heatmap':
                mock_data = generate_mock_stock_data('000001', start_date, end_date)
                df = pd.DataFrame(mock_data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                monthly_returns = df['close'].resample('M').ffill().pct_change()
                monthly_returns = monthly_returns.dropna()
                monthly_df = pd.DataFrame({
                    'date': monthly_returns.index,
                    'returns': monthly_returns.values
                })
                chart_generator.plot_monthly_returns_heatmap(
                    data=monthly_df,
                    title=config.get('title', '月度收益热图'),
                    save_path=file_path,
                    show=False
                )
            elif chart_type == 'trade_analysis':
                df = generate_mock_trade_data(start_date, end_date)
                chart_generator.plot_trade_analysis(
                    trades=df,
                    title=config.get('title', '交易分析'),
                    save_path=file_path,
                    show=False
                )
        
        # 发送文件
        filename = f'chart_{chart_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}{os.path.splitext(file_path)[1]}'
        
        # 读取文件内容并删除临时文件
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 删除临时文件
        try:
            os.unlink(file_path)
        except:
            pass
        
        # 创建响应
        from flask import make_response
        response = make_response(file_content)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        # 设置MIME类型
        if file_path.endswith('.html'):
            response.headers['Content-Type'] = 'text/html'
        else:
            response.headers['Content-Type'] = 'image/png'
        
        return response
        
    except Exception as e:
        logger.error(f'Error downloading visualization: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 计算价格统计数据
def calculate_price_stats(df):
    stats = [
        {
            'name': '起始价格',
            'value': f"¥{df['open'].iloc[0]:.2f}",
            'description': '时间段开始时的开盘价'
        },
        {
            'name': '结束价格',
            'value': f"¥{df['close'].iloc[-1]:.2f}",
            'description': '时间段结束时的收盘价'
        },
        {
            'name': '最高价',
            'value': f"¥{df['high'].max():.2f}",
            'description': '时间段内的最高价格'
        },
        {
            'name': '最低价',
            'value': f"¥{df['low'].min():.2f}",
            'description': '时间段内的最低价格'
        },
        {
            'name': '价格变化',
            'value': f"{(df['close'].iloc[-1] - df['open'].iloc[0]) / df['open'].iloc[0] * 100:.2f}%",
            'description': '价格总体变化百分比'
        }
    ]
    return stats

# 计算投资组合统计数据
def calculate_portfolio_stats(df):
    # 计算总收益
    total_return = (df['equity'].iloc[-1] - df['equity'].iloc[0]) / df['equity'].iloc[0] * 100
    
    # 计算最大回撤
    df['peak'] = df['equity'].cummax()
    df['drawdown'] = (df['equity'] - df['peak']) / df['peak'] * 100
    max_drawdown = df['drawdown'].min()
    
    stats = [
        {
            'name': '起始权益',
            'value': f"¥{df['equity'].iloc[0]:.2f}",
            'description': '初始投资金额'
        },
        {
            'name': '结束权益',
            'value': f"¥{df['equity'].iloc[-1]:.2f}",
            'description': '最终投资金额'
        },
        {
            'name': '总收益率',
            'value': f"{total_return:.2f}%",
            'description': '投资组合总体收益率'
        },
        {
            'name': '最大回撤',
            'value': f"{max_drawdown:.2f}%",
            'description': '投资组合最大亏损百分比'
        }
    ]
    return stats

# 计算收益率统计数据
def calculate_returns_stats(returns):
    stats = [
        {
            'name': '平均日收益',
            'value': f"{returns.mean() * 100:.4f}%",
            'description': '平均每日收益率'
        },
        {
            'name': '收益率标准差',
            'value': f"{returns.std() * 100:.4f}%",
            'description': '收益率波动性'
        },
        {
            'name': '最大单日收益',
            'value': f"{returns.max() * 100:.2f}%",
            'description': '最大的单日涨幅'
        },
        {
            'name': '最大单日亏损',
            'value': f"{returns.min() * 100:.2f}%",
            'description': '最大的单日跌幅'
        }
    ]
    return stats

# 计算交易统计数据
def calculate_trade_stats(df):
    # 计算盈亏交易数量
    winning_trades = df[df['profit'] > 0]
    losing_trades = df[df['profit'] <= 0]
    
    # 计算胜率
    win_rate = len(winning_trades) / len(df) * 100 if len(df) > 0 else 0
    
    # 计算平均盈亏
    avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['profit'].mean() if len(losing_trades) > 0 else 0
    
    # 计算总盈亏
    total_profit = df['profit'].sum()
    
    stats = [
        {
            'name': '总交易次数',
            'value': f"{len(df)}",
            'description': '交易总次数'
        },
        {
            'name': '盈利交易',
            'value': f"{len(winning_trades)}",
            'description': '盈利的交易数量'
        },
        {
            'name': '亏损交易',
            'value': f"{len(losing_trades)}",
            'description': '亏损的交易数量'
        },
        {
            'name': '胜率',
            'value': f"{win_rate:.2f}%",
            'description': '盈利交易占比'
        },
        {
            'name': '平均盈利',
            'value': f"¥{avg_win:.2f}",
            'description': '盈利交易的平均收益'
        },
        {
            'name': '平均亏损',
            'value': f"¥{avg_loss:.2f}",
            'description': '亏损交易的平均损失'
        },
        {
            'name': '总盈亏',
            'value': f"¥{total_profit:.2f}",
            'description': '所有交易的总盈亏'
        }
    ]
    return stats

# 风控数据API接口
@app.route('/api/risk/data', methods=['GET'])
def get_risk_data():
    try:
        # 生成风险数据
        risk_data, thresholds = generate_mock_risk_data()
        
        return jsonify({
            'success': True,
            'riskData': risk_data,
            'thresholds': thresholds
        })
    except Exception as e:
        logger.error(f'Error getting risk data: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 风控趋势数据API接口
@app.route('/api/risk/trend', methods=['GET'])
def get_risk_trend():
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', '2023-01-01')
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # 生成风险趋势数据
        df = generate_mock_risk_trend_data(start_date, end_date)
        
        # 转换为JSON格式
        trend_data = {
            'dates': df['date'].tolist(),
            'marginRatio': df['Margin_Ratio'].tolist(),
            'volatility': df['Volatility'].tolist(),
            'sharpeRatio': df['Sharpe_Ratio'].tolist()
        }
        
        return jsonify({
            'success': True,
            'trendData': trend_data
        })
    except Exception as e:
        logger.error(f'Error getting risk trend data: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 风控阈值设置API接口
@app.route('/api/risk/set_thresholds', methods=['POST'])
def set_risk_thresholds():
    try:
        data = request.json
        new_thresholds = data.get('thresholds', {})
        
        # 在实际应用中，这里应该保存新的阈值到数据库
        # 这里仅做模拟响应
        return jsonify({
            'success': True,
            'message': '阈值设置成功',
            'thresholds': new_thresholds
        })
    except Exception as e:
        logger.error(f'Error setting risk thresholds: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 获取所有通知API接口
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        # 获取查询参数
        type_filter = request.args.get('type')
        read_status = request.args.get('read')
        
        # 过滤通知
        filtered_notifications = notifications_db.copy()
        
        if type_filter:
            filtered_notifications = [n for n in filtered_notifications if n['type'] == type_filter]
        
        if read_status is not None:
            read_status_bool = read_status.lower() == 'true'
            filtered_notifications = [n for n in filtered_notifications if n['read'] == read_status_bool]
        
        # 按时间戳排序（最新的在前）
        filtered_notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'notifications': filtered_notifications,
            'unreadCount': len([n for n in notifications_db if not n['read']])
        })
    except Exception as e:
        logger.error(f'Error getting notifications: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 标记通知为已读API接口
@app.route('/api/notifications/read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    try:
        # 查找通知
        for notification in notifications_db:
            if notification['id'] == notification_id:
                notification['read'] = True
                return jsonify({
                    'success': True,
                    'message': '通知已标记为已读',
                    'notification': notification
                })
        
        # 如果找不到通知
        return jsonify({
            'success': False,
            'message': '通知不存在'
        }), 404
    except Exception as e:
        logger.error(f'Error marking notification as read: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 批量标记通知为已读API接口
@app.route('/api/notifications/read_all', methods=['POST'])
def mark_all_notifications_read():
    try:
        # 标记所有通知为已读
        for notification in notifications_db:
            notification['read'] = True
        
        return jsonify({
            'success': True,
            'message': '所有通知已标记为已读'
        })
    except Exception as e:
        logger.error(f'Error marking all notifications as read: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 删除通知API接口
@app.route('/api/notifications/delete/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    try:
        # 查找并删除通知
        for i, notification in enumerate(notifications_db):
            if notification['id'] == notification_id:
                deleted_notification = notifications_db.pop(i)
                return jsonify({
                    'success': True,
                    'message': '通知已删除',
                    'notification': deleted_notification
                })
        
        # 如果找不到通知
        return jsonify({
            'success': False,
            'message': '通知不存在'
        }), 404
    except Exception as e:
        logger.error(f'Error deleting notification: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 持仓管理API
@app.route('/api/positions', methods=['GET'])
def get_positions():
    try:
        account_id = request.args.get('account_id', 'default')
        positions = position_manager.get_positions(account_id)
        return jsonify({'positions': positions})
    except Exception as e:
        logger.error(f'Error getting positions: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/positions/update', methods=['POST'])
def update_position():
    try:
        data = request.json
        result = position_manager.update_position(
            account_id=data.get('account_id', 'default'),
            symbol=data.get('symbol'),
            quantity=data.get('quantity'),
            price=data.get('price')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f'Error updating position: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/positions/risk', methods=['GET'])
def get_position_risk():
    try:
        account_id = request.args.get('account_id', 'default')
        risk_report = position_manager.evaluate_position_risks(account_id)
        return jsonify(risk_report)
    except Exception as e:
        logger.error(f'Error getting position risk: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 交易执行API
@app.route('/api/trade/exec', methods=['POST'])
def execute_trade():
    try:
        data = request.json
        order = execution_engine.submit_order(
            account_id=data.get('account_id', 'default'),
            symbol=data.get('symbol'),
            side=data.get('side'),  # 'buy' or 'sell'
            quantity=data.get('quantity'),
            price=data.get('price'),
            order_type=data.get('order_type', 'market')
        )
        return jsonify(order)
    except Exception as e:
        logger.error(f'Error executing trade: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_status(order_id):
    try:
        order = execution_engine.get_order_status(order_id)
        if order:
            return jsonify(order)
        return jsonify({'error': '订单不存在'}), 404
    except Exception as e:
        logger.error(f'Error getting order status: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/orders/<string:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    try:
        result = execution_engine.cancel_order(order_id)
        if result['success']:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        logger.error(f'Error canceling order: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 历史交易记录API
@app.route('/api/trade/history', methods=['GET'])
def get_trade_history():
    try:
        account_id = request.args.get('account_id', 'default')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        symbol = request.args.get('symbol')
        
        history = trade_history_manager.get_trade_history(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            symbol=symbol
        )
        return jsonify({'trades': history})
    except Exception as e:
        logger.error(f'Error getting trade history: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/trade/export', methods=['GET'])
def export_trade_history():
    try:
        account_id = request.args.get('account_id', 'default')
        export_format = request.args.get('format', 'csv')
        
        file_data, filename = trade_history_manager.export_trades(
            account_id=account_id,
            export_format=export_format
        )
        
        return send_file(
            io.BytesIO(file_data),
            mimetype='text/csv' if export_format == 'csv' else 'application/vnd.ms-excel',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f'Error exporting trade history: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 账户信息API
@app.route('/api/account', methods=['GET'])
def get_account_info():
    try:
        account_id = request.args.get('account_id', 'A001')
        account = risk_manager.get_account_by_id(account_id)
        if account:
            return jsonify({
                'balance': account['balance'],
                'available_funds': account['balance'] - account['margin'],
                'equity': account['equity'],
                'margin': account['margin'],
                'marginRatio': account['marginRatio'],
                'maxDrawdown': account['maxDrawdown'],
                'dailyProfit': account['dailyProfit']
            })
        # 如果找不到账户，返回默认模拟数据
        return jsonify({
            'balance': 500000.00,
            'available_funds': 300000.00,
            'equity': 700000.00,
            'margin': 100000.00,
            'marginRatio': 170.00,
            'maxDrawdown': -8.50,
            'dailyProfit': 2500.00
        })
    except Exception as e:
        logger.error(f'Error getting account info: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 活跃订单API
@app.route('/api/orders/active', methods=['GET'])
def get_active_orders():
    try:
        account_id = request.args.get('account_id', 'default')
        # 从execution_engine获取所有未完成的订单
        active_orders = [order for order in execution_engine.orders if order['status'] == 'pending']
        # 按账户ID过滤
        if account_id != 'default':
            active_orders = [order for order in active_orders if order['accountId'] == account_id]
        return jsonify({'orders': active_orders})
    except Exception as e:
        logger.error(f'Error getting active orders: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 风控管理API
@app.route('/api/risk/metrics', methods=['GET'])
def get_risk_metrics():
    try:
        account_id = request.args.get('account_id', 'default')
        metrics = risk_manager.calculate_risk_metrics(account_id)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f'Error getting risk metrics: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/risk/monitor', methods=['GET'])
def monitor_risk():
    try:
        account_id = request.args.get('account_id', 'default')
        risk_alerts = risk_manager.monitor_account_risk(account_id)
        return jsonify({'alerts': risk_alerts})
    except Exception as e:
        logger.error(f'Error monitoring risk: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/risk/thresholds', methods=['POST'])
def set_risk_thresholds():
    try:
        data = request.json
        result = risk_manager.set_risk_thresholds(
            account_id=data.get('account_id', 'default'),
            thresholds=data.get('thresholds')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f'Error setting risk thresholds: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 通知管理API
@app.route('/api/notification/config', methods=['GET'])
def get_notification_config():
    try:
        account_id = request.args.get('account_id', 'default')
        config = notification_manager.get_notification_config(account_id)
        return jsonify(config)
    except Exception as e:
        logger.error(f'Error getting notification config: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/notification/config', methods=['POST'])
def update_notification_config():
    try:
        data = request.json
        result = notification_manager.save_notification_config(
            account_id=data.get('account_id', 'default'),
            config=data.get('config')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f'Error updating notification config: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 模拟实时数据更新的API接口
@app.route('/api/data/realtime', methods=['GET'])
def get_realtime_data():
    try:
        # 获取查询参数
        symbols = request.args.getlist('symbols', type=str)
        if not symbols:
            symbols = ['000001', '600036', '600519']
        
        # 生成实时数据
        realtime_data = []
        for symbol in symbols:
            # 随机生成价格变化
            last_price = random.uniform(10, 200)
            change = random.uniform(-2, 2)
            change_percent = (change / last_price) * 100
            
            realtime_data.append({
                'symbol': symbol,
                'lastPrice': round(last_price + change, 2),
                'change': round(change, 2),
                'changePercent': round(change_percent, 2),
                'volume': random.randint(1000000, 10000000),
                'timestamp': datetime.now().timestamp()
            })
        
        return jsonify({
            'success': True,
            'data': realtime_data
        })
    except Exception as e:
        logger.error(f'Error getting realtime data: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # 确保输出目录存在
    if not os.path.exists(chart_config['output_dir']):
        os.makedirs(chart_config['output_dir'])
        
    # 注意：在生产环境中，应该使用gunicorn等WSGI服务器
    app.run(host='0.0.0.0', port=5000, debug=True)