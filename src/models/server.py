from flask import Flask, jsonify, request
import os
import sys
import time
import random
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

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

if __name__ == '__main__':
    # 注意：在生产环境中，应该使用gunicorn等WSGI服务器
    app.run(host='0.0.0.0', port=5000, debug=True)