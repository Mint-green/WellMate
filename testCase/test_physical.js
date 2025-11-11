// 测试物理健康对话接口的Node.js脚本

const https = require('https');
const http = require('http');

// 测试非流式接口
function testPhysicalChat() {
    const url = 'http://localhost:5000/health/chat/physical';
    
    // 测试数据
    const postData = JSON.stringify({
        message: '我最近经常感到疲劳，有什么建议吗？'
    });
    
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };
    
    console.log('正在测试物理健康对话接口...');
    console.log(`请求URL: ${url}`);
    console.log(`请求数据: ${postData}`);
    console.log('-'.repeat(50));
    
    const req = http.request(url, options, (res) => {
        let data = '';
        
        console.log(`状态码: ${res.statusCode}`);
        console.log('响应头:');
        for (let key in res.headers) {
            console.log(`  ${key}: ${res.headers[key]}`);
        }
        
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            console.log('-'.repeat(50));
            console.log('响应内容:');
            try {
                const jsonData = JSON.parse(data);
                console.log(JSON.stringify(jsonData, null, 2));
            } catch (e) {
                console.log(data);
            }
        });
    });
    
    req.on('error', (e) => {
        console.error(`请求失败: ${e.message}`);
    });
    
    req.write(postData);
    req.end();
}

// 测试流式接口
function testPhysicalChatStream() {
    const url = 'http://localhost:5000/health/chat/physical/stream';
    
    // 测试数据
    const postData = JSON.stringify({
        message: '我想了解如何改善睡眠质量？'
    });
    
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };
    
    console.log('\n' + '='.repeat(50));
    console.log('正在测试物理健康对话流式接口...');
    console.log(`请求URL: ${url}`);
    console.log(`请求数据: ${postData}`);
    console.log('-'.repeat(50));
    
    const req = http.request(url, options, (res) => {
        console.log(`状态码: ${res.statusCode}`);
        console.log('响应头:');
        for (let key in res.headers) {
            console.log(`  ${key}: ${res.headers[key]}`);
        }
        
        console.log('-'.repeat(50));
        console.log('流式响应内容:');
        
        res.on('data', (chunk) => {
            console.log(chunk.toString());
        });
        
        res.on('end', () => {
            console.log('\n流式响应结束');
        });
    });
    
    req.on('error', (e) => {
        console.error(`请求失败: ${e.message}`);
    });
    
    req.write(postData);
    req.end();
}

// 执行测试
setTimeout(() => {
    testPhysicalChat();
    
    setTimeout(() => {
        testPhysicalChatStream();
        
        setTimeout(() => {
            console.log('\n' + '='.repeat(50));
            console.log('测试完成！');
        }, 1000);
    }, 1000);
}, 1000);