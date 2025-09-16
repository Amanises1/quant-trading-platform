import requests
import json

# API端点
url = 'http://localhost:5000/api/visualization/generate'

# 请求数据
payload = {
    'chart_type': 'price_chart',
    'stock_symbol': '000001',
    'start_date': '2023-01-01',
    'end_date': '2023-12-31'
}

# 发送请求
print(f"发送请求到: {url}")
print(f"请求数据: {payload}")

try:
    response = requests.post(url, json=payload)
    
    # 检查响应状态
    if response.status_code == 200:
        # 尝试解析JSON响应
        try:
            data = response.json()
            print(f"响应状态码: {response.status_code}")
            print(f"成功: {data.get('success')}")
            print(f"消息: {data.get('message')}")
            print(f"是否包含chart_url: {bool(data.get('chart_url'))}")
            print(f"是否包含stats: {bool(data.get('stats'))}")
        except json.JSONDecodeError:
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容(前500字符): {response.text[:500]}...")
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
except Exception as e:
    print(f"发送请求时发生错误: {e}")