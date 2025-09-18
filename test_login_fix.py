import requests
import json

# API基础URL
BASE_URL = 'http://localhost:5000/api'

# 测试登录函数
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
        
        if response.status_code == 200:
            print(f"✅ 后端登录请求成功")
            # 检查响应格式是否符合前端期望
            if 'success' in result and 'userInfo' in result:
                print(f"✅ 响应格式正确，包含success和userInfo字段")
                if result.get('success'):
                    print(f"✅ 登录成功标志为true")
                else:
                    print(f"❌ 登录成功标志为false")
            else:
                print(f"❌ 响应格式不符合前端期望，缺少必要字段")
        else:
            print(f"❌ 后端登录请求失败")
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录请求失败: {e}")

# 主函数
def main():
    print("开始测试登录功能修复...")
    
    # 使用之前测试过的用户账户
    test_login("testuser_1758182219", "Test@12345")
    
    print("\n=== 登录功能修复测试完成 ===")
    print("请在浏览器中尝试登录，验证修复是否生效")
    print("1. 打开清除本地存储页面: clear_local_storage.html")
    print("2. 然后访问前端登录页面: http://localhost:8082/login")
    print("3. 使用测试账号登录，验证是否成功")

if __name__ == "__main__":
    main()