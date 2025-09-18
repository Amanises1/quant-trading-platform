import requests
import json
import time

# 配置测试参数
base_url = 'http://localhost:8080'
test_user = 'testuser_1758182219'
test_password = 'Test@12345'
temp_new_password = 'Test@54321'

# 登录获取token
def login(username, password):
    print("正在登录用户...")
    login_url = f'{base_url}/api/user/login'
    payload = {
        'username': username,
        'password': password,
        'remember': False
    }
    
    response = requests.post(login_url, json=payload)
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            token = data.get('userInfo', {}).get('token')
            user_id = data.get('userInfo', {}).get('id', '1')
            print(f"登录成功，用户ID: {user_id}, Token: {token}")
            return token, user_id
    
    print("登录失败")
    return None, None

# 测试修改密码
def test_change_password(token, user_id, current_password, new_password):
    if not token:
        print("未获取到有效token，无法测试修改密码")
        return False
    
    print("\n正在测试修改密码...")
    change_password_url = f'{base_url}/api/user/change-password'
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'user_id': user_id,
        'current_password': current_password,
        'new_password': new_password,
        'confirm_password': new_password
    }
    
    response = requests.post(change_password_url, json=payload, headers=headers)
    print(f"修改密码响应状态码: {response.status_code}")
    print(f"修改密码响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"后端响应success标志: {data.get('success')}")
        print(f"后端响应message: {data.get('message')}")
        return data.get('success')
    
    print("修改密码请求失败")
    return False

# 验证修改后的密码能否登录
def verify_new_password(username, old_password, new_password):
    print(f"\n验证旧密码登录...")
    old_token, _ = login(username, old_password)
    print(f"旧密码登录结果: {'成功' if old_token else '失败'}")
    
    print(f"\n验证新密码登录...")
    new_token, _ = login(username, new_password)
    print(f"新密码登录结果: {'成功' if new_token else '失败'}")
    
    return new_token is not None

# 主函数
def main():
    print("===== 密码修改功能测试 =====")
    
    # 1. 登录获取token
    token, user_id = login(test_user, test_password)
    if not token:
        print("登录失败，无法继续测试")
        return
    
    # 2. 测试修改密码
    change_success = test_change_password(token, user_id, test_password, temp_new_password)
    
    # 3. 验证密码修改是否成功
    if change_success:
        print("\n密码修改功能后端验证成功！")
        # 验证新密码是否有效
        verify_new_password(test_user, test_password, temp_new_password)
        
        # 4. 恢复原始密码（确保测试不会影响系统状态）
        # 使用新密码登录
        new_token, _ = login(test_user, temp_new_password)
        if new_token:
            print("\n正在恢复原始密码...")
            test_change_password(new_token, user_id, temp_new_password, test_password)
            print("原始密码恢复完成")
        
        print("\n前端修改建议：")
        print("1. 确保已清除浏览器缓存和localStorage")
        print("2. 使用测试账号登录系统")
        print("3. 前往个人信息页面尝试修改密码")
        print("4. 修改已完成，现在前端应该能正确显示密码修改的成功或失败状态")
    else:
        print("\n密码修改功能测试失败")
    
    print("\n===== 测试完成 =====")

if __name__ == "__main__":
    main()