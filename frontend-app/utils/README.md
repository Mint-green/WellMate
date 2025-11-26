# 环境配置说明

## 概述

本项目使用环境配置来管理不同环境下的API地址和其他配置项。通过环境配置，可以轻松地在开发、测试和生产环境之间切换，而无需修改代码。

## 配置文件

- `env-config.uts`: 环境配置文件，包含不同环境的配置项

## 环境类型

1. **development**: 开发环境，API地址为 `http://localhost:5000`
2. **production**: 生产环境，API地址为 `http://47.113.206.45:5000`
3. **test**: 测试环境，API地址为 `http://47.113.206.45:5000`

## 使用方法

在需要使用环境配置的文件中引入：

```typescript
import envConfig from '@/utils/env-config.uts'

// 获取环境配置
const config = envConfig.getEnvConfig()

// 使用配置项
const baseURL = config.baseURL
```

## 环境切换

环境切换是自动进行的，系统会根据当前运行环境自动选择对应的配置：

- 在本地开发（localhost或127.0.0.1）时使用开发环境配置
- 在其他情况下默认使用生产环境配置

## 自定义环境配置

如果需要添加新的环境或修改现有环境配置，可以修改 `env-config.uts` 文件中的 `configs` 对象。