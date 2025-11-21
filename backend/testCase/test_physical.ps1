# 测试物理健康对话接口的PowerShell脚本

Write-Host "正在测试物理健康对话接口..." -ForegroundColor Green

# 测试非流式接口
Write-Host "`n测试非流式接口:" -ForegroundColor Yellow
$url = "http://localhost:5000/health/chat/physical"

# 测试数据
$body = @{
    message = "我最近经常感到疲劳，有什么建议吗？"
} | ConvertTo-Json

Write-Host "请求URL: $url" -ForegroundColor Cyan
Write-Host "请求数据: $body" -ForegroundColor Cyan

try {
    # 发送POST请求
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "响应内容:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "请求失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试流式接口
Write-Host "`n测试流式接口:" -ForegroundColor Yellow
$streamUrl = "http://localhost:5000/health/chat/physical/stream"

# 测试数据
$streamBody = @{
    message = "我想了解如何改善睡眠质量？"
} | ConvertTo-Json

Write-Host "请求URL: $streamUrl" -ForegroundColor Cyan
Write-Host "请求数据: $streamBody" -ForegroundColor Cyan

try {
    Write-Host "流式响应内容:" -ForegroundColor Cyan
    
    # 发送POST请求（流式）
    $response = Invoke-RestMethod -Uri $streamUrl -Method Post -Body $streamBody -ContentType "application/json" -TimeoutSec 30
    
    # 输出响应
    $response
} catch {
    Write-Host "请求失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n测试完成！" -ForegroundColor Green