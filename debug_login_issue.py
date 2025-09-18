import requests
import json
import time
import webbrowser
import os

# API基础URL
BASE_URL = 'http://localhost:5000/api'
FRONTEND_URL = 'http://localhost:8082'

# 获取所有用户信息（仅用于测试）
def get_all_users():
    try:
        # 读取view_users_table.py的实现方式
        import psycopg2
        conn = psycopg2.connect(
            host='10.208.112.57',
            database='quant_db',
            user='quant_user',
            password='quant_pass'
        )
        cursor = conn.cursor()
        cursor.execute("""SELECT id, username, email, phone, role 
                          FROM users ORDER BY created_at DESC LIMIT 5""")
        users = cursor.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'phone': user[3],
                'role': user[4]
            })
        return user_list
    except Exception as e:
        print(f"获取用户列表失败: {e}")
        # 如果数据库连接失败，返回模拟数据
        return [{'username': 'admin', 'role': 'admin'}]

# 测试后端登录API
def test_backend_login(username, password):
    print(f"\n=== 测试后端登录API: {username} ===")
    url = f'{BASE_URL}/user/login'
    data = {
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        
        print(f"登录状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 检查响应格式
        print("\n=== 响应格式分析 ===")
        if 'success' in result:
            print(f"✅ 响应包含success字段: {result['success']}")
        else:
            print("❌ 响应缺少success字段")
            
        if 'userInfo' in result:
            print(f"✅ 响应包含userInfo字段")
            user_info = result['userInfo']
            if 'token' in user_info:
                print(f"  ✅ userInfo包含token字段")
            else:
                print("  ❌ userInfo缺少token字段")
        else:
            print("❌ 响应缺少userInfo字段")
            
        if response.status_code == 200 and result.get('success'):
            print("\n✅ 后端登录API功能正常")
            return True, result
        else:
            print("\n❌ 后端登录API返回失败")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 登录请求失败: {e}")
        return False, None

# 检查前端登录页面
def check_frontend_login():
    print("\n=== 前端登录页面检查 ===")
    try:
        response = requests.get(f'{FRONTEND_URL}/login', timeout=3)
        print(f"前端登录页面状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 前端登录页面可访问")
            return True
        else:
            print("❌ 前端登录页面访问失败")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 前端服务连接失败: {e}")
        return False

# 主调试函数
def main():
    print("开始调试登录问题...")
    
    # 检查前端服务
    frontend_ok = check_frontend_login()
    if not frontend_ok:
        print("\n❌ 前端服务不可用，请确保已启动前端服务:")
        print("npm run serve")
        return
    
    # 获取最近的用户信息
    users = get_all_users()
    print("\n=== 系统中最近的用户 ===")
    for i, user in enumerate(users):
        print(f"{i+1}. 用户名: {user['username']}, 角色: {user['role']}")
        
    # 提示用户选择测试用户
    print("\n请选择一个用户进行登录测试，默认密码可能是：Test@12345")
    
    # 测试一个已知的用户
    if users:
        test_user = users[0]
        print(f"\n使用用户 '{test_user['username']}' 进行测试...")
        login_success, login_result = test_backend_login(test_user['username'], "Test@12345")
        
        print("\n=== 前端修复说明 ===")
        print("1. 已修复Login.vue中的响应处理逻辑")
        print("   - 之前: 使用 response.data.success 检查登录状态")
        print("   - 现在: 直接使用 result.success 检查登录状态")
        print("   - 原因: axios-config.js的响应拦截器会直接返回处理后的响应数据")
        
        print("\n=== 测试建议 ===")
        print("1. 首先清除浏览器本地存储:")
        print(f"   - 打开: {os.path.abspath('clear_local_storage.html')}")
        print('   - 点击"清除localStorage"按钮')
        print("2. 然后访问前端登录页面:")
        print(f"   - 地址: {FRONTEND_URL}/login")
        print("3. 使用以下测试用户登录:")
        print(f"   - 用户名: {test_user['username']}")
        print("   - 密码: Test@12345")
        print("4. 打开浏览器开发者工具(按F12)，切换到Console标签，观察是否有错误信息")
        
        # 自动打开清除本地存储页面
        webbrowser.open('file://' + os.path.abspath('clear_local_storage.html'))
        # 等待2秒
        time.sleep(2)
        # 自动打开前端登录页面
        webbrowser.open(f'{FRONTEND_URL}/login')
        
        print("\n=== 调试提示 ===")
        print("如果登录仍然失败，请在浏览器控制台查看以下内容：")
        print("1. 网络请求(Network标签)中登录请求的响应内容")
        print("2. 控制台(Console标签)中的错误信息")
        print("3. 确认localStorage中是否正确存储了token和userInfo")

if __name__ == "__main__":
    main()