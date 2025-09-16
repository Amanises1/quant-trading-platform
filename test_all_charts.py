import requests
import json
import time

# API端点
url = 'http://localhost:5000/api/visualization/generate'

def test_chart(chart_type, stock_symbol='000001', start_date='2023-01-01', end_date='2023-12-31'):
    # 请求数据
    payload = {
        'chart_type': chart_type,
        'stock_symbol': stock_symbol,
        'start_date': start_date,
        'end_date': end_date
    }
    
    # 发送请求
    print(f"\n测试图表类型: {chart_type}")
    print(f"请求数据: {payload}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        end_time = time.time()
        
        # 检查响应状态
        if response.status_code == 200:
            # 尝试解析JSON响应
            try:
                data = response.json()
                print(f"响应状态码: {response.status_code}")
                print(f"成功: {data.get('success')}")
                print(f"消息: {data.get('message')}")
                print(f"是否包含chart_url: {bool(data.get('chart_url'))}")
                print(f"是否包含chart_html: {bool(data.get('chart_html'))}")
                print(f"是否包含stats: {bool(data.get('stats'))}")
                print(f"响应时间: {end_time - start_time:.2f}秒")
                
                # 如果有stats，打印部分统计信息
                if data.get('stats'):
                    stats = data['stats']
                    if isinstance(stats, list) and len(stats) > 0:
                        print(f"统计信息条数: {len(stats)}")
                        print(f"统计信息示例: {stats[0]['name']} = {stats[0]['value']}")
                    else:
                        print("统计信息格式异常")
                
                return True
            except json.JSONDecodeError:
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容(前500字符): {response.text[:500]}...")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"发送请求时发生错误: {e}")
        return False

# 测试不同类型的图表
def run_all_tests():
    print("开始测试所有图表类型...")
    print(f"API端点: {url}")
    
    # 测试的图表类型列表 - 只测试服务器支持的类型
    chart_types = [
        'price_chart',
        'candlestick_chart',
        'portfolio_performance',
        # 以下类型不支持
        # 'volume_chart',
        # 'technical_chart'
    ]
    
    results = {}
    for chart_type in chart_types:
        results[chart_type] = test_chart(chart_type)
        # 添加短暂延迟，避免服务器过载
        time.sleep(1)
    
    # 打印测试摘要
    print("\n===== 测试摘要 =====")
    success_count = sum(1 for success in results.values() if success)
    print(f"总测试数: {len(results)}")
    print(f"成功数: {success_count}")
    print(f"成功率: {(success_count/len(results))*100:.1f}%")
    
    if success_count < len(results):
        print("失败的图表类型:")
        for chart_type, success in results.items():
            if not success:
                print(f"- {chart_type}")

if __name__ == "__main__":
    run_all_tests()