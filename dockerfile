FROM python:3.9-slim

# 设置构建参数用于注入版本信息
ARG BUILD_TIMESTAMP="unknown"
ARG BUILD_TAG="unknown"

# 设置环境变量，应用运行时可以读取
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP}
ENV BUILD_TAG=${BUILD_TAG}

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
COPY . .

# 创建版本信息文件
RUN echo "Build Timestamp: ${BUILD_TIMESTAMP}" > /app/version.txt && \
    echo "Build Tag: ${BUILD_TAG}" >> /app/version.txt && \
    echo "Build Date: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" >> /app/version.txt

EXPOSE 5000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]