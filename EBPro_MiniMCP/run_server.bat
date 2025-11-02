@echo off
REM Запуск EBPro Mini-MCP (FastAPI + Uvicorn)
setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%.."
set PROJECT_DIR=%CD%\EBPro_MiniMCP

if exist "%PROJECT_DIR%\.venv" (
    call "%PROJECT_DIR%\.venv\Scripts\activate" 2>nul
) else (
    echo [INFO] Віртуальне середовище не знайдено у "%PROJECT_DIR%\.venv". Створіть його вручну або активуйте інше.
)

python -m uvicorn EBPro_MiniMCP.mcp_server:app --host 0.0.0.0 --port 8000
popd
