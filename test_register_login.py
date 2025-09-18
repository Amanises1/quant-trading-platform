import requests
import json
import time

# API基础URL
BASE_URL = 'http://localhost:5000/api'

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

# 主测试函数
def main():
    print("开始测试注册和登录功能...")
    
    # 测试1: 注册一个新用户
    test_username = f"testuser_{int(time.time())}"
    test_password = "Test@12345"
    test_email = f"{test_username}@example.com"
    test_phone = f"139{time.time()%100000000:.0f}"
    
    # 注册用户
    register_success = test_register(test_username, test_password, test_email, test_phone)
    
    # 如果注册成功，测试登录
    if register_success:
        # 等待1秒确保数据库操作完成
        time.sleep(1)
        
        # 测试正确密码登录
        login_success, user_info = test_login(test_username, test_password)
        
        # 测试错误密码登录
        if login_success:
            print("\n=== 测试错误密码登录 ===")
            wrong_pass_success, _ = test_login(test_username, "wrong_password")
    
    # 测试2: 尝试注册已存在的用户名
    print("\n=== 测试注册已存在的用户名 ===")
    duplicate_success = test_register("admin", "Admin@12345", "admin_duplicate@example.com", "13800138001")
    
    print("\n测试完成！请运行 view_users_table.py 查看更新后的用户表数据")

if __name__ == "__main__":
    main()