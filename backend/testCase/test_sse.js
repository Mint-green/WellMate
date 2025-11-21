// 测试SSE流式接口的JavaScript脚本（Node.js版本）
const http = require('http');

// 设置请求选项
const options = {
  hostname: 'localhost',
  port: 5000,
  path: '/health/chat/text/stream',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
};

console.log('正在连接到SSE流式接口...');

// 发送HTTP请求
const req = http.request(options, (res) => {
  console.log(`成功连接，状态码: ${res.statusCode}`);
  console.log('------------------------------------');
  
  let lineCount = 0;
  const maxLines = 20; // 最多读取20行数据
  const startTime = Date.now();
  
  // 处理流数据
  res.on('data', (chunk) => {
    // 将接收到的数据转换为字符串
    const data = chunk.toString('utf-8');
    
    // 按行分割数据
    const lines = data.split('\n');
    
    // 处理每一行数据
    lines.forEach(line => {
      if (line.trim()) { // 只处理非空行
        console.log(`接收到: ${line}`);
        lineCount++;
      }
    });
    
    // 检查是否达到最大行数或超时
    if (lineCount >= maxLines || Date.now() - startTime > 10000) {
      console.log('\n达到读取限制或超时，结束测试。');
      console.log('------------------------------------');
      console.log(`测试完成，共接收 ${lineCount} 行数据。`);
      req.abort(); // 中止请求
    }
  });
  
  res.on('end', () => {
    console.log('\n连接已关闭。');
  });
});

// 处理错误
req.on('error', (e) => {
  console.error(`请求错误: ${e.message}`);
});

// 结束请求的写入操作
req.end();

// 设置超时处理
setTimeout(() => {
  console.log('\n测试超时，自动结束。');
  req.abort();
}, 15000); // 15秒后自动超时