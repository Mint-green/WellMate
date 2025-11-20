#!/usr/bin/env python3
"""
测试/mental/chat接口是否正常工作
"""

import requests
import json

def test_mental_chat_with_valid_token():
    """测试带有效token的mental/chat接口"""
    
    # 首先需要获取一个有效的token
    login_url = 'http://localhost:5000/api/v1/auth/login'
    login_data = {
        'username': 'demo_user',
        'password': 'demo_pass'
    }
    
    print('=== 获取有效token ===')
    try:
        login_response = requests.post(login_url, json=login_data, timeout=10)
        print(f'登录状态码: {login_response.status_code}')
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('status') == 'success':
                access_token = login_result['data']['access_token']
                print(f'✅ 成功获取token: {access_token[:20]}...')
                
                # 测试mental/chat接口
                print('\n=== 测试mental/chat接口（带有效token） ===')
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "text": "你好，我最近感觉压力很大，应该怎么办？"
                }
                
                try:
                    response = requests.post(
                        "http://localhost:5000/api/v1/health/mental/chat",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    print(f'状态码: {response.status_code}')
                    
                    if response.status_code == 200:
                        result = response.json()
                        print('✅ 接口调用成功！')
                        print(f'响应状态: {result.get("status")}')
                        print(f'消息: {result.get("message")}')
                        
                        if 'data' in result:
                            data_content = result['data']
                            print(f'是否新会话: {data_content.get("is_new_session")}')
                            print(f'session_id: {data_content.get("session_id")}')
                            print(f'AI响应长度: {len(data_content.get("response", ""))} 字符')
                    else:
                        print(f'❌ 请求失败: {response.text}')
                        
                except requests.exceptions.Timeout:
                    print('❌ 请求超时')
                except Exception as e:
                    print(f'❌ 请求异常: {e}')
                    
            else:
                print(f'❌ 登录失败: {login_result.get("message")}')
        else:
            print(f'❌ 登录失败: {login_response.text}')
            
    except Exception as e:
        print(f'❌ 登录请求异常: {e}')

def test_mental_chat_without_token():
    """测试不带token的mental/chat接口"""
    
    print('\n=== 测试mental/chat接口（不带token） ===')
    
    data = {
        "text": "你好，我最近感觉压力很大，应该怎么办？"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/v1/health/mental/chat",
            json=data,
            timeout=10
        )
        
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 401:
            print('✅ 正确返回401未授权错误')
        else:
            print(f'❌ 预期401但返回: {response.status_code}')
            print(f'响应内容: {response.text}')
            
    except Exception as e:
        print(f'❌ 请求异常: {e}')

if __name__ == "__main__":
    print("开始测试/mental/chat接口...")
    
    # 测试不带token的情况
    test_mental_chat_without_token()
    
    # 测试带有效token的情况
    test_mental_chat_with_valid_token()
    
    print("\n测试完成！")