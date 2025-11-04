@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 从配置文件读取ACR仓库配置
call %~dp0read_config.bat acr_repo ACR_REPO
call %~dp0read_config.bat acr_user ACR_USER
call %~dp0read_config.bat acr_registry ACR_REGISTRY
call %~dp0read_config.bat acr_password ACR_PASSWORD
call %~dp0read_config.bat latest_tag LATEST_TAG

:: 验证配置是否成功读取
if "%ACR_REPO%"=="" (
    echo 错误：无法读取配置文件或配置信息不完整。
    echo 请检查 docker_build.conf 文件是否存在且格式正确。
    echo 可以参考 docker_build.conf.example 文件创建配置文件。
    pause
    exit /b 1
)

if "%ACR_USER%"=="" (
    echo 错误：无法读取配置文件或配置信息不完整。
    echo 请检查 docker_build.conf 文件是否存在且格式正确。
    echo 可以参考 docker_build.conf.example 文件创建配置文件。
    pause
    exit /b 1
)

if "%ACR_REGISTRY%"=="" (
    echo 错误：无法读取配置文件或配置信息不完整。
    echo 请检查 docker_build.conf 文件是否存在且格式正确。
    echo 可以参考 docker_build.conf.example 文件创建配置文件。
    pause
    exit /b 1
)

if "%ACR_PASSWORD%"=="" (
    echo 错误：无法读取配置文件或配置信息不完整。
    echo 请检查 docker_build.conf 文件是否存在且格式正确。
    echo 可以参考 docker_build.conf.example 文件创建配置文件。
    pause
    exit /b 1
)

if "%LATEST_TAG%"=="" (
    echo 错误：无法读取配置文件或配置信息不完整。
    echo 请检查 docker_build.conf 文件是否存在且格式正确。
    echo 可以参考 docker_build.conf.example 文件创建配置文件。
    pause
    exit /b 1
)

:: 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未安装Docker或Docker服务未启动。
    echo 请先安装Docker并启动Docker服务后再尝试。
    pause
    exit /b 1
)

:: 智能确定项目根目录
:: 如果当前目录是build目录，则项目根目录是上一级
:: 如果当前目录是项目根目录，则直接使用当前目录
if /i "%CD:~-5%"=="build" (
    set "PROJECT_ROOT=%~dp0.."
) else (
    set "PROJECT_ROOT=%CD%"
)
echo 检测到项目根目录: %PROJECT_ROOT%

:: 生成时间戳（格式：YYYYMMDDHHMM）
for /f "usebackq tokens=1" %%i in (`powershell -Command "Get-Date -Format 'yyyyMMddHHmm'"`) do set TIMESTAMP=%%i

:: 自动生成序号（查找当前时间戳下的最大序号并+1）
set SEQ=1
for /f "tokens=*" %%a in ('docker images --format "{{.Tag}}" %ACR_REPO% 2^>nul ^| findstr "%TIMESTAMP%" ^| sort /r') do (
    if not defined LAST_TAG (
        set LAST_TAG=%%a
        set /a SEQ=!LAST_TAG:~12! + 1
        if !SEQ! gtr 9 set SEQ=9
    )
)

