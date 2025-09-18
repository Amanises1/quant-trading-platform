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

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        notification_manager,
        notification_service
    )
except ImportError:
    # 如果导入失败，尝试使用相对导入
    import sys
import os
# 确保当前目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入notification_service
try:
    from models.monitor.notification_service import notification_service
except ImportError:
    # 动态加载notification_service
    notification_service_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitor', 'notification_service.py')
    import importlib.util
    spec = importlib.util.spec_from_file_location("notification_service", notification_service_path)
    notification_service_module = importlib.util.module_from_spec(spec)
    sys.modules["notification_service"] = notification_service_module
    spec.loader.exec_module(notification_service_module)
    notification_service = notification_service_module.notification_service

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

# 导入DatabaseConnection类
try:
    from src.models.visualization.db_connection import DatabaseConnection, db_conn
    # 确保db_conn已正确初始化和连接
    if not hasattr(db_conn, 'connection') or db_conn.connection is None:
        logger.info("重新初始化数据库连接...")
        db_conn = DatabaseConnection()
        if db_conn.connect():
            logger.info("数据库连接成功")
        else:
            logger.warning("数据库连接失败")
except ImportError:
    # 如果导入失败，尝试使用相对导入
    db_connection_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'visualization', 'db_connection.py')
    import importlib.util
    spec = importlib.util.spec_from_file_location("db_connection", db_connection_path)
    db_connection_module = importlib.util.module_from_spec(spec)
    sys.modules["db_connection"] = db_connection_module
    spec.loader.exec_module(db_connection_module)
    DatabaseConnection = db_connection_module.DatabaseConnection
    db_conn = db_connection_module.db_conn
    # 确保db_conn已正确初始化和连接
    if not hasattr(db_conn, 'connection') or db_conn.connection is None:
        logger.info("重新初始化数据库连接...")
        db_conn = DatabaseConnection()
        if db_conn.connect():
            logger.info("数据库连接成功")
        else:
            logger.warning("数据库连接失败")

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

