@echo off
setlocal
echo Iniciando o devin...
echo.
where pwsh.exe >nul 2>&1
if %errorlevel% equ 0 (
    pwsh.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0devin-N.ps1" %*
    exit /b %ERRORLEVEL%
) else (
    echo pwsh.exe nao encontrado. Instale PowerShell 7 para usar este launcher.
    exit /b 1
)
