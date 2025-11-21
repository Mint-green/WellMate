import requests
import sys
import time

# 测试SSE流式接口的Python脚本

url = "http://localhost:5000/health/chat/text/stream"

print("正在连接到SSE流式接口...")

# 使用stream=True参数保持连接并流式获取数据
with requests.post(url, stream=True, timeout=10) as response:
    if response.status_code == 200:
        print(f"成功连接，状态码: {response.status_code}")
        print("------------------------------------")
        
        line_count = 0
        max_lines = 20  # 最多读取20行数据
        start_time = time.time()
        
        # 逐行读取流数据
        for line in response.iter_lines():
            if line:
                # 解码并打印接收到的数据
                decoded_line = line.decode('utf-8')
                print(f"接收到: {decoded_line}")
                line_count += 1
            
            # 检查是否达到最大行数或超时
            if line_count >= max_lines or time.time() - start_time > 10:
                print("\n达到读取限制或超时，结束测试。")
                break
        
        print("------------------------------------")
        print(f"测试完成，共接收 {line_count} 行数据。")
    else:
        print(f"连接失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")