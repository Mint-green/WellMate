#!/usr/bin/env python3
"""
配置文件读取脚本
支持读取docker_build.conf配置文件
"""

import os
import sys

def read_config(key, config_file=None):
    """
    从配置文件中读取指定键的值
    
    Args:
        key: 要读取的配置键
        config_file: 配置文件路径，默认为docker_build.conf
    
    Returns:
        配置值，如果键不存在或文件不存在则返回None
    """
    if config_file is None:
        # 获取脚本所在目录的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, "docker_build.conf")
    
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_file):
            return None
        
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析配置
        for line in lines:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 解析键值对
            if '=' in line:
                config_key, config_value = line.split('=', 1)
                config_key = config_key.strip()
                config_value = config_value.strip()
                
                if config_key == key:
                    return config_value
        
        return None
    
    except Exception as e:
        # 静默处理错误，返回None
        return None

def main():
    """命令行入口函数"""
    if len(sys.argv) != 2:
        print("用法: python read_config.py <config_key>", file=sys.stderr)
        sys.exit(1)
    
    key = sys.argv[1]
    value = read_config(key)
    
    if value is not None:
        print(value)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()