import requests
import json
import time
import webbrowser
import os

# API基础URL
BASE_URL = 'http://localhost:5000/api'
FRONTEND_URL = 'http://localhost:8082'

# 测试注册用户
def test_register(username, password, email, phone):
    print(f"\n=== 测试用户注册: {username} ===")
    url = f'{BASE_URL}/user/register'
    data = {
        'username': username,
        'password': password,
        'email': email,
        'phone': phone,
        'role': 'user'
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        
        print(f"注册状态码: {response.status_code}")
        print(f"注册响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ 用户 {username} 注册成功")
            return True
        else:
            print(f"❌ 用户 {username} 注册失败")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 注册请求失败: {e}")
        return False

# 测试用户登录
def test_login(username, password):
    print(f"\n=== 测试用户登录: {username} ===")
    url = f'{BASE_URL}/user/login'
    data = {
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        
        print(f"登录状态码: {response.status_code}")
        print(f"登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ 用户 {username} 登录成功")
            # 获取用户信息和token
            user_info = result.get('userInfo')
            if user_info:
                print(f"用户信息: {json.dumps(user_info, ensure_ascii=False, indent=2)}")
            return True, user_info
        else:
            print(f"❌ 用户 {username} 登录失败")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录请求失败: {e}")
        return False, None

# 打开前端页面进行手动测试
def open_frontend_test():
    print("\n=== 打开前端页面进行手动测试 ===")
    print(f"1. 请先访问清除本地存储页面: {os.path.abspath('clear_local_storage.html')}")
    print(f"2. 然后访问前端登录页面: {FRONTEND_URL}/login")
    print("3. 使用注册的用户账户登录，验证路由权限是否正常工作")
    
    # 打开清除本地存储页面
    webbrowser.open('file://' + os.path.abspath('clear_local_storage.html'))
    # 等待2秒
    time.sleep(2)
    # 打开前端登录页面
    webbrowser.open(f'{FRONTEND_URL}/login')

# 检查后端服务是否正常运行
def check_backend_status():
    print("\n=== 检查后端服务状态 ===")
    try:
        response = requests.get(f'{BASE_URL}', timeout=3)
        print(f"后端服务状态码: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 后端服务连接失败: {e}")
        print("请确保后端服务正在运行: python src/models/server.py")
        return False

# 检查前端服务是否正常运行
def check_frontend_status():
    print("\n=== 检查前端服务状态 ===")
    try:
        response = requests.get(FRONTEND_URL, timeout=3)
        print(f"前端服务状态码: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 前端服务连接失败: {e}")
        print("请确保前端服务正在运行: npm run serve")
        return False

# 主测试函数
def main():
    print("开始测试完整的注册登录流程和路由权限验证功能...")
    
    # 检查前后端服务状态
    backend_ok = check_backend_status()
    frontend_ok = check_frontend_status()
    
    if not (backend_ok and frontend_ok):
        print("\n❌ 服务检查不通过，无法继续测试")
        return
    
    # 测试1: 注册一个新用户
    test_username = f"testuser_{int(time.time())}"
    test_password = "Test@12345"
    test_email = f"{test_username}@example.com"
    test_phone = f"139{time.time()%100000000:.0f}"
    
    print(f"\n测试用户信息:")
    print(f"用户名: {test_username}")
    print(f"密码: {test_password}")
    print(f"邮箱: {test_email}")
    print(f"手机号: {test_phone}")
    
    # 注册用户
    register_success = test_register(test_username, test_password, test_email, test_phone)
    
    # 如果注册成功，测试登录
    if register_success:
        # 等待1秒确保数据库操作完成
        time.sleep(1)
        
        # 测试正确密码登录
        login_success, user_info = test_login(test_username, test_password)
        
        if login_success:
            print("\n✅ 注册登录API功能测试通过！")
        
        # 打开前端页面进行手动测试
        open_frontend_test()
        
        print("\n=== 测试完成提示 ===")
        print("1. 请在浏览器中先清除本地存储")
        print("2. 然后使用新注册的账号登录前端系统")
        print("3. 验证是否能够成功访问需要登录权限的页面")
        print("4. 测试完成后，可以运行 view_users_table.py 查看用户数据")

if __name__ == "__main__":
    main()