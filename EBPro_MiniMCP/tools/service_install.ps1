<#
.SYNOPSIS
    Приклад встановлення EBPro Mini-MCP як Windows-сервісу через NSSM.

.DESCRIPTION
    Запустіть скрипт у PowerShell від імені адміністратора. Перед виконанням
    відредагуйте змінні нижче: шлях до NSSM, Python та директорії проєкту.

.NOTES
    NSSM можна завантажити з https://nssm.cc/. Після встановлення оновіть змінну $NssmPath.
#>

$ErrorActionPreference = 'Stop'

# === НАЛАШТУВАННЯ ===
$ProjectDir = "C:\\Automation\\EBPro_MiniMCP"
$PythonExe = "$ProjectDir\\.venv\\Scripts\\python.exe"
$Module = "uvicorn"
$AppModule = "mcp_server:app"
$LogFile = "$ProjectDir\\logs\\service.log"
$NssmPath = "C:\\Tools\\nssm.exe"
$ServiceName = "EBProMiniMCP"
$DisplayName = "EBPro Mini-MCP"
$Description = "HTTP-агент для автоматизації EasyBuilder Pro"
$Port = 8000

# === УСТАНОВКА СЕРВІСУ ===
if (-not (Test-Path $NssmPath)) {
    throw "Не знайдено NSSM за шляхом $NssmPath."
}

if (-not (Test-Path $PythonExe)) {
    throw "Не знайдено Python у $PythonExe. Запустіть встановлення залежностей."
}

$Arguments = "-m $Module $AppModule --host 0.0.0.0 --port $Port"

& $NssmPath install $ServiceName $PythonExe $Arguments
& $NssmPath set $ServiceName DisplayName $DisplayName
& $NssmPath set $ServiceName Description $Description
& $NssmPath set $ServiceName AppDirectory $ProjectDir
& $NssmPath set $ServiceName AppStdout $LogFile
& $NssmPath set $ServiceName AppStderr $LogFile
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

Write-Host "Сервіс $ServiceName встановлено. Використайте 'nssm start $ServiceName' для запуску." -ForegroundColor Green
