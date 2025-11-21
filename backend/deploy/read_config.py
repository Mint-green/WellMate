#!/usr/bin/env python3
import os
import sys

def read_acr_config():
    """读取ACR配置文件"""
    config_file = os.path.join(os.path.dirname(__file__), 'docker_acr.conf')
    
    if not os.path.exists(config_file):
        print(f"错误：配置文件不存在: {config_file}")
        sys.exit(1)
    
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除值中的引号（如果有）
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    config[key] = value
                else:
                    print(f"警告：第{line_num}行格式不正确，跳过: {line}")
        
        # 验证必需字段
        required_fields = ['acr_repo', 'acr_user', 'acr_registry', 'container_name', 'port']
        for field in required_fields:
            if field not in config:
                print(f"错误：配置文件中缺少必需字段: {field}")
                sys.exit(1)
        
        return config
    except Exception as e:
        print(f"错误：读取配置文件失败: {e}")
        sys.exit(1)

def get_config_value(key):
    """获取指定配置值"""
    config = read_acr_config()
    return config.get(key, '')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python read_config.py <config_key>")
        print("可用配置键: acr_repo, acr_user, acr_registry, container_name, port")
        sys.exit(1)
    
    key = sys.argv[1]
    value = get_config_value(key)
    print(value)