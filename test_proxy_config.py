import requests
import time

def test_api_proxy():
    """测试前端API代理配置是否正常工作"""
    try:
        print("\n===== 测试API代理配置 ====")
        print("1. 测试直接访问后端API (预期成功)")
        # 直接访问后端API
        backend_url = 'http://localhost:5000/api/visualization/generate'
        backend_response = requests.post(backend_url, json={
            'chart_type': 'price_chart',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'stock_symbol': '000001',
            'config': {'title': '测试图表'}
        })
        print(f"后端API响应状态码: {backend_response.status_code}")
        if backend_response.status_code == 200:
            print("✓ 后端API直接访问成功")
        else:
            print(f"✗ 后端API直接访问失败，状态码: {backend_response.status_code}")
            return False

        # 等待前端服务器完全启动
        print("\n等待前端服务器初始化...")
        time.sleep(2)

        print("\n2. 测试通过前端代理访问API (预期成功)")
        # 通过前端代理访问API
        frontend_proxy_url = 'http://localhost:8081/api/visualization/generate'
        frontend_response = requests.post(frontend_proxy_url, json={
            'chart_type': 'price_chart',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'stock_symbol': '000001',
            'config': {'title': '测试图表'}
        })
        print(f"前端代理API响应状态码: {frontend_response.status_code}")
        
        if frontend_response.status_code == 200:
            print("✓ 前端代理API访问成功！")
            # 检查响应内容
            response_data = frontend_response.json()
            if response_data.get('success'):
                print("✓ API返回数据正常，success=True")
                if 'chart_url' in response_data or 'chart_html' in response_data:
                    print("✓ 成功获取到图表数据")
                return True
            else:
                print(f"✗ API返回success=False: {response_data.get('message')}")
                return False
        else:
            print(f"✗ 前端代理API访问失败，状态码: {frontend_response.status_code}")
            print(f"   响应内容: {frontend_response.text}")
            return False
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_api_proxy()
    print("\n===== 测试结果总结 =====")
    if success:
        print("✅ API代理配置测试通过！")
        print("   现在前端应用应该可以正常访问后端API，不再出现404错误。")
    else:
        print("❌ API代理配置测试失败！")
        print("   请检查vue.config.js文件中的代理配置是否正确，以及后端服务器是否正常运行。")