:: 版本信息注入配置
set "VERSION_FILE=%PROJECT_ROOT%\version.info"
for /f "usebackq tokens=*" %%d in (`powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set BUILD_DATE=%%d
for /f "tokens=*" %%c in ('git rev-parse --short HEAD 2^>nul') do set GIT_COMMIT=%%c
if "%GIT_COMMIT%"=="" set GIT_COMMIT=unknown
for /f "tokens=*" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set GIT_BRANCH=%%b
if "%GIT_BRANCH%"=="" set GIT_BRANCH=unknown

:: 设置版本标签
set VERSION_TAG=%TIMESTAMP%%SEQ%
set FULL_TAG=%ACR_REPO%:%VERSION_TAG%
set LATEST_FULL_TAG=%ACR_REPO%:%LATEST_TAG%

:: 创建版本信息文件
echo 创建版本信息...
echo REPO_PATH=%ACR_REPO% > %VERSION_FILE%
echo BUILD_TIMESTAMP=%TIMESTAMP% >> %VERSION_FILE%
echo BUILD_TAG=%VERSION_TAG% >> %VERSION_FILE%
echo BUILD_DATE=%BUILD_DATE% >> %VERSION_FILE%
echo GIT_COMMIT=%GIT_COMMIT% >> %VERSION_FILE%
echo GIT_BRANCH=%GIT_BRANCH% >> %VERSION_FILE%

:: 构建Docker镜像（注入版本信息）
echo 正在构建Docker镜像（注入版本信息）...
echo 如果网络连接较慢，可能需要几分钟...

:: 使用重试机制和不同构建方法尝试构建
set MAX_RETRIES=3
set RETRY_COUNT=0

:BUILD_RETRY
set /a RETRY_COUNT=RETRY_COUNT+1
echo 第 %RETRY_COUNT% 次尝试（共 %MAX_RETRIES% 次）...

:: 根据重试次数尝试不同的构建方法
if %RETRY_COUNT% equ 1 (
    echo 使用标准Docker构建...
    docker build --build-arg BUILD_TIMESTAMP="%TIMESTAMP%" --build-arg BUILD_TAG="%VERSION_TAG%" -t "%FULL_TAG%" "%PROJECT_ROOT%"
) else if %RETRY_COUNT% equ 2 (
    echo 尝试启用BuildKit...
    set DOCKER_BUILDKIT=1
    docker build --build-arg BUILD_TIMESTAMP="%TIMESTAMP%" --build-arg BUILD_TAG="%VERSION_TAG%" -t "%FULL_TAG%" "%PROJECT_ROOT%"
) else (
    echo 尝试无缓存和BuildKit...
    set DOCKER_BUILDKIT=1
    docker build --no-cache --build-arg BUILD_TIMESTAMP="%TIMESTAMP%" --build-arg BUILD_TAG="%VERSION_TAG%" -t "%FULL_TAG%" "%PROJECT_ROOT%"
)

if %errorlevel% equ 0 (
    echo 第 %RETRY_COUNT% 次尝试构建成功。
    goto :BUILD_SUCCESS
)

if %RETRY_COUNT% lss %MAX_RETRIES% (
    echo 第 %RETRY_COUNT% 次尝试构建失败。10秒后重试...
    echo 当前问题：DNS解析或网络连接问题
    echo 可用镜像源：DaoCloud, 1Panel
    timeout /t 10 /nobreak >nul
    goto :BUILD_RETRY
) else (
    echo 错误：镜像构建在 %MAX_RETRIES% 次尝试后失败。
    echo.
    echo 网络诊断：
    echo - Docker镜像加速器已配置但DNS解析失败
    echo - 镜像源: https://docker.mirrors.ustc.edu.cn
    echo.
    echo 立即解决方案：
    echo 1. 检查网络连接和DNS设置
    echo 2. 尝试使用VPN（如果在中国大陆）
    echo 3. 等待网络恢复后重试
    echo 4. 临时禁用镜像加速器: 在Docker Desktop设置中移除registry-mirrors配置
    echo.
    echo 测试网络连通性：
    echo   ping docker.mirrors.ustc.edu.cn
    echo   ping hub-mirror.c.163.com
    pause
    exit /b 1
)

:BUILD_SUCCESS

:: 为latest标签也构建一个镜像（使用相同的版本信息）
echo 为latest标签构建镜像...
docker build --build-arg BUILD_TIMESTAMP="%TIMESTAMP%" --build-arg BUILD_TAG="%VERSION_TAG%" --build-arg IMAGE_ID="%FULL_TAG%" -t "%LATEST_FULL_TAG%" "%PROJECT_ROOT%"

echo 镜像构建成功。

:: 检查是否已登录ACR仓库
echo 检查ACR仓库登录状态...
echo 尝试登录到ACR注册表：%ACR_REGISTRY%
echo %ACR_PASSWORD% | docker login %ACR_REGISTRY% --username %ACR_USER% --password-stdin
if %ERRORLEVEL% neq 0 (
    echo 警告：ACR登录失败，可能是网络/DNS问题。
    echo 在某些网络环境中这是正常的。
    echo 镜像构建成功，但推送到ACR的操作被跳过。
    echo 您可以在网络可用时手动推送镜像。
    echo.
    echo 稍后手动推送的命令：
    echo docker tag well-mate-backend:%LATEST_TAG% %ACR_REPO%:%LATEST_TAG%
    echo docker push %ACR_REPO%:%LATEST_TAG%
    echo.
    echo 按任意键继续...
    pause >nul
    exit /b 0
)

:: 推送镜像到ACR
echo 推送镜像到ACR...

:: 给最新的镜像打上latest标签
docker tag %FULL_TAG% %LATEST_FULL_TAG%

echo 推送版本标签：%FULL_TAG%
docker push %FULL_TAG%
if %errorlevel% neq 0 (
    echo 错误：版本标签镜像推送失败。
    pause
    exit /b 1
)

echo 推送最新标签：%LATEST_FULL_TAG%
docker push %LATEST_FULL_TAG%
if %errorlevel% neq 0 (
    echo 错误：最新标签镜像推送失败。
    pause
    exit /b 1
)

echo 成功推送版本：%VERSION_TAG%

echo.
echo ====================================================
echo 构建和推送完成！
echo 镜像标签：%FULL_TAG%
echo 最新镜像标签：%LATEST_FULL_TAG%
echo 建议将此版本号记录在部署文档中。
echo ====================================================

pause