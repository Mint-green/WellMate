@echo off
setlocal enabledelayedexpansion

:: Configuration reading script - Windows version
:: Usage: call read_config.bat <config_key> <return_var>

set CONFIG_FILE=%~dp0docker_build.conf
set KEY_TO_FIND=%~1
set RETURN_VAR=%~2

:: Check if config file exists
if not exist "%CONFIG_FILE%" (
    exit /b 1
)

:: Read config file and find key-value
set FOUND_VALUE=
for /f "usebackq tokens=1,2 delims==" %%A in ("%CONFIG_FILE%") do (
    set LINE_KEY=%%A
    set LINE_VALUE=%%B
    
    :: Remove leading and trailing spaces
    for /f "tokens=*" %%K in ("!LINE_KEY!") do set LINE_KEY=%%K
    for /f "tokens=*" %%V in ("!LINE_VALUE!") do set LINE_VALUE=%%V
    
    :: Skip empty lines and comment lines
    if not "!LINE_KEY!"=="" (
        if not "!LINE_KEY:~0,1!"=="#" (
            if "!LINE_KEY!"=="%KEY_TO_FIND%" (
                set FOUND_VALUE=!LINE_VALUE!
                goto :FOUND
            )
        )
    )
)

:: If key not found
if "%RETURN_VAR%"=="" (
    echo !FOUND_VALUE!
) else (
    endlocal & set %RETURN_VAR%=%FOUND_VALUE%
)
exit /b 0

:FOUND
if "%RETURN_VAR%"=="" (
    echo !FOUND_VALUE!
) else (
    endlocal & set %RETURN_VAR%=%FOUND_VALUE%
)
exit /b 0