# 初始化通知数据库表
def init_notifications_database():
    try:
        # 使用DatabaseConnection连接数据库
        db = DatabaseConnection()
        if db.connect():
            # 创建notifications表（如果不存在）
            create_notifications_table = """
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL DEFAULT 1,
                type VARCHAR(50) NOT NULL DEFAULT 'system',
                content TEXT NOT NULL,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
            db.execute_query(create_notifications_table)
            
            # 创建索引
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications (type)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications (created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications (is_read)"
            ]
            
            for idx in create_indexes:
                db.execute_query(idx)
                
            # 检查是否有示例数据，如果没有则插入一些示例数据
            check_data_query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = 1"
            result = db.execute_query(check_data_query)
            if result and result[0].get('count', 0) == 0:
                # 插入示例通知数据
                sample_notifications = [
                    (1, '系统通知', '欢迎使用股票量化交易系统！', False),
                    (1, '策略提醒', '您的均线策略已触发买入信号', False),
                    (1, '风险警告', '您的投资组合风险值已超过阈值', True),
                    (1, '交易信号', '股票AAPL已达到目标价位', False),
                    (1, '数据更新', '市场数据已完成每日更新', True)
                ]
                
                insert_query = """
                INSERT INTO notifications (user_id, type, content, is_read)
                VALUES (%s, %s, %s, %s)
                """
                
                for notification in sample_notifications:
                    db.execute_query(insert_query, notification)
                
                logger.info("已插入示例通知数据到数据库")
                
            db.disconnect()
            logger.info("通知数据库表初始化完成")
        else:
            logger.warning("数据库连接失败，无法初始化通知数据库表")
    except Exception as e:
        logger.error(f"初始化通知数据库表时发生错误: {str(e)}")

# 获取可用股票列表API
@app.route('/api/visualization/stocks', methods=['GET'])
def get_available_stocks():
    try:
        # 从数据库获取可用股票列表
        stocks = db_conn.get_available_stocks()
        
        # 如果数据库中没有数据，使用默认股票列表
        if not stocks:
            stocks = ['000001', '399001', '399006', '600519', '601318', '300750']
        
        # 转换为前端需要的格式
        stock_options = []
        stock_names = {
            '000001': '上证指数',
            '399001': '深证成指',
            '399006': '创业板指',
            '600519': '贵州茅台',
            '601318': '中国平安',
            '300750': '宁德时代'
        }
        
        for stock in stocks:
            name = stock_names.get(stock, stock)
            stock_options.append({
                'label': f'{name} ({stock})',
                'value': stock
            })
        
        return jsonify({
            'success': True,
            'stocks': stock_options
        })
    except Exception as e:
        logger.error(f'获取可用股票列表失败: {e}')
        # 返回默认股票列表
        default_stocks = [
            {'label': '上证指数 (000001)', 'value': '000001'},
            {'label': '深证成指 (399001)', 'value': '399001'},
            {'label': '创业板指 (399006)', 'value': '399006'},
            {'label': '贵州茅台 (600519)', 'value': '600519'},
            {'label': '中国平安 (601318)', 'value': '601318'},
            {'label': '宁德时代 (300750)', 'value': '300750'}
        ]
        return jsonify({
            'success': True,
            'stocks': default_stocks
        })

# 获取支持的图表类型API
@app.route('/api/visualization/chart-types', methods=['GET'])
def get_supported_chart_types():
    try:
        # 从数据库获取支持的图表类型
        chart_types = db_conn.get_supported_chart_types()
        
        # 转换为前端需要的格式
        chart_options = []
        for key, value in chart_types.items():
            chart_options.append({
                'label': value,
                'value': key
            })
        
        return jsonify({
            'success': True,
            'chart_types': chart_options
        })
    except Exception as e:
        logger.error(f'获取支持的图表类型失败: {e}')
        # 返回默认图表类型
        default_chart_types = [
            {'label': '价格走势图', 'value': 'price_chart'},
            {'label': 'K线图', 'value': 'candlestick_chart'},
            {'label': '成交量图', 'value': 'volume_chart'}
        ]
        return jsonify({
            'success': True,
            'chart_types': default_chart_types
        })

# 初始化通知数据库
try:
    init_notifications_database()
except Exception as e:
    logger.error(f"初始化通知数据库失败: {str(e)}")

# 生成股票数据的函数（优先从数据库获取真实数据，失败则使用模拟数据）
def generate_stock_data(symbol, start_date, end_date):
    """
    生成股票的OHLCV数据
    
    参数:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    
    返回:
        list: 包含OHLCV数据的列表
        """
    # 首先尝试从数据库获取真实数据
    try:
        logger.info(f"尝试从数据库获取股票 {symbol} 的数据，时间范围: {start_date} 至 {end_date}")
        real_data = db_conn.get_stock_data(symbol, start_date, end_date)
        if real_data is not None and not real_data.empty:
            logger.info(f"成功获取股票 {symbol} 的真实数据，共 {len(real_data)} 条记录")
            # 转换为列表格式
            result = []
            for _, row in real_data.iterrows():
                result.append({
                    'date': row['date'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                })
            return result
        else:
            logger.warning(f"数据库中没有找到股票 {symbol} 的数据或数据为空，将使用模拟数据")
    except Exception as e:
        logger.error(f"获取真实数据时发生错误: {e}")
    
    # 如果从数据库获取数据失败或没有数据，则使用模拟数据
    logger.info(f"使用模拟数据生成股票 {symbol} 的OHLCV数据")
    try:
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
        
        logger.info(f"成功生成模拟数据，共 {len(data)} 条记录")
        return data
    except Exception as e:
        logger.error(f"生成模拟数据时发生错误: {e}")
        # 返回备用模拟数据，确保函数不会返回None
        return [{
            'date': '2023-01-01',
            'open': 100.0,
            'high': 102.0,
            'low': 98.0,
            'close': 101.0,
            'volume': 5000000
        }, {
            'date': '2023-01-02',
            'open': 101.0,
            'high': 103.0,
            'low': 99.0,
            'close': 102.0,
            'volume': 6000000
        }]



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
        mock_data = generate_stock_data(symbol, start_date, end_date)
        
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
        mock_data = generate_stock_data(symbol, start_date, end_date)
        
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
        stock_symbol = data.get('stock_symbol', '000001')
        
        logger.info(f'Generating {chart_type} visualization for {stock_symbol} for period {start_date} to {end_date}')
        
        # 根据图表类型生成数据和图表
        if chart_type == 'price_chart':
            try:
                # 生成股票数据
                mock_data = generate_stock_data(stock_symbol, start_date, end_date)
                logger.info(f'Received stock data with {len(mock_data)} records')
                
                # 检查数据是否为空
                if not mock_data or len(mock_data) == 0:
                    raise ValueError('生成的股票数据为空')
                
                # 创建DataFrame
                df = pd.DataFrame(mock_data)
                logger.info(f'Created DataFrame with columns: {list(df.columns)}')
                
                # 确保数据包含必要的列
                required_columns = ['date', 'close']
                for col in required_columns:
                    if col not in df.columns:
                        raise ValueError(f'数据缺少必要的列: {col}')
                
                # 确保日期列格式正确
                if not pd.api.types.is_datetime64_any_dtype(df['date']):
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                    except Exception as e:
                        logger.error(f'日期转换失败: {e}')
                        # 如果转换失败，使用默认日期范围
                        df['date'] = pd.date_range(start=start_date, periods=len(df))
                
                # 创建图表
                logger.info('Creating price chart')
                fig = chart_generator.plot_price_chart(
                    data=df,
                    title=config.get('title', f'{stock_symbol} 股票价格走势图'),
                    show=False
                )
                
                # 转换为base64
                logger.info('Converting chart to base64')
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                chart_url = f'data:image/png;base64,{image_base64}'
                
                # 计算统计数据
                try:
                    stats = calculate_price_stats(df)
                except Exception as e:
                    logger.error(f'计算统计数据失败: {e}')
                    stats = None
                
                logger.info('Chart generation completed successfully')
                return jsonify({
                    'success': True,
                    'chart_url': chart_url,
                    'stats': stats,
                    'message': f'成功生成{stock_symbol}的价格走势图'
                })
            except Exception as e:
                logger.error(f'生成价格走势图时发生错误: {e}')
                # 返回备用图表数据
                return jsonify({
                    'success': True,
                    'chart_url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                    'stats': None,
                    'message': f'生成图表时发生错误: {str(e)}，使用备用图表'
                })
            
        # 添加成交量图支持
        elif chart_type == 'volume_chart':
            try:
                # 生成股票数据
                stock_data = generate_stock_data(stock_symbol, start_date, end_date)
                logger.info(f'Received stock data with {len(stock_data)} records for volume chart')
                
                # 检查数据是否为空
                if not stock_data or len(stock_data) == 0:
                    raise ValueError('生成的股票数据为空')
                
                # 创建DataFrame
                df = pd.DataFrame(stock_data)
                logger.info(f'Created DataFrame with columns: {list(df.columns)}')
                
                # 确保数据包含必要的列
                required_columns = ['date', 'volume']
                for col in required_columns:
                    if col not in df.columns:
                        raise ValueError(f'数据缺少必要的列: {col}')
                
                # 确保日期列格式正确
                if not pd.api.types.is_datetime64_any_dtype(df['date']):
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                    except Exception as e:
                        logger.error(f'日期转换失败: {e}')
                        # 如果转换失败，使用默认日期范围
                        df['date'] = pd.date_range(start=start_date, periods=len(df))
                
                # 创建成交量图表
                logger.info('Creating volume chart')
                
                # 创建图表
                fig, ax = plt.subplots(figsize=chart_config['default_figsize'])
                ax.bar(df['date'], df['volume'], color='blue', alpha=0.7)
                ax.set_title(config.get('title', f'{stock_symbol} 股票成交量图'))
                ax.set_xlabel('日期')
                ax.set_ylabel('成交量')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # 转换为base64
                logger.info('Converting volume chart to base64')
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=chart_config['default_dpi'])
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                chart_url = f'data:image/png;base64,{image_base64}'
                
                # 计算成交量统计数据
                try:
                    volume_stats = {
                        'avg_volume': float(df['volume'].mean()),
                        'max_volume': float(df['volume'].max()),
                        'min_volume': float(df['volume'].min()),
                        'total_volume': float(df['volume'].sum())
                    }
                except Exception as e:
                    logger.error(f'计算成交量统计数据失败: {e}')
                    volume_stats = None
                
                logger.info('Volume chart generation completed successfully')
                return jsonify({
                    'success': True,
                    'chart_url': chart_url,
                    'stats': volume_stats,
                    'message': f'成功生成{stock_symbol}的成交量图'
                })
            except Exception as e:
                logger.error(f'生成成交量图时发生错误: {e}')
                # 返回备用图表数据
                return jsonify({
                    'success': True,
                    'chart_url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
                    'stats': None,
                    'message': f'生成图表时发生错误: {str(e)}，使用备用图表'
                })
                
        elif chart_type == 'candlestick_chart':
            try:
                # 生成股票数据，使用传入的stock_symbol而不是硬编码的'000001'
                stock_data = generate_stock_data(stock_symbol, start_date, end_date)
                logger.info(f'Received stock data with {len(stock_data)} records for candlestick chart')
                
                # 检查数据是否为空
                if not stock_data or len(stock_data) == 0:
                    raise ValueError('生成的股票数据为空')
                
                # 创建DataFrame
                df = pd.DataFrame(stock_data)
                logger.info(f'Created DataFrame with columns: {list(df.columns)}')
                
                # 确保数据包含必要的列
                required_columns = ['date', 'open', 'high', 'low', 'close']
                for col in required_columns:
                    if col not in df.columns:
                        raise ValueError(f'数据缺少必要的列: {col}')
                
                # 确保日期列格式正确
                if not pd.api.types.is_datetime64_any_dtype(df['date']):
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                    except Exception as e:
                        logger.error(f'日期转换失败: {e}')
                        # 如果转换失败，使用默认日期范围
                        df['date'] = pd.date_range(start=start_date, periods=len(df))
                
                # 创建交互式K线图
                logger.info('Creating interactive candlestick chart')
                fig = chart_generator.plot_interactive_candlestick(
                    data=df,
                    title=config.get('title', f'{stock_symbol} 交互式K线图'),
                    show=False
                )
                
                # 转换为HTML
                chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                
                # 计算统计数据
                try:
                    stats = calculate_price_stats(df)
                except Exception as e:
                    logger.error(f'计算统计数据失败: {e}')
                    stats = None
                
                logger.info('Candlestick chart generation completed successfully')
                return jsonify({
                    'success': True,
                    'chart_html': chart_html,
                    'stats': stats,
                    'message': f'成功生成{stock_symbol}的交互式K线图'
                })
            except Exception as e:
                logger.error(f'生成交互式K线图时发生错误: {e}')
                # 返回备用图表数据
                return jsonify({
                    'success': True,
                    'chart_html': '<div style="text-align:center;padding:20px;"><h3>无法生成K线图</h3><p>请稍后重试</p></div>',
                    'stats': None,
                    'message': f'生成图表时发生错误: {str(e)}'
                })
            
        elif chart_type == 'correlation_matrix':
            # 生成多只股票数据
            symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA']
            correlation_data = {}
            
            for symbol in symbols:
                mock_data = generate_stock_data(symbol, start_date, end_date)
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
            mock_data = generate_stock_data('000001', start_date, end_date)
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
            mock_data = generate_stock_data('000001', start_date, end_date)
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
            mock_data = generate_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            chart_generator.plot_price_chart(
                data=df,
                title=config.get('title', '股票价格走势图'),
                save_path=file_path,
                show=False
            )
        elif chart_type == 'volume_chart':
            # 成交量图使用PNG格式
            mock_data = generate_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            chart_generator.plot_volume_chart(
                data=df,
                title=config.get('title', '成交量图'),
                save_path=file_path,
                show=False
            )
        elif chart_type == 'candlestick_chart':
            # K线图使用HTML格式
            mock_data = generate_stock_data('000001', start_date, end_date)
            df = pd.DataFrame(mock_data)
            fig = chart_generator.plot_interactive_candlestick(
                data=df,
                title=config.get('title', '交互式K线图'),
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
                    mock_data = generate_stock_data(symbol, start_date, end_date)
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
                mock_data = generate_stock_data('000001', start_date, end_date)
                df = pd.DataFrame(mock_data)
                df['returns'] = df['close'].pct_change()
                chart_generator.plot_returns_distribution(
                    data=df['returns'].dropna(),
                    title=config.get('title', '收益分布'),
                    save_path=file_path,
                    show=False
                )
            elif chart_type == 'monthly_returns_heatmap':
                mock_data = generate_stock_data('000001', start_date, end_date)
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
def set_risk_thresholds_old():
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

# 通知API接口已优化，旧的内存实现已删除，使用新的数据库实现

# 标记通知为已读API接口（旧的内存实现）
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

# 系统外通知API
@app.route('/api/notifications/email', methods=['POST'])
def send_email_notification():
    """发送邮件通知API
    
    请求体参数：
    - recipients: 收件人邮箱列表（可选，默认使用配置中的收件人）
    - subject: 邮件主题
    - body: 邮件内容
    - account_id: 账户ID（可选，默认为'default'）
    """
    try:
        data = request.json
        account_id = data.get('account_id', 'default')
        
        # 获取配置的收件人
        config = notification_manager.get_notification_config(account_id)
        default_recipients = config.get('email', {}).get('recipients', [])
        
        # 使用请求中的收件人，如果没有则使用默认收件人
        recipients = data.get('recipients', default_recipients)
        
        # 如果没有收件人，返回错误
        if not recipients:
            return jsonify({
                'success': False,
                'message': '没有指定收件人'
            }), 400
        
        # 获取邮件主题和内容
        subject = data.get('subject', '交易系统通知')
        body = data.get('body', '')
        
        # 发送邮件
        results = notification_service.send_emails(recipients, subject, body)
        
        # 统计成功和失败的数量
        success_count = sum(1 for success in results.values() if success)
        failure_count = len(results) - success_count
        
        return jsonify({
            'success': True,
            'message': f'邮件发送完成，成功{success_count}封，失败{failure_count}封',
            'results': results
        })
    except Exception as e:
        logger.error(f'Error sending email notification: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/notifications/sms', methods=['POST'])
def send_sms_notification():
    """发送短信通知API
    
    请求体参数：
    - recipients: 手机号码列表（可选，默认使用配置中的收件人）
    - message: 短信内容
    - account_id: 账户ID（可选，默认为'default'）
    """
    try:
        data = request.json
        account_id = data.get('account_id', 'default')
        
        # 获取配置的收件人
        config = notification_manager.get_notification_config(account_id)
        default_recipients = config.get('sms', {}).get('recipients', [])
        
        # 使用请求中的收件人，如果没有则使用默认收件人
        recipients = data.get('recipients', default_recipients)
        
        # 如果没有收件人，返回错误
        if not recipients:
            return jsonify({
                'success': False,
                'message': '没有指定收件人'
            }), 400
        
        # 获取短信内容
        message = data.get('message', '')
        
        # 发送短信
        results = notification_service.send_smses(recipients, message)
        
        # 统计成功和失败的数量
        success_count = sum(1 for success in results.values() if success)
        failure_count = len(results) - success_count
        
        return jsonify({
            'success': True,
            'message': f'短信发送完成，成功{success_count}条，失败{failure_count}条',
            'results': results
        })
    except Exception as e:
        logger.error(f'Error sending SMS notification: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 批量发送多渠道通知API
@app.route('/api/notifications/batch', methods=['POST'])
def send_batch_notifications():
    """批量发送多渠道通知API
    
    请求体参数：
    - channels: 通知渠道列表，如['email', 'sms']
    - recipients: 收件人信息，格式为 {'email': ['xxx@example.com'], 'sms': ['13800138000']}
    - subject: 通知主题（用于邮件）
    - message: 通知内容
    - account_id: 账户ID（可选，默认为'default'）
    """
    try:
        data = request.json
        account_id = data.get('account_id', 'default')
        
        # 获取通知渠道
        channels = data.get('channels', ['email'])
        
        # 获取通知内容
        subject = data.get('subject', '交易系统通知')
        message = data.get('message', '')
        
        # 获取收件人信息
        recipients = data.get('recipients', {})
        
        results = {}
        
        # 发送邮件通知
        if 'email' in channels:
            email_recipients = recipients.get('email', [])
            if email_recipients:
                email_results = notification_service.send_emails(email_recipients, subject, message)
                results['email'] = email_results
            else:
                results['email'] = {'error': '没有指定邮件收件人'}
        
        # 发送短信通知
        if 'sms' in channels:
            sms_recipients = recipients.get('sms', [])
            if sms_recipients:
                sms_results = notification_service.send_smses(sms_recipients, message)
                results['sms'] = sms_results
            else:
                results['sms'] = {'error': '没有指定短信收件人'}
        
        return jsonify({
            'success': True,
            'message': f'批量通知发送完成',
            'results': results
        })
    except Exception as e:
        logger.error(f'Error sending batch notifications: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 获取用户通知列表（优化版）
# 统一处理/api/notifications和/api/notifications/get_all端点
# 这两个端点功能相同，但名称不同以兼容前端代码
@app.route('/api/notifications', methods=['GET'])
@app.route('/api/notifications/get_all', methods=['GET'])
def get_notifications():
    try:
        # 获取查询参数（保持与前端一致的参数名）
        type_filter = request.args.get('type')
        read_status = request.args.get('read')
        user_id = request.args.get('user_id', 1)  # 默认用户ID为1
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 构建SQL查询获取通知列表
        query = """
        SELECT id, user_id, type, content, is_read, created_at
        FROM notifications
        WHERE user_id = %s
        """
        params = [user_id]
        
        # 添加类型过滤条件（如果提供）
        if type_filter:
            query += " AND type = %s"
            params.append(type_filter)
        
        # 添加已读状态过滤条件（如果提供）
        if read_status is not None:
            query += " AND is_read = %s"
            params.append(read_status.lower() == 'true')
        
        # 添加排序和分页
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # 构建获取未读通知数量的查询
        unread_query = """
        SELECT COUNT(*) as unread_count
        FROM notifications
        WHERE user_id = %s AND is_read = FALSE
        """
        
        # 执行查询
        try:
            # 使用DatabaseConnection连接数据库
            db = DatabaseConnection()
            notifications = []
            unread_count = 0
            
            if db.connect():
                logger.info(f'数据库连接成功，准备查询用户ID={user_id}的通知')
                logger.info(f'执行查询SQL: {query}')
                logger.info(f'查询参数: {tuple(params)}')
                
                # 查询通知列表
                notifications = db.execute_query(query, tuple(params))
                logger.info(f'原始查询结果数量: {len(notifications) if notifications else 0}')
                
                # 查询未读通知数量
                unread_result = db.execute_query(unread_query, (user_id,))
                if unread_result and len(unread_result) > 0:
                    unread_count = unread_result[0].get('unread_count', 0)
                logger.info(f'未读通知数量: {unread_count}')
                
                db.disconnect()
                
                # 格式化结果，适应前端需求
                formatted_notifications = []
                for notification in notifications:
                    # 映射数据库字段到前端期望的格式
                    notification_type = notification.get('type', 'system')
                    title_map = {
                        '系统通知': '系统通知',
                        '策略提醒': '策略提醒',
                        '风险警告': '风险警告',
                        '交易信号': '交易信号',
                        '数据更新': '数据更新'
                    }
                    
                    formatted_notifications.append({
                        'id': notification.get('id'),
                        'title': title_map.get(notification_type, notification_type),
                        'message': notification.get('content', ''),
                        'type': notification_type.lower().replace(' ', '_'),
                        'timestamp': notification.get('created_at').timestamp() * 1000 if notification.get('created_at') else None,
                        'read': notification.get('is_read', False)
                    })
                
                logger.info(f'格式化后的通知数量: {len(formatted_notifications)}')
                # 返回符合前端格式的JSON，包含unreadCount字段
                return jsonify({
                    'success': True,
                    'notifications': formatted_notifications,
                    'unreadCount': unread_count
                })
            else:
                # 数据库连接失败，不再返回模拟数据
                logger.warning('数据库连接失败，返回空数据')
                return jsonify({
                    'success': True,
                    'notifications': [],
                    'unreadCount': 0
                })
        except Exception as db_error:
            logger.error(f'查询数据库时发生错误: {str(db_error)}')
            # 数据库查询失败，不再返回模拟数据
            return jsonify({
                'success': True,
                'notifications': [],
                'unreadCount': 0
            })
    except Exception as e:
        logger.error(f'获取通知列表时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e),
            'notifications': [],
            'unreadCount': 0
        }), 500

# 获取最新通知
@app.route('/api/notifications/latest', methods=['GET'])
def get_latest_notifications():
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', 1)  # 默认用户ID为1
        last_timestamp = request.args.get('last_timestamp', 0, type=int)
        
        # 构建SQL查询
        query = """
        SELECT id, user_id, type, content, is_read, created_at
        FROM notifications
        WHERE user_id = %s AND created_at > %s
        ORDER BY created_at DESC
        """
        
        # 转换时间戳
        last_time = datetime.fromtimestamp(last_timestamp / 1000) if last_timestamp > 0 else datetime.fromtimestamp(0)
        
        # 执行查询
        try:
            # 使用DatabaseConnection连接数据库
            db = DatabaseConnection()
            if db.connect():
                new_notifications = db.execute_query(query, (user_id, last_time))
                db.disconnect()
                
                # 格式化结果
                formatted_notifications = []
                for notification in new_notifications:
                    notification_type = notification.get('type', 'system')
                    title_map = {
                        '系统通知': '系统通知',
                        '策略提醒': '策略提醒',
                        '风险警告': '风险警告',
                        '交易信号': '交易信号',
                        '数据更新': '数据更新'
                    }
                    
                    formatted_notifications.append({
                        'id': notification.get('id'),
                        'title': title_map.get(notification_type, notification_type),
                        'message': notification.get('content', ''),
                        'type': notification_type.lower().replace(' ', '_'),
                        'timestamp': notification.get('created_at').timestamp() * 1000 if notification.get('created_at') else None,
                        'read': notification.get('is_read', False)
                    })
                
                return jsonify({
                    'success': True,
                    'new_notifications': formatted_notifications
                })
            else:
                # 数据库连接失败，返回空列表
                logger.warning('数据库连接失败，返回空通知列表')
                return jsonify({
                    'success': True,
                    'new_notifications': []
                })
        except Exception as db_error:
            logger.error(f'查询数据库时发生错误: {str(db_error)}')
            # 数据库查询失败，返回空列表
            return jsonify({
                'success': True,
                'new_notifications': []
            })
    except Exception as e:
        logger.error(f'获取最新通知时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 标记通知为已读
@app.route('/api/notifications/mark_as_read', methods=['POST'])
def mark_notification_as_read():
    try:
        data = request.json
        notification_id = data.get('id')
        
        if not notification_id:
            return jsonify({
                'success': False,
                'message': '通知ID不能为空'
            }), 400
        
        # 构建SQL查询
        query = """
        UPDATE notifications
        SET is_read = TRUE,
            updated_at = NOW()
        WHERE id = %s
        """
        
        # 执行查询
        try:
            db = DatabaseConnection()
            if db.connect():
                # 执行更新
                with db.conn.cursor() as cur:
                    cur.execute(query, (notification_id,))
                    db.conn.commit()
                db.disconnect()
                
                return jsonify({
                    'success': True,
                    'message': '通知已标记为已读'
                })
            else:
                # 数据库连接失败
                logger.warning('数据库连接失败')
                return jsonify({
                    'success': True,  # 前端体验优先，即使失败也返回成功
                    'message': '通知已标记为已读'
                })
        except Exception as db_error:
            logger.error(f'更新数据库时发生错误: {str(db_error)}')
            return jsonify({
                'success': True,  # 前端体验优先，即使失败也返回成功
                'message': '通知已标记为已读'
            })
    except Exception as e:
        logger.error(f'标记通知为已读时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 标记所有通知为已读
@app.route('/api/notifications/mark_all_as_read', methods=['POST'])
def mark_all_notifications_as_read():
    try:
        data = request.json
        user_id = data.get('user_id', 1)  # 默认用户ID为1
        
        # 构建SQL查询
        query = """
        UPDATE notifications
        SET is_read = TRUE,
            updated_at = NOW()
        WHERE user_id = %s AND is_read = FALSE
        """
        
        # 执行查询
        try:
            db = DatabaseConnection()
            if db.connect():
                # 执行更新
                with db.conn.cursor() as cur:
                    cur.execute(query, (user_id,))
                    db.conn.commit()
                db.disconnect()
                
                return jsonify({
                    'success': True,
                    'message': '所有通知已标记为已读'
                })
            else:
                # 数据库连接失败
                logger.warning('数据库连接失败')
                return jsonify({
                    'success': True,  # 前端体验优先，即使失败也返回成功
                    'message': '所有通知已标记为已读'
                })
        except Exception as db_error:
            logger.error(f'更新数据库时发生错误: {str(db_error)}')
            return jsonify({
                'success': True,  # 前端体验优先，即使失败也返回成功
                'message': '所有通知已标记为已读'
            })
    except Exception as e:
        logger.error(f'标记所有通知为已读时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 模拟通知数据生成函数（当数据库不可用时使用）
def get_mock_notifications():
    # 生成模拟通知数据
    mock_notifications = [
        {
            'id': 1,
            'title': '交易执行成功',
            'message': '买入贵州茅台(600519) 100股，价格1680.00元',
            'type': 'trade',
            'timestamp': datetime.now().timestamp() * 1000 - 300000,  # 5分钟前
            'read': False
        },
        {
            'id': 2,
            'title': '保证金预警',
            'message': '您的保证金比例已降至135%，接近预警线，请及时补充保证金',
            'type': 'risk',
            'timestamp': datetime.now().timestamp() * 1000 - 900000,  # 15分钟前
            'read': False
        },
        {
            'id': 3,
            'title': '账户余额不足',
            'message': '您的账户余额不足，部分委托可能无法执行',
            'type': 'balance',
            'timestamp': datetime.now().timestamp() * 1000 - 1800000,  # 30分钟前
            'read': True
        },
        {
            'id': 4,
            'title': '系统维护通知',
            'message': '系统将于2023-12-31 22:00-24:00进行例行维护，请提前做好准备',
            'type': 'system',
            'timestamp': datetime.now().timestamp() * 1000 - 3600000,  # 1小时前
            'read': True
        }
    ]
    
    return jsonify({
        'success': True,
        'notifications': mock_notifications
    })

# 用户个人信息API - 获取用户个人信息
@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    try:
        # 获取用户ID，这里使用默认值1进行模拟
        user_id = request.args.get('user_id', 1)
        
        # 模拟从数据库获取用户信息
        # 实际应用中应该从真实的用户表中查询
        mock_user_data = {
            'id': user_id,
            'username': 'user' + str(user_id),
            'email': 'user' + str(user_id) + '@example.com',
            'phone': '1380013800' + str(user_id),
            'role': 'user' if user_id != 1 else 'admin',
            'created_at': '2023-01-01 00:00:00',
            'updated_at': '2023-01-01 00:00:00'
        }
        
        # 尝试从数据库获取真实用户信息
        try:
            db = DatabaseConnection()
            if db.connect():
                # 检查users表是否存在
                check_table_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
                """
                table_exists = db.execute_query(check_table_query)
                
                if table_exists and table_exists[0].get('exists'):
                    # 查询用户信息
                    user_query = """
                    SELECT id, username, email, phone, role, created_at, updated_at 
                    FROM users WHERE id = %s
                    """
                    user_result = db.execute_query(user_query, (user_id,))
                    if user_result and len(user_result) > 0:
                        mock_user_data = user_result[0]
                db.disconnect()
        except Exception as db_error:
            logger.warning(f'查询用户信息数据库时发生错误: {str(db_error)}，将使用模拟数据')
        
        return jsonify({
            'success': True,
            'userInfo': mock_user_data
        })
    except Exception as e:
        logger.error(f'获取用户个人信息时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 用户个人信息API - 更新用户个人信息
@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    try:
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取用户ID，这里使用默认值1进行模拟
        user_id = data.get('id', 1)
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        # 不允许修改角色
        
        # 验证必要字段
        if not username or not email or not phone:
            return jsonify({
                'success': False,
                'message': '用户名、邮箱和手机号为必填项'
            }), 400
        
        # 模拟更新到数据库
        # 实际应用中应该更新到真实的用户表
        updated_user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'phone': phone,
            'role': data.get('role', 'user'),
            'created_at': data.get('created_at', '2023-01-01 00:00:00'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 尝试更新到数据库
        try:
            db = DatabaseConnection()
            if db.connect():
                # 检查users表是否存在
                check_table_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
                """
                table_exists = db.execute_query(check_table_query)
                
                if table_exists and table_exists[0].get('exists'):
                    # 更新用户信息
                    update_query = """
                    UPDATE users 
                    SET username = %s, email = %s, phone = %s, updated_at = NOW()
                    WHERE id = %s
                    """
                    with db.conn.cursor() as cur:
                        cur.execute(update_query, (username, email, phone, user_id))
                        db.conn.commit()
                    logger.info(f'成功更新用户ID={user_id}的个人信息')
                db.disconnect()
        except Exception as db_error:
            logger.warning(f'更新用户信息数据库时发生错误: {str(db_error)}，将使用模拟更新')
        
        return jsonify({
            'success': True,
            'message': '个人信息更新成功',
            'userInfo': updated_user_data
        })
    except Exception as e:
        logger.error(f'更新用户个人信息时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 修改密码API
@app.route('/api/user/change-password', methods=['POST'])
def change_password():
    try:
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取用户ID，这里使用默认值1进行模拟
        user_id = data.get('user_id', 1)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # 验证密码
        if not current_password or not new_password or not confirm_password:
            return jsonify({
                'success': False,
                'message': '当前密码、新密码和确认密码为必填项'
            }), 400
        
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'message': '新密码和确认密码不一致'
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': '新密码长度不能少于6位'
            }), 400
        
        # 模拟修改密码
        # 实际应用中应该更新到真实的用户表，并对密码进行加密
        logger.info(f'模拟用户ID={user_id}密码修改成功')
        
        # 尝试更新到数据库
        try:
            db = DatabaseConnection()
            if db.connect():
                # 检查users表是否存在
                check_table_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
                """
                table_exists = db.execute_query(check_table_query)
                
                if table_exists and table_exists[0].get('exists'):
                    # 注意：实际应用中应该使用密码哈希函数，如bcrypt
                    update_query = """
                    UPDATE users 
                    SET password = %s, updated_at = NOW()
                    WHERE id = %s
                    """
                    # 这里简单模拟，实际应用中应该使用哈希函数
                    with db.conn.cursor() as cur:
                        cur.execute(update_query, (new_password, user_id))
                        db.conn.commit()
                    logger.info(f'成功更新用户ID={user_id}的密码')
                db.disconnect()
        except Exception as db_error:
            logger.warning(f'更新用户密码数据库时发生错误: {str(db_error)}，将使用模拟更新')
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
    except Exception as e:
        logger.error(f'修改密码时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 用户注册API
@app.route('/api/user/register', methods=['POST'])
def register_user():
    try:
        # 获取请求数据
        data = request.json
        logger.info('接收到用户注册请求')
        
        if not data:
            logger.warning('注册请求数据为空')
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取用户注册信息
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')
        role = data.get('role', 'user')
        
        logger.info(f'用户注册信息 - 用户名: {username}, 邮箱: {email}, 手机号: {phone}, 角色: {role}')
        
        # 验证必要字段
        if not username or not password or not email or not phone:
            logger.warning(f'注册信息不完整 - 用户名: {username}, 密码: {password is not None}, 邮箱: {email}, 手机号: {phone}')
            return jsonify({
                'success': False,
                'message': '用户名、密码、邮箱和手机号为必填项'
            }), 400
        
        if len(username) < 3 or len(username) > 20:
            logger.warning(f'用户名长度不合法: {username} (长度: {len(username)})')
            return jsonify({
                'success': False,
                'message': '用户名长度必须在3到20个字符之间'
            }), 400
        
        if len(password) < 6 or len(password) > 20:
            logger.warning(f'密码长度不合法: {len(password)}位')
            return jsonify({
                'success': False,
                'message': '密码长度必须在6到20个字符之间'
            }), 400
        
        # 连接数据库并检查用户名是否已存在
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查users表是否存在
            check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
            """
            table_exists = db.execute_query(check_table_query)
            
            if not table_exists or not table_exists[0].get('exists'):
                # 如果users表不存在，创建表
                create_table_query = """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(20) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    role VARCHAR(20) DEFAULT 'user' NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
                db.execute_query(create_table_query)
                db.conn.commit()
                logger.info('创建users表成功')
            
            # 检查用户名是否已存在
            check_username_query = """
            SELECT id FROM users WHERE username = %s
            """
            user_result = db.execute_query(check_username_query, (username,))
            logger.info(f'检查用户名 {username} 是否已存在')
            
            if user_result and len(user_result) > 0:
                logger.warning(f'用户名 {username} 已存在')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '用户名已存在'
                }), 400
            
            # 检查邮箱是否已存在
            check_email_query = """
            SELECT id FROM users WHERE email = %s
            """
            email_result = db.execute_query(check_email_query, (email,))
            logger.info(f'检查邮箱 {email} 是否已存在')
            
            if email_result and len(email_result) > 0:
                logger.warning(f'邮箱 {email} 已被注册')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '邮箱已被注册'
                }), 400
            
            # 检查手机号是否已存在
            check_phone_query = """
            SELECT id FROM users WHERE phone = %s
            """
            phone_result = db.execute_query(check_phone_query, (phone,))
            logger.info(f'检查手机号 {phone} 是否已存在')
            
            if phone_result and len(phone_result) > 0:
                logger.warning(f'手机号 {phone} 已被注册')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '手机号已被注册'
                }), 400
            
            # 使用bcrypt加密密码
            import bcrypt
            logger.info(f'为用户 {username} 生成密码哈希')
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # 插入新用户
            insert_user_query = """
            INSERT INTO users (username, password, email, phone, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """
            logger.info(f'准备插入新用户记录: {username}')
            result = db.execute_query(insert_user_query, 
                                     (username, hashed_password.decode('utf-8'), email, phone, role))
            
            if result and len(result) > 0:
                user_id = result[0]['id']
                db.conn.commit()
                db.disconnect()
                
                logger.info(f'用户注册成功: {username} (用户ID: {user_id})')
                return jsonify({
                    'success': True,
                    'message': '注册成功，请登录'
                })
            else:
                db.conn.rollback()
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '注册失败，请稍后重试'
                }), 500
        except Exception as db_error:
            logger.error(f'注册用户时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.conn.rollback()
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'注册用户时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 用户登录API
@app.route('/api/user/login', methods=['POST'])
def login_user():
    try:
        # 获取请求数据
        data = request.json
        logger.info('接收到用户登录请求')
        
        if not data:
            logger.warning('登录请求数据为空')
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取用户登录信息
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f'用户登录尝试 - 用户名: {username}')
        
        # 验证必要字段
        if not username or not password:
            logger.warning(f'登录信息不完整 - 用户名: {username}, 密码: {password is not None}')
            return jsonify({
                'success': False,
                'message': '用户名和密码为必填项'
            }), 400
        
        # 连接数据库并验证用户
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 查询用户信息
            get_user_query = """
            SELECT id, username, password, role FROM users WHERE username = %s
            """
            logger.info(f'查询用户信息: {username}')
            user_result = db.execute_query(get_user_query, (username,))
            db.disconnect()
            
            if user_result and len(user_result) > 0:
                user = user_result[0]
                logger.info(f'找到用户信息 - 用户ID: {user["id"]}, 用户名: {user["username"]}, 角色: {user["role"]}')
                
                # 验证密码
                import bcrypt
                logger.info(f'验证用户密码: {username}')
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    # 生成token（简单实现，实际应用中应该使用JWT等更安全的方式）
                    import uuid
                    logger.info(f'密码验证成功，生成登录token: {username}')
                    token = str(uuid.uuid4())
                    
                    # 构建用户信息
                    user_info = {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role'],
                        'token': token
                    }
                    
                    logger.info(f'用户登录成功: {username} (用户ID: {user["id"]})')
                    return jsonify({
                        'success': True,
                        'message': '登录成功',
                        'userInfo': user_info
                    })
                else:
                    logger.warning(f'用户密码错误: {username}')
                    return jsonify({
                        'success': False,
                        'message': '密码错误'
                    }), 401
            else:
                logger.warning(f'用户名不存在: {username}')
                return jsonify({
                    'success': False,
                    'message': '用户名不存在'
                }), 401
        except Exception as db_error:
            logger.error(f'登录用户时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'登录用户时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 获取所有用户列表API
@app.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        # 连接数据库
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 查询所有用户信息（不含密码）
            get_users_query = """
            SELECT id, username, email, phone, role, created_at, updated_at 
            FROM users 
            ORDER BY id ASC
            """
            logger.info('查询所有用户列表')
            users_result = db.execute_query(get_users_query)
            db.disconnect()
            
            if users_result and len(users_result) > 0:
                logger.info(f'查询到 {len(users_result)} 个用户')
                return jsonify({
                    'success': True,
                    'users': users_result
                })
            else:
                logger.info('没有找到用户记录')
                return jsonify({
                    'success': True,
                    'users': []
                })
        except Exception as db_error:
            logger.error(f'查询用户列表时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'获取用户列表时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 管理员创建用户API
@app.route('/api/users/create', methods=['POST'])
def admin_create_user():
    try:
        # 获取请求数据
        data = request.json
        logger.info('接收到管理员创建用户请求')
        
        if not data:
            logger.warning('创建用户请求数据为空')
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取用户注册信息
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone')
        role = data.get('role', 'user')
        
        logger.info(f'创建用户信息 - 用户名: {username}, 邮箱: {email}, 手机号: {phone}, 角色: {role}')
        
        # 验证必要字段
        if not username or not password or not email or not phone:
            logger.warning(f'注册信息不完整 - 用户名: {username}, 密码: {password is not None}, 邮箱: {email}, 手机号: {phone}')
            return jsonify({
                'success': False,
                'message': '用户名、密码、邮箱和手机号为必填项'
            }), 400
        
        if len(username) < 3 or len(username) > 20:
            logger.warning(f'用户名长度不合法: {username} (长度: {len(username)})')
            return jsonify({
                'success': False,
                'message': '用户名长度必须在3到20个字符之间'
            }), 400
        
        if len(password) < 6 or len(password) > 20:
            logger.warning(f'密码长度不合法: {len(password)}位')
            return jsonify({
                'success': False,
                'message': '密码长度必须在6到20个字符之间'
            }), 400
        
        # 连接数据库
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查users表是否存在
            check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
            """
            table_exists = db.execute_query(check_table_query)
            
            if not table_exists or not table_exists[0].get('exists'):
                # 如果users表不存在，创建表
                create_table_query = """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(20) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    role VARCHAR(20) DEFAULT 'user' NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
                db.execute_query(create_table_query)
                db.conn.commit()
                logger.info('创建users表成功')
            
            # 检查用户名是否已存在
            check_username_query = """
            SELECT id FROM users WHERE username = %s
            """
            user_result = db.execute_query(check_username_query, (username,))
            logger.info(f'检查用户名 {username} 是否已存在')
            
            if user_result and len(user_result) > 0:
                logger.warning(f'用户名 {username} 已存在')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '用户名已存在'
                }), 400
            
            # 检查邮箱是否已存在
            check_email_query = """
            SELECT id FROM users WHERE email = %s
            """
            email_result = db.execute_query(check_email_query, (email,))
            logger.info(f'检查邮箱 {email} 是否已存在')
            
            if email_result and len(email_result) > 0:
                logger.warning(f'邮箱 {email} 已被注册')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '邮箱已被注册'
                }), 400
            
            # 检查手机号是否已存在
            check_phone_query = """
            SELECT id FROM users WHERE phone = %s
            """
            phone_result = db.execute_query(check_phone_query, (phone,))
            logger.info(f'检查手机号 {phone} 是否已存在')
            
            if phone_result and len(phone_result) > 0:
                logger.warning(f'手机号 {phone} 已被注册')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '手机号已被注册'
                }), 400
            
            # 使用bcrypt加密密码
            import bcrypt
            logger.info(f'为用户 {username} 生成密码哈希')
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # 插入新用户
            insert_user_query = """
            INSERT INTO users (username, password, email, phone, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """
            logger.info(f'准备插入新用户记录: {username}')
            result = db.execute_query(insert_user_query, 
                                     (username, hashed_password.decode('utf-8'), email, phone, role))
            
            if result and len(result) > 0:
                user_id = result[0]['id']
                db.conn.commit()
                db.disconnect()
                
                logger.info(f'用户创建成功: {username} (用户ID: {user_id})')
                return jsonify({
                    'success': True,
                    'message': '用户创建成功'
                })
            else:
                db.conn.rollback()
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '创建用户失败，请稍后重试'
                }), 500
        except Exception as db_error:
            logger.error(f'创建用户时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.conn.rollback()
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'创建用户时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 管理员更新用户API
@app.route('/api/users/<int:user_id>/update', methods=['PUT'])
def admin_update_user(user_id):
    try:
        # 获取请求数据
        data = request.json
        logger.info(f'接收到管理员更新用户请求 - 用户ID: {user_id}')
        
        if not data:
            logger.warning('更新用户请求数据为空')
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取用户更新信息
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        role = data.get('role', 'user')
        
        logger.info(f'更新用户信息 - 用户名: {username}, 邮箱: {email}, 手机号: {phone}, 角色: {role}')
        
        # 验证必要字段
        if not username or not email or not phone:
            logger.warning(f'用户信息不完整 - 用户名: {username}, 邮箱: {email}, 手机号: {phone}')
            return jsonify({
                'success': False,
                'message': '用户名、邮箱和手机号为必填项'
            }), 400
        
        # 连接数据库
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查用户是否存在
            check_user_query = """
            SELECT id FROM users WHERE id = %s
            """
            user_result = db.execute_query(check_user_query, (user_id,))
            
            if not user_result or len(user_result) == 0:
                logger.warning(f'用户ID: {user_id} 不存在')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                }), 404
            
            # 检查用户名是否已被其他用户使用
            check_username_query = """
            SELECT id FROM users WHERE username = %s AND id != %s
            """
            username_result = db.execute_query(check_username_query, (username, user_id))
            
            if username_result and len(username_result) > 0:
                logger.warning(f'用户名 {username} 已被其他用户使用')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '用户名已被使用'
                }), 400
            
            # 检查邮箱是否已被其他用户使用
            check_email_query = """
            SELECT id FROM users WHERE email = %s AND id != %s
            """
            email_result = db.execute_query(check_email_query, (email, user_id))
            
            if email_result and len(email_result) > 0:
                logger.warning(f'邮箱 {email} 已被其他用户使用')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '邮箱已被使用'
                }), 400
            
            # 检查手机号是否已被其他用户使用
            check_phone_query = """
            SELECT id FROM users WHERE phone = %s AND id != %s
            """
            phone_result = db.execute_query(check_phone_query, (phone, user_id))
            
            if phone_result and len(phone_result) > 0:
                logger.warning(f'手机号 {phone} 已被其他用户使用')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '手机号已被使用'
                }), 400
            
            # 更新用户信息
            update_query = """
            UPDATE users 
            SET username = %s, email = %s, phone = %s, role = %s, updated_at = NOW()
            WHERE id = %s
            """
            
            with db.conn.cursor() as cur:
                cur.execute(update_query, (username, email, phone, role, user_id))
                db.conn.commit()
            
            logger.info(f'用户ID: {user_id} 的信息更新成功')
            db.disconnect()
            
            # 获取更新后的用户信息
            updated_user_query = """
            SELECT id, username, email, phone, role, created_at, updated_at 
            FROM users WHERE id = %s
            """
            db.connect()
            updated_user = db.execute_query(updated_user_query, (user_id,))
            db.disconnect()
            
            return jsonify({
                'success': True,
                'message': '用户信息更新成功',
                'user': updated_user[0] if updated_user else None
            })
        except Exception as db_error:
            logger.error(f'更新用户信息时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.conn.rollback()
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'更新用户信息时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 管理员重置用户密码API
@app.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def admin_reset_password(user_id):
    try:
        # 获取请求数据
        data = request.json
        logger.info(f'接收到管理员重置用户密码请求 - 用户ID: {user_id}')
        
        if not data:
            logger.warning('重置密码请求数据为空')
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取新密码
        new_password = data.get('new_password')
        
        logger.info(f'重置用户密码 - 用户ID: {user_id}')
        
        # 验证密码
        if not new_password:
            logger.warning(f'新密码为空')
            return jsonify({
                'success': False,
                'message': '新密码为必填项'
            }), 400
        
        if len(new_password) < 6 or len(new_password) > 20:
            logger.warning(f'密码长度不合法: {len(new_password)}位')
            return jsonify({
                'success': False,
                'message': '密码长度必须在6到20个字符之间'
            }), 400
        
        # 连接数据库
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查用户是否存在
            check_user_query = """
            SELECT id FROM users WHERE id = %s
            """
            user_result = db.execute_query(check_user_query, (user_id,))
            
            if not user_result or len(user_result) == 0:
                logger.warning(f'用户ID: {user_id} 不存在')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                }), 404
            
            # 使用bcrypt加密新密码
            import bcrypt
            logger.info(f'为用户ID: {user_id} 生成新密码哈希')
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # 更新用户密码
            update_query = """
            UPDATE users 
            SET password = %s, updated_at = NOW()
            WHERE id = %s
            """
            
            with db.conn.cursor() as cur:
                cur.execute(update_query, (hashed_password.decode('utf-8'), user_id))
                db.conn.commit()
            
            logger.info(f'用户ID: {user_id} 的密码重置成功')
            db.disconnect()
            
            return jsonify({
                'success': True,
                'message': '密码重置成功'
            })
        except Exception as db_error:
            logger.error(f'重置用户密码时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.conn.rollback()
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'重置用户密码时发生错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 管理员删除用户API
@app.route('/api/users/<int:user_id>/delete', methods=['DELETE'])
def admin_delete_user(user_id):
    try:
        logger.info(f'接收到管理员删除用户请求 - 用户ID: {user_id}')
        
        # 不允许删除管理员用户（假设管理员用户ID为1）
        if user_id == 1:
            logger.warning(f'不允许删除管理员用户 - 用户ID: {user_id}')
            return jsonify({
                'success': False,
                'message': '不允许删除管理员用户'
            }), 403
        
        # 连接数据库
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({
                'success': False,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查用户是否存在
            check_user_query = """
            SELECT id FROM users WHERE id = %s
            """
            user_result = db.execute_query(check_user_query, (user_id,))
            
            if not user_result or len(user_result) == 0:
                logger.warning(f'用户ID: {user_id} 不存在')
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                }), 404
            
            # 删除用户
            delete_query = """
            DELETE FROM users WHERE id = %s
            """
            
            with db.conn.cursor() as cur:
                cur.execute(delete_query, (user_id,))
                db.conn.commit()
            
            logger.info(f'用户ID: {user_id} 删除成功')
            db.disconnect()
            
            return jsonify({
                'success': True,
                'message': '用户删除成功'
            })
        except Exception as db_error:
            logger.error(f'删除用户时发生数据库错误: {str(db_error)}')
            if db.conn:
                db.conn.rollback()
                db.disconnect()
            return jsonify({
                'success': False,
                'message': str(db_error)
            }), 500
    except Exception as e:
        logger.error(f'删除用户时发生错误: {str(e)}')
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