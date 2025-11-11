import requests
import json

# 测试物理健康对话接口的Python脚本

# 测试非流式接口
def test_physical_chat():
    url = "http://localhost:5000/health/chat/physical"
    
    # 测试数据
    test_data = {
        "message": "我最近经常感到疲劳，有什么建议吗？"
    }
    
    print("正在测试物理健康对话接口...")
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        # 发送POST请求
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print("响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print("-" * 50)
        print("响应内容:")
        
        # 尝试解析JSON响应
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            # 如果不是JSON格式，直接打印文本
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

# 测试流式接口
def test_physical_chat_stream():
    url = "http://localhost:5000/health/chat/physical/stream"
    
    # 测试数据
    test_data = {
        "message": "我想了解如何改善睡眠质量？"
    }
    
    print("\n" + "=" * 50)
    print("正在测试物理健康对话流式接口...")
    print(f"请求URL: {url}")
    print(f"请求数据: {json.dumps(test_data, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        # 发送POST请求（流式）
        with requests.post(url, json=test_data, stream=True, timeout=30) as response:
            print(f"状态码: {response.status_code}")
            print("响应头:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            print("-" * 50)
            print("流式响应内容:")
            
            # 逐行读取流数据
            for line in response.iter_lines():
                if line:
                    # 解码并打印接收到的数据
                    decoded_line = line.decode('utf-8')
                    print(decoded_line)
                    
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    # 测试非流式接口
    test_physical_chat()
    
    # 测试流式接口
    test_physical_chat_stream()
    
    print("\n" + "=" * 50)
    print("测试完成！")