# 测试SSE流式接口的PowerShell脚本

# 设置请求URL
$url = "http://localhost:5000/health/chat/text/stream"

# 创建HTTP请求对象
$request = [System.Net.HttpWebRequest]::Create($url)
$request.Method = "POST"
$request.ContentType = "application/json"
$request.Timeout = -1  # 无限超时

# 发送请求并处理响应
try {
    $response = $request.GetResponse()
    $stream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    
    Write-Host "正在接收SSE流数据..."
    Write-Host "------------------------------------"
    
    # 持续读取流数据，设置读取次数上限
    $counter = 0
    $maxLines = 20  # 最多读取20行
    $startTime = Get-Date
    
    while (-not $reader.EndOfStream -and $counter -lt $maxLines) {
        $line = $reader.ReadLine()
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            Write-Host $line
            $counter++
        }
        
        # 添加超时检查，防止无限等待
        $currentTime = Get-Date
        if (($currentTime - $startTime).TotalSeconds -gt 10) {
            Write-Host "
读取超时，已接收 $counter 行数据。"
            break
        }
    }
    
    Write-Host "------------------------------------"
    Write-Host "流数据接收完成，共接收 $counter 行数据。"
} 
catch {
    Write-Host "发生错误: $($_.Exception.Message)"
} 
finally {
    # 确保释放资源
    if ($reader -ne $null) { $reader.Close() }
    if ($stream -ne $null) { $stream.Close() }
    if ($response -ne $null) { $response.Close() }
}